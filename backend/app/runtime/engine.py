"""
LangGraph-based workflow execution engine.

Design:
  • Each Workflow is compiled into a LangGraph StateGraph at execution time.
  • Nodes map to Agent configurations; edges drive routing.
  • A supervisor pattern handles conditional branching when no explicit
    edge condition is specified.
  • Every state transition is broadcast via WebSocket and persisted to the DB.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
import operator

from app.runtime.tools import get_tools_for_agent
from app.websocket.manager import ws_manager
from app.config import settings

logger = logging.getLogger(__name__)

# Ensure LangChain libraries can find credentials via os.environ
import os as _os
if settings.OPENAI_API_KEY:
    _os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
if settings.ANTHROPIC_API_KEY:
    _os.environ.setdefault("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)


# ─── Shared State ──────────────────────────────────────────────────────────────


class WorkflowState(TypedDict):
    """State shared across all nodes in a workflow execution."""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    task: str
    current_node: str
    results: Dict[str, str]          # agent_name -> last output
    next_node: str                   # routing hint set by supervisor/conditional edges
    iteration: int
    max_iterations: int
    execution_id: str
    should_end: bool


# ─── LLM Factory ───────────────────────────────────────────────────────────────


def _make_llm(model: str, temperature: float, max_tokens: int):
    """Instantiate an LLM from the agent config."""
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens)
    if model.startswith("claude"):
        return ChatAnthropic(model=model, temperature=temperature, max_tokens=max_tokens)
    if model.startswith("llama") or model.startswith("mixtral") or model.startswith("gemma") or model.startswith("groq/"):
        groq_model = model.replace("groq/", "")
        return ChatGroq(model=groq_model, temperature=temperature, max_tokens=max_tokens)
    # Default fallback → Groq llama-3.1-8b-instant (free tier)
    if settings.GROQ_API_KEY:
        return ChatGroq(model="llama-3.1-8b-instant", temperature=temperature, max_tokens=max_tokens)
    return ChatOpenAI(model="gpt-4o-mini", temperature=temperature, max_tokens=max_tokens)


# ─── Agent Node Factory ────────────────────────────────────────────────────────


def _make_agent_node(
    agent_cfg: dict,
    node_id: str,
    db_session_factory,
    execution_id: str,
):
    """
    Returns an async callable that LangGraph will invoke as a graph node.

    The node runs a ReAct loop: LLM → (tool calls?) → LLM → … until the LLM
    produces a final response with no tool calls.
    """
    llm = _make_llm(
        agent_cfg.get("model", "gpt-4o-mini"),
        agent_cfg.get("temperature", 0.7),
        agent_cfg.get("max_tokens", 2048),
    )
    tools = get_tools_for_agent(agent_cfg.get("tools") or [])
    tools_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    system_prompt = agent_cfg.get("system_prompt", "You are a helpful assistant.")
    agent_name = agent_cfg.get("name", "Agent")
    agent_id = agent_cfg.get("id", "")
    max_react_iters = agent_cfg.get("guardrails", {}).get("max_tool_iterations", 8)

    async def node_fn(state: WorkflowState) -> dict:
        new_messages: list[BaseMessage] = []

        await ws_manager.broadcast_execution(
            execution_id,
            {
                "type": "agent_start",
                "execution_id": execution_id,
                "node_id": node_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "iteration": state["iteration"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Build message context for this agent
        ctx: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        # Add task as first human message if no messages yet
        if not state["messages"]:
            ctx.append(HumanMessage(content=state["task"]))
        else:
            # Summarise prior agent results for context
            if state["results"]:
                summary = "\n\n".join(
                    f"[{k}]: {v}" for k, v in state["results"].items()
                )
                ctx.append(
                    HumanMessage(
                        content=f"Original task: {state['task']}\n\nPrevious agent outputs:\n{summary}"
                    )
                )
            else:
                ctx.extend(list(state["messages"]))

        token_count = 0

        for _i in range(max_react_iters):
            response: AIMessage = await llm_with_tools.ainvoke(ctx + new_messages)
            new_messages.append(response)
            token_count += getattr(response.usage_metadata, "total_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

            await ws_manager.broadcast_execution(
                execution_id,
                {
                    "type": "agent_message",
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "content": response.content,
                    "has_tool_calls": bool(getattr(response, "tool_calls", None)),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Persist message
            await _persist_message(
                db_session_factory,
                execution_id=execution_id,
                agent_id=agent_id,
                role="assistant",
                content=response.content or "",
                tokens=token_count,
                meta={"node_id": node_id},
            )

            if not getattr(response, "tool_calls", None):
                break

            # Execute tool calls
            for tc in response.tool_calls:
                t_name = tc["name"]
                t_args = tc["args"]
                t_id = tc["id"]
                tool_fn = tools_map.get(t_name)
                if tool_fn:
                    try:
                        # Always try ainvoke first (handles both sync and async tools)
                        t_result = await tool_fn.ainvoke(t_args)
                    except Exception as exc:
                        t_result = f"Tool error: {exc}"
                else:
                    t_result = f"Unknown tool: {t_name}"

                tool_msg = ToolMessage(content=str(t_result), tool_call_id=t_id)
                new_messages.append(tool_msg)

                await ws_manager.broadcast_execution(
                    execution_id,
                    {
                        "type": "tool_result",
                        "execution_id": execution_id,
                        "node_id": node_id,
                        "agent_name": agent_name,
                        "tool": t_name,
                        "result": str(t_result)[:800],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

                await _persist_message(
                    db_session_factory,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    role="tool",
                    content=str(t_result),
                    tokens=0,
                    meta={"tool_name": t_name, "node_id": node_id},
                )

        final_content = ""
        for m in reversed(new_messages):
            if isinstance(m, AIMessage) and m.content:
                final_content = m.content if isinstance(m.content, str) else str(m.content)
                break

        updated_results = {**state["results"], agent_name: final_content}

        await ws_manager.broadcast_execution(
            execution_id,
            {
                "type": "agent_done",
                "execution_id": execution_id,
                "node_id": node_id,
                "agent_name": agent_name,
                "output": final_content[:500],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return {
            "messages": new_messages,
            "current_node": node_id,
            "results": updated_results,
            "iteration": state["iteration"] + 1,
        }

    return node_fn


# ─── Graph Builder ─────────────────────────────────────────────────────────────


def build_langgraph(
    workflow: dict,
    agents_map: Dict[str, dict],
    db_session_factory,
    execution_id: str,
    max_iterations: int = 20,
):
    """
    Dynamically compile a LangGraph StateGraph from the workflow JSON.

    workflow["graph"] schema (stored in DB / sent by frontend):
    {
      "nodes": [{"id": "n1", "data": {"agentId": "uuid", "label": "..."}, ...}],
      "edges": [{"source": "n1", "target": "n2", "data": {"condition": null}}, ...],
      "entryNode": "n1"
    }
    """
    graph_def = workflow.get("graph", {})
    nodes = graph_def.get("nodes", [])
    edges = graph_def.get("edges", [])
    entry_node = graph_def.get("entryNode", "")

    builder = StateGraph(WorkflowState)

    # Add agent nodes
    node_ids = set()
    for node in nodes:
        node_id = node["id"]
        agent_id = node.get("data", {}).get("agentId", "")
        agent_cfg = agents_map.get(agent_id)
        if agent_cfg is None:
            if agent_id == "__template__":
                raise ValueError(
                    f"Node '{node_id}' still has agentId='__template__'. "
                    "Open the workflow in the builder and assign a real agent to each node."
                )
            logger.warning("Agent %s not found for node %s, skipping", agent_id, node_id)
            continue
        node_fn = _make_agent_node(agent_cfg, node_id, db_session_factory, execution_id)
        builder.add_node(node_id, node_fn)
        node_ids.add(node_id)

    # Add edges
    # Build adjacency for conditional routing
    conditional_sources: dict[str, list[dict]] = {}
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        condition = (edge.get("data") or {}).get("condition")

        if src not in node_ids:
            continue

        target_node = END if tgt in ("__end__", "END", "") else tgt
        if isinstance(target_node, str) and target_node not in node_ids and target_node is not END:
            target_node = END

        if condition:
            conditional_sources.setdefault(src, []).append(
                {"target": target_node, "condition": condition}
            )
        else:
            builder.add_edge(src, target_node)

    # Wire conditional edges
    for src, cond_edges in conditional_sources.items():
        mapping = {ce["condition"]: ce["target"] for ce in cond_edges}
        # Add default → END if not covered
        if "default" not in mapping:
            mapping["default"] = END

        def make_router(m=mapping):
            def router(state: WorkflowState) -> str:
                hint = state.get("next_node", "default")
                return m.get(hint, m.get("default", END))
            return router

        builder.add_conditional_edges(src, make_router(), mapping)

    if not entry_node or entry_node not in node_ids:
        entry_node = nodes[0]["id"] if nodes else None

    if entry_node:
        builder.add_edge(START, entry_node)

    return builder.compile()


# ─── Execution Runner ──────────────────────────────────────────────────────────


async def run_workflow(
    workflow: dict,
    agents_map: Dict[str, dict],
    task_input: str,
    execution_id: str,
    db_session_factory,
    max_iterations: int = 20,
) -> str:
    """Execute a workflow and return the final output string."""

    graph = build_langgraph(workflow, agents_map, db_session_factory, execution_id, max_iterations)

    initial_state: WorkflowState = {
        "messages": [],
        "task": task_input,
        "current_node": "",
        "results": {},
        "next_node": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "execution_id": execution_id,
        "should_end": False,
    }

    await ws_manager.broadcast_execution(
        execution_id,
        {
            "type": "execution_start",
            "execution_id": execution_id,
            "task": task_input,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    try:
        final_state = await graph.ainvoke(initial_state, config={"recursion_limit": max_iterations + 5})
        # Final result = last agent's output
        results = final_state.get("results", {})
        output = list(results.values())[-1] if results else "Workflow completed."
    except Exception as exc:
        logger.exception("Workflow execution failed: %s", exc)
        output = f"Execution error: {exc}"
        await ws_manager.broadcast_execution(
            execution_id,
            {
                "type": "execution_error",
                "execution_id": execution_id,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        raise

    await ws_manager.broadcast_execution(
        execution_id,
        {
            "type": "execution_complete",
            "execution_id": execution_id,
            "output": output[:1000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return output


# ─── Single-Agent Runner (for Telegram / direct chat) ─────────────────────────


async def run_single_agent(
    agent_cfg: dict,
    user_message: str,
    conversation_history: List[BaseMessage],
    execution_id: str,
    db_session_factory,
) -> str:
    """Run a single agent with a conversation history. Used by Telegram bot."""
    llm = _make_llm(
        agent_cfg.get("model", "gpt-4o-mini"),
        agent_cfg.get("temperature", 0.7),
        agent_cfg.get("max_tokens", 2048),
    )
    tools = get_tools_for_agent(agent_cfg.get("tools") or [])
    tools_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    system_prompt = agent_cfg.get("system_prompt", "You are a helpful assistant.")
    agent_id = agent_cfg.get("id", "")

    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    messages.extend(conversation_history)
    messages.append(HumanMessage(content=user_message))

    final = ""
    for _ in range(8):
        response: AIMessage = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if response.content:
            final = response.content if isinstance(response.content, str) else str(response.content)

        await _persist_message(
            db_session_factory,
            execution_id=execution_id,
            agent_id=agent_id,
            role="assistant",
            content=final,
            tokens=0,
            meta={"channel": "telegram"},
        )

        if not getattr(response, "tool_calls", None):
            break

        for tc in response.tool_calls:
            tool_fn = tools_map.get(tc["name"])
            if tool_fn:
                try:
                    # ainvoke handles both sync and async tools correctly
                    t_result = await tool_fn.ainvoke(tc["args"])
                except Exception as exc:
                    t_result = f"Tool error: {exc}"
            else:
                t_result = f"Unknown tool: {tc['name']}"
            messages.append(ToolMessage(content=str(t_result), tool_call_id=tc["id"]))

    return final or "I'm sorry, I couldn't generate a response. Please try again."


# ─── DB Helper ────────────────────────────────────────────────────────────────


async def _persist_message(
    db_session_factory,
    execution_id: str,
    agent_id: str,
    role: str,
    content: str,
    tokens: int = 0,
    meta: dict | None = None,
):
    try:
        from app.models.message import Message

        async with db_session_factory() as session:
            msg = Message(
                execution_id=execution_id,
                agent_id=agent_id or None,
                role=role,
                content=content,
                tokens_used=tokens,
                meta=meta or {},
            )
            session.add(msg)
            await session.commit()
    except Exception as exc:
        logger.warning("Failed to persist message: %s", exc)
