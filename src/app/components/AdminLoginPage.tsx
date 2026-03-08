import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, Loader2, Shield } from "lucide-react";
import * as api from "../api";

export function AdminLoginPage() {
  const navigate = useNavigate();
  const [adminMode, setAdminMode] = useState<"signin" | "signup">("signin");
  const [adminExists, setAdminExists] = useState<boolean | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const ensureAdminStatus = async () => {
    try {
      const exists = await api.adminExists();
      setAdminExists(exists);
      setAdminMode(exists ? "signin" : "signup");
    } catch {
      setAdminExists(null);
    }
  };

  useEffect(() => {
    void ensureAdminStatus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const profile =
        adminMode === "signup"
          ? await api.adminSignup(name, email, password)
          : await api.login(email, password, "admin");
      localStorage.setItem(api.TOKEN_KEY, profile.access_token);
      localStorage.setItem(api.PROFILE_KEY, JSON.stringify(profile));
      navigate("/admin");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Admin authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-background">
      <div className="w-full max-w-md bg-white rounded-2xl border border-gray-100 shadow-sm p-8 space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-600 text-white flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl text-foreground">Admin Access</h1>
            <p className="text-sm text-muted-foreground">Separate admin login page</p>
          </div>
        </div>

        <div className="text-sm p-3 rounded-xl bg-slate-50 border border-slate-200">
          {adminExists === false ? "No admin found. Create first admin account." : "Admin sign in"}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {adminMode === "signup" && (
            <div>
              <label className="text-sm text-gray-600 mb-1.5 block">Full name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
              />
            </div>
          )}
          <div>
            <label className="text-sm text-gray-600 mb-1.5 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1.5 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
            />
          </div>
          {error && <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {adminMode === "signup" ? "Creating admin..." : "Signing in..."}
              </>
            ) : (
              <>
                {adminMode === "signup" ? "Create Admin" : "Sign In"}
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
