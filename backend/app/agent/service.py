from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.models import AgentConversation, AgentMessage, PendingAction
from app.agent.planner import AgentPlanner
from app.agent.rag import RAGService
from app.agent.schemas import (
    ActionDecisionResponse,
    AgentContext,
    AgentConversationRead,
    AgentMessageRequest,
    AgentMessageResponse,
    MemoryCreate,
)
from app.agent.tools import AgentTool, ToolRuntime, build_tool_registry
from app.audit.service import AuditService
from app.core.errors import AppError
from app.core.logging import logger
from app.core.security import CurrentUser


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tools = build_tool_registry()
        self.planner = AgentPlanner()

    async def respond(self, user: CurrentUser, request: AgentMessageRequest) -> AgentMessageResponse:
        conversation = await self._conversation(user, request.conversation_id)
        await self._add_message(conversation, "user", request.message)
        await AuditService(self.db).record(
            user.id,
            "agent.request",
            "agent_conversation",
            conversation.id,
            {"message_length": len(request.message)},
        )
        await self._remember_if_useful(user, request.message)

        context = AgentContext(user_id=user.id, role=user.role.value, timezone=user.timezone)
        history = [{"role": item.role, "content": item.content} for item in conversation.messages]
        plan = await self.planner.plan(
            request.message,
            context,
            [tool.definition for tool in self.tools.values()],
            history,
        )

        if plan.clarification:
            return await self._reply(conversation, plan.clarification)
        if plan.direct_answer:
            return await self._reply(conversation, plan.direct_answer)
        if not plan.tool_name or plan.tool_name not in self.tools:
            return await self._reply(conversation, "I could not select a safe platform capability for that request. Please rephrase it.")

        tool = self.tools[plan.tool_name]
        if user.role.value not in tool.definition.allowed_roles:
            message = f"Your {user.role.value} account is not allowed to use {tool.definition.name}."
            await self._audit_tool(user, conversation.id, tool, "permission_denied", 0, message)
            return await self._reply(conversation, message, tool.definition.name)

        await AuditService(self.db).record(
            user.id,
            "agent.tool_selected",
            "agent_conversation",
            conversation.id,
            {"tool": tool.definition.name, "risk": tool.definition.risk.value},
        )

        if tool.definition.risk.value == "write_requires_confirmation":
            description = self._describe_action(tool.definition.name, plan.arguments)
            action = PendingAction(
                conversation_id=conversation.id,
                user_id=user.id,
                tool_name=tool.definition.name,
                arguments=plan.arguments,
                description=description,
                status="pending",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )
            self.db.add(action)
            await self.db.commit()
            await AuditService(self.db).record(
                user.id,
                "agent.action_proposed",
                "pending_action",
                action.id,
                {"tool": tool.definition.name, "expires_at": action.expires_at.isoformat()},
            )
            message = f"I can {description}. Please confirm before I make this change."
            await self._add_message(conversation, "assistant", message, tool.definition.name)
            return AgentMessageResponse(
                message=message,
                conversation_id=conversation.id,
                requires_confirmation=True,
                pending_action_id=action.id,
                proposed_action=description,
                tool_name=tool.definition.name,
            )

        started = perf_counter()
        try:
            result = await tool.handler(ToolRuntime(self.db, user), plan.arguments)
            duration_ms = (perf_counter() - started) * 1000
            await self._audit_tool(user, conversation.id, tool, "success", duration_ms)
            return await self._reply(conversation, self._format_result(tool.definition.name, result), tool.definition.name)
        except AppError as exc:
            duration_ms = (perf_counter() - started) * 1000
            await self._audit_tool(user, conversation.id, tool, "error", duration_ms, exc.message)
            return await self._reply(conversation, f"I couldn't complete that: {exc.message}", tool.definition.name)
        except Exception as exc:
            duration_ms = (perf_counter() - started) * 1000
            logger.exception("Agent read tool failed tool=%s", tool.definition.name)
            await self._audit_tool(user, conversation.id, tool, "error", duration_ms, type(exc).__name__)
            return await self._reply(conversation, "That platform lookup failed unexpectedly. The error was logged with your request ID.", tool.definition.name)

    async def confirm_action(self, user: CurrentUser, action_id: str) -> ActionDecisionResponse:
        action = await self._pending_action(user, action_id)
        if action.expires_at < datetime.now(timezone.utc):
            action.status = "expired"
            await self.db.commit()
            raise AppError("This proposed action expired. Ask the assistant to propose it again", status.HTTP_409_CONFLICT)
        tool = self.tools.get(action.tool_name)
        if tool is None or user.role.value not in tool.definition.allowed_roles:
            raise AppError("You no longer have permission to execute this action", status.HTTP_403_FORBIDDEN)

        started = perf_counter()
        try:
            result = await tool.handler(ToolRuntime(self.db, user), action.arguments)
            action.status = "executed"
            action.executed_at = datetime.now(timezone.utc)
            await self.db.commit()
            duration_ms = (perf_counter() - started) * 1000
            await self._audit_tool(user, action.conversation_id, tool, "success", duration_ms)
            await AuditService(self.db).record(
                user.id, "agent.action_confirmed", "pending_action", action.id, {"tool": tool.definition.name}
            )
            message = self._format_result(tool.definition.name, result)
            conversation = await self._conversation(user, action.conversation_id)
            await self._add_message(conversation, "assistant", message, tool.definition.name)
            return ActionDecisionResponse(action_id=action.id, status=action.status, message=message, result=result)
        except AppError as exc:
            await self.db.rollback()
            action = await self._pending_action(user, action_id)
            action.status = "failed"
            await self.db.commit()
            duration_ms = (perf_counter() - started) * 1000
            await self._audit_tool(user, action.conversation_id, tool, "error", duration_ms, exc.message)
            suggestion = ""
            if tool.definition.name in {"book_session", "reschedule_session"} and "availab" in exc.message.casefold():
                alternatives = await self.tools["search_tutors"].handler(ToolRuntime(self.db, user), {"query": action.arguments.get("subject", "")})
                names = [item["display_name"] for item in alternatives["tutors"][:3]]
                if names:
                    suggestion = f" Other tutors to consider: {', '.join(names)}."
            return ActionDecisionResponse(action_id=action.id, status="failed", message=f"I couldn't execute that action: {exc.message}.{suggestion}")

    async def reject_action(self, user: CurrentUser, action_id: str) -> ActionDecisionResponse:
        action = await self._pending_action(user, action_id)
        action.status = "rejected"
        await self.db.commit()
        await AuditService(self.db).record(user.id, "agent.action_rejected", "pending_action", action.id, {"tool": action.tool_name})
        return ActionDecisionResponse(action_id=action.id, status="rejected", message="The proposed action was discarded. Nothing was changed.")

    async def list_conversations(self, user: CurrentUser) -> list[AgentConversationRead]:
        result = await self.db.execute(
            select(AgentConversation)
            .options(selectinload(AgentConversation.messages))
            .where(AgentConversation.user_id == user.id)
            .order_by(AgentConversation.updated_at.desc())
        )
        return [self._conversation_read(item) for item in result.scalars().all()]

    async def _conversation(self, user: CurrentUser, conversation_id: str | None) -> AgentConversation:
        if conversation_id:
            result = await self.db.execute(
                select(AgentConversation).options(selectinload(AgentConversation.messages)).where(
                    AgentConversation.id == conversation_id,
                    AgentConversation.user_id == user.id,
                )
            )
            item = result.scalar_one_or_none()
            if item is None:
                raise AppError("Agent conversation not found", status.HTTP_404_NOT_FOUND)
            return item
        item = AgentConversation(user_id=user.id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item, attribute_names=["messages"])
        return item

    async def _pending_action(self, user: CurrentUser, action_id: str) -> PendingAction:
        result = await self.db.execute(
            select(PendingAction).where(PendingAction.id == action_id, PendingAction.user_id == user.id)
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise AppError("Pending action not found", status.HTTP_404_NOT_FOUND)
        if action.status != "pending":
            raise AppError(f"This action is already {action.status}", status.HTTP_409_CONFLICT)
        return action

    async def _add_message(self, conversation: AgentConversation, role: str, content: str, tool_name: str | None = None) -> None:
        message = AgentMessage(conversation_id=conversation.id, role=role, content=content, tool_name=tool_name)
        self.db.add(message)
        conversation.updated_at = datetime.now(timezone.utc)
        conversation.messages.append(message)
        if len(conversation.messages) >= 6:
            conversation.summary = " ".join(item.content for item in conversation.messages[-6:])[:1500]
        await self.db.commit()

    async def _reply(self, conversation: AgentConversation, message: str, tool_name: str | None = None) -> AgentMessageResponse:
        await self._add_message(conversation, "assistant", message, tool_name)
        return AgentMessageResponse(message=message, conversation_id=conversation.id, tool_name=tool_name)

    async def _remember_if_useful(self, user: CurrentUser, message: str) -> None:
        lower = message.casefold()
        useful = any(marker in lower for marker in ["i prefer", "i learn best", "my learning goal", "my goal is"])
        sensitive = any(marker in lower for marker in ["password", "address", "medical", "diagnosis", "social security", "credit card"])
        if useful and not sensitive:
            kind = "learning_goal" if "goal" in lower else "preference"
            await RAGService(self.db).add_memory(user, MemoryCreate(kind=kind, content=message))

    async def _audit_tool(self, user: CurrentUser, conversation_id: str, tool: AgentTool, result_status: str, duration_ms: float, error: str | None = None) -> None:
        await AuditService(self.db).record(
            user.id,
            "agent.tool_result",
            "agent_conversation",
            conversation_id,
            {"tool": tool.definition.name, "status": result_status, "duration_ms": round(duration_ms, 2), "error": error},
        )

    @staticmethod
    def _describe_action(tool_name: str, arguments: dict[str, Any]) -> str:
        descriptions = {
            "book_session": f"request a {arguments.get('subject', 'tutoring')} session for {arguments.get('starts_at')}",
            "cancel_session": "cancel the selected upcoming session",
            "reschedule_session": f"propose moving the session to {arguments.get('starts_at')}",
            "update_profile": f"update your profile fields: {', '.join(arguments)}",
            "send_message": f"send this message: {arguments.get('body', '')}",
            "create_reminder": f"create a reminder for {arguments.get('remind_at')}",
        }
        return descriptions.get(tool_name, tool_name.replace("_", " "))

    @staticmethod
    def _format_result(tool_name: str, result: dict[str, Any]) -> str:
        if tool_name == "search_tutors":
            tutors = result["tutors"]
            return "I found: " + "; ".join(f"{item['display_name']} ({', '.join(subject['subject'] for subject in item['subjects'])}, rating {item['rating']})" for item in tutors) if tutors else "I couldn't find an active tutor matching that request."
        if tool_name == "check_availability":
            return "That time is available." if result["available"] else f"That time is unavailable: {result.get('reason')}."
        if tool_name == "list_upcoming_sessions":
            sessions = result["sessions"]
            return "Your upcoming sessions: " + "; ".join(f"{item['subject']} with {item['tutor_name']} at {item['starts_at']} ({item['status']})" for item in sessions) if sessions else "You do not have any upcoming sessions."
        if tool_name == "answer_platform_question":
            return result["answer"] or "I could not find that in the platform documentation."
        if tool_name == "search_homework":
            docs = result["homework"]
            return "Relevant homework: " + "; ".join(f"{item['title']}: {item['content'][:250]}" for item in docs) if docs else "I couldn't find homework matching that request."
        if tool_name == "summarize_conversation":
            return result["summary"]
        if tool_name == "book_session":
            return f"The session request was created for {result['session']['starts_at']}."
        if tool_name == "cancel_session":
            return "The session was cancelled."
        if tool_name == "reschedule_session":
            return "The new session time was proposed and now needs the other participant's approval."
        if tool_name == "update_profile":
            return "Your profile was updated."
        if tool_name == "send_message":
            return "Your message was sent."
        if tool_name == "create_reminder":
            return f"Your reminder was scheduled for {result['reminder']['remind_at']}."
        return "The request completed successfully."

    @staticmethod
    def _conversation_read(item: AgentConversation) -> AgentConversationRead:
        return AgentConversationRead(
            id=item.id,
            summary=item.summary,
            created_at=item.created_at,
            updated_at=item.updated_at,
            messages=item.messages,
        )
