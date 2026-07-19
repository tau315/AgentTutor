from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.rag import RAGService
from app.agent.schemas import AgentActionRisk, AgentToolDefinition
from app.core.errors import AppError
from app.core.security import CurrentUser
from app.messaging.schemas import MessageCreate
from app.messaging.service import MessagingService
from app.notifications.service import NotificationService
from app.scheduling.service import SchedulingService
from app.sessions.schemas import SessionDecision, SessionRequest, SessionReschedule, SessionScope
from app.sessions.service import SessionService
from app.tutors.schemas import TutorSearchFilters
from app.tutors.service import TutorService
from app.users.schemas import UserProfileUpdate
from app.users.service import UserService


@dataclass
class ToolRuntime:
    db: AsyncSession
    user: CurrentUser


ToolHandler = Callable[[ToolRuntime, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class AgentTool:
    definition: AgentToolDefinition
    handler: ToolHandler


def as_json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


async def search_tutors_tool(runtime: ToolRuntime, args: dict) -> dict:
    tutors = await TutorService(runtime.db).search_tutors(TutorSearchFilters())
    query_tokens = set(str(args.get("query", "")).casefold().split())

    def score(tutor) -> tuple[int, float]:
        text = " ".join([tutor.display_name, tutor.bio or "", *[f"{item.subject} {item.expertise or ''}" for item in tutor.subjects]]).casefold()
        return (sum(token.strip(".,?!") in text for token in query_tokens), tutor.rating)
    ranked = sorted(tutors, key=score, reverse=True)
    return {"tutors": [as_json(item) for item in ranked[:5]]}


async def check_availability_tool(runtime: ToolRuntime, args: dict) -> dict:
    result = await SchedulingService(runtime.db).check(
        args["tutor_id"], datetime.fromisoformat(args["starts_at"].replace("Z", "+00:00")), datetime.fromisoformat(args["ends_at"].replace("Z", "+00:00"))
    )
    return as_json(result)


async def list_upcoming_sessions_tool(runtime: ToolRuntime, args: dict) -> dict:
    sessions = await SessionService(runtime.db).list_sessions(runtime.user, SessionScope.upcoming)
    return {"sessions": [as_json(item) for item in sessions]}


async def answer_platform_question_tool(runtime: ToolRuntime, args: dict) -> dict:
    documents = await RAGService(runtime.db).search(runtime.user, args["query"], "platform")
    return {"answer": "\n\n".join(item.content for item in documents), "sources": [item.title for item in documents]}


async def search_homework_tool(runtime: ToolRuntime, args: dict) -> dict:
    documents = await RAGService(runtime.db).search(runtime.user, args["query"], "homework")
    return {"homework": [as_json(item) for item in documents]}


async def summarize_conversation_tool(runtime: ToolRuntime, args: dict) -> dict:
    service = MessagingService(runtime.db)
    conversation_id = args.get("conversation_id")
    if conversation_id:
        thread = await service.get_thread(runtime.user, conversation_id)
    else:
        threads = await service.list_threads(runtime.user)
        if not threads:
            return {"summary": "You do not have any tutoring conversations yet."}
        thread = threads[0]
    recent = thread.messages[-20:]
    if not recent:
        return {"summary": "This conversation does not contain any messages yet."}
    summary = " ".join(f"{'You' if item.sender_id == runtime.user.id else 'Other participant'}: {item.body}" for item in recent)
    return {"conversation_id": thread.id, "summary": summary}


async def book_session_tool(runtime: ToolRuntime, args: dict) -> dict:
    item = await SessionService(runtime.db).request_session(runtime.user, SessionRequest(**args))
    return {"session": as_json(item)}


async def cancel_session_tool(runtime: ToolRuntime, args: dict) -> dict:
    session_id = args.get("session_id")
    if not session_id:
        upcoming = await SessionService(runtime.db).list_sessions(runtime.user, SessionScope.upcoming)
        if not upcoming:
            raise AppError("You do not have an upcoming session to cancel")
        session_id = upcoming[0].id
    item = await SessionService(runtime.db).cancel(runtime.user, session_id, SessionDecision(reason="Cancelled through AI assistant"))
    return {"session": as_json(item)}


async def reschedule_session_tool(runtime: ToolRuntime, args: dict) -> dict:
    session_id = args.get("session_id")
    if not session_id:
        upcoming = await SessionService(runtime.db).list_sessions(runtime.user, SessionScope.upcoming)
        if not upcoming:
            raise AppError("You do not have an upcoming session to reschedule")
        session_id = upcoming[0].id
    item = await SessionService(runtime.db).reschedule(runtime.user, session_id, SessionReschedule(starts_at=args["starts_at"], ends_at=args["ends_at"]))
    return {"session": as_json(item)}


async def update_profile_tool(runtime: ToolRuntime, args: dict) -> dict:
    profile = await UserService(runtime.db).update_profile(runtime.user, UserProfileUpdate(**args))
    return {"profile": as_json(profile)}


async def send_message_tool(runtime: ToolRuntime, args: dict) -> dict:
    service = MessagingService(runtime.db)
    conversation_id = args.get("conversation_id")
    if not conversation_id:
        threads = await service.list_threads(runtime.user)
        if len(threads) != 1:
            raise AppError("Specify a conversation ID because you do not have exactly one conversation")
        conversation_id = threads[0].id
    thread = await service.send_message(runtime.user, conversation_id, MessageCreate(body=args["body"]))
    return {"conversation": as_json(thread)}


async def create_reminder_tool(runtime: ToolRuntime, args: dict) -> dict:
    item = await NotificationService(runtime.db).schedule_reminder(
        runtime.user, args["body"], datetime.fromisoformat(args["remind_at"].replace("Z", "+00:00"))
    )
    return {"reminder": {"id": item.id, "body": item.body, "remind_at": item.remind_at.isoformat(), "status": item.status}}


def build_tool_registry() -> dict[str, AgentTool]:
    specifications = [
        ("search_tutors", "Search and recommend active tutors from existing profile data.", AgentActionRisk.read, ["student", "tutor", "admin"], search_tutors_tool),
        ("check_availability", "Check a tutor's weekly availability and blocked times.", AgentActionRisk.read, ["student", "tutor", "admin"], check_availability_tool),
        ("list_upcoming_sessions", "List only sessions visible to the authenticated user.", AgentActionRisk.read, ["student", "tutor", "admin"], list_upcoming_sessions_tool),
        ("answer_platform_question", "Answer platform questions using retrieved platform documentation.", AgentActionRisk.read, ["student", "tutor", "admin"], answer_platform_question_tool),
        ("search_homework", "Search only homework documents owned by the authenticated user.", AgentActionRisk.read, ["student"], search_homework_tool),
        ("summarize_conversation", "Summarize a tutoring conversation the user may access.", AgentActionRisk.read, ["student", "tutor"], summarize_conversation_tool),
        ("book_session", "Request a tutoring session for the authenticated student.", AgentActionRisk.write_requires_confirmation, ["student"], book_session_tool),
        ("cancel_session", "Cancel a session the authenticated user participates in.", AgentActionRisk.write_requires_confirmation, ["student", "tutor", "admin"], cancel_session_tool),
        ("reschedule_session", "Propose a new time for a visible session.", AgentActionRisk.write_requires_confirmation, ["student", "tutor", "admin"], reschedule_session_tool),
        ("update_profile", "Update the authenticated user's own profile.", AgentActionRisk.write_requires_confirmation, ["student", "tutor", "admin"], update_profile_tool),
        ("send_message", "Send a message as the authenticated conversation participant.", AgentActionRisk.write_requires_confirmation, ["student", "tutor"], send_message_tool),
        ("create_reminder", "Create a personal in-app reminder.", AgentActionRisk.write_requires_confirmation, ["student", "tutor", "admin"], create_reminder_tool),
    ]
    return {
        name: AgentTool(AgentToolDefinition(name=name, description=description, risk=risk, allowed_roles=roles), handler)
        for name, description, risk, roles, handler in specifications
    }
