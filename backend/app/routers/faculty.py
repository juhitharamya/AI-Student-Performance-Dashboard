from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.dependencies import require_faculty
from app.schemas.faculty import (
    AnalyticsData,
    AverageReport,
    AverageReportRequest,
    FacultyStats,
    FileAnalysis,
    FilterOptions,
    UploadedFile,
    UploadedFileList,
)
from app.services import faculty_service

router = APIRouter(
    prefix="/faculty",
    tags=["Faculty"],
    dependencies=[Depends(require_faculty)],  # 🔒 all routes require faculty JWT
)


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=FacultyStats,
    summary="Faculty dashboard – key stats cards",
)
def get_stats() -> FacultyStats:
    """
    Returns aggregated KPIs shown on the faculty dashboard:
    total students, average performance, document count, and pass rate.
    """
    return faculty_service.get_stats()


# ── Document management ───────────────────────────────────────────────────────

@router.get(
    "/uploads",
    response_model=UploadedFileList,
    summary="List all uploaded documents",
)
def list_uploads() -> UploadedFileList:
    """Return all uploaded documents stored on the server."""
    return {"files": faculty_service.get_files()}


@router.post(
    "/uploads",
    response_model=UploadedFile,
    status_code=201,
    summary="Upload a new document",
)
def upload_file(
    file: UploadFile = File(..., description="CSV or XLSX file to upload"),
    subject: str = Form("General", description="Subject the file belongs to"),
    department: str = Form("", description="Department (e.g. CSM)"),
    year: str = Form("", description="Year (e.g. 2nd Year)"),
    section: str = Form("", description="Section (e.g. Section A)"),
) -> UploadedFile:
    """
    Accept a multipart file upload.  
    Supported formats: **.csv**, **.xlsx**  
    Max recommended size: **10 MB**
    """
    return faculty_service.add_file(file, subject, department, year, section)


@router.delete(
    "/uploads/{file_id}",
    summary="Delete an uploaded document",
)
def delete_upload(file_id: str) -> dict:
    """Permanently remove a document from the store by its ID."""
    return faculty_service.delete_file(file_id)


@router.get(
    "/uploads/{file_id}/analyze",
    response_model=FileAnalysis,
    summary="Parse and analyse a specific uploaded document",
)
def analyze_upload(file_id: str) -> FileAnalysis:
    """
    Reads the stored raw bytes for an uploaded CSV file, auto-detects numeric
    columns, and returns per-column descriptive statistics together with a
    grade-distribution breakdown and per-student marks list ready for charting.

    Pre-seeded demo files (IDs `1`–4`) return representative seeded data.
    """
    return faculty_service.analyze_file(file_id)


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get(
    "/analytics",
    response_model=AnalyticsData,
    summary="Chart data for the Analytics tab",
)
def get_analytics(
    department: str | None = None,
    year: str | None = None,
    section: str | None = None,
    subject: str | None = None,
) -> AnalyticsData:
    """
    Returns student marks (bar), performance trend (line), and grade
    distribution (pie) data.  All query params are optional filters.
    """
    return faculty_service.get_analytics(department, year, section, subject)


# ── Average report ────────────────────────────────────────────────────────────

@router.post(
    "/average",
    response_model=AverageReport,
    summary="Generate an average performance report",
)
def generate_average(body: AverageReportRequest) -> AverageReport:
    """
    Compute an aggregated performance report across **2 or more** selected
    documents.  Provide their IDs in the request body.
    """
    return faculty_service.generate_average_report(body.file_ids)


# ── Filter options ────────────────────────────────────────────────────────────

@router.get(
    "/filter-options",
    response_model=FilterOptions,
    summary="Dropdown options for department / year / section / subject",
)
def get_filter_options() -> FilterOptions:
    """Provides the lists used to populate the filter dropdowns on the frontend."""
    return faculty_service.get_filter_options()
