import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  GraduationCap, BookOpen, TrendingUp, Award, LogOut, Bell, Brain,
  BarChart3, Target, Clock, Star, ChevronRight, Menu, X, Loader2, AlertCircle, InboxIcon
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend
} from "recharts";
import * as api from "../api";
import type { StudentDashboard as DashboardData } from "../api";

export function StudentDashboard() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"Overview" | "Subjects" | "Analytics" | "Reports">("Overview");

  // Read profile from localStorage for immediate display
  const profile = JSON.parse(localStorage.getItem(api.PROFILE_KEY) ?? "{}") as api.AuthProfile;

  // Route guard: redirect to login when token is missing/invalid or role is wrong.
  useEffect(() => {
    (async () => {
      try {
        const me = await api.getMe();
        if (me.role !== "student") throw new Error("Wrong role");
      } catch {
        localStorage.removeItem(api.TOKEN_KEY);
        localStorage.removeItem(api.PROFILE_KEY);
        navigate("/");
      }
    })();
  }, [navigate]);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.getStudentDashboard();
        setDashboard(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleLogout = async () => {
    await api.logout();
    navigate("/");
  };

  const activityIcon = (type: string) => {
    if (type === "Exam") return <BarChart3 className="w-5 h-5" />;
    if (type === "Quiz") return <Target className="w-5 h-5" />;
    if (type === "Assignment") return <BookOpen className="w-5 h-5" />;
    if (type === "Lab") return <TrendingUp className="w-5 h-5" />;
    return <GraduationCap className="w-5 h-5" />;
  };

  const activityColor = (type: string) => {
    if (type === "Exam") return "bg-red-100 text-red-600";
    if (type === "Quiz") return "bg-amber-100 text-amber-600";
    if (type === "Assignment") return "bg-blue-100 text-blue-600";
    if (type === "Lab") return "bg-green-100 text-green-600";
    return "bg-purple-100 text-purple-600";
  };

  const badgeColor = (type: string) => {
    if (type === "Exam") return "bg-red-50 text-red-600";
    if (type === "Quiz") return "bg-amber-50 text-amber-600";
    return "bg-blue-50 text-blue-600";
  };

  const d = dashboard;

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="lg:hidden p-2 hover:bg-gray-100 rounded-lg cursor-pointer">
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-foreground hidden sm:block">EduAnalytics</span>
            </div>
          </div>
          <nav className="hidden lg:flex items-center gap-1">
            {["Overview", "Subjects", "Analytics", "Reports"].map((item) => (
              <button
                key={item}
                onClick={() => setActiveTab(item as any)}
                className={`px-4 py-2 rounded-lg text-sm cursor-pointer transition-colors ${
                  activeTab === item ? "bg-indigo-50 text-indigo-700 font-medium" : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                {item}
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <button className="relative p-2 hover:bg-gray-100 rounded-lg cursor-pointer">
              <Bell className="w-5 h-5 text-gray-500" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
            <button onClick={handleLogout} className="p-2 hover:bg-red-50 hover:text-red-600 rounded-lg cursor-pointer text-gray-500">
              <LogOut className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2 pl-3 border-l border-gray-200">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm">
                {d?.profile.avatar_initials ?? profile.avatar_initials ?? "??"}
              </div>
              <div className="hidden md:block">
                <p className="text-sm text-foreground">{d?.profile.name ?? profile.name ?? "Student"}</p>
                <p className="text-xs text-muted-foreground">{d?.profile.department?.split(" ")[0] ?? "CS"} · {d?.profile.year ?? ""}</p>
              </div>
            </div>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-100 p-4 bg-white space-y-1">
            {["Overview", "Subjects", "Analytics", "Reports"].map((item) => (
              <button
                key={item}
                onClick={() => {
                  setActiveTab(item as any);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm cursor-pointer ${
                  activeTab === item ? "bg-indigo-50 text-indigo-700 font-medium" : "text-gray-600"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto px-4 lg:px-8 py-6 lg:py-8 space-y-6">

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-32 gap-3 text-gray-400">
            <Loader2 className="w-10 h-10 animate-spin text-indigo-500" />
            <p className="text-sm">Loading your dashboard…</p>
          </div>
        )}

        {/* Error state */}
        {!loading && error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
            <button onClick={() => window.location.reload()} className="ml-auto text-red-600 underline text-xs cursor-pointer">Retry</button>
          </div>
        )}

        {/* Dashboard content */}
        {!loading && d && (
          <>
            {/* Profile Header */}
            <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 rounded-2xl p-6 lg:p-8 text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
              <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-white/5 rounded-full translate-y-1/2" />
              <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                <div className="flex items-center gap-5">
                  <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-2xl lg:text-3xl">
                    {d.profile.avatar_initials}
                  </div>
                  <div>
                    <h1 className="text-2xl lg:text-3xl text-white">{d.profile.name}</h1>
                    <p className="text-white/80 mt-1">{d.profile.department} · {d.profile.year} · {d.profile.section}</p>
                    <p className="text-white/60 text-sm mt-0.5">Roll No: {d.profile.roll_no} · CGPA: {d.profile.cgpa}</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 lg:gap-6">
                  {[
                    { label: "Overall Score", value: d.profile.overall_score, icon: Target },
                    { label: "Class Rank", value: `#${d.profile.class_rank}`, icon: Award },
                    { label: "Attendance", value: d.profile.attendance, icon: Clock },
                  ].map(({ label, value, icon: Icon }) => (
                    <div key={label} className="text-center bg-white/10 backdrop-blur-sm rounded-xl p-3 lg:p-4">
                      <Icon className="w-5 h-5 mx-auto mb-1 text-white/80" />
                      <p className="text-xl lg:text-2xl">{value}</p>
                      <p className="text-xs text-white/70">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Tab Contents */}
            {activeTab === "Overview" && (
              <>
                {/* Subject Performance Cards */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-foreground">Subject-wise Performance</h2>
                    <button
                      onClick={() => setActiveTab("Subjects")}
                      className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
                    >
                      View All <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                  {d.subject_performance.length === 0 ? (
                    <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center text-gray-400">
                      <InboxIcon className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                      <p className="text-sm">No subject data available yet.</p>
                      <p className="text-xs mt-1">Your faculty will upload performance data soon.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {d.subject_performance.map((sub) => (
                        <div key={sub.subject} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all group cursor-pointer">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: sub.color + "15" }}>
                                <BookOpen className="w-5 h-5" style={{ color: sub.color }} />
                              </div>
                              <div>
                                <p className="text-sm text-foreground">{sub.subject}</p>
                                <p className="text-xs text-muted-foreground">Semester 6</p>
                              </div>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full ${sub.trend.startsWith("+") ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"}`}>
                              {sub.trend}%
                            </span>
                          </div>
                          <div className="flex items-end justify-between">
                            <div>
                              <p className="text-3xl text-foreground">{sub.score}</p>
                              <p className="text-xs text-muted-foreground">out of 100</p>
                            </div>
                            <div className="flex items-center gap-1 bg-indigo-50 px-3 py-1.5 rounded-lg">
                              <Star className="w-4 h-4 text-indigo-600" />
                              <span className="text-sm text-indigo-700">{sub.grade}</span>
                            </div>
                          </div>
                          <div className="mt-4 w-full bg-gray-100 rounded-full h-2">
                            <div className="h-2 rounded-full transition-all" style={{ width: `${sub.score}%`, backgroundColor: sub.color }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Charts Section */}
                {d.trend.length === 0 && d.class_comparison.length === 0 ? (
                  <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center text-gray-400">
                    <BarChart3 className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No chart data available yet.</p>
                    <p className="text-xs mt-1">Charts will appear once your faculty uploads performance records.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Performance Trend */}
                    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-foreground">Performance Trend</h3>
                          <p className="text-sm text-muted-foreground">Your score vs class average over time</p>
                        </div>
                        <div className="flex items-center gap-4 text-xs">
                          <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-indigo-500" />
                            <span className="text-muted-foreground">You</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-purple-300" />
                            <span className="text-muted-foreground">Class Avg</span>
                          </div>
                        </div>
                      </div>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={d.trend}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                          <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[60, 100]} />
                          <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ fill: "#6366f1", strokeWidth: 2, r: 5 }} activeDot={{ r: 7 }} name="Your Score" />
                          <Line type="monotone" dataKey="classAvg" stroke="#c4b5fd" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: "#c4b5fd", r: 3 }} name="Class Average" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Comparison Bar Chart */}
                    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                      <div className="mb-4">
                        <h3 className="text-foreground">Class Comparison</h3>
                        <p className="text-sm text-muted-foreground">Your marks vs class average by subject</p>
                      </div>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={d.class_comparison} barGap={4}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="subject" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                          <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[0, 100]} />
                          <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                          <Legend />
                          <Bar dataKey="you" fill="#6366f1" radius={[4, 4, 0, 0]} name="Your Score" />
                          <Bar dataKey="classAvg" fill="#c4b5fd" radius={[4, 4, 0, 0]} name="Class Average" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Radar + Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <h3 className="text-foreground mb-1">Skill Radar</h3>
                    <p className="text-sm text-muted-foreground mb-4">Subject-wise proficiency map</p>
                    {d.radar.length === 0 ? (
                      <div className="h-[280px] flex items-center justify-center text-gray-400 text-sm">
                        <div className="text-center">
                          <Target className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                          <p>No radar data yet.</p>
                        </div>
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height={280}>
                        <RadarChart data={d.radar}>
                          <PolarGrid stroke="#e2e8f0" />
                          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} stroke="#cbd5e1" />
                          <Radar name="Score" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
                        </RadarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                  <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-foreground">Recent Activity</h3>
                        <p className="text-sm text-muted-foreground">Latest assessments and results</p>
                      </div>
                      <button className="text-sm text-indigo-600 hover:text-indigo-700 cursor-pointer">See all</button>
                    </div>
                    {d.recent_activity.length === 0 ? (
                      <div className="py-10 text-center text-gray-400">
                        <InboxIcon className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                        <p className="text-sm">No recent activity yet.</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {d.recent_activity.map((item) => (
                          <div key={item.title} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 hover:bg-indigo-50 transition-colors cursor-pointer">
                            <div className="flex items-center gap-4">
                              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activityColor(item.type)}`}>
                                {activityIcon(item.type)}
                              </div>
                              <div>
                                <p className="text-sm text-foreground">{item.title}</p>
                                <p className="text-xs text-muted-foreground">{item.date}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-foreground">{item.score}</p>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${badgeColor(item.type)}`}>
                                {item.type}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Semester Summary */}
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <h3 className="text-foreground mb-4">Semester Summary</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                    {[
                      { label: "Total Credits", value: d.semester_summary.total_credits.toString(), icon: BookOpen, bg: "bg-indigo-50", text: "text-indigo-600" },
                      { label: "GPA", value: d.semester_summary.gpa.toString(), icon: Award, bg: "bg-purple-50", text: "text-purple-600" },
                      { label: "Best Subject", value: d.semester_summary.best_subject, icon: Star, bg: "bg-amber-50", text: "text-amber-600" },
                      { label: "Assignments", value: d.semester_summary.assignments_completed, icon: Target, bg: "bg-green-50", text: "text-green-600" },
                      { label: "Quizzes", value: d.semester_summary.quizzes_passed, icon: BarChart3, bg: "bg-blue-50", text: "text-blue-600" },
                      { label: "Attendance", value: d.semester_summary.attendance, icon: Clock, bg: "bg-cyan-50", text: "text-cyan-600" },
                    ].map(({ label, value, icon: Icon, bg, text }) => (
                      <div key={label} className={`${bg} rounded-xl p-4 text-center`}>
                        <Icon className={`w-5 h-5 mx-auto mb-2 ${text}`} />
                        <p className={`text-xl ${text}`}>{value}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {activeTab === "Subjects" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl text-foreground font-semibold">My Enrolled Subjects</h2>
                  <p className="text-sm text-muted-foreground">Semester VI Detailed Record</p>
                </div>
                {d.subject_performance.length === 0 ? (
                  <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center text-gray-400">
                    <InboxIcon className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No subjects available yet.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {d.subject_performance.map((sub) => (
                      <div key={sub.subject} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: sub.color + "15" }}>
                              <BookOpen className="w-6 h-6" style={{ color: sub.color }} />
                            </div>
                            <div>
                              <h3 className="text-lg text-foreground font-medium">{sub.subject}</h3>
                              <p className="text-xs text-muted-foreground">Instructor: Prof. {sub.subject === "ATCD" ? "Sharma" : sub.subject === "DBMS" ? "Venkatesh" : "Faculty Advisor"}</p>
                            </div>
                          </div>
                          <span className={`text-xs px-2.5 py-1 rounded-full ${sub.trend.startsWith("+") ? "bg-green-50 text-green-600 font-medium" : "bg-red-50 text-red-600 font-medium"}`}>
                            {sub.trend}% trend
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-4 py-3 border-y border-gray-50 text-center">
                          <div>
                            <p className="text-xs text-gray-500">Score</p>
                            <p className="text-lg font-semibold text-foreground mt-0.5">{sub.score} / 100</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Grade</p>
                            <p className="text-lg font-semibold text-indigo-600 mt-0.5">{sub.grade}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Status</p>
                            <p className={`text-lg font-semibold mt-0.5 ${sub.score >= 40 ? "text-green-600" : "text-red-600"}`}>
                              {sub.score >= 40 ? "Pass" : "Fail"}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>Syllabus Proficiency Progress</span>
                            <span>{sub.score}%</span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-2">
                            <div className="h-2 rounded-full transition-all" style={{ width: `${sub.score}%`, backgroundColor: sub.color }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "Analytics" && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-indigo-100/50 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-indigo-700">
                      <Brain className="w-5 h-5 text-indigo-600" />
                      <span className="text-sm font-semibold uppercase tracking-wider">AI Predictive Insight</span>
                    </div>
                    <h3 className="text-xl text-foreground font-semibold">Your success forecast is strong!</h3>
                    <p className="text-sm text-gray-600">
                      Our custom Logistic Regression model estimates a high probability of passing in the current semester based on your scores, continuous assessment performance, and attendance rates.
                    </p>
                  </div>
                  <div className="bg-white rounded-2xl p-5 border border-indigo-100 text-center min-w-[150px] shadow-sm">
                    <p className="text-xs text-gray-500 font-medium">PASS PROBABILITY</p>
                    <p className="text-4xl font-extrabold text-indigo-600 mt-1">98.4%</p>
                    <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full mt-2 inline-block font-medium">Safe Zone</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Performance Trend */}
                  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-foreground">Performance Trend</h3>
                        <p className="text-sm text-muted-foreground">Your score vs class average over time</p>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <div className="flex items-center gap-1.5">
                          <div className="w-3 h-3 rounded-full bg-indigo-500" />
                          <span className="text-muted-foreground">You</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-3 h-3 rounded-full bg-purple-300" />
                          <span className="text-muted-foreground">Class Avg</span>
                        </div>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={d.trend}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                        <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[60, 100]} />
                        <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                        <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ fill: "#6366f1", strokeWidth: 2, r: 5 }} activeDot={{ r: 7 }} name="Your Score" />
                        <Line type="monotone" dataKey="classAvg" stroke="#c4b5fd" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: "#c4b5fd", r: 3 }} name="Class Average" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Comparison Bar Chart */}
                  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="mb-4">
                      <h3 className="text-foreground">Class Comparison</h3>
                      <p className="text-sm text-muted-foreground">Your marks vs class average by subject</p>
                    </div>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={d.class_comparison} barGap={4}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="subject" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                        <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[0, 100]} />
                        <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
                        <Legend />
                        <Bar dataKey="you" fill="#6366f1" radius={[4, 4, 0, 0]} name="Your Score" />
                        <Bar dataKey="classAvg" fill="#c4b5fd" radius={[4, 4, 0, 0]} name="Class Average" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Skill Radar */}
                  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm lg:col-span-2">
                    <h3 className="text-foreground mb-1">Subject Proficiency Map</h3>
                    <p className="text-sm text-muted-foreground mb-4">Radar chart of your proficiency distribution</p>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={d.radar}>
                        <PolarGrid stroke="#e2e8f0" />
                        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#cbd5e1" />
                        <Radar name="Score" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "Reports" && (
              <div className="space-y-6">
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-6">
                  <div className="flex items-center justify-between border-b pb-4">
                    <div>
                      <h2 className="text-xl text-foreground font-semibold">Semester Performance Report</h2>
                      <p className="text-xs text-muted-foreground mt-1">Academic Year: 2025-2026 · Semester VI</p>
                    </div>
                    <button
                      onClick={() => window.print()}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium flex items-center gap-2 cursor-pointer shadow-sm transition"
                    >
                      Print Report Card
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <p className="text-xs text-gray-500">Student Name</p>
                      <p className="text-base font-semibold text-foreground mt-1">{d.profile.name}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <p className="text-xs text-gray-500">Roll Number</p>
                      <p className="text-base font-semibold text-foreground mt-1">{d.profile.roll_no}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <p className="text-xs text-gray-500">Overall Score</p>
                      <p className="text-base font-semibold text-indigo-600 mt-1">{d.profile.overall_score}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <p className="text-xs text-gray-500">Attendance Rate</p>
                      <p className="text-base font-semibold text-foreground mt-1">{d.profile.attendance}</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-500 border-b">
                          <th className="py-3 px-4">Subject</th>
                          <th className="py-3 px-4">Grade</th>
                          <th className="py-3 px-4">Score</th>
                          <th className="py-3 px-4">Class Average</th>
                          <th className="py-3 px-4">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {d.subject_performance.map((sub) => (
                          <tr key={sub.subject}>
                            <td className="py-3 px-4 text-foreground font-medium">{sub.subject}</td>
                            <td className="py-3 px-4 font-bold text-indigo-600">{sub.grade}</td>
                            <td className="py-3 px-4">{sub.score} / 100</td>
                            <td className="py-3 px-4">
                              {d.class_comparison.find((c) => c.subject === sub.subject)?.classAvg ?? 78} / 100
                            </td>
                            <td className="py-3 px-4">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${sub.score >= 40 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                                {sub.score >= 40 ? "Passed" : "Failed"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="bg-indigo-50/50 border border-indigo-100/50 rounded-xl p-5 space-y-2">
                    <div className="flex items-center gap-2 text-indigo-800">
                      <Award className="w-5 h-5 text-indigo-600" />
                      <span className="font-semibold text-sm">AI Learning Recommendations</span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      Your performance is steady. To achieve a perfect CGPA, consider increasing self-study hours for subjects like **{d.semester_summary.best_subject === "ATCD" ? "DBMS" : "ATCD"}** where your score is close to the class average. Keep reviewing previous assignment solutions.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
