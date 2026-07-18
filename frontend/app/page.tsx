import Link from "next/link";
import { getHealth } from "../lib/api";

export default async function HomePage() {
  const health = await getHealth();

  return (
    <main className="shell">
      <section>
        <h1>AgentTutor</h1>
        <p>Backend status: {health.status}</p>
        <p>Project scaffold for an AI-assisted tutoring platform.</p>
        <nav>
          <Link href="/dashboard/student">Student dashboard</Link>
          <Link href="/dashboard/tutor">Tutor dashboard</Link>
          <Link href="/dashboard/admin">Admin dashboard</Link>
          <Link href="/ai-chat">AI chat</Link>
        </nav>
      </section>
    </main>
  );
}

