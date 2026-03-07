import { useState, useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import {
  LayoutDashboard, Upload, BarChart3, LogOut, Bell, ChevronDown,
  FileText, Calendar, Trash2, Eye, CheckSquare, X, Menu, Brain, TrendingUp, Pencil,
  Users, GraduationCap, Upload as UploadIcon, Loader2, AlertCircle, InboxIcon
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from "recharts";
import * as api from "../api";
import type { UploadedFile, FacultyStats, AnalyticsData, FilterOptions, SectionPerf, FileAnalysis, StudentListItem, UploadedFileMarkRow } from "../api";

const sidebarItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "upload", label: "Student Marks", icon: Upload },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "students", label: "Student List", icon: Users },
];

interface SelectableFile extends UploadedFile {
  selected: boolean;
}

function ErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
      <AlertCircle className="w-4 h-4 shrink-0" />
      <span className="flex-1">{message}</span>
      <button onClick={onDismiss} className="p-1 hover:bg-red-100 rounded-lg cursor-pointer">
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

function LoadingSpinner({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      <p className="text-sm">{text}</p>
    </div>
  );
}

export function FacultyDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ── Profile from localStorage ──────────────────────────────────────────────
  const profile = JSON.parse(localStorage.getItem(api.PROFILE_KEY) ?? "{}") as api.AuthProfile;

  // Route guard: redirect to login when token is missing/invalid or role is wrong.
  useEffect(() => {
    (async () => {
      try {
        const me = await api.getMe();
        if (me.role !== "faculty") throw new Error("Wrong role");
      } catch {
        localStorage.removeItem(api.TOKEN_KEY);
        localStorage.removeItem(api.PROFILE_KEY);
        navigate("/");
      }
    })();
  }, [navigate]);

  // ── Dashboard tab state ────────────────────────────────────────────────────
  const [stats, setStats] = useState<FacultyStats | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [dashLoading, setDashLoading] = useState(true);
  const [dashError, setDashError] = useState("");
  const [dashDept, setDashDept] = useState("");
  const [dashYear, setDashYear] = useState("");
  const [dashSection, setDashSection] = useState("");
  const [dashSubject, setDashSubject] = useState("");
  const [dashTestType, setDashTestType] = useState("");
  const [dashFilterApplied, setDashFilterApplied] = useState<Record<string, string>>({});
  const [recentUploads, setRecentUploads] = useState<UploadedFile[]>([]);
  const [recentUploadsLoading, setRecentUploadsLoading] = useState(false);
  const [recentUploadsError, setRecentUploadsError] = useState("");

  // ── Upload tab state ───────────────────────────────────────────────────────
  const [files, setFiles] = useState<SelectableFile[]>([]);
  const [uploadsLoading, setUploadsLoading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [viewingFile, setViewingFile] = useState<SelectableFile | null>(null);
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [editingFile, setEditingFile] = useState<SelectableFile | null>(null);
  const [editColumns, setEditColumns] = useState<string[]>([]);
  const [editMarks, setEditMarks] = useState<
    (Omit<UploadedFileMarkRow, "components"> & { components: Record<string, string> })[]
  >([]);
  const [editLoading, setEditLoading] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Analytics tab state ────────────────────────────────────────────────────
  const [department, setDepartment] = useState("");
  const [year, setYear] = useState("");
  const [section, setSection] = useState("");
  const [subject, setSubject] = useState("");
  const [testType, setTestType] = useState("");
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    departments: [], years: [], sections: [], subjects: [], test_types: [],
  });
  const [analyticsTab, setAnalyticsTab] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState("");

  // ── Average tab state ──────────────────────────────────────────────────────
  const [studentList, setStudentList] = useState<StudentListItem[]>([]);
  const [studentListLoading, setStudentListLoading] = useState(false);
  const [studentListError, setStudentListError] = useState("");
  const [studentDept, setStudentDept] = useState("");
  const [studentYear, setStudentYear] = useState("");
  const [studentSection, setStudentSection] = useState("");

  const selectedFiles = files.filter((f) => f.selected);
  const totalCandidates = editColumns.filter((c) => /total|marks|overall|grand/i.test(c.trim().toLowerCase()));
  const totalKeyScore = (c: string) => {
    const s = c.trim().toLowerCase();
    if (s.includes("total")) return 3;
    if (s.includes("marks")) return 2;
    if (s.includes("overall") || s.includes("grand")) return 1;
    return 0;
  };
  const editTotalKey = totalCandidates.length > 0
    ? [...totalCandidates].sort((a, b) => totalKeyScore(b) - totalKeyScore(a))[0]
    : null;
  const editComponentCols = totalCandidates.length > 0
    ? editColumns.filter((c) => !totalCandidates.includes(c))
    : editColumns;

  const loadStudentList = useCallback(async (fileIds?: string[]) => {
    setStudentListLoading(true);
    setStudentListError("");
    try {
      const rows = await api.getStudentList({
        fileIds,
        department: studentDept || undefined,
        year: studentYear || undefined,
        section: studentSection || undefined,
      });
      setStudentList(rows);
    } catch (e: unknown) {
      setStudentListError(e instanceof Error ? e.message : "Failed to load student list");
    } finally {
      setStudentListLoading(false);
    }
  }, [studentDept, studentYear, studentSection]);

  // ── Logout ─────────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    await api.logout();
    navigate("/");
  };

  // ── Load dashboard data on mount ───────────────────────────────────────────
  useEffect(() => {
    (async () => {
      setDashLoading(true);
      try {
        const [s, a] = await Promise.all([api.getFacultyStats(), api.getAnalytics()]);
        setStats(s);
        setAnalytics(a);
      } catch (e: unknown) {
        setDashError(e instanceof Error ? e.message : "Failed to load dashboard");
      } finally {
        setDashLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (activeTab !== "dashboard") return;
    (async () => {
      setRecentUploadsLoading(true);
      setRecentUploadsError("");
      try {
        const list = await api.getUploads();
        setRecentUploads(list);
      } catch (e: unknown) {
        setRecentUploadsError(e instanceof Error ? e.message : "Failed to load recent uploads");
      } finally {
        setRecentUploadsLoading(false);
      }
    })();
  }, [activeTab]);

  // ── Dashboard View button ────────────────────────────────────────────
  const handleDashView = useCallback(async () => {
    setDashLoading(true);
    setDashError("");
    try {
      const filters = {
        department: dashDept || undefined,
        year: dashYear || undefined,
        section: dashSection || undefined,
        subject: dashSubject || undefined,
        test_type: dashTestType || undefined,
      };
      const [s, a] = await Promise.all([api.getFacultyStats(filters), api.getAnalytics(filters)]);
      setStats(s);
      setAnalytics(a);
      const applied: Record<string, string> = {};
      if (dashDept) applied["Department"] = dashDept;
      if (dashYear) applied["Year"] = dashYear;
      if (dashSection) applied["Section"] = dashSection;
      if (dashSubject) applied["Subject"] = dashSubject;
      if (dashTestType) applied["Test"] = dashTestType;
      setDashFilterApplied(applied);
    } catch (e: unknown) {
      setDashError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setDashLoading(false);
    }
  }, [dashDept, dashYear, dashSection, dashSubject, dashTestType]);

  // ── Load uploads when upload tab is opened ─────────────────────────────────
  useEffect(() => {
    if (activeTab !== "upload" && activeTab !== "students") return;
    (async () => {
      setUploadsLoading(true);
      try {
        const list = await api.getUploads();
        setFiles(list.map((f) => ({ ...f, selected: false })));
      } catch (e: unknown) {
        setUploadError(e instanceof Error ? e.message : "Failed to load files");
      } finally {
        setUploadsLoading(false);
      }
    })();
  }, [activeTab]);

  // ── Load filter options once ────────────────────────────────────────────────
  useEffect(() => {
    if (activeTab !== "students") return;
    const ids = selectedFiles.length > 0 ? selectedFiles.map((f) => f.id) : undefined;
    if (!ids && !studentDept && !studentYear && !studentSection) {
      setStudentList([]);
      return;
    }
    loadStudentList(ids);
    // We intentionally only fetch on tab open; use the Refresh button after changing selection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, loadStudentList, selectedFiles.length, studentDept, studentYear, studentSection]);

  useEffect(() => {
    api.getFilterOptions().then(setFilterOptions).catch(() => { });
  }, []);

  // ── Load analytics when analytics tab is opened or filters change ──────────
  useEffect(() => {
    if (activeTab !== "analytics") return;
    (async () => {
      setAnalyticsLoading(true);
      setAnalyticsError("");
      try {
        const a = await api.getAnalytics({ department, year, section, subject, test_type: testType || undefined });
        setAnalyticsTab(a);
      } catch (e: unknown) {
        setAnalyticsError(e instanceof Error ? e.message : "Failed to load analytics");
      } finally {
        setAnalyticsLoading(false);
      }
    })();
  }, [activeTab, department, year, section, subject, testType]);

  // ── File helpers ───────────────────────────────────────────────────────────
  const handleUploadFile = useCallback(async (file: File) => {
    setUploading(true);
    setUploadError("");
    try {
      const newFile = await api.uploadFile(file, {
        subject: subject || "General",
        department: department || "",
        year: year || "",
        section: section || "",
      });
      setFiles((prev) => [{ ...newFile, selected: false }, ...prev]);
      setRecentUploads((prev) => [newFile, ...prev]);
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [subject, department, year, section]);

  const handleOpenFile = useCallback(async (file: SelectableFile) => {
    setViewingFile(file);
    setFileAnalysis(null);
    setAnalyzeError("");
    setAnalyzeLoading(true);
    try {
      const result = await api.analyzeUpload(file.id);
      setFileAnalysis(result);
    } catch (e: unknown) {
      setAnalyzeError(e instanceof Error ? e.message : "Could not load analysis");
    } finally {
      setAnalyzeLoading(false);
    }
  }, []);

  const handleCloseModal = useCallback(() => {
    setViewingFile(null);
    setFileAnalysis(null);
    setAnalyzeError("");
  }, []);

  const handleCloseEditModal = useCallback(() => {
    setEditingFile(null);
    setEditColumns([]);
    setEditMarks([]);
    setEditError("");
    setEditLoading(false);
    setEditSaving(false);
  }, []);

  const handleEditFile = useCallback(async (file: SelectableFile) => {
    setEditingFile(file);
    setEditError("");
    setEditLoading(true);
    try {
      const payload = await api.getUploadMarks(file.id);
      setEditColumns(payload.columns);
      setEditMarks(
        payload.rows.map((r) => ({
          id: r.id,
          name: r.name,
          roll_no: r.roll_no,
          total: r.total,
          components: Object.fromEntries(
            (payload.columns ?? []).map((c) => [c, r.components?.[c] == null ? "" : String(r.components[c])])
          ),
        }))
      );
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Failed to load marks");
    } finally {
      setEditLoading(false);
    }
  }, []);

  const handleSaveEditedMarks = useCallback(async () => {
    if (!editingFile) return;
    setEditSaving(true);
    setEditError("");
    try {
      const payload: UploadedFileMarkRow[] = editMarks.map((r) => {
        const components: Record<string, number | null> = {};
        for (const c of editColumns) {
          const raw = (r.components?.[c] ?? "").trim();
          if (!raw) {
            components[c] = null;
            continue;
          }
          const v = Number(raw);
          if (!Number.isFinite(v)) throw new Error(`Invalid number for "${c}" (student: ${r.name})`);
          components[c] = v;
        }
        return { id: r.id, name: r.name, roll_no: r.roll_no, total: r.total, components };
      });
      const updated = await api.updateUploadMarks(editingFile.id, payload);
      setEditColumns(updated.columns);
      setEditMarks(
        updated.rows.map((r) => ({
          id: r.id,
          name: r.name,
          roll_no: r.roll_no,
          total: r.total,
          components: Object.fromEntries(updated.columns.map((c) => [c, r.components?.[c] == null ? "" : String(r.components[c])])),
        }))
      );
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Failed to save marks");
    } finally {
      setEditSaving(false);
    }
  }, [editingFile, editMarks, editColumns]);

  const handleDownloadEditedCsv = useCallback(async () => {
    if (!editingFile) return;
    setEditError("");
    try {
      const blob = await api.downloadUploadMarksCsv(editingFile.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const base = (editingFile.name || "marks").replace(/\.[^.]+$/, "");
      a.href = url;
      a.download = `${base}_edited.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Failed to download CSV");
    }
  }, [editingFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUploadFile(file);
  }, [handleUploadFile]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUploadFile(file);
    e.target.value = "";
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteUpload(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
      setRecentUploads((prev) => prev.filter((f) => f.id !== id));
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const toggleFileSelect = (id: string) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, selected: !f.selected } : f)));
  };

  // ── Reusable sub-components ────────────────────────────────────────────────
  const SelectDropdown = (
    { label, value, onChange, options, includeAll = true }:
    { label: string; value: string; onChange: (v: string) => void; options: string[]; includeAll?: boolean }
  ) => (
    <div>
      <label className="text-sm text-gray-500 mb-1.5 block">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2.5 rounded-xl border border-gray-200 bg-white appearance-none cursor-pointer text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all"
        >
          {includeAll ? (
            <option value="">All {label}s</option>
          ) : (
            <option value="">Select {label}</option>
          )}
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
    </div>
  );

  // ── Stat cards derived from API data ───────────────────────────────────────
  const statsCards = stats ? [
    { label: "Total Students", value: stats.total_students.toString(), change: stats.total_students_change, icon: Users, color: "from-indigo-500 to-indigo-600" },
    { label: "Avg Performance", value: `${stats.avg_performance}%`, change: stats.avg_performance_change, icon: TrendingUp, color: "from-purple-500 to-purple-600" },
    { label: "Documents", value: stats.total_documents.toString(), change: stats.total_documents_change, icon: FileText, color: "from-blue-500 to-blue-600" },
    { label: "Pass Rate", value: `${stats.pass_rate}%`, change: stats.pass_rate_change, icon: GraduationCap, color: "from-cyan-500 to-cyan-600" },
  ] : [];

  return (
    <div className="min-h-screen bg-background flex">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx,.pdf"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-100 flex flex-col transition-transform duration-300 ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-sm text-foreground">EduAnalytics</p>
              <p className="text-xs text-muted-foreground">Faculty Panel</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {sidebarItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); setSidebarOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm cursor-pointer ${activeTab === id
                ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg shadow-indigo-500/25"
                : "text-gray-600 hover:bg-gray-50"
                }`}
            >
              <Icon className="w-5 h-5" />
              {label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all text-sm cursor-pointer"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="bg-white border-b border-gray-100 px-4 lg:px-8 py-4 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2 hover:bg-gray-100 rounded-lg cursor-pointer">
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg text-foreground">
                {activeTab === "dashboard" && "Dashboard Overview"}
                {activeTab === "upload" && "Student Marks"}
                {activeTab === "analytics" && "Performance Analytics"}
                {activeTab === "students" && "Student List"}
              </h1>
              <p className="text-sm text-muted-foreground">
                Welcome back, {profile.name || "Faculty"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative p-2 hover:bg-gray-100 rounded-lg cursor-pointer">
              <Bell className="w-5 h-5 text-gray-500" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
            <div className="flex items-center gap-2 pl-3 border-l border-gray-200">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-sm">
                {profile.avatar_initials || "??"}
              </div>
              <div className="hidden md:block">
                <p className="text-sm text-foreground">{profile.name?.split(" ").slice(-1)[0] || "Faculty"}</p>
                <p className="text-xs text-muted-foreground">Professor</p>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">

          {/* ── Dashboard Tab ────────────────────────────────────────────── */}
          {activeTab === "dashboard" && (
            dashLoading ? <LoadingSpinner text="Loading dashboard…" /> :
              dashError ? <ErrorBanner message={dashError} onDismiss={() => setDashError("")} /> :
                <div className="space-y-6">
                  {/* Filter Bar */}
                  <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                    <p className="text-sm text-gray-500 mb-3">Filter Dashboard</p>
                    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                      <SelectDropdown label="Department" value={dashDept} onChange={setDashDept} options={filterOptions.departments} />
                      <SelectDropdown label="Year" value={dashYear} onChange={setDashYear} options={filterOptions.years} />
                      <SelectDropdown label="Section" value={dashSection} onChange={setDashSection} options={filterOptions.sections} />
                      <SelectDropdown label="Subject" value={dashSubject} onChange={setDashSubject} options={filterOptions.subjects} />
                      <SelectDropdown label="Test" value={dashTestType} onChange={setDashTestType} options={filterOptions.test_types} />
                      <div className="flex items-end">
                        <button
                          onClick={handleDashView}
                          className="w-full px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm hover:opacity-90 transition-opacity cursor-pointer"
                        >
                          View
                        </button>
                      </div>
                    </div>
                    {Object.keys(dashFilterApplied).length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        <span className="text-xs text-gray-400">Showing:</span>
                        {Object.entries(dashFilterApplied).map(([k, v]) => (
                          <span key={k} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">{k}: {v}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {statsCards.map(({ label, value, change, icon: Icon, color }) => (
                      <div key={label} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-3">
                          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
                            <Icon className="w-5 h-5 text-white" />
                          </div>
                          <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">{change}</span>
                        </div>
                        <p className="text-2xl text-foreground">{value}</p>
                        <p className="text-sm text-muted-foreground">{label}</p>
                      </div>
                    ))}
                  </div>

                  {/* Charts Row */}
                  {analytics && analytics.student_marks.length > 0 ? (
                    <>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                          <h3 className="text-foreground mb-4">Student Marks Distribution</h3>
                          <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={analytics.student_marks}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                              <Bar dataKey="marks" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
                              <defs>
                                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="0%" stopColor="#6366f1" />
                                  <stop offset="100%" stopColor="#8b5cf6" />
                                </linearGradient>
                              </defs>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                          <h3 className="text-foreground mb-4">Grade Distribution</h3>
                          <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                              <Pie data={analytics.grade_distribution} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value">
                                {analytics.grade_distribution.map((entry) => (
                                  <Cell key={entry.name} fill={entry.color} />
                                ))}
                              </Pie>
                              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                              <Legend />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                          <h3 className="text-foreground mb-4">Performance Trend</h3>
                          <ResponsiveContainer width="100%" height={220}>
                            <LineChart data={analytics.performance_trend}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                              <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                              <Line type="monotone" dataKey="avg" stroke="#6366f1" strokeWidth={3} dot={{ fill: "#6366f1", strokeWidth: 2, r: 5 }} activeDot={{ r: 7 }} />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                          <h3 className="text-foreground mb-4">Recent Uploads</h3>
                          <div className="space-y-3">
                            {recentUploadsLoading ? (
                              <div className="text-center py-10 text-gray-400 text-sm">Loading uploadsâ€¦</div>
                            ) : recentUploadsError ? (
                              <div className="text-center py-10 text-red-600 text-sm">{recentUploadsError}</div>
                            ) : recentUploads.length === 0 ? (
                              <div className="text-center py-10 text-gray-400 text-sm">No uploads yet</div>
                            ) : recentUploads.slice(0, 4).map((file) => (
                              <div key={file.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 hover:bg-indigo-50 transition-colors">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-indigo-600" />
                                  </div>
                                  <div>
                                    <p className="text-sm text-foreground">{file.name}</p>
                                    <p className="text-xs text-muted-foreground">{file.subject} &middot; {file.size}</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-muted-foreground hidden sm:block">{file.date}</span>
                                  <Calendar className="w-4 h-4 text-gray-400" />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-16 text-center text-gray-400">
                      <InboxIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p className="text-sm mb-1">No data yet</p>
                      <p className="text-xs mb-4">Upload a CSV or XLSX file and click View to see filtered results.</p>
                      <button onClick={() => setActiveTab("upload")} className="px-5 py-2 bg-indigo-600 text-white rounded-xl text-sm hover:bg-indigo-700 transition-colors cursor-pointer">
                        Go to Upload
                      </button>
                    </div>
                  )}
                </div>
          )}

          {/* \u2500\u2500 Upload Tab \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */}
          {activeTab === "upload" && (
            <div className="space-y-6">
              {/* Filters */}
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-foreground mb-4">Select Parameters</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                  <SelectDropdown label="Department" value={department} onChange={setDepartment} options={filterOptions.departments} />
                  <SelectDropdown label="Year" value={year} onChange={setYear} options={filterOptions.years} />
                  <SelectDropdown label="Section" value={section} onChange={setSection} options={filterOptions.sections} />
                  <SelectDropdown label="Subject" value={subject} onChange={setSubject} options={filterOptions.subjects} />
                  <SelectDropdown label="Test" value={testType} onChange={setTestType} options={filterOptions.test_types} />
                </div>
              </div>

              {uploadError && <ErrorBanner message={uploadError} onDismiss={() => setUploadError("")} />}

              <div className="grid grid-cols-1 gap-6">
                <div className="space-y-6">
                  {/* Drag & Drop */}
                  <div
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`bg-white rounded-2xl border-2 border-dashed p-10 text-center transition-all cursor-pointer ${dragOver ? "border-indigo-500 bg-indigo-50" : "border-gray-200 hover:border-indigo-300"
                      }`}
                  >
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                      {uploading ? (
                        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                      ) : (
                        <UploadIcon className="w-8 h-8 text-indigo-600" />
                      )}
                    </div>
                    <p className="text-foreground mb-1">
                      {uploading ? "Uploading…" : "Drag & drop files here"}
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">Support CSV, XLSX, PDF files up to 10MB</p>
                    <button
                      onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                      disabled={uploading}
                      className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg shadow-indigo-500/25 cursor-pointer disabled:opacity-50"
                    >
                      Browse Files
                    </button>
                  </div>

                  {/* Uploaded Files List */}
                  <div>
                    <h3 className="text-foreground mb-4">
                      Uploaded Files
                      {files.length > 0 && <span className="text-sm text-muted-foreground ml-2">({files.length})</span>}
                    </h3>
                    {uploadsLoading ? (
                      <LoadingSpinner text="Loading files…" />
                    ) : files.length === 0 ? (
                      <div className="text-center py-12 text-gray-400 text-sm">No files uploaded yet</div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {files.map((file) => (
                          <div
                            key={file.id}
                            className={`bg-white rounded-xl p-4 border transition-all ${file.selected ? "border-indigo-500 shadow-md shadow-indigo-500/10" : "border-gray-100 shadow-sm"
                              }`}
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <button onClick={() => toggleFileSelect(file.id)} className="cursor-pointer">
                                  <CheckSquare className={`w-5 h-5 ${file.selected ? "text-indigo-600" : "text-gray-300"}`} />
                                </button>
                                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                                  <FileText className="w-5 h-5 text-indigo-600" />
                                </div>
                              </div>
                              <div className="flex gap-1">
                                <button onClick={() => handleOpenFile(file)} className="p-1.5 hover:bg-indigo-50 rounded-lg cursor-pointer">
                                  <Eye className="w-4 h-4 text-gray-400 hover:text-indigo-600" />
                                </button>
                                <button onClick={() => handleEditFile(file)} className="p-1.5 hover:bg-purple-50 rounded-lg cursor-pointer">
                                  <Pencil className="w-4 h-4 text-gray-400 hover:text-purple-600" />
                                </button>
                                <button onClick={() => handleDelete(file.id)} className="p-1.5 hover:bg-red-50 rounded-lg cursor-pointer">
                                  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-600" />
                                </button>
                              </div>
                            </div>
                            <p className="text-sm text-foreground truncate">{file.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-muted-foreground">{file.date}</span>
                              <span className="text-xs text-muted-foreground">·</span>
                              <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">{file.subject}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>
          )
          }

          {/* ── Analytics Tab ─────────────────────────────────────────────── */}
          {
            activeTab === "analytics" && (
              <div className="space-y-6">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <h3 className="text-foreground mb-4">Select Parameters</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                    <SelectDropdown label="Department" value={department} onChange={setDepartment} options={filterOptions.departments} />
                    <SelectDropdown label="Year" value={year} onChange={setYear} options={filterOptions.years} />
                    <SelectDropdown label="Section" value={section} onChange={setSection} options={filterOptions.sections} />
                    <SelectDropdown label="Subject" value={subject} onChange={setSubject} options={filterOptions.subjects} />
                    <SelectDropdown label="Test" value={testType} onChange={setTestType} options={filterOptions.test_types} />
                  </div>
                </div>

                {analyticsError && <ErrorBanner message={analyticsError} onDismiss={() => setAnalyticsError("")} />}

                {analyticsLoading ? <LoadingSpinner text="Loading analytics…" /> : analyticsTab && analyticsTab.student_marks.length > 0 ? (
                  <>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Student Marks</h3>
                        <p className="text-sm text-muted-foreground mb-4">Individual student performance in selected subject</p>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={analyticsTab.student_marks}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                            <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                            <Bar dataKey="marks" fill="url(#barGradient2)" radius={[6, 6, 0, 0]} />
                            <defs>
                              <linearGradient id="barGradient2" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#6366f1" />
                                <stop offset="100%" stopColor="#8b5cf6" />
                              </linearGradient>
                            </defs>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Performance Trend</h3>
                        <p className="text-sm text-muted-foreground mb-4">Class average over time</p>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={analyticsTab.performance_trend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                            <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                            <Line type="monotone" dataKey="avg" stroke="#8b5cf6" strokeWidth={3} dot={{ fill: "#8b5cf6", strokeWidth: 2, r: 5 }} activeDot={{ r: 7 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Grade Distribution</h3>
                        <p className="text-sm text-muted-foreground mb-4">Overall grade breakdown</p>
                        <ResponsiveContainer width="100%" height={280}>
                          <PieChart>
                            <Pie data={analyticsTab.grade_distribution} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={4} dataKey="value">
                              {analyticsTab.grade_distribution.map((entry) => (
                                <Cell key={entry.name} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Key Insights</h3>
                        <p className="text-sm text-muted-foreground mb-4">Performance analysis based on uploaded data</p>
                        <div className="space-y-3">
                          {(() => {
                            const marks = analyticsTab.student_marks;
                            const vals = marks.map(m => m.marks);
                            const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
                            const top = marks.reduce((a, b) => b.marks > a.marks ? b : a, marks[0]);
                            const atRisk = marks.filter(m => m.marks < avg);
                            const passRate = Math.round(100 * vals.filter(v => v >= 40).length / vals.length);
                            const gradeB = Math.round(100 * vals.filter(v => v >= 70).length / vals.length);
                            return [
                              { title: "Top Performer", desc: `${top.name} scored highest with ${top.marks}/100.`, color: "bg-green-50 text-green-700 border-green-200" },
                              { title: "At Risk", desc: atRisk.length > 0 ? `${atRisk.map(m => m.name).slice(0, 3).join(", ")} scored below class average (${Math.round(avg)}).` : "No students below class average.", color: "bg-amber-50 text-amber-700 border-amber-200" },
                              { title: "Class Average", desc: `Average score is ${Math.round(avg)}/100 across ${vals.length} students.`, color: "bg-blue-50 text-blue-700 border-blue-200" },
                              { title: "Grade Distribution", desc: `${gradeB}% scored B grade or above. Pass rate: ${passRate}%.`, color: "bg-purple-50 text-purple-700 border-purple-200" },
                            ].map(({ title, desc, color }) => (
                              <div key={title} className={`p-4 rounded-xl border ${color}`}>
                                <p className="text-sm mb-0.5">{title}</p>
                                <p className="text-xs opacity-80">{desc}</p>
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    </div>

                    {/* Section Performance Breakdown */}
                    {analyticsTab!.section_breakdown.length > 0 && (
                      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Section-wise Performance</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Average marks and pass rate per section
                          {department ? ` — ${department}` : ""}
                          {year ? ` · ${year}` : ""}
                          {subject ? ` · ${subject}` : ""}
                        </p>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <ResponsiveContainer width="100%" height={260}>
                            <BarChart data={analyticsTab!.section_breakdown} barCategoryGap="30%">
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                              <XAxis dataKey="section" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                              <Tooltip
                                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
                                formatter={(val: number, name: string) =>
                                  [val, name === "avg" ? "Avg Score" : "Pass Rate %"]
                                }
                              />
                              <Legend />
                              <Bar dataKey="avg" name="Avg Score" fill="#6366f1" radius={[6, 6, 0, 0]} />
                              <Bar dataKey="pass_rate" name="Pass Rate %" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                          <div className="space-y-3 pt-1">
                            {(analyticsTab!.section_breakdown as SectionPerf[]).map((s) => (
                              <div key={s.section} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
                                <div>
                                  <p className="text-sm text-foreground">{s.section}</p>
                                  <p className="text-xs text-muted-foreground">{s.total_students} students</p>
                                </div>
                                <div className="flex gap-4 text-right">
                                  <div>
                                    <p className="text-sm text-indigo-600">{s.avg}</p>
                                    <p className="text-xs text-muted-foreground">Avg</p>
                                  </div>
                                  <div>
                                    <p className="text-sm text-purple-600">{s.pass_rate}%</p>
                                    <p className="text-xs text-muted-foreground">Pass</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Student Detail Table */}
                    {(analyticsTab!.student_detail_list?.length ?? 0) > 0 && (
                      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                        <h3 className="text-foreground mb-1">Student Performance Detail</h3>
                        <p className="text-sm text-muted-foreground mb-4">Individual ML analysis — ranked by marks</p>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-100">
                                {["Rank", "Roll No", "Name", "Marks", "Grade", "Category", "Risk"].map(h => (
                                  <th key={h} className="text-left py-3 px-3 text-xs text-gray-400 font-medium">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {analyticsTab!.student_detail_list!.map((p) => {
                                const catColor = p.performance_category === "Excellent" ? "bg-green-100 text-green-700" : p.performance_category === "Good" ? "bg-blue-100 text-blue-700" : p.performance_category === "At Risk" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700";
                                const gradeColor = p.predicted_grade === "A" ? "text-green-600" : p.predicted_grade === "B" ? "text-blue-600" : p.predicted_grade === "C" ? "text-yellow-600" : p.predicted_grade === "D" ? "text-orange-600" : "text-red-600";
                                return (
                                  <tr key={p.name} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                                    <td className="py-3 px-3 text-gray-500 font-medium">#{p.rank}</td>
                                    <td className="py-3 px-3 text-gray-500">{p.roll_no || "—"}</td>
                                    <td className="py-3 px-3 text-foreground font-medium">{p.name}</td>
                                    <td className="py-3 px-3 text-foreground">{p.marks}</td>
                                    <td className={`py-3 px-3 font-bold ${gradeColor}`}>{p.predicted_grade}</td>
                                    <td className="py-3 px-3"><span className={`px-2 py-0.5 rounded-full text-xs ${catColor}`}>{p.performance_category}</span></td>
                                    <td className="py-3 px-3">
                                      <div className="flex items-center gap-2">
                                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden" style={{ minWidth: 60 }}>
                                          <div className={`h-full rounded-full ${p.risk_score > 70 ? "bg-red-500" : p.risk_score > 40 ? "bg-yellow-400" : "bg-green-500"}`} style={{ width: `${p.risk_score}%` }} />
                                        </div>
                                        <span className="text-xs text-gray-400 shrink-0">{p.risk_score}%</span>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                  </>
                ) : !analyticsLoading && (
                  <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-16 text-center text-gray-400">
                    <InboxIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm mb-1">No data yet</p>
                    <p className="text-xs mb-4">Upload a CSV or XLSX with student names and marks to see analytics here.</p>
                    <button
                      onClick={() => setActiveTab("upload")}
                      className="px-5 py-2 bg-indigo-600 text-white rounded-xl text-sm hover:bg-indigo-700 transition-colors cursor-pointer"
                    >
                      Go to Upload
                    </button>
                  </div>
                )}
              </div>
            )
          }

          {/* ── Student List Tab ─────────────────────────────────────────── */}
          {
            activeTab === "students" && (
              <div className="space-y-6">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div>
                      <h3 className="text-foreground mb-1">Student List</h3>
                      <p className="text-sm text-muted-foreground">Students and marks parsed from your uploaded documents.</p>
                    </div>
                    <button
                      onClick={() => loadStudentList(selectedFiles.length > 0 ? selectedFiles.map((f) => f.id) : undefined)}
                      disabled={
                        studentListLoading ||
                        (selectedFiles.length === 0 && !studentDept && !studentYear && !studentSection)
                      }
                      className="px-5 py-2.5 rounded-xl text-sm transition-all cursor-pointer flex items-center gap-2 bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {studentListLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Refreshing…</> : "Refresh"}
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-4">
                    Tip: Select one or more files in <span className="text-foreground">Student Marks</span> to filter this list.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                    <SelectDropdown label="Department" value={studentDept} onChange={setStudentDept} options={filterOptions.departments} includeAll={false} />
                    <SelectDropdown label="Year" value={studentYear} onChange={setStudentYear} options={filterOptions.years} includeAll={false} />
                    <SelectDropdown label="Section" value={studentSection} onChange={setStudentSection} options={filterOptions.sections} includeAll={false} />
                  </div>
                </div>

                {studentListError && <ErrorBanner message={studentListError} onDismiss={() => setStudentListError("")} />}

                {studentListLoading ? (
                  <LoadingSpinner text="Loading students…" />
                ) : studentList.length === 0 ? (
                  <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-16 text-center text-gray-400">
                    <InboxIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm mb-1">No student data yet</p>
                    <p className="text-xs mb-4">Upload a CSV/XLSX marks sheet to populate the student list.</p>
                    <button
                      onClick={() => setActiveTab("upload")}
                      className="px-5 py-2 bg-indigo-600 text-white rounded-xl text-sm hover:bg-indigo-700 transition-colors cursor-pointer"
                    >
                      Go to Upload
                    </button>
                  </div>
                ) : (
                  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-foreground">Students</h3>
                      <p className="text-sm text-muted-foreground">{studentList.length} rows</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500 border-b">
                            <th className="py-3 pr-4 font-medium">Roll No</th>
                            <th className="py-3 pr-4 font-medium">Name</th>
                            <th className="py-3 pr-4 font-medium">Subject</th>
                            <th className="py-3 pr-4 font-medium">Marks</th>
                            <th className="py-3 pr-4 font-medium">File</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {[...studentList]
                            .sort((a, b) => (a.roll_no ?? a.name).localeCompare(b.roll_no ?? b.name))
                            .map((row) => {
                              const fileName = files.find((f) => f.id === row.file_id)?.name ?? row.file_id;
                              return (
                                <tr key={`${row.file_id}:${row.roll_no ?? row.name}:${row.subject}`} className="hover:bg-gray-50">
                                  <td className="py-3 pr-4 text-foreground">{row.roll_no ?? "—"}</td>
                                  <td className="py-3 pr-4 text-foreground">{row.name}</td>
                                  <td className="py-3 pr-4">
                                    <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">{row.subject}</span>
                                  </td>
                                  <td className="py-3 pr-4 text-foreground">{Number.isFinite(row.marks) ? Math.round(row.marks) : row.marks}</td>
                                  <td className="py-3 pr-4 text-muted-foreground truncate max-w-[240px]">{fileName}</td>
                                </tr>
                              );
                            })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )
          }

          {/* ── Edit Marks Modal ─────────────────────────────────────────── */}
          {
            editingFile && (
              <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={handleCloseEditModal}>
                <div
                  className="bg-white rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                        <Pencil className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="text-foreground text-sm">Edit Student Marks</h3>
                        <p className="text-xs text-muted-foreground truncate max-w-[52ch]">
                          {editingFile.name} &middot; {editingFile.subject} &middot; {editingFile.date}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleDownloadEditedCsv}
                        disabled={editLoading || editSaving}
                        className="px-3 py-2 rounded-xl text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors cursor-pointer disabled:opacity-50"
                      >
                        Download CSV
                      </button>
                      <button
                        onClick={handleSaveEditedMarks}
                        disabled={editLoading || editSaving}
                        className="px-3 py-2 rounded-xl text-sm bg-indigo-600 hover:bg-indigo-700 text-white transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-2"
                      >
                        {editSaving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</> : "Save"}
                      </button>
                      <button onClick={handleCloseEditModal} className="p-2 hover:bg-gray-100 rounded-xl cursor-pointer">
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  <div className="p-6 overflow-auto">
                    {editError && <div className="mb-4"><ErrorBanner message={editError} onDismiss={() => setEditError("")} /></div>}

                    {editLoading ? (
                      <LoadingSpinner text="Loading marks…" />
                    ) : (
                      editColumns.length === 0 ? (
                        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center text-gray-400">
                          <InboxIcon className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                          <p className="text-sm mb-1">No component columns found</p>
                          <p className="text-xs">This upload only has Total marks, or the database migration for per-component marks isn’t applied.</p>
                        </div>
                      ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 border-b">
                              <th className="py-3 pr-4 font-medium sticky top-0 left-0 bg-white z-30 min-w-[200px] border-r border-gray-100">Roll No</th>
                              <th className="py-3 pr-4 font-medium sticky top-0 left-[200px] bg-white z-30 min-w-[240px] border-r border-gray-100">Name</th>
                              {editComponentCols.map((c) => (
                                <th key={c} className="py-3 pr-4 font-medium whitespace-nowrap sticky top-0 bg-white z-10">{c}</th>
                              ))}
                              <th className="py-3 pr-4 font-medium sticky top-0 bg-white z-10">Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {editMarks.map((row) => (
                              <tr key={row.id} className="hover:bg-gray-50">
                                <td className="py-2 pr-4 sticky left-0 bg-white z-20 border-r border-gray-100">
                                  <input
                                    value={row.roll_no ?? ""}
                                    onChange={(e) => setEditMarks((prev) => prev.map((r) => (r.id === row.id ? { ...r, roll_no: e.target.value } : r)))}
                                    className="w-full min-w-[200px] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
                                    placeholder="Roll No"
                                  />
                                </td>
                                <td className="py-2 pr-4 sticky left-[200px] bg-white z-20 border-r border-gray-100">
                                  <input
                                    value={row.name}
                                    onChange={(e) => setEditMarks((prev) => prev.map((r) => (r.id === row.id ? { ...r, name: e.target.value } : r)))}
                                    className="w-full min-w-[240px] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
                                    placeholder="Student name"
                                  />
                                </td>
                                {editComponentCols.map((col) => (
                                  <td key={col} className="py-2 pr-4">
                                    <input
                                      value={row.components?.[col] ?? ""}
                                      onChange={(e) => setEditMarks((prev) => prev.map((r) => {
                                        if (r.id !== row.id) return r;
                                        const components = { ...(r.components || {}), [col]: e.target.value };
                                        let total = 0;
                                        if (editTotalKey) {
                                          const v = Number((components[editTotalKey] ?? "").trim());
                                          total = Number.isFinite(v) ? v : 0;
                                        } else {
                                          total = editComponentCols.reduce((acc, c) => {
                                            const v = Number((components[c] ?? "").trim());
                                            return Number.isFinite(v) ? acc + v : acc;
                                          }, 0);
                                        }
                                        return { ...r, components, total };
                                      }))}
                                      className="w-full min-w-[120px] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
                                      placeholder="0"
                                      inputMode="decimal"
                                    />
                                  </td>
                                ))}
                                <td className="py-2 pr-4 text-foreground font-medium whitespace-nowrap">
                                  {editTotalKey ? (
                                    <input
                                      value={row.components?.[editTotalKey] ?? ""}
                                      onChange={(e) => setEditMarks((prev) => prev.map((r) => {
                                        if (r.id !== row.id) return r;
                                        const components = { ...(r.components || {}), [editTotalKey]: e.target.value };
                                        const v = Number((components[editTotalKey] ?? "").trim());
                                        const total = Number.isFinite(v) ? v : 0;
                                        return { ...r, components, total };
                                      }))}
                                      className="w-full min-w-[120px] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
                                      placeholder="0"
                                      inputMode="decimal"
                                    />
                                  ) : (
                                    Number.isFinite(row.total) ? Math.round(row.total * 10) / 10 : row.total
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            )
          }

          {/* ── File Analysis Modal ────────────────────────────────────────── */}
          {
            viewingFile && (
              <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={handleCloseModal}>
                <div
                  className="bg-white rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-indigo-600" />
                      </div>
                      <div>
                        <h3 className="text-foreground text-sm">{viewingFile.name}</h3>
                        <p className="text-xs text-muted-foreground">
                          {viewingFile.subject} &middot; {viewingFile.date} &middot; {viewingFile.size}
                          {viewingFile.department ? ` · ${viewingFile.department}` : ""}
                          {viewingFile.section ? ` · ${viewingFile.section}` : ""}
                        </p>
                      </div>
                    </div>
                    <button onClick={handleCloseModal} className="p-2 hover:bg-gray-100 rounded-xl cursor-pointer">
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Body */}
                  <div className="overflow-y-auto flex-1 p-6 space-y-6">
                    {analyzeLoading && <LoadingSpinner text="Analysing file…" />}
                    {analyzeError && <ErrorBanner message={analyzeError} onDismiss={() => setAnalyzeError("")} />}

                    {fileAnalysis && (
                      <>
                        {/* Class Stats */}
                        {fileAnalysis.class_insights && (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {[
                              { label: "Students", value: fileAnalysis.row_count, color: "bg-indigo-50 text-indigo-700" },
                              { label: "Class Average", value: `${fileAnalysis.class_insights.mean}`, color: "bg-blue-50 text-blue-700" },
                              { label: "Pass Rate", value: `${fileAnalysis.class_insights.pass_rate}%`, color: "bg-green-50 text-green-700" },
                              { label: "At Risk", value: fileAnalysis.class_insights.at_risk_count, color: "bg-red-50 text-red-700" },
                            ].map(({ label, value, color }) => (
                              <div key={label} className={`rounded-xl p-4 ${color}`}>
                                <p className="text-xs opacity-70">{label}</p>
                                <p className="text-xl mt-1">{value}</p>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Topper / Lowest Performer Highlights + Grade Pie */}
                        {fileAnalysis.class_insights && (
                          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                            <div className="flex flex-col gap-3">
                              {fileAnalysis.class_insights.topper && (
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-green-50 border border-green-100">
                                  <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center text-sm">🏆</div>
                                  <div>
                                    <p className="text-xs text-green-600">Subject Topper</p>
                                    <p className="text-sm text-green-800 font-medium">{fileAnalysis.class_insights.topper.name}</p>
                                    <p className="text-xs text-green-500">{fileAnalysis.class_insights.topper.marks}/100</p>
                                  </div>
                                </div>
                              )}
                              {fileAnalysis.class_insights.lowest_performer && (
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-red-50 border border-red-100">
                                  <div className="w-8 h-8 rounded-full bg-red-200 flex items-center justify-center text-sm">⚠️</div>
                                  <div>
                                    <p className="text-xs text-red-600">Needs Attention</p>
                                    <p className="text-sm text-red-800 font-medium">{fileAnalysis.class_insights.lowest_performer.name}</p>
                                    <p className="text-xs text-red-500">{fileAnalysis.class_insights.lowest_performer.marks}/100</p>
                                  </div>
                                </div>
                              )}
                              <div className="flex items-center gap-3 p-3 rounded-xl bg-blue-50 border border-blue-100">
                                <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center text-sm">📊</div>
                                <div>
                                  <p className="text-xs text-blue-600">Pass / Fail</p>
                                  <p className="text-sm text-blue-800 font-medium">{fileAnalysis.class_insights.pass_rate}% / {fileAnalysis.class_insights.fail_rate}%</p>
                                </div>
                              </div>
                            </div>
                            <div className="lg:col-span-2">
                              <p className="text-xs text-gray-400 mb-2">Grade Distribution</p>
                              <ResponsiveContainer width="100%" height={180}>
                                <PieChart>
                                  <Pie data={fileAnalysis.grade_distribution} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4} dataKey="value">
                                    {fileAnalysis.grade_distribution.map((entry) => (
                                      <Cell key={entry.name} fill={entry.color} />
                                    ))}
                                  </Pie>
                                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                                  <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                                </PieChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        )}

                        {/* Student table with ML predictions */}
                        {fileAnalysis.ml_predictions.length > 0 && (
                          <div>
                            <h4 className="text-sm text-foreground mb-3 flex items-center gap-2">
                              <Brain className="w-4 h-4 text-indigo-500" /> ML Performance Predictions
                            </h4>
                            <div className="overflow-x-auto rounded-xl border border-gray-100">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="bg-gray-50 text-left">
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Rank</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Roll No</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Student</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Marks</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Grade</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Cluster</th>
                                    <th className="px-4 py-3 text-xs text-gray-500 font-medium">Risk</th>
                                  </tr>
                                </thead>
                                <tbody>

                                  {fileAnalysis.ml_predictions.map((p, i) => (
                                    <tr key={p.name} className="border-t border-gray-50 hover:bg-gray-50 transition-colors">
                                      <td className="px-4 py-2.5 text-xs text-gray-400">{i + 1}</td>
                                      <td className="px-4 py-2.5 text-foreground">{p.name}</td>
                                      <td className="px-4 py-2.5">
                                        <span className="font-medium">{p.marks}</span>
                                        <span className="text-xs text-gray-400">/100</span>
                                      </td>
                                      <td className="px-4 py-2.5">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${p.predicted_grade === "A" ? "bg-green-100 text-green-700" :
                                          p.predicted_grade === "B" ? "bg-blue-100 text-blue-700" :
                                            p.predicted_grade === "C" ? "bg-yellow-100 text-yellow-700" :
                                              p.predicted_grade === "D" ? "bg-orange-100 text-orange-700" :
                                                "bg-red-100 text-red-700"
                                          }`}>{p.predicted_grade}</span>
                                      </td>
                                      <td className="px-4 py-2.5">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs ${p.cluster === "High Performer" ? "bg-indigo-50 text-indigo-700" :
                                          p.cluster === "Above Average" ? "bg-blue-50 text-blue-700" :
                                            p.cluster === "Below Average" ? "bg-amber-50 text-amber-700" :
                                              "bg-red-50 text-red-700"
                                          }`}>{p.cluster}</span>
                                      </td>
                                      <td className="px-4 py-2.5">
                                        <div className="flex items-center gap-2">
                                          <div className="flex-1 bg-gray-100 rounded-full h-1.5 w-16">
                                            <div
                                              className={`h-1.5 rounded-full ${p.risk_score > 65 ? "bg-red-500" :
                                                p.risk_score > 40 ? "bg-amber-400" : "bg-green-400"
                                                }`}
                                              style={{ width: `${p.risk_score}%` }}
                                            />
                                          </div>
                                          <span className="text-xs text-gray-500">{p.risk_score}%</span>
                                        </div>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* AI Recommendations */}
                        {(fileAnalysis.class_insights?.recommendations?.length ?? 0) > 0 && (
                          <div>
                            <h4 className="text-sm text-foreground mb-3 flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-purple-500" /> AI Recommendations
                            </h4>
                            <div className="space-y-2">
                              {fileAnalysis.class_insights!.recommendations.map((rec, i) => (
                                <div key={i} className="flex gap-3 p-3 rounded-xl bg-purple-50 border border-purple-100">
                                  <span className="text-purple-400 text-xs mt-0.5 shrink-0">{i + 1}.</span>
                                  <p className="text-xs text-purple-700">{rec}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            )
          }
        </main >
      </div >
    </div >
  );
}
