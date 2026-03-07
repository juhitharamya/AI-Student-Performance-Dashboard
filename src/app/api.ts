/**
 * Typed API client for the AI Student Performance Dashboard backend.
 * Base URL: http://localhost:8000/api/v1
 */

const BASE = "http://localhost:8000/api/v1";

// ── Storage keys ──────────────────────────────────────────────────────────────
export const TOKEN_KEY = "auth_token";
export const PROFILE_KEY = "auth_profile";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthProfile {
    access_token: string;
    token_type: string;
    role: "faculty" | "student";
    name: string;
    avatar_initials: string;
}

export interface MeResponse {
    id: string;
    name: string;
    email: string;
    role: "faculty" | "student";
    avatar_initials: string;
}

export interface UploadedFile {
    id: string;
    name: string;
    date: string;
    subject: string;
    department: string;
    year: string;
    section: string;
    size: string;
}

export interface FacultyStats {
    total_students: number;
    total_students_change: string;
    avg_performance: number;
    avg_performance_change: string;
    total_documents: number;
    total_documents_change: string;
    pass_rate: number;
    pass_rate_change: string;
}

export interface SectionPerf {
    section: string;
    avg: number;
    pass_rate: number;
    total_students: number;
}

export interface AnalyticsData {
    student_marks: { name: string; marks: number }[];
    performance_trend: { month: string; avg: number }[];
    grade_distribution: { name: string; value: number; color: string }[];
    section_breakdown: SectionPerf[];
    student_detail_list: MLPrediction[];
    filters_applied: Record<string, string | null>;
}

export interface AverageReport {
    avg_score: number;
    pass_rate: number;
    highest_score: number;
    lowest_score: number;
    student_marks: { name: string; marks: number }[];
    grade_distribution: { name: string; value: number; color: string }[];
    source_files: string[];
}

export interface StudentListItem {
    file_id: string;
    subject: string;
    name: string;
    roll_no: string;
    marks: number;
}

export interface UploadedFileMarkRow {
    id: string;
    name: string;
    roll_no: string;
    total: number;
    components: Record<string, number | null>;
}

export interface UploadedFileMarksResponse {
    columns: string[];
    rows: UploadedFileMarkRow[];
}

export interface FilterOptions {
    departments: string[];
    years: string[];
    sections: string[];
    subjects: string[];
}

export interface StudentDashboard {
    profile: {
        name: string;
        roll_no: string;
        cgpa: number;
        year: string;
        section: string;
        department: string;
        avatar_initials: string;
        overall_score: string;
        class_rank: number;
        attendance: string;
    };
    subject_performance: {
        subject: string;
        score: number;
        grade: string;
        trend: string;
        color: string;
    }[];
    trend: { month: string; score: number; classAvg: number }[];
    class_comparison: { subject: string; you: number; classAvg: number }[];
    radar: { subject: string; A: number; fullMark: number }[];
    recent_activity: { title: string; date: string; score: string; type: string }[];
    semester_summary: {
        total_credits: number;
        gpa: number;
        best_subject: string;
        assignments_completed: string;
        quizzes_passed: string;
        attendance: string;
        overall_score: string;
        class_rank: number;
    };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
        let detail: string = res.statusText || `HTTP ${res.status}`;
        try {
            const err = await res.json();
            if (err && typeof err === "object" && "detail" in err) {
                const d = (err as { detail?: unknown }).detail;
                if (typeof d === "string") detail = d;
                else detail = JSON.stringify(d);
            } else {
                detail = JSON.stringify(err);
            }
        } catch {
            try {
                const text = await res.text();
                if (text) detail = text;
            } catch {
                // ignore
            }
        }
        throw new Error(`HTTP ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function login(
    email: string,
    password: string,
    role: string
): Promise<AuthProfile> {
    const res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role }),
    });
    return handleResponse<AuthProfile>(res);
}

export async function getMe(): Promise<MeResponse> {
    const res = await fetch(`${BASE}/auth/me`, {
        headers: authHeaders(),
    });
    return handleResponse<MeResponse>(res);
}

export async function logout(): Promise<void> {
    await fetch(`${BASE}/auth/logout`, {
        method: "POST",
        headers: authHeaders(),
    });
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(PROFILE_KEY);
}

// ── Faculty ───────────────────────────────────────────────────────────────────

export async function getFacultyStats(filters?: {
    department?: string;
    year?: string;
    section?: string;
    subject?: string;
}): Promise<FacultyStats> {
    const params = new URLSearchParams();
    if (filters?.department) params.set("department", filters.department);
    if (filters?.year) params.set("year", filters.year);
    if (filters?.section) params.set("section", filters.section);
    if (filters?.subject) params.set("subject", filters.subject);
    const qs = params.toString();
    const url = qs ? `${BASE}/faculty/stats?${qs}` : `${BASE}/faculty/stats`;
    const res = await fetch(url, { headers: authHeaders() });
    return handleResponse<FacultyStats>(res);
}

export async function getUploads(): Promise<UploadedFile[]> {
    const res = await fetch(`${BASE}/faculty/uploads`, { headers: authHeaders() });
    const data = await handleResponse<{ files: UploadedFile[] }>(res);
    return data.files;
}

export async function uploadFile(
    file: File,
    meta: { subject: string; department: string; year: string; section: string }
): Promise<UploadedFile> {
    const form = new FormData();
    form.append("file", file);
    form.append("subject", meta.subject || "General");
    form.append("department", meta.department || "");
    form.append("year", meta.year || "");
    form.append("section", meta.section || "");
    const res = await fetch(`${BASE}/faculty/uploads`, {
        method: "POST",
        headers: authHeaders(),
        body: form,
    });
    return handleResponse<UploadedFile>(res);
}

export async function deleteUpload(fileId: string): Promise<void> {
    const res = await fetch(`${BASE}/faculty/uploads/${fileId}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    await handleResponse<unknown>(res);
}

export async function analyzeUpload(fileId: string): Promise<FileAnalysis> {
    const res = await fetch(`${BASE}/faculty/uploads/${fileId}/analyze`, {
        headers: authHeaders(),
    });
    return handleResponse<FileAnalysis>(res);
}

export async function getUploadMarks(fileId: string): Promise<UploadedFileMarksResponse> {
    const res = await fetch(`${BASE}/faculty/uploads/${fileId}/marks`, {
        headers: authHeaders(),
    });
    return handleResponse<UploadedFileMarksResponse>(res);
}

export async function updateUploadMarks(fileId: string, marks: UploadedFileMarkRow[]): Promise<UploadedFileMarksResponse> {
    const res = await fetch(`${BASE}/faculty/uploads/${fileId}/marks`, {
        method: "PUT",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ marks }),
    });
    return handleResponse<UploadedFileMarksResponse>(res);
}

