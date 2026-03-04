import csv
import io
import logging
import statistics
import uuid
from datetime import datetime
from fastapi import HTTPException, UploadFile, status

from app.core import data_store as db

logger = logging.getLogger(__name__)

# In-memory store for raw file bytes {file_id: bytes}
_FILE_CONTENTS: dict[str, bytes] = {}
_FILE_NAMES: dict[str, str] = {}   # {file_id: original_filename}

# Grade-bucket colors (A → F)
_GRADE_COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"]

# Known column-name sets for classification
_NAME_ALIASES = {"name", "student", "student_name", "student name", "sname", "studentname"}

# HIGH priority roll aliases — matched first (explicit roll/reg identifiers)
_ROLL_ALIASES_HIGH = {
    "roll", "roll_no", "rollno", "roll no", "roll number", "rollnumber",
    "reg", "reg_no", "regno", "student_id",
}
# LOW priority roll aliases — matched only if no high-priority match found
# (these are often just sequential index columns)
_ROLL_ALIASES_LOW = {"sno", "s.no", "serial", "id", "no", "sl.no", "sl no", "sr.no", "sr no"}
_ROLL_ALIASES = _ROLL_ALIASES_HIGH | _ROLL_ALIASES_LOW

_MARKS_ALIASES = {
    "marks", "score", "scores", "total", "total_marks", "totalmarks",
    "final", "final_marks", "finalmarks", "grade_points", "obtained",
    "marks_obtained", "result", "exam", "exam_marks", "marks/100",
    "grand total", "grandtotal", "overall", "aggregate", "sum",
}


# ── Column classification helpers ─────────────────────────────────────────────

def _clean_header(h: str) -> str:
    """Lowercase and strip parenthetical suffixes: 'Total (100)' → 'total'."""
    s = str(h).strip().lower()
    if "(" in s:
        s = s[:s.index("(")].strip()
    # Strip trailing numbers/spaces: 'total100' → 'total', 'marks 100' → 'marks'
    s = s.rstrip(" 0123456789")
    return s.strip()


def _is_name_col(h: str) -> bool:
    return _clean_header(h) in _NAME_ALIASES or str(h).strip().lower() in _NAME_ALIASES


def _is_roll_col(h: str) -> bool:
    return str(h).strip().lower() in _ROLL_ALIASES


def _is_roll_col_high(h: str) -> bool:
    """True only for explicit roll/reg columns (not generic index cols like S.No)."""
    return str(h).strip().lower() in _ROLL_ALIASES_HIGH


def _is_marks_col(h: str) -> bool:
    clean = _clean_header(h)
    return clean in _MARKS_ALIASES or str(h).strip().lower() in _MARKS_ALIASES


def _is_numeric_col(col: str, rows: list[dict]) -> bool:
    """Return True if ≥70% of non-empty values in this column are numeric."""
    vals = [rows[i].get(col) for i in range(min(20, len(rows)))]
    numeric = 0
    total = 0
    for v in vals:
        if v is None or str(v).strip() == "":
            continue
        total += 1
        try:
            float(str(v).replace(",", ""))
            numeric += 1
        except ValueError:
            pass
    return total > 0 and (numeric / total) >= 0.7


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_marks(file_id: str) -> list[dict]:
    """
    Parse marks from raw bytes (CSV, XLSX, or PDF).
    Returns list of {name, marks, roll_no} dicts.
    """
    raw = _FILE_CONTENTS.get(file_id, b"")
    name = _FILE_NAMES.get(file_id, "")
    if not raw:
        return []
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if ext == "xlsx" or ext == "xls":
        return _parse_xlsx(raw)
    if ext == "pdf":
        return _parse_pdf(raw)
    return _parse_csv(raw)


def _parse_csv(raw: bytes) -> list[dict]:
    try:
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            # Try with different delimiter
            reader2 = csv.DictReader(io.StringIO(text), delimiter=";")
            rows = list(reader2)
    except Exception as e:
        logger.warning("CSV parse error: %s", e)
        return []
    return _extract_marks(rows)


def _parse_xlsx(raw: bytes) -> list[dict]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        ws = wb.active
        rows_raw = list(ws.iter_rows(values_only=True))
    except Exception as e:
        logger.warning("XLSX parse error: %s", e)
        return []

    if not rows_raw:
        return []

    # First non-empty row as headers
    headers = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(rows_raw[0])]
    rows = []
    for row in rows_raw[1:]:
        if any(c is not None and str(c).strip() != "" for c in row):
            rows.append(dict(zip(headers, row)))
    return _extract_marks(rows)


