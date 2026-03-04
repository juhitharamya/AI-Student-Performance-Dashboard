"""
Student service — serves real data from faculty-uploaded files by matching
the logged-in student's name or roll number against parsed mark records.
"""

import statistics
from app.core import data_store as db
from app.core.data_store import USERS

# Colour palette for subject cards
_SUBJECT_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
    "#10b981", "#3b82f6", "#ef4444", "#14b8a6",
]


def _get_user(user_id: str) -> dict | None:
    return next((u for u in USERS if u["id"] == user_id and u["role"] == "student"), None)


def _parse_marks_for_user(user: dict) -> list[dict]:
    """
    Scan all faculty-uploaded files and return mark records that belong to
    this student (matched by roll_no or name, case-insensitive).
    Returns list of {subject, marks, roll_no, name} dicts.
    """
    from app.services.faculty_service import _parse_marks  # lazy import

    student_name = (user.get("name") or "").strip().lower()
    student_roll = (user.get("roll_no") or "").strip().lower()

    results = []
    for f in db.UPLOADED_FILES:
        marks_list = _parse_marks(f["id"])
        for m in marks_list:
            row_name = (m.get("name") or "").strip().lower()
            row_roll = (m.get("roll_no") or "").strip().lower()

            name_match = student_name and student_name in row_name
            roll_match = student_roll and student_roll == row_roll

            if name_match or roll_match:
                results.append({
                    "subject": f.get("subject", "Unknown"),
                    "marks": m["marks"],
                    "roll_no": m.get("roll_no", ""),
                    "name": m.get("name", ""),
                    "file_id": f["id"],
                })
                break  # only one record per file
    return results


def _letter_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"


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

    # Derive overall score from uploaded data for this student
    marks_data = _parse_marks_for_user(user)
    if marks_data:
        avg = round(statistics.mean(m["marks"] for m in marks_data), 1)
        overall_score: str | float = avg
        # Compute rank among all students who appear in the same files
        all_scores = _collect_all_scores(marks_data)
        rank = sum(1 for s in all_scores if s > avg) + 1
    else:
        overall_score = "—"
        rank = 0

    name = user.get("name", "Student")
    initials = _make_initials(name)

    return {
        "name": name,
        "roll_no": user.get("roll_no", "N/A"),
        "cgpa": user.get("cgpa", 0.0),
        "year": user.get("year", "1st Year"),
        "section": user.get("section", "A"),
        "department": user.get("department", "General"),
        "avatar_initials": initials,
        "overall_score": overall_score,
        "class_rank": rank,
        "attendance": user.get("attendance", "—"),
    }


def _make_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


def _collect_all_scores(student_marks: list[dict]) -> list[float]:
    """Collect all students' scores from the same files for ranking."""
    from app.services.faculty_service import _parse_marks
    all_scores: list[float] = []
    seen_files: set[str] = set()
    for m in student_marks:
        fid = m.get("file_id", "")
        if fid and fid not in seen_files:
            seen_files.add(fid)
            for row in _parse_marks(fid):
                all_scores.append(row["marks"])
    return all_scores


def get_subject_performance(user_id: str = "") -> list[dict]:
    if not user_id:
        return []
    user = _get_user(user_id)
    if not user:
        return []
    marks_data = _parse_marks_for_user(user)
    if not marks_data:
        return []

    results = []
    for i, m in enumerate(marks_data):
        score = round(m["marks"])
        grade = _letter_grade(m["marks"])
        color = _SUBJECT_COLORS[i % len(_SUBJECT_COLORS)]
        results.append({
            "subject": m["subject"],
            "score": score,
            "grade": grade,
            "trend": "+0",
            "color": color,
        })
    return results


def get_performance_trend(user_id: str = "") -> list[dict]:
    if not user_id:
        return []
    user = _get_user(user_id)
    if not user:
        return []
    marks_data = _parse_marks_for_user(user)
    if not marks_data:
        return []

    # Build one point per subject upload (ordered by subject name for consistency)
    trend = []
    for m in marks_data:
        # Get class avg for the same file
        from app.services.faculty_service import _parse_marks
        all_marks = [r["marks"] for r in _parse_marks(m["file_id"])]
        class_avg = round(statistics.mean(all_marks), 1) if all_marks else 0
        trend.append({
            "month": m["subject"][:8],
            "score": round(m["marks"]),
            "classAvg": class_avg,
        })
    return trend


def get_class_comparison(user_id: str = "") -> list[dict]:
    if not user_id:
        return []
    user = _get_user(user_id)
    if not user:
        return []
    marks_data = _parse_marks_for_user(user)
    if not marks_data:
        return []

    comparison = []
    for m in marks_data:
        from app.services.faculty_service import _parse_marks
        all_marks = [r["marks"] for r in _parse_marks(m["file_id"])]
        class_avg = round(statistics.mean(all_marks), 1) if all_marks else 0
        comparison.append({
            "subject": m["subject"][:8],
            "you": round(m["marks"]),
            "classAvg": class_avg,
        })
    return comparison


def get_radar_data(user_id: str = "") -> list[dict]:
    if not user_id:
        return []
    user = _get_user(user_id)
    if not user:
        return []
    marks_data = _parse_marks_for_user(user)
    if not marks_data:
        return []

    return [
        {"subject": m["subject"][:8], "A": round(m["marks"])}
        for m in marks_data
    ]


def get_recent_activity(user_id: str = "") -> list[dict]:
    if not user_id:
        return []
    user = _get_user(user_id)
    if not user:
        return []
    marks_data = _parse_marks_for_user(user)
    if not marks_data:
        return []

    activity = []
    for m in marks_data:
        score = round(m["marks"])
        activity.append({
            "title": f"{m['subject']} — Marks",
            "date": "This semester",
            "score": f"{score}/100",
            "type": "Exam",
        })
    return activity


def get_semester_summary(user_id: str = "") -> dict:
    if not user_id:
        return _empty_summary()
    user = _get_user(user_id)
    if not user:
        return _empty_summary()
    marks_data = _parse_marks_for_user(user)

    if not marks_data:
        return _empty_summary()

    avg = statistics.mean(m["marks"] for m in marks_data)
    gpa = round(avg / 25, 2)  # rough GPA on 4.0 scale
    best = max(marks_data, key=lambda m: m["marks"])

    return {
        "total_credits": len(marks_data) * 4,
        "gpa": gpa,
        "best_subject": best["subject"],
        "assignments_completed": f"{len(marks_data)}/{len(marks_data)}",
        "quizzes_passed": f"{sum(1 for m in marks_data if m['marks'] >= 40)}/{len(marks_data)}",
        "attendance": user.get("attendance", "—"),
        "overall_score": round(avg, 1),
        "class_rank": 0,
    }


def _empty_summary() -> dict:
    return {
        "total_credits": 0, "gpa": 0.0, "best_subject": "—",
        "assignments_completed": "—", "quizzes_passed": "—",
        "attendance": "—", "overall_score": "—", "class_rank": 0,
    }


def get_full_dashboard(user_id: str) -> dict:
    """Return the complete student dashboard payload."""
    return {
        "profile": get_student_profile(user_id),
        "subject_performance": get_subject_performance(user_id),
        "trend": get_performance_trend(user_id),
        "class_comparison": get_class_comparison(user_id),
        "radar": get_radar_data(user_id),
        "recent_activity": get_recent_activity(user_id),
        "semester_summary": get_semester_summary(user_id),
    }
