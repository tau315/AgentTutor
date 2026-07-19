import re
from datetime import datetime

from app.agent.provider import OllamaProvider
from app.agent.schemas import AgentContext, AgentToolDefinition, ToolPlan
from app.core.config import settings


UUID_PATTERN = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
DATETIME_PATTERN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})"


class AgentPlanner:
    async def plan(
        self,
        message: str,
        context: AgentContext,
        tools: list[AgentToolDefinition],
        history: list[dict],
    ) -> ToolPlan:
        if settings.llm_provider == "ollama":
            try:
                return await self._ollama_plan(message, context, tools, history)
            except Exception:
                # A local-model outage should not disable the deterministic core tools.
                pass
        return self._fallback_plan(message)

    async def _ollama_plan(self, message: str, context: AgentContext, tools: list[AgentToolDefinition], history: list[dict]) -> ToolPlan:
        system = (
            "You route AgentTutor requests to exactly one finite tool. Never invent identifiers. "
            "Use clarification when required arguments are missing. Write tools are proposed, not executed. "
            f"Authenticated role={context.role}, timezone={context.timezone}, current_time={datetime.now().isoformat()}. "
            f"Tools: {[tool.model_dump() for tool in tools]}"
        )
        response = await OllamaProvider().structured_chat(
            [{"role": "system", "content": system}, *history[-8:], {"role": "user", "content": message}],
            ToolPlan.model_json_schema(),
        )
        return ToolPlan.model_validate(response)

    def _fallback_plan(self, message: str) -> ToolPlan:
        lower = message.casefold()
        ids = re.findall(UUID_PATTERN, message)
        datetimes = re.findall(DATETIME_PATTERN, message)

        if any(word in lower for word in ["upcoming session", "my sessions", "my schedule"]):
            return ToolPlan(tool_name="list_upcoming_sessions")
        if "homework" in lower:
            return ToolPlan(tool_name="search_homework", arguments={"query": message})
        if "summar" in lower and "conversation" in lower:
            return ToolPlan(tool_name="summarize_conversation", arguments={"conversation_id": ids[0] if ids else None})
        if any(word in lower for word in ["recommend", "find a tutor", "search tutor", "which tutor"]):
            return ToolPlan(tool_name="search_tutors", arguments={"query": message, "recommend": "recommend" in lower})
        if "available" in lower or "availability" in lower:
            if not ids or len(datetimes) < 2:
                return ToolPlan(clarification="Which tutor and exact start/end time should I check? Include the tutor ID and times with UTC offsets.")
            return ToolPlan(tool_name="check_availability", arguments={"tutor_id": ids[0], "starts_at": datetimes[0], "ends_at": datetimes[1]})
        cancellation_command = any(phrase in lower for phrase in ["cancel my session", "cancel the session", "please cancel", "cancel session"])
        if cancellation_command:
            return ToolPlan(tool_name="cancel_session", arguments={"session_id": ids[0] if ids else None})
        if "reschedule" in lower:
            if len(datetimes) < 2:
                return ToolPlan(clarification="What exact new start and end time should I propose? Include UTC offsets.")
            return ToolPlan(tool_name="reschedule_session", arguments={"session_id": ids[0] if ids else None, "starts_at": datetimes[0], "ends_at": datetimes[1]})
        if "book" in lower and "session" in lower:
            if not ids or len(datetimes) < 2:
                return ToolPlan(clarification="Which tutor, subject, and exact start/end time should I request? Include the tutor ID and UTC offsets.")
            subject = next((name for name in ["calculus", "algebra", "physics", "chemistry", "biology", "computer science", "math"] if name in lower), "Tutoring")
            return ToolPlan(tool_name="book_session", arguments={"tutor_id": ids[0], "subject": subject.title(), "starts_at": datetimes[0], "ends_at": datetimes[1]})
        if "update" in lower and "profile" in lower:
            name_match = re.search(r"display name (?:to|is) ([\w .'-]+)", message, re.IGNORECASE)
            timezone_match = re.search(r"timezone (?:to|is) ([A-Za-z_]+/[A-Za-z_]+)", message)
            changes = {key: value for key, value in {"display_name": name_match.group(1).strip() if name_match else None, "timezone": timezone_match.group(1) if timezone_match else None}.items() if value}
            if not changes:
                return ToolPlan(clarification="Which profile field should I update? I can change your display name or time zone.")
            return ToolPlan(tool_name="update_profile", arguments=changes)
        if "send" in lower and "message" in lower:
            body = message.split(":", 1)[1].strip() if ":" in message else None
            if not body:
                return ToolPlan(clarification="What message should I send? Put the message text after a colon.")
            return ToolPlan(tool_name="send_message", arguments={"conversation_id": ids[0] if ids else None, "body": body})
        if "remind me" in lower:
            if not datetimes:
                return ToolPlan(clarification="When should I remind you? Include an exact date/time with a UTC offset.")
            body = re.sub(DATETIME_PATTERN, "", message, count=1).replace("remind me", "").strip(" :")
            return ToolPlan(tool_name="create_reminder", arguments={"remind_at": datetimes[0], "body": body or "AgentTutor reminder"})
        return ToolPlan(tool_name="answer_platform_question", arguments={"query": message})
