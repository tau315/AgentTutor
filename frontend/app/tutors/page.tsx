"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, Search, Star } from "lucide-react";
import { ApiError, searchTutors, Tutor, TutorFilters } from "../../lib/api";


export default function TutorsPage() {
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [subject, setSubject] = useState("");
  const [expertise, setExpertise] = useState("");
  const [sort, setSort] = useState<TutorFilters["sort"]>("relevance");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadTutors(filters: TutorFilters = {}) {
    setLoading(true);
    setError("");
    try {
      setTutors(await searchTutors(filters));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load tutors");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTutors();
  }, []);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadTutors({ subject, expertise, sort });
  }

  return (
    <main>
      <header className="topbar">
        <Link className="brand" href="/">AgentTutor</Link>
        <nav aria-label="Main navigation">
          <Link className="active" href="/tutors">Find tutors</Link>
          <Link href="/sessions">Sessions</Link>
          <Link href="/ai-chat">AI chat</Link>
        </nav>
      </header>

      <section className="marketplace-heading">
        <div>
          <p className="eyebrow">Tutor marketplace</p>
          <h1>Find the right tutor</h1>
          <p>Search by subject or expertise, then compare rates and ratings.</p>
        </div>
      </section>

      <section className="marketplace-layout">
        <form className="filters" onSubmit={submitSearch}>
          <label>
            Subject
            <input
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="Calculus"
            />
          </label>
          <label>
            Expertise
            <input
              value={expertise}
              onChange={(event) => setExpertise(event.target.value)}
              placeholder="Exam preparation"
            />
          </label>
          <label>
            Sort by
            <select value={sort} onChange={(event) => setSort(event.target.value as TutorFilters["sort"])}>
              <option value="relevance">Relevance</option>
              <option value="rating">Highest rated</option>
              <option value="price_low">Lowest price</option>
              <option value="name">Name</option>
            </select>
          </label>
          <button className="primary-button" type="submit">
            <Search size={18} aria-hidden="true" /> Search
          </button>
        </form>

        <div className="results" aria-live="polite">
          <div className="results-header">
            <h2>Available tutors</h2>
            {!loading && !error && <span>{tutors.length} found</span>}
          </div>

          {loading && <p className="status-message">Loading tutors...</p>}
          {error && <p className="status-message error-message">{error}</p>}
          {!loading && !error && tutors.length === 0 && (
            <p className="status-message">No active tutors match those filters yet.</p>
          )}

          <div className="tutor-list">
            {tutors.map((tutor) => (
              <article className="tutor-card" key={tutor.id}>
                <div className="tutor-initial" aria-hidden="true">
                  {tutor.display_name.charAt(0).toUpperCase()}
                </div>
                <div className="tutor-card-body">
                  <div className="tutor-title-row">
                    <div>
                      <h3>{tutor.display_name}</h3>
                      <div className="rating"><Star size={16} aria-hidden="true" /> {tutor.rating.toFixed(1)}</div>
                    </div>
                    <strong>{tutor.hourly_rate ? `$${tutor.hourly_rate}/hr` : "Rate pending"}</strong>
                  </div>
                  <p>{tutor.bio || "This tutor has not added a bio yet."}</p>
                  <div className="subject-list">
                    {tutor.subjects.map((item) => <span key={item.id}>{item.subject}</span>)}
                  </div>
                  <Link className="profile-link" href={`/tutors/${tutor.id}`}>
                    View profile <ArrowRight size={17} aria-hidden="true" />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
