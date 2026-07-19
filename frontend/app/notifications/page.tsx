"use client";

import { useEffect, useState } from "react";
import { Bell, Check } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";
import { getNotifications, markNotificationRead, Notification } from "../../lib/api";


export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  useEffect(() => { getNotifications().then(setItems).catch(() => setItems([])); }, []);
  async function markRead(id: string) { const updated = await markNotificationRead(id); setItems((all) => all.map((item) => item.id === id ? updated : item)); }
  return <main><AppHeader /><section className="workspace-page"><div className="page-title"><div><p className="eyebrow">Inbox</p><h1>Notifications</h1></div><Bell /></div>{items.length === 0 && <p className="status-message">No notifications yet.</p>}<div className="notification-list">{items.map((item) => <article className={item.read_at ? "read" : ""} key={item.id}><div><h2>{item.title}</h2><p>{item.body}</p><time>{new Date(item.created_at).toLocaleString()}</time></div>{!item.read_at && <button className="icon-button" title="Mark read" onClick={() => void markRead(item.id)}><Check /></button>}</article>)}</div></section></main>;
}
