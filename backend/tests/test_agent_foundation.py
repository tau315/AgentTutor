import asyncio
import math

from app.agent.planner import AgentPlanner
from app.agent.rag import embed_text
from app.agent.schemas import AgentActionRisk
from app.agent.tools import build_tool_registry


def test_embedding_is_deterministic_and_normalized():
    first = embed_text("calculus derivatives")
    second = embed_text("calculus derivatives")

    assert first == second
    assert len(first) == 384
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)


def test_tool_registry_separates_reads_from_confirmed_writes():
    tools = build_tool_registry()

    assert tools["search_tutors"].definition.risk == AgentActionRisk.read
    assert tools["book_session"].definition.risk == AgentActionRisk.write_requires_confirmation
    assert "student" in tools["book_session"].definition.allowed_roles
    assert "tutor" not in tools["book_session"].definition.allowed_roles


def test_planner_clarifies_incomplete_booking_request():
    plan = AgentPlanner()._fallback_plan("Book a calculus session")

    assert plan.tool_name is None
    assert "tutor" in plan.clarification.casefold()


def test_planner_routes_platform_question_to_rag():
    plan = AgentPlanner()._fallback_plan("How do cancellations work?")

    assert plan.tool_name == "answer_platform_question"
    assert plan.arguments["query"] == "How do cancellations work?"


def test_planner_does_not_treat_cancellation_question_as_an_action():
    plan = AgentPlanner()._fallback_plan("How do session cancellations work?")

    assert plan.tool_name == "answer_platform_question"


def test_planner_never_executes_write_tools_directly():
    plan = AgentPlanner()._fallback_plan(
        "Book a calculus session with 6b4c8630-3699-4eb1-bdc8-782d81358c03 "
        "2026-08-04T17:00:00-04:00 2026-08-04T18:00:00-04:00"
    )
    tool = build_tool_registry()[plan.tool_name]

    assert tool.definition.risk == AgentActionRisk.write_requires_confirmation