export async function downloadUploadMarksCsv(fileId: string): Promise<Blob> {
    const res = await fetch(`${BASE}/faculty/uploads/${fileId}/marks/export`, {
        headers: authHeaders(),
    });
    if (!res.ok) {
        // reuse existing error handler for consistent messages
        await handleResponse<unknown>(res);
    }
    return res.blob();
}

export async function getStudentList(fileIds?: string[]): Promise<StudentListItem[]> {
    const params = new URLSearchParams();
    for (const id of fileIds ?? []) params.append("file_ids", id);
    const qs = params.toString();
    const url = qs ? `${BASE}/faculty/students?${qs}` : `${BASE}/faculty/students`;
    const res = await fetch(url, { headers: authHeaders() });
    return handleResponse<StudentListItem[]>(res);
}

export async function getAnalytics(filters?: {
    department?: string;
    year?: string;
    section?: string;
    subject?: string;
}): Promise<AnalyticsData> {
    const params = new URLSearchParams();
    if (filters?.department) params.set("department", filters.department);
    if (filters?.year) params.set("year", filters.year);
    if (filters?.section) params.set("section", filters.section);
    if (filters?.subject) params.set("subject", filters.subject);
    const res = await fetch(`${BASE}/faculty/analytics?${params}`, {
        headers: authHeaders(),
    });
    return handleResponse<AnalyticsData>(res);
}

export interface MLPrediction {
    name: string;
    roll_no: string;
    marks: number;
    predicted_grade: string;
    cluster: string;
    performance_category: string;
    risk_score: number;
    z_score: number;
    pass_probability: number | null;
    predicted_marks: number | null;
    rank: number;
}

export interface ClassInsights {
    mean: number;
    stdev: number;
    pass_rate: number;
    fail_rate: number;
    highest: number;
    lowest: number;
    cluster_distribution: Record<string, number>;
    at_risk_count: number;
    top_performer_count: number;
    failed_count: number;
    topper: { name: string; marks: number } | null;
    lowest_performer: { name: string; marks: number } | null;
    recommendations: string[];
}

export interface FileAnalysis {
    file_id: string;
    file_name: string;
    subject: string;
    department: string;
    year: string;
    section: string;
    row_count: number;
    columns: { name: string; mean: number; median: number; min: number; max: number; stdev: number }[];
    grade_distribution: { name: string; value: number; color: string }[];
    student_marks: { name: string; marks: number }[];
    ml_predictions: MLPrediction[];
    class_insights: ClassInsights | null;
    lr_available: boolean;
    has_multi_column: boolean;
    predicted_vs_actual: { name: string; actual: number; predicted: number }[];
}

export async function generateAverage(fileIds: string[]): Promise<AverageReport> {
    const res = await fetch(`${BASE}/faculty/average`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ file_ids: fileIds }),
    });
    return handleResponse<AverageReport>(res);
}

export async function getFilterOptions(): Promise<FilterOptions> {
    const res = await fetch(`${BASE}/faculty/filter-options`, {
        headers: authHeaders(),
    });
    return handleResponse<FilterOptions>(res);
}

// ── Student ───────────────────────────────────────────────────────────────────

export async function getStudentDashboard(): Promise<StudentDashboard> {
    const res = await fetch(`${BASE}/student/dashboard`, {
        headers: authHeaders(),
    });
    return handleResponse<StudentDashboard>(res);
}
