# Enterprise AI Support Platform

A production-grade, multi-agent AI support system built with **LangGraph** and **Gemini 2.5 Flash**. The platform classifies incoming support tickets, routes them to specialized handlers, and — across 12 progressive sessions — gains tool use, memory, security, multi-agent orchestration, and a full audit trail.

**Current state: Session 1 of 12 — The Blueprint**

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Session Roadmap](#session-roadmap)

---

## Architecture Overview

```
User Ticket
     │
     ▼
┌─────────────────┐
│  classify_node  │  ← Gemini 2.5 Flash (temperature=0)
│  (LLM call)     │    classifies into 4 categories
└────────┬────────┘
         │ route_by_category()
    ┌────┴─────────────────────┐
    ▼        ▼        ▼        ▼
technical  billing  fraud   general
 handler   handler  handler  handler
    │        │        │        │
    └────────┴────────┴────────┘
                  │
                  ▼
            final_response
```

The graph is built with **LangGraph's StateGraph**, compiled once at module load, and invoked per ticket. Every session extends the graph by adding nodes and edges — nothing is ever removed.

---

## Project Structure

```
pythonProject1/
├── support_agent.py   # Core: LangGraph graph, state, classifier, router, handlers
├── api.py             # FastAPI backend — REST + Server-Sent Events streaming
├── index.html         # HTML/JS frontend (served by FastAPI on port 8000)
├── requirements.txt   # Python dependencies
├── .env               # API keys (never committed)
└── .gitignore
```

---

## How It Works

### 1. State Schema — `SupportState`

A 17-field `TypedDict` that carries all data through the graph. Fields are pre-declared for all 12 sessions so the schema never breaks between upgrades:

| Field | Session Added | Purpose |
|---|---|---|
| `raw_input` | 1 | Original user message, never mutated |
| `sanitized_input` | 1/6 | PII-cleaned version (pass-through until Session 6) |
| `category` | 1 | Classification result: `technical`, `billing`, `fraud`, `general` |
| `messages` | 2 | Full conversation history (append-safe) |
| `customer_data` | 2 | CRM lookup result |
| `tool_results` | 2 | All tool call results (append-safe) |
| `pii_detected` | 6 | Whether PII was found in the input |
| `injection_detected` | 6 | Whether a prompt injection was attempted |
| `is_safe` | 6 | Composite safety gate |
| `system_summary` | 5 | Compressed conversation history |
| `iteration_count` | 3 | ReAct loop counter (circuit breaker) |
| `internal_notes` | 8 | Parallel agent scratchpad (append-safe) |
| `delegation_count` | 8 | Supervisor routing counter |
| `next_worker` | 8 | Supervisor's chosen next agent |
| `github_draft` | 10 | Proposed GitHub issue before human approval |
| `github_issue_url` | 10 | Created issue URL |
| `final_response` | 1 | The response returned to the user |

### 2. Classifier Node

Calls Gemini 2.5 Flash with a strict system prompt. The response goes through 3 defense layers:
1. **Normalize** — strip whitespace, lowercase, remove punctuation
2. **Validate** — check against the 4-category allowlist; default to `general` on failure
3. **Log** — print the ticket preview and result for observability

### 3. Router

A pure Python function (no LLM call) that maps `state["category"]` to the correct handler node name. Falls back to `general_handler` for any unexpected value.

### 4. Handler Stubs

Four handlers, each returning a `final_response` string. In Session 1 these are stubs — they will be replaced with full implementations across subsequent sessions:

- `technical_handler` → replaced in Session 2 (tool calls + ReAct)
- `billing_handler` → replaced in Session 2 (tool calls + ReAct)
- `fraud_handler` → replaced in Session 9 (parallel agent swarm)
- `general_handler` → permanent (stays simple throughout all sessions)

### 5. Streaming

`stream_ticket()` uses LangGraph's `.stream()` API to yield `(node_name, snapshot)` tuples as each node completes. The HTML frontend consumes these via Server-Sent Events for live step-by-step display.

---

## Setup & Installation

### Prerequisites

- Python 3.12+
- A [Google AI Studio](https://aistudio.google.com) API key (Gemini access)

### Steps

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd pythonProject1
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
```

> Never commit the `.env` file. It is already listed in `.gitignore`.

---

## Running the Project

You have two ways to run the platform. Choose one:

### Option A — HTML frontend via FastAPI (recommended)

```bash
python api.py
```

Opens at `http://localhost:8000`. Serves the `index.html` frontend with:
- Dark-themed, glassmorphism UI
- Sample ticket pills (Technical / Billing / Fraud / General)
- SSE-based live streaming execution trace
- Execution Inspector with state snapshot
- Built-in session verification panel

### Option B — CLI test harness

```bash
python support_agent.py
```

Runs 5 test cases (one per category + one adversarial) and the full session verification suite directly in the terminal. No browser needed.

---

## API Reference

The FastAPI backend (`api.py`) exposes three endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/run` | Run a ticket synchronously. Returns `category`, `final_response`, `is_safe`, `pii_detected`, `iteration_count`. |
| `POST` | `/api/stream` | Stream graph execution as Server-Sent Events. Each event is `{"node": str, "category": str, "response": str}`. Final event is `{"done": true}`. |
| `POST` | `/api/verify` | Run the Session 1 verification suite. Returns `{"passed": bool}`. |
| `GET` | `/health` | Health check. Returns `{"status": "ok", "session": 1}`. |

**Example request:**
```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"ticket": "My payment was charged twice this month."}'
```

---

## Session Roadmap

The platform is built across 12 sessions. Each session extends `support_agent.py` without removing anything from the previous session.

| Session | Name | What Gets Built |
|---|---|---|
| **1** | **The Blueprint** ✅ | Graph skeleton, `SupportState` schema, Gemini classifier, conditional router, 4 handler stubs, streaming, CLI test harness |
| **2** | **The Hands** | Tool calling: `get_customer_details()` (CRM lookup) and `search_knowledge_base()` (KB search). `llm.bind_tools()`, `ToolNode`, `agent_node`, `respond_node`. Billing and technical stubs replaced with a full ReAct-capable agent. |
| **3** | **The Loop** | ReAct (Reason + Act) pattern for the agent node. Loop counter + circuit breaker using `iteration_count` to prevent infinite tool-call loops. |
| **4** | **The Memory** | Thread-level persistence with LangGraph's `SqliteSaver` checkpointer. Conversations survive process restarts. Thread selector added to the frontend. |
| **5** | **The Summarizer** | Automatic conversation compression. When `messages` exceeds a token threshold, a summarization node condenses history into `system_summary` and clears old messages. |
| **6** | **The Shield** | Security layer: regex-based PII detection (emails, phone numbers, SSNs, card numbers), prompt injection detection, and a safety gate node that blocks unsafe inputs before classification. `pii_detected`, `injection_detected`, and `is_safe` fields activated. |
| **7** | **The Specialist** | A dedicated specialist agent for complex technical tickets. Fine-tuned system prompt, extended tool set, and escalation logic when the general agent cannot resolve within the loop limit. |
| **8** | **The Supervisor** | Supervisor agent that orchestrates multiple worker agents. Uses `next_worker` and `delegation_count` to decide which specialist handles a ticket. Dynamic routing beyond the original 4 categories. |
| **9** | **The Swarm** | Parallel agent execution for fraud tickets. Multiple specialized fraud-detection agents run concurrently, write to `internal_notes`, and a merge node consolidates findings into a single fraud assessment. `fraud_handler` stub replaced. |
| **10** | **The Writer** | GitHub integration. For unresolvable technical tickets, the agent drafts a GitHub issue and stores it in `github_draft` before requesting approval. |
| **11** | **The Gatekeeper** | Human-in-the-loop approval gate using LangGraph's `interrupt`. The frontend shows the GitHub issue draft with Approve / Deny / Edit buttons. On approval, the issue is created and `github_issue_url` is populated. |
| **12** | **The Auditor** | Full audit trail. Every state transition is persisted. Time-travel controls in the UI let you inspect any historical checkpoint. Structured audit log exported per ticket. |

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent framework | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Gemini 2.5 Flash via `langchain-google-genai` |
| Backend API | FastAPI + Uvicorn |
| Frontend | Vanilla HTML/CSS/JS |
| Environment | python-dotenv |