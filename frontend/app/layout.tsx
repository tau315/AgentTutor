import type { ReactNode } from "react";
import "./styles.css";

export const metadata = {
  title: "AgentTutor",
  description: "AI-assisted tutoring platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

