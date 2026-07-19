"use client";

import { useEffect, useState } from "react";
import { CalendarClock, Check, RotateCcw, X } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";
import { ApiError, getMe, getSessions, rescheduleSession, sessionAction, TutoringSession, UserProfile } from "../../lib/api";


export default function SessionsPage() {
  const [scope, setScope] = useState<"upcoming" | "history">("upcoming");
  const [sessions, setSessions] = useState<TutoringSession[]>([]);
  const [me, setMe] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  async function load(nextScope = scope) {
    try { const [user, items] = await Promise.all([getMe(), getSessions(nextScope)]); setMe(user); setSessions(items); setError(""); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Could not load sessions"); }
  }
  useEffect(() => { void load(); }, [scope]);

  async function act(id: string, action: "accept" | "reject" | "cancel") {
    await sessionAction(id, action); await load();
  }
  async function reschedule(id: string) {
    await rescheduleSession(id, new Date(start).toISOString(), new Date(end).toISOString()); setEditing(null); await load();
  }

  return <main><AppHeader /><section className="workspace-page">
    <div className="page-title"><div><p className="eyebrow">Calendar</p><h1>Sessions</h1></div><CalendarClock size={26} /></div>
    <div className="segmented-control"><button className={scope === "upcoming" ? "selected" : ""} onClick={() => setScope("upcoming")}>Upcoming</button><button className={scope === "history" ? "selected" : ""} onClick={() => setScope("history")}>History</button></div>
    {error && <p className="status-message error-message">{error}. Sign in from the Account page if needed.</p>}
    {!error && sessions.length === 0 && <p className="status-message">No {scope} sessions.</p>}
    <div className="agenda-list">{sessions.map((item) => {
      const canDecide = item.status === "requested" && me?.id !== item.requested_by_user_id;
      return <article className="agenda-item" key={item.id}>
        <time><strong>{new Date(item.starts_at).toLocaleDateString([], { month: "short", day: "numeric" })}</strong><span>{new Date(item.starts_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span></time>
        <div><div className="agenda-heading"><h2>{item.subject}</h2><span className={`status-pill ${item.status}`}>{item.status}</span></div><p>{me?.role === "student" ? item.tutor_name : item.student_name}</p><p>{new Date(item.starts_at).toLocaleString()} - {new Date(item.ends_at).toLocaleTimeString()}</p>
          {editing === item.id && <div className="inline-form"><input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} /><input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} /><button className="primary-button" onClick={() => void reschedule(item.id)}>Propose</button></div>}
        </div>
        <div className="action-row">{canDecide && <><button className="icon-button success" title="Accept" onClick={() => void act(item.id, "accept")}><Check /></button><button className="icon-button danger" title="Reject" onClick={() => void act(item.id, "reject")}><X /></button></>}{["requested", "booked"].includes(item.status) && <><button className="icon-button" title="Reschedule" onClick={() => setEditing(item.id)}><RotateCcw /></button><button className="icon-button danger" title="Cancel" onClick={() => void act(item.id, "cancel")}><X /></button></>}</div>
      </article>;
    })}</div>
  </section></main>;
}
