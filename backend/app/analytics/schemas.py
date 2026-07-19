from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    user_count: int
    tutor_count: int
    active_tutor_count: int
    session_count: int
    booked_session_count: int
    ai_usage_count: int
    agent_tool_calls: int
    failed_agent_tool_calls: int
    average_tool_latency_ms: float
