from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, Response

from app.core.dependencies import require_faculty
from app.schemas.faculty import (
    AnalyticsData,
    AverageReport,
    AverageReportRequest,
    FacultyStats,
    FileAnalysis,
    FilterOptions,
    StudentListItem,
    UploadedFileMarkRow,
    UploadedFileMarksResponse,
    UpdateUploadedFileMarksRequest,
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
def get_stats(
    current_user: dict = Depends(require_faculty),
    department: str | None = None,
    year: str | None = None,
    section: str | None = None,
    subject: str | None = None,
) -> FacultyStats:
    """
    Returns aggregated KPIs shown on the faculty dashboard:
    total students, average performance, document count, and pass rate.
    """
    return faculty_service.get_stats(current_user["id"], department, year, section, subject)


# ── Document management ───────────────────────────────────────────────────────

@router.get(
    "/uploads",
    response_model=UploadedFileList,
    summary="List all uploaded documents",
)
def list_uploads(current_user: dict = Depends(require_faculty)) -> UploadedFileList:
    """Return all uploaded documents stored on the server."""
    return {"files": faculty_service.get_files(current_user["id"])}


@router.post(
    "/uploads",
    response_model=UploadedFile,
    status_code=201,
    summary="Upload a new document",
)
def upload_file(
    current_user: dict = Depends(require_faculty),
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
    return faculty_service.add_file(
        file,
        subject,
        department,
        year,
        section,
        faculty_user_id=current_user["id"],
    )


@router.delete(
    "/uploads/{file_id}",
    summary="Delete an uploaded document",
)
def delete_upload(file_id: str, current_user: dict = Depends(require_faculty)) -> dict:
    """Permanently remove a document from the store by its ID."""
    return faculty_service.delete_file(file_id, current_user["id"])


@router.get(
    "/uploads/{file_id}/analyze",
    response_model=FileAnalysis,
    summary="Parse and analyse a specific uploaded document",
)
def analyze_upload(file_id: str, current_user: dict = Depends(require_faculty)) -> FileAnalysis:
    """
    Reads the stored raw bytes for an uploaded CSV file, auto-detects numeric
    columns, and returns per-column descriptive statistics together with a
    grade-distribution breakdown and per-student marks list ready for charting.

    Pre-seeded demo files (IDs `1`–4`) return representative seeded data.
    """
    return faculty_service.analyze_file(file_id, current_user["id"])


@router.get(
    "/uploads/{file_id}/marks",
    response_model=UploadedFileMarksResponse,
    summary="List persisted marks rows for an upload",
)
def list_upload_marks(file_id: str, current_user: dict = Depends(require_faculty)) -> UploadedFileMarksResponse:
    return faculty_service.get_uploaded_file_marks(file_id, current_user["id"])


@router.put(
    "/uploads/{file_id}/marks",
    response_model=UploadedFileMarksResponse,
    summary="Update persisted marks rows for an upload",
)
def update_upload_marks(
    file_id: str,
    body: UpdateUploadedFileMarksRequest,
    current_user: dict = Depends(require_faculty),
) -> UploadedFileMarksResponse:
    return faculty_service.update_uploaded_file_marks(file_id, current_user["id"], [m.model_dump() for m in body.marks])


@router.get(
    "/uploads/{file_id}/marks/export",
    summary="Download (edited) marks as CSV",
)
def export_upload_marks(file_id: str, current_user: dict = Depends(require_faculty)) -> Response:
    csv_text, filename = faculty_service.export_uploaded_file_marks_csv(file_id, current_user["id"])
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get(
    "/analytics",
    response_model=AnalyticsData,
    summary="Chart data for the Analytics tab",
)
def get_analytics(
    current_user: dict = Depends(require_faculty),
    department: str | None = None,
    year: str | None = None,
    section: str | None = None,
    subject: str | None = None,
) -> AnalyticsData:
    """
    Returns student marks (bar), performance trend (line), and grade
    distribution (pie) data.  All query params are optional filters.
    """
    return faculty_service.get_analytics(current_user["id"], department, year, section, subject)


# ── Average report ────────────────────────────────────────────────────────────

@router.post(
    "/average",
    response_model=AverageReport,
    summary="Generate an average performance report",
)
def generate_average(body: AverageReportRequest, current_user: dict = Depends(require_faculty)) -> AverageReport:
    """
    Compute an aggregated performance report across **2 or more** selected
    documents.  Provide their IDs in the request body.
    """
    return faculty_service.generate_average_report(body.file_ids, current_user["id"])


# ── Filter options ────────────────────────────────────────────────────────────

@router.get(
    "/filter-options",
    response_model=FilterOptions,
    summary="Dropdown options for department / year / section / subject",
)
def get_filter_options() -> FilterOptions:
    """Provides the lists used to populate the filter dropdowns on the frontend."""
    return faculty_service.get_filter_options()


@router.get(
    "/students",
    response_model=list[StudentListItem],
    summary="List students from uploaded marks",
)
def list_students(
    current_user: dict = Depends(require_faculty),
    file_ids: list[str] | None = Query(None, description="Optional uploaded file IDs to scope the list"),
) -> list[StudentListItem]:
    return faculty_service.get_student_list(current_user["id"], file_ids)
