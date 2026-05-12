# 📰 Newsletter Agent

> An autonomous AI agent that researches, writes, critiques, and publishes newsletters — with a Human-in-the-Loop approval gate.


## 🎯 What It Does

Give the agent a plain-English goal like:

> *"Create a weekly newsletter on the latest AI agent news"*

The agent autonomously:
1. **Plans** a step-by-step execution strategy
2. **Researches** the latest AI news via Tavily web search
3. **Summarizes** the top 5–7 articles
4. **Writes** a polished Markdown newsletter
5. **Critiques** its own draft and improves it
6. **Pauses** for human review *(Human-in-the-Loop)*
7. **Publishes** the approved newsletter to file + SQLite

---

## 🧠 Architecture

```
Browser UI (index.html)
       ↓
Flask REST API (app.py)
       ↓
LangGraph Agent (agent.py)
   ├── planner       → Creates execution plan
   ├── research      → Fetches news via Tavily
   ├── summarize     → Condenses into bullet points
   ├── write         → Generates full newsletter
   ├── critic        → Self-reviews and improves draft
   ├── human_review  → ⏸ PAUSES for approval (HITL)
   └── send          → Saves newsletter.md
       ↓
SQLite Database (database.py) + newsletter.md
```

### Agent Pipeline (7 Nodes)

| Step | Node | What it does |
|------|------|-------------|
| 1 | `planner` | LLM creates a 7-step execution plan |
| 2 | `research` | Tavily fetches 7 latest AI news articles |
| 3 | `summarize` | LLM condenses into 5–7 focused bullets |
| 4 | `write` | LLM generates full Markdown newsletter |
| 5 | `critic` | LLM self-reviews and rewrites for clarity |
| 6 | `human_review` | Graph pauses — waits for human approval |
| 7 | `send` | Saves final newsletter to file + DB |

### HITL — How Pause & Resume Works

```
Run Agent  →  planner → research → summarize → write → critic
                                                              ↓
                                              interrupt_before=['human_review']
                                              Graph PAUSES → saves state to MemorySaver
                                              Draft returned to browser
                                                              ↓
                                              User clicks Approve
                                                              ↓
                                              resume(thread_id) → input=None
                                              LangGraph loads checkpoint → resumes
                                              human_review → send → DONE
```

---

## 🗂️ Project Structure

```
newsletter-agent/
├── agent.py          # LangGraph pipeline — all 7 nodes + state
├── app.py            # Flask REST API — 5 endpoints
├── tools.py          # Tavily search + file save tools
├── prompts.py        # All LLM prompt templates
├── database.py       # SQLite wrapper (init, save, fetch)
├── templates/
│   └── index.html    # Browser UI
├── newsletter.md     # Output — generated newsletter
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed with `llama3.2` pulled
- Tavily API key — free at [tavily.com](https://tavily.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/SohamBirlaa/News-Letter-Agent---LangGraph-LangChain.git
cd newsletter-agent

# Install dependencies
pip install -r requirements.txt

# Pull the local LLM
ollama pull llama3.2
```

### Configuration

Create a `.env` file in the root:

```env
TAVILY_API_KEY=your_tavily_key_here
FLASK_SECRET_KEY=any_random_string
```

### Run

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## 🌐 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Serves the browser UI |
| `POST` | `/run-agent` | Start agent — returns draft newsletter |
| `POST` | `/approve` | Resume agent — publish final newsletter |
| `GET` | `/get-newsletter-file` | Read `newsletter.md` from disk |
| `GET` | `/history` | List all saved newsletters |
| `GET` | `/newsletter/<id>` | Fetch one newsletter by ID |

---

## 🔁 Modes

| Mode | Behaviour |
|------|-----------|
| `human` | Agent pauses before publishing — waits for approval |
| `auto` | Fully autonomous — no approval needed, publishes directly |

Pass `mode` in the `/run-agent` request body. Default is `human`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph |
| LLM | Ollama (llama3.2) — runs locally, no API cost |
| Web Search | Tavily |
| Backend | Flask |
| Database | SQLite |
| Frontend | HTML + CSS + Vanilla JS |

---

## 💾 Database Schema

```sql
CREATE TABLE newsletters (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    goal       TEXT,
    content    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## ✅ Assignment Requirements Checklist

| Requirement | Status |
|-------------|--------|
| Multi-step reasoning (plan → research → write → review → output) | ✅ 7-node pipeline |
| Minimum 2–3 tools | ✅ Tavily search + LLM summarizer + newsletter file generator |
| Self-reflection / critique step | ✅ Dedicated `critic` node |
| Single function call `run_newsletter_agent(goal)` | ✅ |
| Human-in-the-Loop toggle | ✅ `human` / `auto` mode |
| Simple frontend | ✅ Flask-served browser UI |
| LangGraph or LangChain | ✅ LangGraph |

---

## 📄 License

MIT