def _parse_pdf(raw: bytes) -> list[dict]:
    """Extract tabular data from PDF using pdfplumber."""
    try:
        import pdfplumber
        rows: list[dict] = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                if not rows:
                    # Use first row as headers
                    headers = [str(h).strip() if h else f"col{i}" for i, h in enumerate(table[0])]
                    for data_row in table[1:]:
                        if any(c and str(c).strip() for c in data_row):
                            rows.append(dict(zip(headers, data_row)))
                else:
                    # Subsequent pages — skip header row and append data
                    for data_row in table[1:]:
                        if any(c and str(c).strip() for c in data_row):
                            rows.append(dict(zip(headers, data_row)))
    except ImportError:
        logger.warning("pdfplumber not installed — cannot parse PDF files")
        return []
    except Exception as e:
        logger.warning("PDF parse error: %s", e)
        return []
    return _extract_marks(rows)


def _col_mean(col: str, rows: list[dict]) -> float:
    """Return mean of numeric values in this column (0 if none)."""
    vals = []
    for r in rows[:50]:
        v = r.get(col)
        if v is None:
            continue
        try:
            vals.append(float(str(v).replace(",", "")))
        except (TypeError, ValueError):
            pass
    return sum(vals) / len(vals) if vals else 0.0


def _extract_marks(rows: list[dict]) -> list[dict]:
    """
    Given a list of row dicts, intelligently find name/roll/marks columns.

    Priority for marks column:
      1. Column whose cleaned name is in _MARKS_ALIASES (strips parentheticals like '(100)')
      2. Numeric column with the HIGHEST mean value (total/final always has largest values)
      3. Last numeric column

    Priority for roll column:
      1. High-priority roll names (roll_no, reg_no, student_id, etc.)
      2. Low-priority index names (s.no, sno, serial, id) — only if no high-priority found
    """
    if not rows:
        return []

    headers = list(rows[0].keys())

    # ── Find name column ──────────────────────────────────────────────────────
    name_col = next((c for c in headers if _is_name_col(c)), None)
    if name_col is None:
        name_col = next(
            (c for c in headers if not _is_roll_col(c) and not _is_numeric_col(c, rows)),
            headers[0]
        )

    # ── Find roll column (high priority first, then low priority) ─────────────
    roll_col = next((c for c in headers if _is_roll_col_high(c)), None)
    if roll_col is None:
        # Only use low-priority (S.No etc.) if there's no proper roll column
        roll_col = next((c for c in headers if _is_roll_col(c)), None)

    excluded: set[str] = {c for c in (name_col, roll_col) if c is not None}

    # ── Find marks column ────────────────────────────────────────────────────
    # Step 1: Name-based match (strips parentheticals like '(100)')
    marks_col = next(
        (c for c in headers if _is_marks_col(c) and c not in excluded),
        None,
    )

    if marks_col is None:
        # Step 2: Pick the numeric col with the HIGHEST mean
        # (total/final marks always have the largest values vs component marks)
        numeric_candidates = [
            c for c in headers if c not in excluded and _is_numeric_col(c, rows)
        ]
        if numeric_candidates:
            marks_col = max(numeric_candidates, key=lambda c: _col_mean(c, rows))

    if not marks_col:
        logger.warning("No marks column found. headers=%s", headers)
        return []

    # ── Build result ──────────────────────────────────────────────────────────
    result = []
    for r in rows[:500]:
        try:
            raw_name = str(r.get(name_col, "")).strip()
            if not raw_name or raw_name.lower() in ("none", "nan", ""):
                continue

            # Handle formula cells (None) by summing other numeric SCORE cols
            raw_val = r.get(marks_col)
            if raw_val is None:
                # Sum all numeric cols that are NOT name/roll/index columns
                other_numerics = [
                    c for c in headers
                    if c not in excluded                  # not name or roll col
                    and c != marks_col                    # not the total col itself
                    and not _is_roll_col(c)               # exclude S.No / serial / id
                    and _is_numeric_col(c, rows)
                ]
                computed = 0.0
                ok = False
                for c in other_numerics:
                    v = r.get(c)
                    if v is not None:
                        try:
                            computed += float(str(v).replace(",", ""))
                            ok = True
                        except (TypeError, ValueError):
                            pass
                if not ok:
                    continue
                marks = computed
            else:
                marks = float(str(raw_val).replace(",", ""))

            roll_val = ""
            if roll_col:
                roll_val = str(r.get(roll_col, "")).strip()
                # Ignore purely numeric roll values from index-type cols (S.No)
                # by preferring the real roll if there's an alphanumeric-looking col
                if roll_val.isdigit() and not _is_roll_col_high(roll_col):
                    # Look for a better alphanumeric roll col
                    better = next(
                        (c for c in headers
                         if c not in excluded and c != name_col and c != marks_col
                         and not _is_numeric_col(c, rows) and c != roll_col),
                        None,
                    )
                    if better:
                        roll_val = str(r.get(better, "")).strip()

            result.append({
                "name": raw_name,
                "roll_no": roll_val,
                "marks": marks,
            })
        except (TypeError, ValueError):
            continue
    return result


