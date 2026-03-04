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


def _user_id(current_user: dict = Depends(require_student)) -> str:
    return current_user["id"]


router = APIRouter(
    prefix="/student",
    tags=["Student"],
    dependencies=[Depends(require_student)],
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
    profile, subjects, charts, activity, and summary — in a single request.
    """
    return student_service.get_full_dashboard(user_id)


# ── Individual endpoints ──────────────────────────────────────────────────────

@router.get("/profile", response_model=StudentProfile, summary="Student profile card")
def get_profile(user_id: str = Depends(_user_id)) -> StudentProfile:
    return student_service.get_student_profile(user_id)


@router.get("/subjects", response_model=list[SubjectScore], summary="Subject-wise performance")
def get_subjects(user_id: str = Depends(_user_id)) -> list[SubjectScore]:
    return student_service.get_subject_performance(user_id)


@router.get("/trend", response_model=list[TrendPoint], summary="Monthly score trend")
def get_trend(user_id: str = Depends(_user_id)) -> list[TrendPoint]:
    return student_service.get_performance_trend(user_id)


@router.get("/comparison", response_model=list[ComparisonPoint], summary="Your score vs class average")
def get_comparison(user_id: str = Depends(_user_id)) -> list[ComparisonPoint]:
    return student_service.get_class_comparison(user_id)


@router.get("/radar", response_model=list[RadarPoint], summary="Radar chart data")
def get_radar(user_id: str = Depends(_user_id)) -> list[RadarPoint]:
    return student_service.get_radar_data(user_id)


@router.get("/activity", response_model=list[ActivityItem], summary="Recent assessments")
def get_activity(user_id: str = Depends(_user_id)) -> list[ActivityItem]:
    return student_service.get_recent_activity(user_id)


@router.get("/summary", response_model=SemesterSummary, summary="Semester summary")
def get_summary(user_id: str = Depends(_user_id)) -> SemesterSummary:
    return student_service.get_semester_summary(user_id)
