from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.agent.schemas import AgentActionRisk, AgentContext, AgentToolDefinition


ToolHandler = Callable[[AgentContext, dict], Awaitable[dict]]


@dataclass(frozen=True)
class AgentTool:
    definition: AgentToolDefinition
    handler: ToolHandler


async def search_tutors_tool(context: AgentContext, args: dict) -> dict:
    raise NotImplementedError("Agent tutor search tool is not implemented yet.")


async def check_availability_tool(context: AgentContext, args: dict) -> dict:
    raise NotImplementedError("Agent availability tool is not implemented yet.")


async def book_session_tool(context: AgentContext, args: dict) -> dict:
    raise NotImplementedError("Agent booking tool is not implemented yet.")


def build_tool_registry() -> dict[str, AgentTool]:
    tools = [
        AgentTool(
            definition=AgentToolDefinition(
                name="search_tutors",
                description="Search tutors by subject, expertise, and basic filters.",
                risk=AgentActionRisk.read,
            ),
            handler=search_tutors_tool,
        ),
        AgentTool(
            definition=AgentToolDefinition(
                name="check_availability",
                description="Check tutor availability for a requested time window.",
                risk=AgentActionRisk.read,
            ),
            handler=check_availability_tool,
        ),
        AgentTool(
            definition=AgentToolDefinition(
                name="book_session",
                description="Book a tutoring session after user confirmation.",
                risk=AgentActionRisk.write_requires_confirmation,
            ),
            handler=book_session_tool,
        ),
    ]
    return {tool.definition.name: tool for tool in tools}

