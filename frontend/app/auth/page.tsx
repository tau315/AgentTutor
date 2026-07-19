"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, UserPlus } from "lucide-react";
import { ApiError, login, saveToken, signup } from "../../lib/api";
import { AppHeader } from "../../components/AppHeader";


export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"student" | "tutor">("student");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = mode === "login"
        ? await login(email, password)
        : await signup({ email, password, role, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone });
      saveToken(result.access_token);
      router.push(role === "tutor" ? "/dashboard/tutor" : "/sessions");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Authentication failed");
    }
  }

  return <main><AppHeader /><section className="auth-page">
    <div className="segmented-control">
      <button className={mode === "login" ? "selected" : ""} onClick={() => setMode("login")}>Login</button>
      <button className={mode === "signup" ? "selected" : ""} onClick={() => setMode("signup")}>Sign up</button>
    </div>
    <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
    <form className="stack-form" onSubmit={submit}>
      <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      {mode === "signup" && <label>Account type<select value={role} onChange={(e) => setRole(e.target.value as "student" | "tutor")}><option value="student">Student</option><option value="tutor">Tutor</option></select></label>}
      {error && <p className="form-error">{error}</p>}
      <button className="primary-button" type="submit">{mode === "login" ? <LogIn size={18} /> : <UserPlus size={18} />}{mode === "login" ? "Login" : "Create account"}</button>
    </form>
  </section></main>;
}
