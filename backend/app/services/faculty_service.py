import csv
import io
import statistics
import uuid
from datetime import datetime
from fastapi import HTTPException, UploadFile, status

from app.core import data_store as db

# In-memory store for raw file bytes {file_id: bytes}
_FILE_CONTENTS: dict[str, bytes] = {}
_FILE_NAMES: dict[str, str] = {}   # {file_id: original_filename}

# Grade-bucket colors (A → F)
_GRADE_COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_marks(file_id: str) -> list[dict]:
    """
    Parse marks from raw bytes (CSV or XLSX).
    Returns list of {name, marks} dicts.
    """
    raw = _FILE_CONTENTS.get(file_id, b"")
    name = _FILE_NAMES.get(file_id, "")
    if not raw:
        return []
    if name.lower().endswith(".xlsx"):
        return _parse_xlsx(raw)
    return _parse_csv(raw)


def _parse_csv(raw: bytes) -> list[dict]:
    try:
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception:
        return []
    return _extract_marks(rows)


def _parse_xlsx(raw: bytes) -> list[dict]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        ws = wb.active
        rows_raw = list(ws.iter_rows(values_only=True))
    except Exception:
        return []

    if not rows_raw:
        return []

    # First row as headers
    headers = [str(h).strip() if h is not None else "" for h in rows_raw[0]]
    rows = [dict(zip(headers, row)) for row in rows_raw[1:] if any(c is not None for c in row)]
    return _extract_marks(rows)


def _extract_marks(rows: list[dict]) -> list[dict]:
    """Given a list of row dicts, find name/roll/marks columns and return enriched dicts."""
    if not rows:
        return []

    headers = list(rows[0].keys())
    name_col = next(
        (c for c in headers if str(c).strip().lower() in
         ("name", "student", "student_name", "student name")),
        None,
    )
    roll_col = next(
        (c for c in headers if str(c).strip().lower() in
         ("roll", "roll_no", "rollno", "roll no", "reg", "reg_no", "id", "student_id")),
        None,
    )
    # If no name col found try first non-roll col
    if name_col is None:
        name_col = next((c for c in headers if c != roll_col), headers[0])

    # Pick first numeric column (not name/roll) as marks
    marks_col = None
    for col in headers:
        if col in (name_col, roll_col):
            continue
        try:
            float(rows[0][col] if rows[0][col] is not None else "")
            marks_col = col
            break
        except (TypeError, ValueError):
            pass

    if not marks_col:
        return []

    result = []
    for r in rows[:200]:
        try:
            name = str(r.get(name_col, "")).strip()
            marks = float(r[marks_col])
            if name:
                result.append({
                    "name": name,
                    "roll_no": str(r.get(roll_col, "")).strip() if roll_col else "",
                    "marks": marks,
                })
        except (TypeError, ValueError):
            pass
    return result


def _parse_raw_rows(file_id: str) -> tuple[list[dict], list[str]]:
    """Return (all_rows, headers) for multi-column analysis."""
    raw = _FILE_CONTENTS.get(file_id, b"")
    name = _FILE_NAMES.get(file_id, "")
    if not raw:
        return [], []
    try:
        if name.lower().endswith(".xlsx"):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
            ws = wb.active
            rows_raw = list(ws.iter_rows(values_only=True))
            if not rows_raw:
                return [], []
            headers = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(rows_raw[0])]
            rows = [dict(zip(headers, row)) for row in rows_raw[1:] if any(c is not None for c in row)]
        else:
            text = raw.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            headers = reader.fieldnames or []
        return rows, list(headers)
    except Exception:
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
    size_label = f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes >= 1024 else f"{size_bytes} B"

    file_id = str(uuid.uuid4())
    fname = upload.filename or f"upload_{uuid.uuid4().hex[:8]}.csv"
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
    if fname.lower().endswith(".xlsx"):
        student_marks = _parse_xlsx(raw)
    else:
        student_marks = _parse_csv(raw)

    if not student_marks:
        raise HTTPException(status_code=422, detail="Could not find name/marks columns in this file.")

    marks_vals = [m["marks"] for m in student_marks]
    grade_dist = _grade_distribution(marks_vals)

    # ── Column stats ──────────────────────────────────────────────────────────
    col_stats = [
        {
            "name": "marks",
            "mean": round(statistics.mean(marks_vals), 2),
            "median": round(statistics.median(marks_vals), 2),
            "min": min(marks_vals),
            "max": max(marks_vals),
            "stdev": round(statistics.stdev(marks_vals), 2) if len(marks_vals) > 1 else 0.0,
        }
    ]

    # ── ML predictions (multi-column path if available) ───────────────────────
    from app.services import ml_service
    all_rows, headers = _parse_raw_rows(file_id)
    if len(headers) > 2 and all_rows:
        ml_result = ml_service.predict_multi(student_marks, all_rows, headers)
    else:
        ml_result = ml_service.predict(student_marks)

    # ── Predicted vs actual for dual bar chart ────────────────────────────────
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
    """
    Return chart data filtered by provided params.
    Also return section_breakdown and student_detail_list for the analytics tab.
    """
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

    # Build student detail list with ML predictions
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
    """Aggregate performance per section across all uploaded files (optionally filtered)."""
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
