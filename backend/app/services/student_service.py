"""
Student service — fetches real mark data from SQLite-backed faculty uploads,
matching the logged-in student's name or roll number against parsed records.
"""

import statistics
import app.core.database as _db
from app.models.student_user import StudentUser
from app.models.uploaded_file import UploadedFile
from app.models.student_mark import StudentMark
from sqlalchemy import func

_SUBJECT_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
    "#10b981", "#3b82f6", "#ef4444", "#14b8a6",
]


def _normalize_roll_no_str(s: str) -> str:
    value = (s or "").strip()
    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]
    return value


def _get_user(user_id: str) -> dict | None:
    with _db.SessionLocal() as db:
        u = db.query(StudentUser).filter(StudentUser.id == user_id).first()
        return u.to_dict() if u else None


def _all_file_records() -> list[dict]:
    """Deprecated: student dashboards no longer parse files from disk."""
    return []


def _parse_marks_for_user(user: dict) -> list[dict]:
    """
    Return the most recent mark per subject for this student.

    Matching rules:
      - Prefer exact roll_no match when available
      - Else fallback to case-insensitive name contains match
    """
    student_name = (user.get("name") or "").strip().lower()
    student_roll_raw = (user.get("roll_no") or "").strip()
    student_roll = _normalize_roll_no_str(student_roll_raw).lower()

    with _db.SessionLocal() as db:
        q = (
            db.query(StudentMark, UploadedFile)
            .join(UploadedFile, UploadedFile.id == StudentMark.uploaded_file_id)
        )
        if student_roll:
            candidates = {student_roll}
            # Handle legacy rows that may have come from Excel numeric cells (e.g. "2301.0").
            if student_roll.isdigit():
                candidates.add(f"{student_roll}.0")
            q = q.filter(func.lower(StudentMark.roll_no).in_(sorted(candidates)))
        elif student_name:
            q = q.filter(func.lower(StudentMark.student_name).like(f"%{student_name}%"))
        else:
            return []

        rows = q.order_by(UploadedFile.created_at.desc()).all()

    seen_subjects: set[str] = set()
    results: list[dict] = []
    for sm, uf in rows:
        subj = uf.subject or "Unknown"
        if subj in seen_subjects:
            continue
        seen_subjects.add(subj)
        results.append(
            {
                "subject": subj,
                "marks": float(sm.marks),
                "roll_no": sm.roll_no or "",
                "name": sm.student_name,
                "file_id": uf.id,
            }
        )
    return results


def _letter_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"


def _make_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


def _collect_all_scores(student_marks: list[dict]) -> list[float]:
    file_ids = [m.get("file_id") for m in student_marks if m.get("file_id")]
    if not file_ids:
        return []
    with _db.SessionLocal() as db:
        rows = (
            db.query(StudentMark.marks)
            .filter(StudentMark.uploaded_file_id.in_(file_ids))
            .all()
        )
        return [float(r[0]) for r in rows]


def _class_avg_by_file(file_ids: list[str]) -> dict[str, float]:
    if not file_ids:
        return {}
    with _db.SessionLocal() as db:
        rows = (
            db.query(StudentMark.uploaded_file_id, StudentMark.marks)
            .filter(StudentMark.uploaded_file_id.in_(file_ids))
            .all()
        )
    buckets: dict[str, list[float]] = {}
    for fid, marks in rows:
        buckets.setdefault(fid, []).append(float(marks))
    # UI schema expects integers for class averages.
    return {fid: int(round(statistics.mean(vals))) if vals else 0 for fid, vals in buckets.items()}


# ── Public API ────────────────────────────────────────────────────────────────

