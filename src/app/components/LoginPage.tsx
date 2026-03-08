import { useState } from "react";
import { useNavigate } from "react-router";
import { GraduationCap, Users, ArrowRight, BookOpen, BarChart3, Brain, Loader2 } from "lucide-react";
import * as api from "../api";

export function LoginPage() {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState<"faculty" | "student" | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole) return;
    setError("");
    setLoading(true);
    try {
      const profile = await api.login(email, password, selectedRole);
      localStorage.setItem(api.TOKEN_KEY, profile.access_token);
      localStorage.setItem(api.PROFILE_KEY, JSON.stringify(profile));
      navigate(selectedRole === "faculty" ? "/faculty" : "/student");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-700 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <Brain className="w-7 h-7" />
            </div>
            <span className="text-2xl tracking-tight">EduAnalytics AI</span>
          </div>
          <h1 className="text-4xl mb-4 leading-tight">AI-Powered Student<br />Performance Analytics</h1>
          <p className="text-lg text-white/80 mb-12 max-w-md">
            Transform academic data into actionable insights. Track, analyze, and improve student performance with intelligent analytics.
          </p>
          <div className="space-y-4">
            {[
              { icon: BarChart3, text: "Real-time performance dashboards" },
              { icon: BookOpen, text: "Smart document analysis" },
              { icon: Brain, text: "AI-generated insights & trends" },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3 text-white/90">
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                  <Icon className="w-4 h-4" />
                </div>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          <h2 className="text-2xl text-foreground mb-1">Welcome back</h2>
          <p className="text-muted-foreground mb-8">Select your role and sign in to continue</p>

          <div className="grid grid-cols-2 gap-3 mb-8">
            <button
              onClick={() => setSelectedRole("faculty")}
              className={`p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer text-left ${selectedRole === "faculty"
                ? "border-indigo-500 bg-indigo-50 shadow-sm"
                : "border-gray-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/50"
                }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${selectedRole === "faculty" ? "bg-indigo-500 text-white" : "bg-gray-100 text-gray-500"}`}>
                <Users className="w-5 h-5" />
              </div>
              <p className={`text-sm ${selectedRole === "faculty" ? "text-indigo-700" : "text-gray-700"}`}>Faculty</p>
              <p className="text-xs text-muted-foreground mt-0.5">Manage & analyze</p>
            </button>
            <button
              onClick={() => setSelectedRole("student")}
              className={`p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer text-left ${selectedRole === "student"
                ? "border-purple-500 bg-purple-50 shadow-sm"
                : "border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50/50"
                }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${selectedRole === "student" ? "bg-purple-500 text-white" : "bg-gray-100 text-gray-500"}`}>
                <GraduationCap className="w-5 h-5" />
              </div>
              <p className={`text-sm ${selectedRole === "student" ? "text-purple-700" : "text-gray-700"}`}>Student</p>
              <p className="text-xs text-muted-foreground mt-0.5">View performance</p>
            </button>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-sm text-gray-600 mb-1.5 block">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1.5 block">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all outline-none"
              />
            </div>

            {error && <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

            <button
              type="submit"
              disabled={!selectedRole || loading}
              className={`w-full py-3 rounded-xl text-white flex items-center justify-center gap-2 transition-all duration-200 cursor-pointer ${selectedRole && !loading
                ? "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/25"
                : "bg-gray-300 cursor-not-allowed"
                }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
