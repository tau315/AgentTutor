function apiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  }
  if (typeof window !== "undefined" && window.location.hostname === "localhost" && window.location.port === "3001") {
    return "http://localhost:8001";
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("access_token") : null;
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      body?.detail ?? response.statusText,
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// ---- typed endpoint functions ----

export interface HealthStatus {
  status: string;
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export function saveToken(token: string): void {
  window.localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  window.localStorage.removeItem("access_token");
}

export interface TokenResponse { access_token: string; token_type: string }
export interface UserProfile { id: string; email: string; role: "student" | "tutor" | "admin"; display_name: string | null; timezone: string; is_active: boolean }

export function signup(data: { email: string; password: string; role: "student" | "tutor"; timezone: string }): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/signup", { method: "POST", body: JSON.stringify(data) });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const form = new URLSearchParams({ username: email, password });
  const response = await fetch(`${apiBaseUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.detail ?? response.statusText);
  }
  return response.json();
}

export function getMe(): Promise<UserProfile> { return request<UserProfile>("/users/me"); }

export interface TutorSubject {
  id: string;
  subject: string;
  expertise: string | null;
}

export interface Tutor {
  id: string;
  display_name: string;
  bio: string | null;
  subjects: TutorSubject[];
  hourly_rate: string | null;
  rating: number;
  is_active: boolean;
}

export interface TutorFilters {
  subject?: string;
  expertise?: string;
  sort?: "relevance" | "rating" | "price_low" | "name";
}

export function searchTutors(filters: TutorFilters = {}): Promise<Tutor[]> {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const suffix = query.size ? `?${query.toString()}` : "";
  return request<Tutor[]>(`/tutors${suffix}`);
}

export function getTutor(tutorId: string): Promise<Tutor> {
  return request<Tutor>(`/tutors/${tutorId}`);
}

export interface SessionEvent { id: string; action: string; details: string | null; created_at: string }
export interface TutoringSession {
  id: string; tutor_id: string; tutor_name: string; student_id: string; student_name: string;
  subject: string; notes: string | null; starts_at: string; ends_at: string;
  status: "requested" | "booked" | "rejected" | "cancelled" | "completed";
  requested_by_user_id: string; cancellation_reason: string | null; events: SessionEvent[];
}

export function getSessions(scope: "upcoming" | "history" | "all" = "upcoming"): Promise<TutoringSession[]> {
  return request<TutoringSession[]>(`/sessions?scope=${scope}`);
}

export function requestSession(data: { tutor_id: string; subject: string; notes?: string; starts_at: string; ends_at: string }): Promise<TutoringSession> {
  return request<TutoringSession>("/sessions", { method: "POST", body: JSON.stringify(data) });
}

export function sessionAction(id: string, action: "accept" | "reject" | "cancel", reason = ""): Promise<TutoringSession> {
  return request<TutoringSession>(`/sessions/${id}/${action}`, { method: "POST", body: JSON.stringify({ reason: reason || null }) });
}

export function rescheduleSession(id: string, startsAt: string, endsAt: string): Promise<TutoringSession> {
  return request<TutoringSession>(`/sessions/${id}/reschedule`, { method: "POST", body: JSON.stringify({ starts_at: startsAt, ends_at: endsAt }) });
}

export interface AvailabilityWindow { id?: string; weekday: number; start_time: string; end_time: string; timezone: string }
export interface BlockedTime { id: string; starts_at: string; ends_at: string; reason: string | null }
export function getAvailability(): Promise<AvailabilityWindow[]> { return request<AvailabilityWindow[]>("/scheduling/availability/me"); }
export function saveAvailability(windows: AvailabilityWindow[]): Promise<AvailabilityWindow[]> {
  return request<AvailabilityWindow[]>("/scheduling/availability/me", { method: "PUT", body: JSON.stringify({ windows: windows.map(({ id, ...window }) => window) }) });
}
export function getBlockedTimes(): Promise<BlockedTime[]> { return request<BlockedTime[]>("/scheduling/blocks/me"); }
export function addBlockedTime(data: { starts_at: string; ends_at: string; reason?: string }): Promise<BlockedTime> {
  return request<BlockedTime>("/scheduling/blocks/me", { method: "POST", body: JSON.stringify(data) });
}
export function deleteBlockedTime(id: string): Promise<void> { return request<void>(`/scheduling/blocks/me/${id}`, { method: "DELETE" }); }

export interface Message { id: string; sender_id: string; body: string; created_at: string }
export interface Conversation { id: string; student_id: string; student_name: string; tutor_id: string; tutor_name: string; created_at: string; messages: Message[] }
export function getConversations(): Promise<Conversation[]> { return request<Conversation[]>("/messages"); }
export function createConversation(data: { tutor_id?: string; student_id?: string }): Promise<Conversation> {
  return request<Conversation>("/messages", { method: "POST", body: JSON.stringify(data) });
}
export function sendMessage(id: string, body: string): Promise<Conversation> {
  return request<Conversation>(`/messages/${id}/messages`, { method: "POST", body: JSON.stringify({ body }) });
}

export interface Notification { id: string; kind: string; title: string; body: string; resource_id: string | null; read_at: string | null; created_at: string }
export function getNotifications(): Promise<Notification[]> { return request<Notification[]>("/notifications"); }
export function markNotificationRead(id: string): Promise<Notification> { return request<Notification>(`/notifications/${id}/read`, { method: "PATCH" }); }

export interface Analytics {
  user_count: number; tutor_count: number; active_tutor_count: number; session_count: number;
  booked_session_count: number; ai_usage_count: number; agent_tool_calls: number;
  failed_agent_tool_calls: number; average_tool_latency_ms: number;
}
export interface Report { id: string; reporter_id: string; target_user_id: string | null; reason: string; details: string | null; status: string; admin_notes: string | null; created_at: string }
export interface AuditLog { id: string; actor_user_id: string | null; action: string; resource_type: string; resource_id: string | null; details: Record<string, unknown>; created_at: string }
export function getAnalytics(): Promise<Analytics> { return request<Analytics>("/analytics/overview"); }
export function getUsers(): Promise<UserProfile[]> { return request<UserProfile[]>("/users"); }
export function getAdminTutors(): Promise<Tutor[]> { return request<Tutor[]>("/tutors/admin/all"); }
export function getReports(): Promise<Report[]> { return request<Report[]>("/admin/reports"); }
export function getAuditLogs(): Promise<AuditLog[]> { return request<AuditLog[]>("/audit-logs"); }
export function updateUser(id: string, data: { role?: string; is_active?: boolean }): Promise<UserProfile> { return request<UserProfile>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) }); }
export function updateTutorAdmin(id: string, data: { rating?: number; is_active?: boolean }): Promise<Tutor> { return request<Tutor>(`/tutors/admin/${id}`, { method: "PATCH", body: JSON.stringify(data) }); }
export function updateReport(id: string, data: { status: string; admin_notes?: string }): Promise<Report> { return request<Report>(`/admin/reports/${id}`, { method: "PATCH", body: JSON.stringify(data) }); }

export interface AgentMessage { id: string; role: "user" | "assistant"; content: string; tool_name: string | null; created_at: string }
export interface AgentConversation { id: string; summary: string | null; created_at: string; updated_at: string; messages: AgentMessage[] }
export interface AgentReply {
  message: string; conversation_id: string; requires_confirmation: boolean;
  pending_action_id: string | null; proposed_action: string | null; tool_name: string | null;
}
export interface AgentActionResult { action_id: string; status: string; message: string; result: Record<string, unknown> | null }
export function getAgentConversations(): Promise<AgentConversation[]> { return request<AgentConversation[]>("/agent/conversations"); }
export function chatWithAgent(message: string, conversationId?: string): Promise<AgentReply> {
  return request<AgentReply>("/agent/chat", { method: "POST", body: JSON.stringify({ message, conversation_id: conversationId ?? null }) });
}
export function decideAgentAction(actionId: string, decision: "confirm" | "reject"): Promise<AgentActionResult> {
  return request<AgentActionResult>(`/agent/actions/${actionId}/${decision}`, { method: "POST" });
}

export interface KnowledgeDocument { id: string; category: "platform" | "homework"; title: string; content: string; created_at: string }
export interface UserMemory { id: string; kind: "preference" | "learning_goal"; content: string; sensitive: boolean; created_at: string }
export function getDocuments(category: "platform" | "homework" = "homework"): Promise<KnowledgeDocument[]> { return request<KnowledgeDocument[]>(`/agent/documents?category=${category}`); }
export function addDocument(data: { category: "platform" | "homework"; title: string; content: string }): Promise<KnowledgeDocument> {
  return request<KnowledgeDocument>("/agent/documents", { method: "POST", body: JSON.stringify(data) });
}
export function deleteDocument(id: string): Promise<void> { return request<void>(`/agent/documents/${id}`, { method: "DELETE" }); }
export function getMemories(): Promise<UserMemory[]> { return request<UserMemory[]>("/agent/memories"); }
export function addMemory(data: { kind: "preference" | "learning_goal"; content: string }): Promise<UserMemory> {
  return request<UserMemory>("/agent/memories", { method: "POST", body: JSON.stringify(data) });
}
export function deleteMemory(id: string): Promise<void> { return request<void>(`/agent/memories/${id}`, { method: "DELETE" }); }

export function getMyTutorProfile(): Promise<Tutor> { return request<Tutor>("/tutors/me"); }
export function updateMyTutorProfile(data: {
  display_name?: string; bio?: string; hourly_rate?: number | null; is_active?: boolean;
  subjects?: Array<{ subject: string; expertise?: string }>;
}): Promise<Tutor> { return request<Tutor>("/tutors/me", { method: "PATCH", body: JSON.stringify(data) }); }