def _parse_raw_rows(file_id: str) -> tuple[list[dict], list[str]]:
    """Return (all_rows, headers) for multi-column analysis."""
    raw = _FILE_CONTENTS.get(file_id, b"")
    name_str = _FILE_NAMES.get(file_id, "")
    if not raw:
        return [], []
    try:
        ext = name_str.lower().rsplit(".", 1)[-1] if "." in name_str else ""
        if ext in ("xlsx", "xls"):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
            ws = wb.active
            rows_raw = list(ws.iter_rows(values_only=True))
            if not rows_raw:
                return [], []
            headers = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(rows_raw[0])]
            rows = [dict(zip(headers, row)) for row in rows_raw[1:] if any(c is not None for c in row)]
        elif ext == "pdf":
            rows = _extract_marks(_parse_pdf(raw))  # simplified for now
            headers = list(rows[0].keys()) if rows else []
        else:
            text = raw.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            headers = list(reader.fieldnames or [])
        return rows, headers
    except Exception as e:
        logger.warning("_parse_raw_rows error: %s", e)
        return [], []


def _grade_distribution(marks: list[float]) -> list[dict]:
    buckets: dict[str, int] = {
        "A (≥85)": 0, "B (70-84)": 0, "C (55-69)": 0, "D (40-54)": 0, "F (<40)": 0,
    }
    for v in marks:
        if v >= 85:   buckets["A (≥85)"] += 1
        elif v >= 70: buckets["B (70-84)"] += 1
        elif v >= 55: buckets["C (55-69)"] += 1
        elif v >= 40: buckets["D (40-54)"] += 1
        else:         buckets["F (<40)"] += 1
    return [
        {"name": k, "value": v, "color": c}
        for (k, v), c in zip(buckets.items(), _GRADE_COLORS) if v > 0
    ]


def _col_stats(rows: list[dict], numeric_cols: list[str]) -> list[dict]:
    """Compute mean/median/min/max/stdev for each numeric column."""
    result = []
    for col in numeric_cols:
        vals = []
        for r in rows:
            v = r.get(col)
            if v is None:
                continue
            try:
                vals.append(float(str(v).replace(",", "")))
            except (TypeError, ValueError):
                pass
        if not vals:
            continue
        result.append({
            "name": str(col),
            "mean": round(statistics.mean(vals), 2),
            "median": round(statistics.median(vals), 2),
            "min": min(vals),
            "max": max(vals),
            "stdev": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
        })
    return result


def _filter_files(
    department: str | None = None,
    year: str | None = None,
    section: str | None = None,
    subject: str | None = None,
) -> list[dict]:
    """Return uploaded files matching all provided filters (empty string = no filter)."""
    result = []
    for f in db.UPLOADED_FILES:
        if department and f.get("department", "") and f["department"] != department:
            continue
        if year and f.get("year", "") and f["year"] != year:
            continue
        if section and f.get("section", "") and f["section"] != section:
            continue
        if subject and f.get("subject", "") and f["subject"] != subject:
            continue
        result.append(f)
    return result


def _marks_from_files(files: list[dict]) -> list[dict]:
    """Merge student marks from a list of file metadata dicts."""
    result: list[dict] = []
    for f in files:
        result.extend(_parse_marks(f["id"]))
    return result


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats(
    department: str | None = None,
    year: str | None = None,
    section: str | None = None,
    subject: str | None = None,
) -> dict:
    files = _filter_files(department, year, section, subject)
    all_marks = _marks_from_files(files)
    total_docs = len(db.UPLOADED_FILES)

    if not all_marks:
        return {
            "total_students": 0,
            "total_students_change": "—",
            "avg_performance": 0.0,
            "avg_performance_change": "—",
            "total_documents": total_docs,
            "total_documents_change": "—",
            "pass_rate": 0.0,
            "pass_rate_change": "—",
        }

    marks_vals = [m["marks"] for m in all_marks]
    avg = round(statistics.mean(marks_vals), 1)
    pass_rate = round(100 * sum(1 for v in marks_vals if v >= 40) / len(marks_vals), 1)

    return {
        "total_students": len(all_marks),
        "total_students_change": "—",
        "avg_performance": avg,
        "avg_performance_change": "—",
        "total_documents": total_docs,
        "total_documents_change": "—",
        "pass_rate": pass_rate,
        "pass_rate_change": "—",
    }


