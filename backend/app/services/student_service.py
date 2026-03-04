from app.core import data_store as db
from app.core.data_store import USERS


def get_student_profile(user_id: str) -> dict:
    """Fetch the student record from USERS store."""
    user = next((u for u in USERS if u["id"] == user_id and u["role"] == "student"), None)
    if not user:
        return {
            "name": "Student",
            "roll_no": "N/A",
            "cgpa": 0.0,
            "year": "N/A",
            "section": "N/A",
            "department": "N/A",
            "avatar_initials": "??",
            "overall_score": "—",
            "class_rank": 0,
            "attendance": "—",
        }
    return {
        "name": user["name"],
        "roll_no": user.get("roll_no", "N/A"),
        "cgpa": user.get("cgpa", 0.0),
        "year": user.get("year", "N/A"),
        "section": user.get("section", "N/A"),
        "department": user.get("department", "N/A"),
        "avatar_initials": user.get("avatar_initials", "??"),
        "overall_score": "—",
        "class_rank": 0,
        "attendance": "—",
    }


def get_subject_performance() -> list[dict]:
    return []


def get_performance_trend() -> list[dict]:
    return []


def get_class_comparison() -> list[dict]:
    return []


def get_radar_data() -> list[dict]:
    return []


def get_recent_activity() -> list[dict]:
    return []


def get_semester_summary() -> dict:
    return {
        "total_credits": 0,
        "gpa": 0.0,
        "best_subject": "—",
        "assignments_completed": "—",
        "quizzes_passed": "—",
        "attendance": "—",
        "overall_score": "—",
        "class_rank": 0,
    }


def get_full_dashboard(user_id: str) -> dict:
    """Return the entire student dashboard payload. Charts are empty until faculty uploads real data."""
    return {
        "profile": get_student_profile(user_id),
        "subject_performance": get_subject_performance(),
        "trend": get_performance_trend(),
        "class_comparison": get_class_comparison(),
        "radar": get_radar_data(),
        "recent_activity": get_recent_activity(),
        "semester_summary": get_semester_summary(),
    }
