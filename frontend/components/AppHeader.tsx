"use client";

import Link from "next/link";
import { Bell, Bot, Brain } from "lucide-react";


export function AppHeader() {
  return (
    <header className="topbar">
      <Link className="brand" href="/">AgentTutor</Link>
      <nav aria-label="Main navigation">
        <Link href="/tutors">Tutors</Link>
        <Link href="/sessions">Sessions</Link>
        <Link href="/messages">Messages</Link>
        <Link className="icon-link" href="/ai-chat" title="AI assistant"><Bot size={18} /></Link>
        <Link className="icon-link" href="/memory" title="Memory and homework"><Brain size={18} /></Link>
        <Link className="icon-link" href="/notifications" title="Notifications"><Bell size={18} /></Link>
        <Link href="/auth">Account</Link>
      </nav>
    </header>
  );
}
