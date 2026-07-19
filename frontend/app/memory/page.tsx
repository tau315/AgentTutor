"use client";

import { FormEvent, useEffect, useState } from "react";
import { BookOpen, Brain, Trash2 } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";
import { addDocument, addMemory, deleteDocument, deleteMemory, getDocuments, getMemories, KnowledgeDocument, UserMemory } from "../../lib/api";

export default function MemoryPage() {
  const [memories, setMemories] = useState<UserMemory[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [memory, setMemory] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [nextMemories, nextDocuments] = await Promise.all([getMemories(), getDocuments()]);
    setMemories(nextMemories); setDocuments(nextDocuments);
  }
  useEffect(() => { load().catch((reason: Error) => setError(reason.message)); }, []);

  async function saveMemory(event: FormEvent) {
    event.preventDefault(); setError("");
    try { await addMemory({ kind: "preference", content: memory }); setMemory(""); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save memory"); }
  }
  async function saveDocument(event: FormEvent) {
    event.preventDefault(); setError("");
    try { await addDocument({ category: "homework", title, content }); setTitle(""); setContent(""); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save homework"); }
  }

  return <><AppHeader /><main className="memory-page">
    <div className="page-title"><div><p className="eyebrow">Your data</p><h1>Memory & homework</h1></div></div>
    {error && <p className="form-error">{error}</p>}
    <div className="memory-grid">
      <section><header><Brain /><h2>Assistant memory</h2></header>
        <form className="stack-form" onSubmit={saveMemory}><label>Useful preference<input required value={memory} onChange={(event) => setMemory(event.target.value)} placeholder="I prefer visual explanations" /></label><button className="primary-button">Add memory</button></form>
        <div className="plain-list">{memories.map((item) => <article key={item.id}><div><strong>{item.kind.replaceAll("_", " ")}</strong><p>{item.content}</p></div><button className="icon-button danger" title="Delete memory" onClick={async () => { await deleteMemory(item.id); await load(); }}><Trash2 /></button></article>)}</div>
      </section>
      <section><header><BookOpen /><h2>Homework knowledge</h2></header>
        <form className="stack-form" onSubmit={saveDocument}><label>Title<input required value={title} onChange={(event) => setTitle(event.target.value)} /></label><label>Notes or homework text<textarea required value={content} onChange={(event) => setContent(event.target.value)} /></label><button className="primary-button">Add homework</button></form>
        <div className="plain-list">{documents.map((item) => <article key={item.id}><div><strong>{item.title}</strong><p>{item.content}</p></div><button className="icon-button danger" title="Delete homework" onClick={async () => { await deleteDocument(item.id); await load(); }}><Trash2 /></button></article>)}</div>
      </section>
    </div>
  </main></>;
}
