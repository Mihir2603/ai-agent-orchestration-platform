# 🤖 AI Agent Orchestration Platform

A full-stack platform to create AI agents, connect them into multi-agent workflows, and interact with them live via Telegram. Built with FastAPI, LangGraph, React, and Groq.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [API Keys Setup](#api-keys-setup)
4. [Feature Guide](#feature-guide)
5. [Pre-built Workflows](#pre-built-workflows)
6. [Telegram Bot](#telegram-bot)
7. [Running Tests](#running-tests)
8. [Project Structure](#project-structure)
9. [Adding New Workflows / Channels](#extending-the-platform)
10. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

### Requirements
- Python 3.11+
- Node.js 18+

### 1. Clone & Install

```bash
cd Assessment-Project

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure API Keys

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=gsk_...          # FREE — get at https://console.groq.com
OPENAI_API_KEY=sk-...          # Optional — https://platform.openai.com
TELEGRAM_BOT_TOKEN=...         # From @BotFather on Telegram
TELEGRAM_GATEWAY_AGENT_ID=...  # UUID of your agent (from UI after creating one)
```

> **Minimum required:** Only `GROQ_API_KEY` is needed to run agents. Telegram is optional.

### 3. Start the Platform

**Terminal 1 — Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Open the App

| Service | URL |
|---------|-----|
| **Web UI** | http://127.0.0.1:5173 |
| **API Docs** | http://127.0.0.1:8002/api/docs |
| **Health Check** | http://127.0.0.1:8002/api/health |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Browser (React + Vite)                        │
│  Dashboard │ Agents CRUD │ ReactFlow Builder │ Monitor │ Channels    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST /api/* + WebSocket /ws
┌────────────────────────────▼────────────────────────────────────────┐
│                        FastAPI Backend                               │
│                                                                      │
│  ┌─────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │  REST API   │  │  WebSocket Manager │  │   Telegram Bot     │   │
│  │  /api/...   │  │  (live event feed) │  │ python-telegram-   │   │
│  └──────┬──────┘  └────────────────────┘  │    bot v21 async   │   │
│         │                                  └────────┬───────────┘   │
│  ┌──────▼──────────────────────────────────────────▼───────────┐   │
│  │                  LangGraph 1.x Runtime Engine                │   │
│  │  StateGraph — compiled dynamically from workflow JSON        │   │
│  │  Agent Nodes — per-agent ReAct loops with tool calls        │   │
│  │  Tools: web_search · calculator · python_repl · datetime    │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                              │                                        │
│  ┌───────────────────────────▼──────────────────────────────────┐   │
│  │             SQLite (async via aiosqlite)                      │   │
│  │  agents · workflows · executions · messages · channels        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Technology Decisions

| Layer | Choice | Why |
|-------|--------|-----|
| **AI Framework** | LangGraph 1.x | Explicit state machine → easy conditional routing, feedback loops, per-node memory |
| **LLM** | Groq (llama-3.1-8b-instant) | Free tier, fast inference; also supports OpenAI + Anthropic via same interface |
| **Backend** | FastAPI + SQLAlchemy async | Fully async: WebSocket streaming + DB writes without blocking |
| **Database** | SQLite (aiosqlite) | Zero setup for local dev; swap to Postgres via `DATABASE_URL` change |
| **Frontend** | React + Vite + Tailwind + ReactFlow | ReactFlow = purpose-built visual graph editor; Tailwind keeps UI lean |
| **Messaging** | Telegram (python-telegram-bot 21) | Most accessible real-time channel; runs in the same asyncio loop as FastAPI |

---

## 🔑 API Keys Setup

### Groq (Required — Free)
1. Go to → https://console.groq.com
2. Sign up → **API Keys** → Create key
3. Add to `.env`: `GROQ_API_KEY=gsk_xxx`

### OpenAI (Optional)
1. Go to → https://platform.openai.com/api-keys
2. Create key → Add to `.env`: `OPENAI_API_KEY=sk-proj-xxx`
3. Set agent model to `gpt-4o-mini` or `gpt-4o`

### Anthropic (Optional)
1. Go to → https://console.anthropic.com/settings/keys
2. Create key → Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-xxx`
3. Set agent model to `claude-3-5-haiku-20241022`

### Telegram Bot
1. Open Telegram → search **@BotFather** → send `/newbot`
2. Follow prompts → copy the token
3. Add to `.env`: `TELEGRAM_BOT_TOKEN=1234567890:AAFxxx`
4. Create an agent in the UI → copy its UUID from the URL bar
5. Add to `.env`: `TELEGRAM_GATEWAY_AGENT_ID=<uuid>`
6. Restart the backend

> **Supported models by prefix:**
> - `gpt-*` → OpenAI
> - `claude-*` → Anthropic
> - `llama-*`, `mixtral-*`, `gemma-*` → Groq (free)

---

## 🎯 Feature Guide

### 1. Dashboard (`/`)
- Total agents, workflows, executions at a glance
- Recent execution history with status badges
- Quick-launch buttons

### 2. Agents (`/agents`)

**Create an agent:**
1. Click **New Agent**
2. Fill in:
   - **Name** — display name (e.g. `Researcher`)
   - **Role** — short role description (e.g. `Senior Researcher`)
   - **System Prompt** — the agent's personality and instructions
   - **Model** — `llama-3.1-8b-instant` (Groq, free) or `gpt-4o-mini`
   - **Tools** — capabilities to give the agent (see below)
   - **Memory** — toggle to remember past messages (window size)
3. Click **Save**

**Available Tools:**

| Tool | Description |
|------|-------------|
| `web_search` | Searches DuckDuckGo for real-time information |
| `calculator` | Evaluates math expressions safely |
| `get_current_datetime` | Returns the current UTC date/time |
| `python_repl` | Executes Python code snippets |
| `write_output_file` | Saves text content to a file |
| `read_output_file` | Reads a previously saved file |
| `word_count` | Counts words in a given text |

> ⚠️ **Groq + Tools Note:** Groq's Llama models can occasionally produce malformed tool calls. If an agent fails with tool errors, either remove the tools or switch the model to `gpt-4o-mini`.

### 3. Workflows (`/workflows`)

- See all workflows and templates
- Click **Use Template** to start from a pre-built pipeline
- Click **Run** on any workflow → enter a task → watch it execute
- Each execution is stored with full message history

### 4. Workflow Builder (`/workflows/new` or edit any workflow)

- **Drag** agent nodes onto the canvas
- **Connect** nodes by drawing arrows between them (output → input)
- **Entry node** = the first agent to run (set in the top-right panel)
- **Edges** can carry conditions (e.g. `if_urgent`) for branching logic
- Click **Save** then **Run** to execute

> ⚠️ **Important:** Every node must have a real agent assigned (not `__template__`). Click a node → select agent from the dropdown before saving.

### 5. Monitor (`/monitor`)

Real-time execution dashboard:
- Live WebSocket stream of every agent step
- Tool call inputs and outputs
- Inter-agent message passing
- Token usage per agent
- Execution status (pending → running → completed/failed)

**Tip:** Open Monitor *before* running a workflow to watch it live.

### 6. Channels (`/channels`)

Connect external messaging services:
1. Click **Add Channel**
2. Select type: `telegram` (or `slack`)
3. Enter bot token + select the gateway agent
4. Toggle **Active** → bot starts immediately

---

## 🔗 Pre-built Workflows

### Research & Report
```
Researcher → Analyst → Writer
```
- **Researcher** uses `web_search` to gather information
- **Analyst** synthesizes findings into key insights
- **Writer** produces a polished final report

**Example task:** `"Research the latest trends in AI agents for 2025"`

### Customer Support Pipeline
```
Triage Agent → Support Specialist → Escalation Agent
```
- **Triage** classifies the issue (simple/complex/urgent)
- **Specialist** provides a detailed solution
- **Escalation** handles unresolved or complex cases with senior response

**Example task:** `"My order #12345 has not arrived after 2 weeks. I am frustrated!"`

---

## 📱 Telegram Bot

The Telegram bot connects any agent to a real chat interface.

### Setup
```env
TELEGRAM_BOT_TOKEN=8859332791:AAH...
TELEGRAM_GATEWAY_AGENT_ID=88e27d12-ca41-495c-8999-0342c6b22629
```

### Commands
| Command | Action |
|---------|--------|
| `/start` | Introduction message |
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| Any text | Agent replies with AI response |

### Features
- **Real-time datetime** automatically injected into every response
- **Conversation memory** — remembers last 20 messages per user
- **Multi-user** — each Telegram user gets their own conversation context
- Long responses automatically split at 4000-char Telegram limit

### Test it
1. Open Telegram → search `@mihir_263_bot`
2. Send `/start`
3. Try: `"What time is it?"`, `"Tell me a joke"`, `"What is 144 * 25?"`

---

## 🧪 Running Tests

```bash
cd backend
source .venv/bin/activate
pytest ../tests/test_platform.py -v
```

**20 tests covering:**
- Agent CRUD (create, read, update, delete)
- Workflow CRUD + template seeding
- Execution creation
- Tool registry
- LangGraph graph builder (no LLM calls)
- Channel management
- WebSocket manager

Expected output:
```
20 passed in ~3s
```

---

## 📁 Project Structure

```
Assessment-Project/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   │   ├── agents.py     # GET/POST/PUT/DELETE /api/agents
│   │   │   ├── workflows.py  # Workflow CRUD + execute
│   │   │   ├── executions.py # Execution history + messages
│   │   │   └── channels.py   # Channel (Telegram/Slack) management
│   │   ├── runtime/
│   │   │   ├── engine.py     # LangGraph engine (build + run workflows)
│   │   │   └── tools.py      # Built-in agent tools
│   │   ├── channels/
│   │   │   └── telegram.py   # Async Telegram bot
│   │   ├── websocket/
│   │   │   └── manager.py    # WebSocket broadcaster
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── config.py         # Settings (reads from .env)
│   │   ├── database.py       # Async DB engine + session factory
│   │   └── main.py           # FastAPI app entry point
│   ├── templates/
│   │   ├── research_report.json    # Pre-built template
│   │   └── customer_support.json   # Pre-built template
│   ├── data/                 # SQLite database files
│   ├── .env                  # ← Your API keys go here
│   ├── .env.example          # Template for .env
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/            # Dashboard, Agents, Workflows, Monitor, Channels
│       ├── components/       # Layout, AgentNode, ExecutionLog
│       ├── hooks/            # useWebSocket
│       ├── api/              # axios client + typed API functions
│       └── types/            # TypeScript types
├── tests/
│   └── test_platform.py      # 20 integration tests
├── docker-compose.yml
├── setup.sh
└── README.md
```

---

## 🔧 Extending the Platform

### Adding a New Workflow Template

1. Create a JSON file in `backend/templates/your_template.json`:

```json
{
  "name": "My Custom Pipeline",
  "description": "What this workflow does",
  "template_type": "my_template",
  "graph": {
    "entryNode": "node1",
    "nodes": [
      {
        "id": "node1",
        "type": "agentNode",
        "position": { "x": 100, "y": 200 },
        "data": {
          "agentId": "__template__",
          "label": "First Agent",
          "templateRole": "first_agent"
        }
      }
    ],
    "edges": []
  }
}
```

2. The template is auto-seeded on next backend startup.

### Adding a New Tool

In `backend/app/runtime/tools.py`:

```python
from langchain_core.tools import tool

@tool
async def my_tool(param: str) -> str:
    """Description of what the tool does."""
    # your logic here
    return "result"
```

Then register it in the `TOOL_REGISTRY` and `TOOL_DESCRIPTIONS` dicts at the bottom of the file.

### Adding a New Messaging Channel

1. Create `backend/app/channels/my_channel.py` with a `start_my_channel_bot(token, agent_id)` async function
2. Add channel type handling in `backend/app/api/channels.py` (in the `create_channel` route)
3. Add graceful shutdown in `backend/app/channels/telegram.py`'s pattern as reference

---

## 🐛 Troubleshooting

### Backend won't start — port already in use
```bash
# Find and use a different port
uvicorn app.main:app --host 127.0.0.1 --port 8002
# Update frontend/vite.config.ts proxy target to match
```

### Agent execution fails with `429 quota exceeded`
- OpenAI/Anthropic keys have no credits
- **Fix:** Switch agent model to `llama-3.1-8b-instant` (Groq, free)

### Workflow fails with `agentId='__template__'`
- A workflow node has no real agent assigned
- **Fix:** Open the workflow in the Builder → click each node → select a real agent → Save

### Workflow fails with `INVALID_CONCURRENT_GRAPH_UPDATE`
- Workflow has forked edges (one node connects to two nodes simultaneously)
- **Fix:** Make the workflow sequential — each node connects to only one next node

### Groq tool call errors (`tool_use_failed`)
- Groq's Llama model generates malformed tool calls for some tools
- **Fix:** Remove tools from the agent, or switch to `gpt-4o-mini`

### Telegram bot not responding
1. Check backend logs: `tail -f /tmp/backend.log`
2. Verify bot token is correct in `.env`
3. Verify `TELEGRAM_GATEWAY_AGENT_ID` points to an existing agent:
   ```bash
   curl http://127.0.0.1:8002/api/agents/<uuid>
   ```
4. Restart backend to reload the channel config

### Tests failing
```bash
cd backend
source .venv/bin/activate
# Run with verbose output
pytest ../tests/test_platform.py -v --tb=short
```

---

## 📊 API Reference

Full interactive docs at: **http://127.0.0.1:8002/api/docs**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List all agents |
| `/api/agents` | POST | Create agent |
| `/api/agents/{id}` | PUT | Update agent |
| `/api/agents/{id}` | DELETE | Delete agent |
| `/api/agents/tools` | GET | List available tools |
| `/api/workflows` | GET | List all workflows |
| `/api/workflows/templates` | GET | List template workflows |
| `/api/workflows/{id}/execute` | POST | Run a workflow |
| `/api/executions` | GET | List execution history |
| `/api/executions/{id}/messages` | GET | Get execution messages |
| `/api/channels` | GET/POST | Manage messaging channels |
| `/ws?channel=global` | WebSocket | Real-time event stream |

---

*Built for the Yuno AI Engineer Hiring Challenge — AI Agent Orchestration Platform*
