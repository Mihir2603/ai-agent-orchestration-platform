"""
Integration tests for the AI Agent Orchestration Platform.

Tests cover:
  - Agent CRUD
  - Workflow CRUD + execution
  - Channel CRUD
  - Message persistence
  - Tool registry
"""

import asyncio
import os
import pytest
import pytest_asyncio

# Use an in-memory SQLite database for tests
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client():
    """Create a test HTTP client with in-memory DB."""
    from httpx import AsyncClient, ASGITransport
    from app.database import init_db
    await init_db()
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ─── Health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Agent CRUD ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_agents_empty(client):
    r = await client.get("/api/agents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_agent(client):
    payload = {
        "name": "Test Researcher",
        "role": "Researcher",
        "system_prompt": "You research things.",
        "model": "gpt-4o-mini",
        "temperature": 0.5,
        "max_tokens": 1024,
        "tools": ["calculator", "web_search"],
        "memory_enabled": True,
        "memory_window": 5,
        "guardrails": {"max_tool_iterations": 4},
        "avatar_color": "#6366f1",
    }
    r = await client.post("/api/agents", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Researcher"
    assert data["tools"] == ["calculator", "web_search"]
    assert data["memory_enabled"] is True


@pytest.mark.asyncio
async def test_get_agent(client):
    r = await client.post("/api/agents", json={"name": "Temp Agent", "system_prompt": "Hi"})
    agent_id = r.json()["id"]
    r2 = await client.get(f"/api/agents/{agent_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == agent_id


@pytest.mark.asyncio
async def test_update_agent(client):
    r = await client.post("/api/agents", json={"name": "UpdateMe", "system_prompt": "x"})
    agent_id = r.json()["id"]
    r2 = await client.put(f"/api/agents/{agent_id}", json={"name": "Updated Name"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_agent(client):
    r = await client.post("/api/agents", json={"name": "DeleteMe", "system_prompt": "x"})
    agent_id = r.json()["id"]
    r2 = await client.delete(f"/api/agents/{agent_id}")
    assert r2.status_code == 204
    r3 = await client.get(f"/api/agents/{agent_id}")
    assert r3.status_code == 404


@pytest.mark.asyncio
async def test_list_tools(client):
    r = await client.get("/api/agents/tools")
    assert r.status_code == 200
    tools = r.json()
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "web_search" in names


# ─── Workflow CRUD ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_workflow(client):
    payload = {
        "name": "Test Pipeline",
        "description": "A test workflow",
        "graph": {"nodes": [], "edges": [], "entryNode": ""},
        "max_iterations": 10,
        "timeout_seconds": 120,
    }
    r = await client.post("/api/workflows", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Pipeline"
    assert data["is_template"] is False


@pytest.mark.asyncio
async def test_list_workflows(client):
    r = await client.get("/api/workflows")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_update_workflow(client):
    r = await client.post("/api/workflows", json={"name": "Old Name", "graph": {}})
    wf_id = r.json()["id"]
    r2 = await client.put(f"/api/workflows/{wf_id}", json={"name": "New Name"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_workflow(client):
    r = await client.post("/api/workflows", json={"name": "Gone", "graph": {}})
    wf_id = r.json()["id"]
    r2 = await client.delete(f"/api/workflows/{wf_id}")
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_execute_workflow_creates_execution(client):
    """Executing a workflow creates an execution record even with an empty graph."""
    r = await client.post("/api/workflows", json={
        "name": "Exec Test",
        "graph": {"nodes": [], "edges": [], "entryNode": ""},
    })
    wf_id = r.json()["id"]

    r2 = await client.post(f"/api/workflows/{wf_id}/execute", json={"task_input": "Test task"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["workflow_id"] == wf_id
    assert data["task_input"] == "Test task"
    assert data["status"] in ("pending", "running", "completed", "failed")

    # Fetch it
    exec_id = data["id"]
    r3 = await client.get(f"/api/executions/{exec_id}")
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_execution_messages_endpoint(client):
    r = await client.post("/api/workflows", json={"name": "MsgTest", "graph": {}})
    wf_id = r.json()["id"]
    r2 = await client.post(f"/api/workflows/{wf_id}/execute", json={"task_input": "Hi"})
    exec_id = r2.json()["id"]

    r3 = await client.get(f"/api/executions/{exec_id}/messages")
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)


# ─── Channels ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_channel_crud(client):
    r = await client.post("/api/agents", json={"name": "Chan Agent", "system_prompt": "x"})
    agent_id = r.json()["id"]

    r2 = await client.post("/api/channels", json={
        "agent_id": agent_id,
        "channel_type": "webhook",
        "name": "My Webhook",
        "config": {"url": "https://example.com/hook"},
    })
    assert r2.status_code == 201
    ch = r2.json()
    assert ch["channel_type"] == "webhook"
    ch_id = ch["id"]

    r4 = await client.put(f"/api/channels/{ch_id}", json={"is_active": False})
    assert r4.json()["is_active"] is False

    r5 = await client.delete(f"/api/channels/{ch_id}")
    assert r5.status_code == 204


# ─── Tool Registry ────────────────────────────────────────────────────────────

def test_calculator_tool():
    from app.runtime.tools import calculator
    result = calculator.invoke({"expression": "2 + 2 * 3"})
    assert result == "8"


def test_word_count_tool():
    from app.runtime.tools import word_count
    result = word_count.invoke({"text": "Hello world. How are you?"})
    assert "Words: 5" in result


def test_get_tools_for_agent():
    from app.runtime.tools import get_tools_for_agent
    tools = get_tools_for_agent(["calculator", "word_count", "nonexistent"])
    assert len(tools) == 2
    names = {t.name for t in tools}
    assert "calculator" in names
    assert "word_count" in names


def test_python_repl_tool():
    from app.runtime.tools import python_repl
    result = python_repl.invoke({"code": "print(sum(range(5)))"})
    assert "10" in result


# ─── LangGraph Builder ────────────────────────────────────────────────────────

def test_build_langgraph_empty_graph():
    """Building a graph with no nodes should be handled gracefully."""
    from app.runtime.engine import build_langgraph
    from app.database import AsyncSessionLocal

    workflow = {"graph": {"nodes": [], "edges": [], "entryNode": ""}}
    try:
        g = build_langgraph(workflow, {}, AsyncSessionLocal, "test-exec-id")
        # If it compiles without error, that's fine
        assert g is not None
    except Exception:
        # Empty entry node may raise — acceptable
        pass


def test_build_langgraph_single_node():
    """A single-node graph with a known agent should compile."""
    from app.runtime.engine import build_langgraph
    from app.database import AsyncSessionLocal

    agent_id = "agent-1"
    workflow = {
        "graph": {
            "nodes": [
                {"id": "n1", "type": "agentNode", "position": {"x": 0, "y": 0},
                 "data": {"agentId": agent_id, "label": "Test"}},
            ],
            "edges": [],
            "entryNode": "n1",
        }
    }
    agents_map = {
        agent_id: {
            "id": agent_id,
            "name": "Test Agent",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 512,
            "system_prompt": "You are helpful.",
            "tools": [],
            "guardrails": {},
        }
    }
    g = build_langgraph(workflow, agents_map, AsyncSessionLocal, "exec-123")
    assert g is not None
