# 📰 Newsletter Agent

> An autonomous AI agent that researches, writes, critiques, and publishes newsletters — with a Human-in-the-Loop approval gate, full CI/CD pipeline, and live deployment.

[![CI/CD](https://github.com/SohamBirlaa/News-Letter-Agent---LangGraph-LangChain/actions/workflows/test.yml/badge.svg)](https://github.com/SohamBirlaa/News-Letter-Agent---LangGraph-LangChain/actions)
[![Docker](https://img.shields.io/badge/docker-sohambirlaa%2Fnewsletter--agent-blue)](https://hub.docker.com/r/sohambirlaa/newsletter-agent)
[![Live](https://img.shields.io/badge/live-render.com-brightgreen)](https://news-letter-agent-langgraph-langchain.onrender.com)

**🌐 Live Demo:** [https://news-letter-agent-langgraph-langchain.onrender.com](https://news-letter-agent-langgraph-langchain.onrender.com)

---

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
                                              thread_id stored in Flask session
                                              Draft returned to browser
                                                              ↓
                                              User reads draft → clicks Approve
                                                              ↓
                                              resume(thread_id) → input=None
                                              LangGraph loads checkpoint → resumes
                                              human_review → send → DONE
```

---

## 🗂️ Project Structure

```
newsletter-agent/
├── agent.py                    # LangGraph pipeline — all 7 nodes + state
├── app.py                      # Flask REST API — 5 endpoints
├── tools.py                    # Tavily search + file save tools
├── prompts.py                  # All LLM prompt templates
├── database.py                 # SQLite wrapper (init, save, fetch)
├── templates/
│   └── index.html              # Browser UI
├── tests/
│   ├── conftest.py             # Shared fixtures + env setup
│   ├── test_unit.py            # 55 unit + integration tests
│   └── test_e2e.py             # 22 Selenium E2E tests
├── Dockerfile                  # Container definition
├── .dockerignore               # Clean image config
├── render.yaml                 # Render.com deployment config
├── pyproject.toml              # pytest config
├── .env.example                # Environment variable reference
├── .github/
│   └── workflows/
│       └── test.yml            # GitHub Actions CI/CD pipeline
├── newsletter.md               # Output — generated newsletter
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Groq API key — free at [console.groq.com](https://console.groq.com)
- Tavily API key — free at [tavily.com](https://tavily.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/SohamBirlaa/News-Letter-Agent---LangGraph-LangChain.git
cd newsletter-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root (see `.env.example`):

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_AP_KEY=your_tavily_api_key_here
```

### Run Locally

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

### Run with Docker

```bash
# Pull from Docker Hub
docker pull sohambirlaa/newsletter-agent:latest

# Run with environment variables
docker run -p 5000:5000 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_AP_KEY=your_key \
  sohambirlaa/newsletter-agent:latest
```

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest selenium webdriver-manager

# Unit + integration tests (no server needed)
pytest tests/test_unit.py -v

# E2E tests (requires: python app.py running)
pytest tests/test_e2e.py -v

# Full suite
pytest -v
```

### Test Coverage

| Section | Tests | Status |
|---------|-------|--------|
| Agent nodes (planner, research, summarize, write, critic, human_review, send) | 21 | ✅ |
| review_router() conditional logic | 4 | ✅ |
| safe_llm_call() helper | 4 | ✅ |
| Database functions | 8 | ✅ |
| Tools (Tavily + file save) | 5 | ✅ |
| Flask API endpoints | 13 | ✅ |
| Selenium E2E browser tests | 22 | ✅ |
| **Total** | **77** | **✅ 77/77** |

---

## 🔁 CI/CD Pipeline

Every push to `main` triggers:

```
git push
    ↓
GitHub Actions
    ↓
Job 1: Run 55 unit tests
    ↓ (pass hone par)
Job 2: Build Docker image → push to Docker Hub
    ↓
Render.com auto-deploys
    ↓
Live at onrender.com 🎉
```

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
| `auto` | Fully autonomous — publishes directly |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph |
| LLM | Groq API (llama-3.3-70b-versatile) — free, fast |
| Web Search | Tavily |
| Backend | Flask + Gunicorn |
| Database | SQLite |
| Frontend | HTML + CSS + Vanilla JS |
| Testing | pytest + Selenium |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Deployment | Render.com |

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

## ✅ Features Checklist

| Feature | Status |
|---------|--------|
| Multi-step reasoning (plan → research → write → review → publish) | ✅ 7-node pipeline |
| Minimum 2–3 tools | ✅ Tavily search + LLM + file generator |
| Self-reflection / critique step | ✅ Dedicated `critic` node |
| Human-in-the-Loop toggle | ✅ `human` / `auto` mode |
| Pause & resume with thread_id | ✅ LangGraph MemorySaver + Flask session |
| Simple frontend | ✅ Flask-served browser UI |
| Newsletter history | ✅ SQLite + sidebar |
| Unit + integration tests | ✅ 55 pytest tests |
| E2E browser tests | ✅ 22 Selenium tests |
| Dockerized | ✅ Docker Hub: sohambirlaa/newsletter-agent |
| CI/CD pipeline | ✅ GitHub Actions |
| Live deployment | ✅ Render.com |

---

## 📄 License

MIT