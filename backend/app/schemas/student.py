from pydantic import BaseModel


# ── Profile ───────────────────────────────────────────────────────────────────

class StudentProfile(BaseModel):
    name: str
    roll_no: str
    cgpa: float
    year: str
    section: str
    department: str
    avatar_initials: str
    overall_score: str
    class_rank: int
    attendance: str


# ── Subject performance ───────────────────────────────────────────────────────

class SubjectScore(BaseModel):
    subject: str
    score: int
    grade: str
    trend: str
    color: str


# ── Trend & comparison ────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    month: str
    score: int
    classAvg: int


class ComparisonPoint(BaseModel):
    subject: str
    you: int
    classAvg: int


class RadarPoint(BaseModel):
    subject: str
    A: int
    fullMark: int


# ── Recent activity ───────────────────────────────────────────────────────────

class ActivityItem(BaseModel):
    title: str
    date: str
    score: str
    type: str


# ── Semester summary ──────────────────────────────────────────────────────────

class SemesterSummary(BaseModel):
    total_credits: int
    gpa: float
    best_subject: str
    assignments_completed: str
    quizzes_passed: str
    attendance: str
    overall_score: str
    class_rank: int


# ── Aggregated dashboard payload ──────────────────────────────────────────────

class StudentDashboardData(BaseModel):
    profile: StudentProfile
    subject_performance: list[SubjectScore]
    trend: list[TrendPoint]
    class_comparison: list[ComparisonPoint]
    radar: list[RadarPoint]
    recent_activity: list[ActivityItem]
    semester_summary: SemesterSummary
