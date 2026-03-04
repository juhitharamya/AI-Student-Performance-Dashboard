from pydantic import BaseModel


# ── Stats cards ───────────────────────────────────────────────────────────────

class FacultyStats(BaseModel):
    total_students: int
    total_students_change: str
    avg_performance: float
    avg_performance_change: str
    total_documents: int
    total_documents_change: str
    pass_rate: float
    pass_rate_change: str


# ── Uploaded files ────────────────────────────────────────────────────────────

class UploadedFile(BaseModel):
    id: str
    name: str
    date: str
    subject: str
    department: str = ""
    year: str = ""
    section: str = ""
    size: str


class UploadedFileList(BaseModel):
    files: list[UploadedFile]


# ── Chart data ────────────────────────────────────────────────────────────────

class StudentMark(BaseModel):
    name: str
    marks: int


class TrendPoint(BaseModel):
    month: str
    avg: float


class GradeSlice(BaseModel):
    name: str
    value: int
    color: str


class SectionPerformance(BaseModel):
    section: str
    avg: float
    pass_rate: float
    total_students: int


# ── ML predictions ────────────────────────────────────────────────────────────

class MLPrediction(BaseModel):
    name: str
    roll_no: str = ""
    marks: float
    predicted_grade: str
    cluster: str
    performance_category: str = "Average"
    risk_score: int
    z_score: float
    pass_probability: float | None = None
    predicted_marks: float | None = None
    rank: int = 0


class ClassInsights(BaseModel):
    mean: float
    stdev: float
    pass_rate: float
    fail_rate: float = 0.0
    highest: float
    lowest: float
    cluster_distribution: dict
    at_risk_count: int
    top_performer_count: int
    failed_count: int
    topper: dict | None = None
    lowest_performer: dict | None = None
    recommendations: list[str]


# ── Analytics data ────────────────────────────────────────────────────────────

class AnalyticsData(BaseModel):
    student_marks: list[StudentMark]
    performance_trend: list[TrendPoint]
    grade_distribution: list[GradeSlice]
    section_breakdown: list[SectionPerformance] = []
    student_detail_list: list[MLPrediction] = []
    filters_applied: dict | None = None


# ── Average report ────────────────────────────────────────────────────────────

class AverageReportRequest(BaseModel):
    file_ids: list[str]


class AverageReport(BaseModel):
    avg_score: float
    pass_rate: float
    highest_score: int
    lowest_score: int
    student_marks: list[StudentMark]
    grade_distribution: list[GradeSlice]
    source_files: list[str] = []


# ── Dropdown options ──────────────────────────────────────────────────────────

class FilterOptions(BaseModel):
    departments: list[str]
    years: list[str]
    sections: list[str]
    subjects: list[str]


# ── File analysis ─────────────────────────────────────────────────────────────

class ColumnStats(BaseModel):
    name: str
    mean: float
    median: float
    min: float
    max: float
    stdev: float


class FileAnalysis(BaseModel):
    file_id: str
    file_name: str
    subject: str
    department: str = ""
    year: str = ""
    section: str = ""
    row_count: int
    columns: list[ColumnStats]
    grade_distribution: list[GradeSlice]
    student_marks: list[StudentMark]
    ml_predictions: list[MLPrediction] = []
    class_insights: ClassInsights | None = None
    lr_available: bool = False
    has_multi_column: bool = False
    predicted_vs_actual: list[dict] = []
