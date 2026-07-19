import Link from "next/link";
import { CalendarDays, MessageSquare, Search } from "lucide-react";
import { AppHeader } from "../../../components/AppHeader";

export default function StudentDashboardPage() {
  return <main><AppHeader /><section className="workspace-page"><div className="page-title"><div><p className="eyebrow">Student workspace</p><h1>Dashboard</h1></div></div><div className="shortcut-grid"><Link href="/tutors"><Search /><strong>Find a tutor</strong><span>Search subjects and expertise</span></Link><Link href="/sessions"><CalendarDays /><strong>My calendar</strong><span>Upcoming sessions and history</span></Link><Link href="/messages"><MessageSquare /><strong>Messages</strong><span>Talk with your tutors</span></Link></div></section></main>;
}
