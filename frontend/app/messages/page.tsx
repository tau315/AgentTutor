"use client";

import { FormEvent, useEffect, useState } from "react";
import { Send } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";
import { ApiError, Conversation, getConversations, getMe, sendMessage, UserProfile } from "../../lib/api";


export default function MessagesPage() {
  const [threads, setThreads] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [me, setMe] = useState<UserProfile | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { Promise.all([getConversations(), getMe()]).then(([items, user]) => { setThreads(items); setMe(user); setSelected(items[0]?.id ?? null); }).catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load messages")); }, []);
  const thread = threads.find((item) => item.id === selected);
  async function submit(event: FormEvent) { event.preventDefault(); if (!thread || !body.trim()) return; const updated = await sendMessage(thread.id, body); setThreads((items) => items.map((item) => item.id === updated.id ? updated : item)); setBody(""); }
  return <main><AppHeader /><section className="message-workspace">
    <aside><h1>Messages</h1>{error && <p className="form-error">{error}</p>}{threads.map((item) => <button className={selected === item.id ? "selected" : ""} key={item.id} onClick={() => setSelected(item.id)}><strong>{me?.role === "student" ? item.tutor_name : item.student_name}</strong><span>{item.messages.at(-1)?.body ?? "No messages yet"}</span></button>)}</aside>
    <section className="conversation-panel">{thread ? <><header><h2>{me?.role === "student" ? thread.tutor_name : thread.student_name}</h2></header><div className="message-list">{thread.messages.map((message) => <div className={message.sender_id === me?.id ? "message mine" : "message"} key={message.id}><p>{message.body}</p><time>{new Date(message.created_at).toLocaleString()}</time></div>)}</div>{me?.role !== "admin" && <form className="message-composer" onSubmit={submit}><input value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write a message" /><button className="icon-button success" title="Send"><Send /></button></form>}</> : <p className="status-message">Select a conversation.</p>}</section>
  </section></main>;
}
