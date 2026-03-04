"""
Student service — fetches real mark data from SQLite-backed faculty uploads,
matching the logged-in student's name or roll number against parsed records.
"""

import statistics
import app.core.database as _db
from app.models.user import User
from app.models.uploaded_file import UploadedFile

_SUBJECT_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
    "#10b981", "#3b82f6", "#ef4444", "#14b8a6",
]


def _get_user(user_id: str) -> dict | None:
    with _db.SessionLocal() as db:
        u = db.query(User).filter(User.id == user_id, User.role == "student").first()
        return u.to_dict() if u else None


def _all_file_records() -> list[dict]:
    """Return all uploaded file records (metadata + file_path) from DB."""
    with _db.SessionLocal() as db:
        files = db.query(UploadedFile).all()
        # Include file_path so student_service can call _parse_marks_from_path
        return [
            {**f.to_dict(), "file_path": f.file_path}
            for f in files
        ]


def _parse_marks_for_user(user: dict) -> list[dict]:
    """
    Scan all faculty-uploaded files and return mark records that belong to
    this student (matched by roll_no or name, case-insensitive).
    """
    from app.services.faculty_service import _parse_marks_from_path

    student_name = (user.get("name") or "").strip().lower()
    student_roll = (user.get("roll_no") or "").strip().lower()

    results = []
    for f in _all_file_records():
        marks_list = _parse_marks_from_path(f["file_path"], f["name"])
        for m in marks_list:
            row_name = (m.get("name") or "").strip().lower()
            row_roll = (m.get("roll_no") or "").strip().lower()
            name_match = student_name and student_name in row_name
            roll_match = student_roll and student_roll == row_roll
            if name_match or roll_match:
                results.append({
                    "subject":   f.get("subject", "Unknown"),
                    "marks":     m["marks"],
                    "roll_no":   m.get("roll_no", ""),
                    "name":      m.get("name", ""),
                    "file_id":   f["id"],
                    "file_path": f["file_path"],
                    "file_name": f["name"],
                })
                break
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
    from app.services.faculty_service import _parse_marks_from_path
    all_scores: list[float] = []
    seen: set[str] = set()
    for m in student_marks:
        fid = m.get("file_id", "")
        if fid and fid not in seen:
            seen.add(fid)
            for row in _parse_marks_from_path(m["file_path"], m["file_name"]):
                all_scores.append(row["marks"])
    return all_scores


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
    if marks_data:
        avg = round(statistics.mean(m["marks"] for m in marks_data), 1)
        overall = avg
        rank = sum(1 for s in _collect_all_scores(marks_data) if s > avg) + 1
    else:
        overall = "—"
        rank = 0

    return {
        "name":             user["name"],
        "roll_no":          user.get("roll_no", "N/A"),
        "cgpa":             user.get("cgpa", 0.0),
        "year":             user.get("year", "1st Year"),
        "section":          user.get("section", "A"),
        "department":       user.get("department", "General"),
        "avatar_initials":  _make_initials(user["name"]),
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
    from app.services.faculty_service import _parse_marks_from_path
    trend = []
    for m in marks_data:
        all_marks = [r["marks"] for r in _parse_marks_from_path(m["file_path"], m["file_name"])]
        class_avg = round(statistics.mean(all_marks), 1) if all_marks else 0
        trend.append({"month": m["subject"][:8], "score": round(m["marks"]), "classAvg": class_avg})
    return trend


def get_class_comparison(user_id: str = "") -> list[dict]:
    if not user_id: return []
    user = _get_user(user_id)
    if not user: return []
    from app.services.faculty_service import _parse_marks_from_path
    marks_data = _parse_marks_for_user(user)
    result = []
    for m in marks_data:
        all_marks = [r["marks"] for r in _parse_marks_from_path(m["file_path"], m["file_name"])]
        class_avg = round(statistics.mean(all_marks), 1) if all_marks else 0
        result.append({"subject": m["subject"][:8], "you": round(m["marks"]), "classAvg": class_avg})
    return result


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
        "overall_score":           round(avg, 1),
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
