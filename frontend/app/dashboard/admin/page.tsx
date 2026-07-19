"use client";

import { useEffect, useState } from "react";
import { Activity, CalendarDays, Clock3, GraduationCap, TriangleAlert, Users } from "lucide-react";
import { AppHeader } from "../../../components/AppHeader";
import { Analytics, AuditLog, getAnalytics, getAuditLogs, getReports, getSessions, getUsers, Report, TutoringSession, updateReport, updateUser, UserProfile } from "../../../lib/api";

type View = "users" | "sessions" | "reports" | "logs";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<Analytics | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [sessions, setSessions] = useState<TutoringSession[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [view, setView] = useState<View>("users");
  const [error, setError] = useState("");
  async function load() { try { const [m, u, s, r, l] = await Promise.all([getAnalytics(), getUsers(), getSessions("all"), getReports(), getAuditLogs()]); setMetrics(m); setUsers(u); setSessions(s); setReports(r); setLogs(l); } catch { setError("Sign in with an admin account to view platform operations."); } }
  useEffect(() => { void load(); }, []);
  async function toggleUser(user: UserProfile) { const updated = await updateUser(user.id, { is_active: !user.is_active }); setUsers((all) => all.map((item) => item.id === updated.id ? updated : item)); }
  async function resolve(report: Report) { const updated = await updateReport(report.id, { status: "resolved" }); setReports((all) => all.map((item) => item.id === updated.id ? updated : item)); }
  return <main><AppHeader /><section className="admin-page"><div className="page-title"><div><p className="eyebrow">Platform operations</p><h1>Admin dashboard</h1></div></div>{error && <p className="status-message error-message">{error}</p>}{metrics && <div className="metric-grid"><div><Users /><span>Users</span><strong>{metrics.user_count}</strong></div><div><GraduationCap /><span>Tutors</span><strong>{metrics.tutor_count}</strong></div><div><CalendarDays /><span>Sessions</span><strong>{metrics.session_count}</strong></div><div><Activity /><span>Agent tool calls</span><strong>{metrics.agent_tool_calls}</strong></div><div><TriangleAlert /><span>Failed tool calls</span><strong>{metrics.failed_agent_tool_calls}</strong></div><div><Clock3 /><span>Average tool latency</span><strong>{metrics.average_tool_latency_ms} ms</strong></div></div>}
    <div className="admin-tabs">{(["users", "sessions", "reports", "logs"] as View[]).map((item) => <button className={view === item ? "selected" : ""} onClick={() => setView(item)} key={item}>{item}</button>)}</div>
    {view === "users" && <div className="data-table"><div className="table-row table-head"><span>Email</span><span>Role</span><span>Status</span><span>Action</span></div>{users.map((user) => <div className="table-row" key={user.id}><span>{user.email}</span><span>{user.role}</span><span>{user.is_active ? "Active" : "Inactive"}</span><button className="text-button" onClick={() => void toggleUser(user)}>{user.is_active ? "Deactivate" : "Activate"}</button></div>)}</div>}
    {view === "sessions" && <div className="data-table"><div className="table-row table-head"><span>Subject</span><span>Student</span><span>Tutor</span><span>Status</span></div>{sessions.map((item) => <div className="table-row" key={item.id}><span>{item.subject}</span><span>{item.student_name}</span><span>{item.tutor_name}</span><span>{item.status}</span></div>)}</div>}
    {view === "reports" && <div className="data-table"><div className="table-row table-head"><span>Reason</span><span>Details</span><span>Status</span><span>Action</span></div>{reports.map((item) => <div className="table-row" key={item.id}><span>{item.reason}</span><span>{item.details || "-"}</span><span>{item.status}</span><button className="text-button" disabled={item.status === "resolved"} onClick={() => void resolve(item)}>Resolve</button></div>)}</div>}
    {view === "logs" && <div className="data-table"><div className="table-row table-head"><span>Time</span><span>Action</span><span>Result</span><span>Actor</span></div>{logs.map((item) => <div className="table-row" key={item.id}><span>{new Date(item.created_at).toLocaleString()}</span><span>{item.action}{item.details.tool ? `: ${String(item.details.tool)}` : ""}</span><span>{String(item.details.status ?? item.resource_type)}{item.details.duration_ms ? ` (${String(item.details.duration_ms)} ms)` : ""}</span><span>{item.actor_user_id || "system"}</span></div>)}</div>}
  </section></main>;
}
