import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { Edit2, Loader2, LogOut, Shield, Trash2, UserPlus, X } from "lucide-react";
import * as api from "../api";

export function AdminDashboard() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<api.AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    role: "faculty" as "faculty" | "student",
    name: "",
    email: "",
    password: "",
    department: "",
    roll_no: "",
  });

  const [editingUser, setEditingUser] = useState<api.AdminUserItem | null>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    password: "",
    department: "",
    roll_no: "",
  });

  const handleAuthError = (err: unknown) => {
    const msg = err instanceof Error ? err.message : "An error occurred";
    setError(msg);
    if (msg.includes("no longer exists") || msg.includes("404") || msg.includes("401") || msg.includes("token")) {
      setTimeout(() => {
        localStorage.removeItem(api.TOKEN_KEY);
        localStorage.removeItem(api.PROFILE_KEY);
        navigate("/admin-login");
      }, 2000);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const list = await api.getAdminUsers();
      setUsers(list);
    } catch (e: unknown) {
      handleAuthError(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const me = await api.getMe();
        if (me.role !== "admin") throw new Error("Wrong role");
      } catch {
        localStorage.removeItem(api.TOKEN_KEY);
        localStorage.removeItem(api.PROFILE_KEY);
        navigate("/admin-login");
        return;
      }
      await loadUsers();
    })();
  }, [navigate]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createAdminUser(form);
      setForm({
        role: "faculty",
        name: "",
        email: "",
        password: "",
        department: "",
        roll_no: "",
      });
      await loadUsers();
    } catch (e: unknown) {
      handleAuthError(e);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (user: api.AdminUserItem) => {
    setEditingUser(user);
    setEditForm({
      name: user.name || "",
      email: user.email || "",
      password: "",
      department: user.department || "",
      roll_no: user.roll_no || "",
    });
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setSaving(true);
    setError("");
    try {
      await api.updateAdminUser(editingUser.id, {
        role: editingUser.role as "faculty" | "student",
        ...editForm,
      });
      setEditingUser(null);
      await loadUsers();
    } catch (e: unknown) {
      handleAuthError(e);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (userId: string, role: "faculty" | "student") => {
    if (!window.confirm("Are you sure you want to delete this account?")) return;
    setLoading(true);
    setError("");
    try {
      await api.deleteAdminUser(userId, role);
      await loadUsers();
    } catch (e: unknown) {
      handleAuthError(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = useMemo(
    () => users.sort((a, b) => `${a.role}-${a.name}`.localeCompare(`${b.role}-${b.name}`)),
    [users]
  );
  const facultyUsers = useMemo(() => filteredUsers.filter((u) => u.role === "faculty"), [filteredUsers]);
  const studentUsers = useMemo(() => filteredUsers.filter((u) => u.role === "student"), [filteredUsers]);

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-700 mb-1">
              <Shield className="w-5 h-5" />
              <span className="text-sm">Admin Panel</span>
            </div>
            <h1 className="text-2xl text-foreground">User Access Management</h1>
          </div>
          <button
            onClick={async () => {
              await api.logout();
              navigate("/admin-login");
            }}
            className="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-sm flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        {error && <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        <form onSubmit={handleCreate} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2 text-foreground">
            <UserPlus className="w-5 h-5 text-indigo-600" />
            <h2>Create Faculty / Student Login</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select
              value={form.role}
              onChange={(e) => setForm((p) => ({ ...p, role: e.target.value as "faculty" | "student" }))}
              className="px-3 py-2.5 rounded-xl border border-gray-200 bg-white"
            >
              <option value="faculty">Faculty</option>
              <option value="student">Student</option>
            </select>
            {form.role === "faculty" && (
              <input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="Name" required className="px-3 py-2.5 rounded-xl border border-gray-200" />
            )}
            <input value={form.email} type="email" onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} placeholder="Email" required className="px-3 py-2.5 rounded-xl border border-gray-200" />
            <input value={form.password} type="password" onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))} placeholder="Password (min 6)" required className="px-3 py-2.5 rounded-xl border border-gray-200" />
            <input value={form.department} onChange={(e) => setForm((p) => ({ ...p, department: e.target.value }))} placeholder="Department" className="px-3 py-2.5 rounded-xl border border-gray-200" />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating…</> : "Create Login Access"}
          </button>
        </form>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-foreground">Created Accounts</h2>
            <button onClick={loadUsers} className="px-4 py-2 rounded-xl border border-gray-200 text-sm hover:bg-gray-50">Refresh</button>
          </div>
          {loading ? (
            <div className="py-8 text-center text-gray-500">Loading...</div>
          ) : (
            <div className="space-y-8">
              <div>
                <h3 className="text-foreground mb-3">Faculty Accounts ({facultyUsers.length})</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="py-2 pr-4">Name</th>
                        <th className="py-2 pr-4">Email</th>
                        <th className="py-2 pr-4">Department</th>
                        <th className="py-2 pr-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {facultyUsers.map((u) => (
                        <tr key={u.id}>
                          <td className="py-2 pr-4">{u.name}</td>
                          <td className="py-2 pr-4">{u.email}</td>
                          <td className="py-2 pr-4">{u.department || "—"}</td>
                          <td className="py-2 pr-4 text-right">
                            <div className="flex justify-end gap-1.5">
                              <button
                                onClick={() => startEdit(u)}
                                className="p-1.5 rounded-lg hover:bg-indigo-50 hover:text-indigo-600 text-gray-400 transition"
                                title="Edit Account"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(u.id, "faculty")}
                                className="p-1.5 rounded-lg hover:bg-red-50 hover:text-red-600 text-gray-400 transition"
                                title="Delete Account"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="text-foreground mb-3">Student Accounts ({studentUsers.length})</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="py-2 pr-4">Roll No</th>
                        <th className="py-2 pr-4">Name</th>
                        <th className="py-2 pr-4">Email</th>
                        <th className="py-2 pr-4">Department</th>
                        <th className="py-2 pr-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {studentUsers.map((u) => (
                        <tr key={u.id}>
                          <td className="py-2 pr-4">{u.roll_no || "—"}</td>
                          <td className="py-2 pr-4">{u.name}</td>
                          <td className="py-2 pr-4">{u.email}</td>
                          <td className="py-2 pr-4">{u.department || "—"}</td>
                          <td className="py-2 pr-4 text-right">
                            <div className="flex justify-end gap-1.5">
                              <button
                                onClick={() => startEdit(u)}
                                className="p-1.5 rounded-lg hover:bg-indigo-50 hover:text-indigo-600 text-gray-400 transition"
                                title="Edit Account"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(u.id, "student")}
                                className="p-1.5 rounded-lg hover:bg-red-50 hover:text-red-600 text-gray-400 transition"
                                title="Delete Account"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Edit User Modal */}
        {editingUser && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 w-full max-w-md space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-lg font-medium text-foreground">
                    Edit {editingUser.role === "faculty" ? "Faculty" : "Student"} Account
                  </h2>
                </div>
                <button
                  onClick={() => setEditingUser(null)}
                  className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUpdate} className="space-y-4">
                {editingUser.role === "faculty" && (
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-gray-500 font-medium">Name</label>
                    <input
                      value={editForm.name}
                      onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
                      required
                      className="px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}
                {editingUser.role === "student" && (
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-gray-500 font-medium">Roll No</label>
                    <input
                      value={editForm.roll_no}
                      onChange={(e) => setEditForm((p) => ({ ...p, roll_no: e.target.value }))}
                      className="px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs text-gray-500 font-medium">Email</label>
                  <input
                    value={editForm.email}
                    type="email"
                    onChange={(e) => setEditForm((p) => ({ ...p, email: e.target.value }))}
                    required
                    className="px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs text-gray-500 font-medium">Password (leave empty to keep current)</label>
                  <input
                    value={editForm.password}
                    type="password"
                    onChange={(e) => setEditForm((p) => ({ ...p, password: e.target.value }))}
                    placeholder="New Password (min 6)"
                    className="px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs text-gray-500 font-medium">Department</label>
                  <input
                    value={editForm.department}
                    onChange={(e) => setEditForm((p) => ({ ...p, department: e.target.value }))}
                    className="px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditingUser(null)}
                    className="px-4 py-2 rounded-xl border border-gray-200 text-sm hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium disabled:opacity-50 transition"
                  >
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