# ── File management ───────────────────────────────────────────────────────────

def get_files() -> list[dict]:
    return db.UPLOADED_FILES


def get_file_by_id(file_id: str) -> dict:
    file = next((f for f in db.UPLOADED_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"File with id '{file_id}' not found.")
    return file


def add_file(
    upload: UploadFile,
    subject: str,
    department: str = "",
    year: str = "",
    section: str = "",
) -> dict:
    content = upload.file.read()
    size_bytes = len(content)
    size_label = f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes >= 1_048_576 else f"{size_bytes // 1024} KB" if size_bytes >= 1024 else f"{size_bytes} B"

    fname = upload.filename or f"upload_{uuid.uuid4().hex[:8]}.csv"
    ext = fname.lower().rsplit(".", 1)[-1] if "." in fname else ""
    allowed = {"csv", "xlsx", "xls", "pdf"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '.{ext}'. Allowed: CSV, Excel, PDF.")

    file_id = str(uuid.uuid4())
    new_file = {
        "id": file_id,
        "name": fname,
        "date": datetime.now().strftime("%b %d, %Y"),
        "subject": subject or "General",
        "department": department or "",
        "year": year or "",
        "section": section or "",
        "size": size_label,
    }
    db.UPLOADED_FILES.insert(0, new_file)
    _FILE_CONTENTS[file_id] = content
    _FILE_NAMES[file_id] = fname
    return new_file


def delete_file(file_id: str) -> dict:
    file = get_file_by_id(file_id)
    db.UPLOADED_FILES[:] = [f for f in db.UPLOADED_FILES if f["id"] != file_id]
    _FILE_CONTENTS.pop(file_id, None)
    _FILE_NAMES.pop(file_id, None)
    return {"message": f"File '{file['name']}' deleted successfully."}


def analyze_file(file_id: str) -> dict:
    file_meta = get_file_by_id(file_id)
    raw = _FILE_CONTENTS.get(file_id)

    if raw is None:
        raise HTTPException(status_code=422, detail="No content found. Please re-upload the file.")

    fname = _FILE_NAMES.get(file_id, "")
    ext = fname.lower().rsplit(".", 1)[-1] if "." in fname else ""

    if ext in ("xlsx", "xls"):
        student_marks = _parse_xlsx(raw)
    elif ext == "pdf":
        student_marks = _parse_pdf(raw)
    else:
        student_marks = _parse_csv(raw)

    if not student_marks:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract student marks from this file. "
                "Ensure it has columns named 'name'/'student' and 'marks'/'score'/'total'."
            ),
        )

    marks_vals = [m["marks"] for m in student_marks]

    # ── Normalize marks to 0-100 if the scale is different ────────────────────
    max_mark = max(marks_vals)
    if max_mark > 100:
        scale = 100.0 / max_mark
        marks_vals = [round(v * scale, 1) for v in marks_vals]
        for i, m in enumerate(student_marks):
            m["marks"] = marks_vals[i]

    grade_dist = _grade_distribution(marks_vals)

    # ── Full raw rows + multi-column stats ────────────────────────────────────
    all_rows, headers = _parse_raw_rows(file_id)

    # Identify all real numeric (score) columns — exclude name + roll cols
    score_cols = [
        h for h in headers
        if not _is_name_col(h) and not _is_roll_col(h) and _is_numeric_col(h, all_rows)
    ] if all_rows else []

    col_stats = _col_stats(all_rows, score_cols) if score_cols else [
        {
            "name": "marks",
            "mean": round(statistics.mean(marks_vals), 2),
            "median": round(statistics.median(marks_vals), 2),
            "min": min(marks_vals),
            "max": max(marks_vals),
            "stdev": round(statistics.stdev(marks_vals), 2) if len(marks_vals) > 1 else 0.0,
        }
    ]

    # ── ML predictions ────────────────────────────────────────────────────────
    from app.services import ml_service

    # Multi-column mode: only if there are ≥2 actual score columns (not just name+roll+marks)
    is_multi = len(score_cols) >= 2 and len(all_rows) >= 3
    if is_multi:
        ml_result = ml_service.predict_multi(student_marks, all_rows, headers)
    else:
        ml_result = ml_service.predict(student_marks)

    # ── Predicted vs actual bar chart ─────────────────────────────────────────
    predicted_vs_actual = []
    if ml_result.get("lr_available"):
        for p in ml_result["predictions"]:
            if p.get("predicted_marks") is not None:
                predicted_vs_actual.append({
                    "name": p["name"],
                    "actual": p["marks"],
                    "predicted": p["predicted_marks"],
                })

    return {
        "file_id": file_id,
        "file_name": file_meta["name"],
        "subject": file_meta["subject"],
        "department": file_meta.get("department", ""),
        "year": file_meta.get("year", ""),
        "section": file_meta.get("section", ""),
        "row_count": len(student_marks),
        "columns": col_stats,
        "grade_distribution": grade_dist,
        "student_marks": [{"name": m["name"], "marks": int(m["marks"])} for m in student_marks],
        "ml_predictions": ml_result["predictions"],
        "class_insights": ml_result["class_insights"],
        "lr_available": ml_result.get("lr_available", False),
        "has_multi_column": ml_result.get("has_multi_column", False),
        "predicted_vs_actual": predicted_vs_actual,
    }


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_analytics(
    department: str | None,
    year: str | None,
    section: str | None,
    subject: str | None,
) -> dict:
    files = _filter_files(department, year, section, subject)
    all_marks = _marks_from_files(files)

    if not all_marks:
        return {
            "student_marks": [],
            "performance_trend": [],
            "grade_distribution": [],
            "section_breakdown": [],
            "student_detail_list": [],
            "filters_applied": {
                "department": department, "year": year,
                "section": section, "subject": subject,
            },
        }

    marks_vals = [m["marks"] for m in all_marks]
    avg = round(statistics.mean(marks_vals), 1)
    performance_trend = [{"month": "Current", "avg": avg}]
    grade_dist = _grade_distribution(marks_vals)
    section_breakdown = _compute_section_breakdown(department, year, subject)

    from app.services import ml_service
    ml_result = ml_service.predict(all_marks)
    student_detail_list = ml_result["predictions"]

    return {
        "student_marks": [{"name": m["name"], "marks": int(m["marks"])} for m in all_marks],
        "performance_trend": performance_trend,
        "grade_distribution": grade_dist,
        "section_breakdown": section_breakdown,
        "student_detail_list": student_detail_list,
        "filters_applied": {
            "department": department, "year": year,
            "section": section, "subject": subject,
        },
    }


