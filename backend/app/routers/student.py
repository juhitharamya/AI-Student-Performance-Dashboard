from fastapi import APIRouter, Depends

from app.core.dependencies import require_student
from app.schemas.student import (
    ActivityItem,
    ComparisonPoint,
    RadarPoint,
    SemesterSummary,
    StudentDashboardData,
    StudentProfile,
    SubjectScore,
    TrendPoint,
)
from app.services import student_service

# Helper: extract user_id from the authenticated student token
def _user_id(current_user: dict = Depends(require_student)) -> str:
    return current_user["id"]

router = APIRouter(
    prefix="/student",
    tags=["Student"],
    dependencies=[Depends(require_student)],  # 🔒 all routes require student JWT
)


# ── Full dashboard (single round-trip) ────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=StudentDashboardData,
    summary="Full student dashboard payload in one request",
)
def get_dashboard(user_id: str = Depends(_user_id)) -> StudentDashboardData:
    """
    Returns the complete data set needed to render the student dashboard —
    profile, subjects, charts, activity, and summary — in a single request
    to minimise network round-trips.
    """
    return student_service.get_full_dashboard(user_id)


# ── Individual endpoints (granular access) ────────────────────────────────────

@router.get(
    "/profile",
    response_model=StudentProfile,
    summary="Student profile card",
)
def get_profile(user_id: str = Depends(_user_id)) -> StudentProfile:
    """Returns the student's name, roll number, CGPA, rank and attendance."""
    return student_service.get_student_profile(user_id)


@router.get(
    "/subjects",
    response_model=list[SubjectScore],
    summary="Subject-wise performance cards",
)
def get_subjects() -> list[SubjectScore]:
    """Returns score, grade, and trend for every enrolled subject."""
    return student_service.get_subject_performance()


@router.get(
    "/trend",
    response_model=list[TrendPoint],
    summary="Monthly score trend vs class average",
)
def get_trend() -> list[TrendPoint]:
    """Time-series data used to draw the performance trend line chart."""
    return student_service.get_performance_trend()


@router.get(
    "/comparison",
    response_model=list[ComparisonPoint],
    summary="Your score vs class average per subject",
)
def get_comparison() -> list[ComparisonPoint]:
    """Data for the grouped bar chart comparing student vs class average."""
    return student_service.get_class_comparison()


@router.get(
    "/radar",
    response_model=list[RadarPoint],
    summary="Radar / spider chart data",
)
def get_radar() -> list[RadarPoint]:
    """Subject proficiency scores for the skill radar chart."""
    return student_service.get_radar_data()


@router.get(
    "/activity",
    response_model=list[ActivityItem],
    summary="Recent assessments and results",
)
def get_activity() -> list[ActivityItem]:
    """Latest assignments, exams, quizzes, labs, and projects."""
    return student_service.get_recent_activity()


@router.get(
    "/summary",
    response_model=SemesterSummary,
    summary="Semester summary (credits, GPA, attendance…)",
)
def get_summary() -> SemesterSummary:
    """High-level semester statistics shown in the summary card at the bottom."""
    return student_service.get_semester_summary()