def get_student_profile(user_id: str) -> dict:
    user = _get_user(user_id)
    if not user:
        return {
            "name": "Student", "roll_no": "N/A", "cgpa": 0.0,
            "year": "N/A", "section": "N/A", "department": "N/A",
            "avatar_initials": "??", "overall_score": "—",
            "class_rank": 0, "attendance": "—",
        }

    marks_data = _parse_marks_for_user(user)

    # Prefer real student name + class metadata from uploaded records when the
    # user's profile is still the auto-generated defaults.
    profile_name = user.get("name") or "Student"
    profile_roll = user.get("roll_no") or "N/A"
    profile_year = user.get("year") or "1st Year"
    profile_section = user.get("section") or "Section A"
    profile_department = user.get("department") or "General"

    if marks_data:
        roll_norm = _normalize_roll_no_str(profile_roll).lower()
        if roll_norm and (profile_name or "").strip().lower() == roll_norm:
            profile_name = marks_data[0].get("name") or profile_name

        latest_file_id = marks_data[0].get("file_id")
        if latest_file_id:
            with _db.SessionLocal() as db:
                uf = db.query(UploadedFile).filter(UploadedFile.id == latest_file_id).first()
                if uf:
                    if profile_department in {"", "General", "N/A"} and (uf.department or "").strip():
                        profile_department = uf.department
                    if profile_year in {"", "1st Year", "N/A"} and (uf.year or "").strip():
                        profile_year = uf.year
                    if profile_section in {"", "Section A", "A", "N/A"} and (uf.section or "").strip():
                        profile_section = uf.section

        avg = round(statistics.mean(m["marks"] for m in marks_data), 1)
        overall = avg
        rank = sum(1 for s in _collect_all_scores(marks_data) if s > avg) + 1
    else:
        overall = "—"
        rank = 0

    return {
        "name":             profile_name,
        "roll_no":          profile_roll,
        "cgpa":             user.get("cgpa", 0.0),
        "year":             profile_year,
        "section":          profile_section,
        "department":       profile_department,
        "avatar_initials":  _make_initials(profile_name),
        "overall_score":    overall,
        "class_rank":       rank,
        "attendance":       user.get("attendance", "—"),
    }


def get_subject_performance(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    marks_data = _parse_marks_for_user(user)
    return [
        {
            "subject": m["subject"],
            "score":   round(m["marks"]),
            "grade":   _letter_grade(m["marks"]),
            "trend":   "+0",
            "color":   _SUBJECT_COLORS[i % len(_SUBJECT_COLORS)],
        }
        for i, m in enumerate(marks_data)
    ]


def get_performance_trend(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    marks_data = _parse_marks_for_user(user)
    file_ids = [m["file_id"] for m in marks_data]
    class_avg = _class_avg_by_file(file_ids)
    return [
        {
            "month": m["subject"][:8],
            "score": int(round(m["marks"])),
            "classAvg": int(class_avg.get(m["file_id"], 0) or 0),
        }
        for m in marks_data
    ]


def get_class_comparison(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    marks_data = _parse_marks_for_user(user)
    file_ids = [m["file_id"] for m in marks_data]
    class_avg = _class_avg_by_file(file_ids)
    return [
        {
            "subject": m["subject"][:8],
            "you": int(round(m["marks"])),
            "classAvg": int(class_avg.get(m["file_id"], 0) or 0),
        }
        for m in marks_data
    ]


def get_radar_data(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    marks_data = _parse_marks_for_user(user)
    return [
        {"subject": m["subject"][:8], "A": round(m["marks"]), "fullMark": 100}
        for m in marks_data
    ]


def get_recent_activity(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    marks_data = _parse_marks_for_user(user)
    return [
        {"title": f"{m['subject']} — Marks", "date": "This semester",
         "score": f"{round(m['marks'])}/100", "type": "Exam"}
        for m in marks_data
    ]


def get_semester_summary(user_id: str = "") -> dict:
    if not user_id: return _empty_summary()
    user = _get_user(user_id)
    if not user: return _empty_summary()
    marks_data = _parse_marks_for_user(user)
    if not marks_data: return _empty_summary()

    avg = statistics.mean(m["marks"] for m in marks_data)
    best = max(marks_data, key=lambda m: m["marks"])
    return {
        "total_credits":           len(marks_data) * 4,
        "gpa":                     round(avg / 25, 2),
        "best_subject":            best["subject"],
        "assignments_completed":   f"{len(marks_data)}/{len(marks_data)}",
        "quizzes_passed":          f"{sum(1 for m in marks_data if m['marks'] >= 40)}/{len(marks_data)}",
        "attendance":              user.get("attendance", "—"),
        "overall_score":           str(round(avg, 1)),
        "class_rank":              0,
    }


def _empty_summary() -> dict:
    return {
        "total_credits": 0, "gpa": 0.0, "best_subject": "—",
        "assignments_completed": "—", "quizzes_passed": "—",
        "attendance": "—", "overall_score": "—", "class_rank": 0,
    }


def get_full_dashboard(user_id: str) -> dict:
    return {
        "profile":             get_student_profile(user_id),
        "subject_performance": get_subject_performance(user_id),
        "trend":               get_performance_trend(user_id),
        "class_comparison":    get_class_comparison(user_id),
        "radar":               get_radar_data(user_id),
        "recent_activity":     get_recent_activity(user_id),
        "semester_summary":    get_semester_summary(user_id),
    }