def _compute_section_breakdown(
    department: str | None,
    year: str | None,
    subject: str | None,
) -> list[dict]:
    """Aggregate performance per section across all uploaded files."""
    section_map: dict[str, list[float]] = {}
    for f in db.UPLOADED_FILES:
        if department and f.get("department") and f["department"] != department:
            continue
        if year and f.get("year") and f["year"] != year:
            continue
        if subject and f.get("subject") and f["subject"] != subject:
            continue
        sec = f.get("section") or "Unknown"
        marks = _parse_marks(f["id"])
        if marks:
            vals = [m["marks"] for m in marks]
            section_map.setdefault(sec, []).extend(vals)

    result = []
    for sec, vals in sorted(section_map.items()):
        avg = round(statistics.mean(vals), 1)
        pass_rate = round(100 * sum(1 for v in vals if v >= 40) / len(vals), 1)
        result.append({
            "section": sec,
            "avg": avg,
            "pass_rate": pass_rate,
            "total_students": len(vals),
        })
    return result


# ── Average report ────────────────────────────────────────────────────────────

def generate_average_report(file_ids: list[str]) -> dict:
    if len(file_ids) < 2:
        raise HTTPException(status_code=400,
                            detail="At least 2 files must be selected.")

    combined_marks: list[dict] = []
    for fid in file_ids:
        get_file_by_id(fid)
        combined_marks.extend(_parse_marks(fid))

    if not combined_marks:
        raise HTTPException(status_code=422,
                            detail="No parseable data found in the selected files.")

    marks_vals = [m["marks"] for m in combined_marks]
    return {
        "avg_score": round(statistics.mean(marks_vals), 1),
        "pass_rate": round(100 * sum(1 for v in marks_vals if v >= 40) / len(marks_vals), 1),
        "highest_score": max(marks_vals),
        "lowest_score": min(marks_vals),
        "student_marks": combined_marks[:20],
        "grade_distribution": _grade_distribution(marks_vals),
        "source_files": file_ids,
    }


# ── Filter options ────────────────────────────────────────────────────────────

def get_filter_options() -> dict:
    return {
        "departments": db.DEPARTMENTS,
        "years": db.YEARS,
        "sections": db.SECTIONS,
        "subjects": db.SUBJECTS,
    }
