"use client";

import { useEffect, useState } from "react";
import { Plus, Save, Trash2 } from "lucide-react";
import { AppHeader } from "../../../components/AppHeader";
import { addBlockedTime, AvailabilityWindow, BlockedTime, deleteBlockedTime, getAvailability, getBlockedTimes, getMyTutorProfile, saveAvailability, Tutor, updateMyTutorProfile } from "../../../lib/api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function TutorDashboardPage() {
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [message, setMessage] = useState("");
  const [blocks, setBlocks] = useState<BlockedTime[]>([]);
  const [blockStart, setBlockStart] = useState("");
  const [blockEnd, setBlockEnd] = useState("");
  const [blockReason, setBlockReason] = useState("");
  const [profile, setProfile] = useState<Tutor>();
  const [subjectLines, setSubjectLines] = useState("");
  useEffect(() => { Promise.all([getAvailability(), getBlockedTimes(), getMyTutorProfile()]).then(([available, unavailable, tutor]) => { setWindows(available); setBlocks(unavailable); setProfile(tutor); setSubjectLines(tutor.subjects.map((item) => `${item.subject}${item.expertise ? ` | ${item.expertise}` : ""}`).join("\n")); }).catch(() => setMessage("Sign in with a tutor account to edit your profile and availability.")); }, []);
  function addWindow() { setWindows((items) => [...items, { weekday: 0, start_time: "09:00", end_time: "17:00", timezone: Intl.DateTimeFormat().resolvedOptions().timeZone }]); }
  function update(index: number, field: keyof AvailabilityWindow, value: string | number) { setWindows((items) => items.map((item, i) => i === index ? { ...item, [field]: value } : item)); }
  async function save() { setWindows(await saveAvailability(windows)); setMessage("Weekly availability saved."); }
  async function addBlock() { const saved = await addBlockedTime({ starts_at: new Date(blockStart).toISOString(), ends_at: new Date(blockEnd).toISOString(), reason: blockReason }); setBlocks((all) => [...all, saved]); setBlockStart(""); setBlockEnd(""); setBlockReason(""); }
  async function removeBlock(id: string) { await deleteBlockedTime(id); setBlocks((all) => all.filter((item) => item.id !== id)); }
  async function saveProfile() {
    if (!profile) return;
    const subjects = subjectLines.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => { const [subject, expertise] = line.split("|").map((part) => part.trim()); return { subject, expertise: expertise || undefined }; });
    const updated = await updateMyTutorProfile({ display_name: profile.display_name, bio: profile.bio ?? "", hourly_rate: profile.hourly_rate ? Number(profile.hourly_rate) : null, is_active: profile.is_active, subjects });
    setProfile(updated); setMessage("Tutor profile saved.");
  }
  return <main><AppHeader /><section className="workspace-page"><div className="page-title"><div><p className="eyebrow">Tutor workspace</p><h1>Profile & availability</h1></div></div>{message && <p className="inline-notice">{message}</p>}{profile && <section className="tutor-profile-editor"><h2>Public tutor profile</h2><div className="stack-form"><label>Display name<input value={profile.display_name} onChange={(e) => setProfile({ ...profile, display_name: e.target.value })} /></label><label>Bio<textarea value={profile.bio ?? ""} onChange={(e) => setProfile({ ...profile, bio: e.target.value })} /></label><label>Hourly rate<input type="number" min="0" step="0.01" value={profile.hourly_rate ?? ""} onChange={(e) => setProfile({ ...profile, hourly_rate: e.target.value })} /></label><label>Subjects, one per line (Subject | Expertise)<textarea value={subjectLines} onChange={(e) => setSubjectLines(e.target.value)} /></label><label className="checkbox-label"><input type="checkbox" checked={profile.is_active} onChange={(e) => setProfile({ ...profile, is_active: e.target.checked })} /> Visible in tutor search</label><button className="primary-button" onClick={() => void saveProfile()}><Save size={18} /> Save profile</button></div></section>}
    <section className="blocked-section"><div className="page-title"><div><h2>Weekly availability</h2><p className="section-copy">Times repeat every week in the selected time zone.</p></div><button className="secondary-button" onClick={addWindow}><Plus size={17} /> Add window</button></div><div className="availability-editor">{windows.map((item, index) => <div key={item.id ?? index}><select value={item.weekday} onChange={(e) => update(index, "weekday", Number(e.target.value))}>{DAYS.map((day, dayIndex) => <option value={dayIndex} key={day}>{day}</option>)}</select><input type="time" value={item.start_time.slice(0, 5)} onChange={(e) => update(index, "start_time", e.target.value)} /><span>to</span><input type="time" value={item.end_time.slice(0, 5)} onChange={(e) => update(index, "end_time", e.target.value)} /><input value={item.timezone} onChange={(e) => update(index, "timezone", e.target.value)} /><button className="icon-button danger" title="Remove" onClick={() => setWindows((all) => all.filter((_, i) => i !== index))}><Trash2 /></button></div>)}</div><button className="primary-button save-button" onClick={() => void save()}><Save size={18} /> Save availability</button></section>
    <section className="blocked-section"><h2>Blocked times</h2><p className="section-copy">Use these for appointments, travel, or any exception to your weekly hours.</p><div className="blocked-form"><input type="datetime-local" value={blockStart} onChange={(e) => setBlockStart(e.target.value)} /><input type="datetime-local" value={blockEnd} onChange={(e) => setBlockEnd(e.target.value)} /><input placeholder="Reason" value={blockReason} onChange={(e) => setBlockReason(e.target.value)} /><button className="secondary-button" disabled={!blockStart || !blockEnd} onClick={() => void addBlock()}><Plus size={17} /> Block time</button></div><div className="blocked-list">{blocks.map((block) => <div key={block.id}><span>{new Date(block.starts_at).toLocaleString()} - {new Date(block.ends_at).toLocaleString()}</span><span>{block.reason || "Unavailable"}</span><button className="icon-button danger" title="Remove block" onClick={() => void removeBlock(block.id)}><Trash2 /></button></div>)}</div></section>
  </section></main>;
}
