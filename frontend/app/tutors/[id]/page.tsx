"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, CalendarPlus, Clock, Star } from "lucide-react";
import { ApiError, getTutor, requestSession, Tutor } from "../../../lib/api";
import { AppHeader } from "../../../components/AppHeader";


export default function TutorProfilePage() {
  const params = useParams<{ id: string }>();
  const [tutor, setTutor] = useState<Tutor | null>(null);
  const [error, setError] = useState("");
  const [subject, setSubject] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");

  useEffect(() => {
    getTutor(params.id)
      .then(setTutor)
      .catch((caught) => {
        setError(caught instanceof ApiError ? caught.message : "Could not load tutor");
      });
  }, [params.id]);

  async function book(event: FormEvent) {
    event.preventDefault();
    setBookingMessage("");
    try {
      await requestSession({ tutor_id: params.id, subject, starts_at: new Date(startsAt).toISOString(), ends_at: new Date(endsAt).toISOString() });
      setBookingMessage("Request sent. The tutor can now accept it.");
    } catch (caught) {
      setBookingMessage(caught instanceof ApiError ? caught.message : "Could not request session");
    }
  }

  return (
    <main>
      <AppHeader />
      <section className="profile-page">
        <Link className="back-link" href="/tutors"><ArrowLeft size={17} /> Back to tutors</Link>
        {!tutor && !error && <p className="status-message">Loading tutor...</p>}
        {error && <p className="status-message error-message">{error}</p>}
        {tutor && (
          <>
            <div className="profile-header">
              <div className="profile-initial" aria-hidden="true">{tutor.display_name.charAt(0).toUpperCase()}</div>
              <div>
                <p className="eyebrow">Tutor profile</p>
                <h1>{tutor.display_name}</h1>
                <div className="profile-facts">
                  <span><Star size={17} /> {tutor.rating.toFixed(1)} rating</span>
                  <span><Clock size={17} /> {tutor.hourly_rate ? `$${tutor.hourly_rate} per hour` : "Rate pending"}</span>
                </div>
              </div>
            </div>
            <div className="profile-content">
              <section>
                <h2>About</h2>
                <p>{tutor.bio || "This tutor has not added a bio yet."}</p>
              </section>
              <section>
                <h2>Subjects and expertise</h2>
                <div className="expertise-list">
                  {tutor.subjects.map((item) => (
                    <div key={item.id}>
                      <strong>{item.subject}</strong>
                      <span>{item.expertise || "General tutoring"}</span>
                    </div>
                  ))}
                </div>
              </section>
              <section className="booking-section">
                <h2>Request a session</h2>
                <form className="stack-form" onSubmit={book}>
                  <label>Subject<select value={subject} onChange={(e) => setSubject(e.target.value)} required><option value="">Choose a subject</option>{tutor.subjects.map((item) => <option key={item.id}>{item.subject}</option>)}</select></label>
                  <label>Starts<input type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} required /></label>
                  <label>Ends<input type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} required /></label>
                  {bookingMessage && <p className="inline-notice">{bookingMessage}</p>}
                  <button className="primary-button" type="submit"><CalendarPlus size={18} /> Request session</button>
                </form>
              </section>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
