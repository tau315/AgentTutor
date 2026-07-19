"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bot, Check, Plus, Send, X } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";
import {
  AgentConversation, AgentReply, ApiError, chatWithAgent, decideAgentAction, getAgentConversations,
} from "../../lib/api";

export default function AiChatPage() {
  const [conversations, setConversations] = useState<AgentConversation[]>([]);
  const [selectedId, setSelectedId] = useState<string>();
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<AgentReply>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load(preferredId?: string) {
    const items = await getAgentConversations();
    setConversations(items);
    setSelectedId(preferredId ?? selectedId ?? items[0]?.id);
  }

  useEffect(() => { load().catch((reason: ApiError) => setError(reason.message)); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || busy) return;
    setBusy(true); setError(""); setPending(undefined);
    const message = draft.trim();
    setDraft("");
    try {
      const reply = await chatWithAgent(message, selectedId);
      if (reply.requires_confirmation) setPending(reply);
      await load(reply.conversation_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The assistant request failed");
    } finally { setBusy(false); }
  }

  async function decide(decision: "confirm" | "reject") {
    if (!pending?.pending_action_id) return;
    setBusy(true); setError("");
    try {
      const result = await decideAgentAction(pending.pending_action_id, decision);
      setPending(undefined);
      await load(pending.conversation_id);
      if (decision === "reject") setError(result.message);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The action decision failed");
    } finally { setBusy(false); }
  }

  const selected = conversations.find((item) => item.id === selectedId);
  return <>
    <AppHeader />
    <main className="agent-workspace">
      <aside>
        <div className="agent-sidebar-heading"><h1>Assistant</h1><button className="icon-button" title="New conversation" onClick={() => { setSelectedId(undefined); setPending(undefined); }}><Plus /></button></div>
        {conversations.map((item) => <button key={item.id} className={item.id === selectedId ? "selected" : ""} onClick={() => { setSelectedId(item.id); setPending(undefined); }}>
          <strong>{item.summary?.slice(0, 54) || "New conversation"}</strong>
          <span>{new Date(item.updated_at).toLocaleString()}</span>
        </button>)}
      </aside>
      <section className="agent-panel">
        <header><Bot /><div><h2>AgentTutor assistant</h2><span>Actions require your approval</span></div></header>
        <div className="agent-messages">
          {!selected?.messages.length && <div className="agent-empty"><Bot /><h2>What can I help with?</h2></div>}
          {selected?.messages.map((message) => <article className={`agent-message ${message.role}`} key={message.id}>
            <span>{message.role === "assistant" ? "Assistant" : "You"}</span><p>{message.content}</p>
            {message.tool_name && <small>{message.tool_name.replaceAll("_", " ")}</small>}
          </article>)}
          {pending && <div className="approval-panel"><strong>Confirm this action?</strong><p>{pending.proposed_action}</p><div className="action-row">
            <button className="primary-button" disabled={busy} onClick={() => decide("confirm")}><Check /> Confirm</button>
            <button className="secondary-button" disabled={busy} onClick={() => decide("reject")}><X /> Reject</button>
          </div></div>}
          {error && <p className="form-error">{error}</p>}
        </div>
        <form className="agent-composer" onSubmit={submit}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about tutors, sessions, homework, or platform tasks" aria-label="Message" />
          <button className="icon-button success" disabled={busy || !draft.trim()} title="Send"><Send /></button>
        </form>
      </section>
    </main>
  </>;
}
