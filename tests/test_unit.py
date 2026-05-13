"""
=============================================================
 UNIT & INTEGRATION TESTS — Newsletter Agent
 Run with:  pytest tests/test_unit.py -v
=============================================================

What is tested here:
  - Every agent node function in isolation
  - review_router() conditional logic
  - safe_llm_call() error handling
  - All database.py functions against a temp SQLite DB
  - All 5 Flask routes using Flask test client
  - tools.py functions with mocked external calls

Mocking strategy:
  - LLM calls  → patch("agent.safe_llm_call") — ChatOllama is a Pydantic model
                 so patch("agent.llm.invoke") doesn't work. Patching safe_llm_call
                 directly is cleaner and tests the same logic.
  - Tavily      → unittest.mock.patch("tools.tavily.search")
  - File I/O    → unittest.mock.patch("builtins.open")
  - DB          → real SQLite but in a temp file, cleaned up after
"""

import os
import sys
import sqlite3
import tempfile
import pytest
from unittest.mock import MagicMock, patch, mock_open

# ── make sure project root is on path ──────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── patch env vars BEFORE importing agent ──────────────────
os.environ.setdefault("TAVILY_AP_KEY", "test-key")


# ===========================================================
#  SECTION 1 — AGENT NODE TESTS
# ===========================================================

class TestPlannerNode:
    """Tests for the planner() node function."""

    def test_planner_returns_plan_on_valid_goal(self):
        """planner() should call LLM and return a plan dict."""
        from agent import planner

        with patch("agent.safe_llm_call", return_value="1. Research\n2. Write\n3. Review"):
            result = planner({"goal": "Write an AI newsletter"})

        assert "plan" in result
        assert "Research" in result["plan"]

    def test_planner_returns_error_on_empty_goal(self):
        """planner() should return error dict when goal is empty."""
        from agent import planner

        result = planner({"goal": ""})

        assert "error" in result
        assert "Goal is required" in result["error"]

    def test_planner_returns_error_on_missing_goal_key(self):
        """planner() should handle missing 'goal' key gracefully."""
        from agent import planner

        result = planner({})

        assert "error" in result

    def test_planner_returns_error_when_llm_fails(self):
        """planner() should catch LLM exceptions and return error."""
        from agent import planner

        with patch("agent.safe_llm_call", side_effect=Exception("LLM timeout")):
            result = planner({"goal": "Write a newsletter"})

        assert "error" in result


class TestResearchNode:
    """Tests for the research() node function."""

    def test_research_returns_news_on_success(self):
        """research() should return news when Tavily finds results."""
        from agent import research

        with patch("tools.tavily.search", return_value={
            "results": [
                {"title": "AI in 2025", "url": "http://example.com", "content": "AI is growing fast."}
            ]
        }):
            result = research({})

        assert "news" in result
        assert "AI in 2025" in result["news"]

    def test_research_returns_error_when_no_results(self):
        """research() should return error when Tavily returns empty."""
        from agent import research

        with patch("tools.tavily.search", return_value={"results": []}):
            result = research({})

        assert "error" in result

    def test_research_returns_error_on_tavily_exception(self):
        """
        When Tavily throws, search_ai_news() catches it and returns an
        error string. research() receives that string as news (non-empty),
        so it returns {"news": "Error occurred: ..."} rather than {"error": ...}.
        This test verifies that actual behaviour.
        """
        from agent import research

        with patch("tools.tavily.search", side_effect=Exception("API limit")):
            result = research({})

        # search_ai_news catches the exception and returns "Error occurred: ..."
        # so research() gets a non-empty string and stores it under "news"
        assert "news" in result
        assert "Error occurred" in result["news"]


class TestSummarizeNode:
    """Tests for the summarize() node function."""

    def test_summarize_returns_summary(self):
        """summarize() should return a summary from LLM."""
        from agent import summarize

        with patch("agent.safe_llm_call", return_value="• AI agents are growing\n• OpenAI launched new tools"):
            result = summarize({"news": "Some long news text here..."})

        assert "summary" in result
        assert "AI agents" in result["summary"]

    def test_summarize_handles_empty_news(self):
        """summarize() should still call LLM even with empty news string."""
        from agent import summarize

        with patch("agent.safe_llm_call", return_value="No news available."):
            result = summarize({"news": ""})

        assert "summary" in result

    def test_summarize_returns_error_on_llm_failure(self):
        """summarize() should catch LLM failure."""
        from agent import summarize

        with patch("agent.safe_llm_call", side_effect=RuntimeError("Model crashed")):
            result = summarize({"news": "Some news"})

        assert "error" in result


class TestWriteNewsletterNode:
    """Tests for the write_newsletter() node function."""

    def test_write_newsletter_returns_newsletter(self):
        """write_newsletter() should return formatted newsletter."""
        from agent import write_newsletter

        with patch("agent.safe_llm_call", return_value="# AI Weekly\n\n## Intro\nThis week in AI..."):
            result = write_newsletter({"summary": "Bullet point news..."})

        assert "newsletter" in result
        assert "AI Weekly" in result["newsletter"]

    def test_write_newsletter_returns_error_on_llm_failure(self):
        """write_newsletter() should catch LLM failure."""
        from agent import write_newsletter

        with patch("agent.safe_llm_call", side_effect=Exception("Timeout")):
            result = write_newsletter({"summary": "Some summary"})

        assert "error" in result


class TestCriticNode:
    """Tests for the critic() node function."""

    def test_critic_returns_improved_newsletter(self):
        """critic() should return improved newsletter content."""
        from agent import critic

        original = "# AI News\n\nBad grammar here. Repetitive repetitive."
        improved  = "# AI News\n\nGrammar is correct. Content is clear."

        with patch("agent.safe_llm_call", return_value=improved):
            result = critic({"newsletter": original})

        assert "newsletter" in result
        assert result["newsletter"] == improved

    def test_critic_overwrites_newsletter_field(self):
        """critic() must update the newsletter field, not create a new one."""
        from agent import critic

        with patch("agent.safe_llm_call", return_value="Improved version."):
            result = critic({"newsletter": "Original version."})

        assert "newsletter" in result
        assert "plan" not in result   # critic should not add unrelated keys

    def test_critic_returns_error_on_llm_failure(self):
        """critic() should catch LLM failure."""
        from agent import critic

        with patch("agent.safe_llm_call", side_effect=Exception("Error")):
            result = critic({"newsletter": "Some newsletter"})

        assert "error" in result


class TestHumanReviewNode:
    """Tests for the human_review() node function."""

    def test_human_review_sets_awaiting_flag(self):
        """human_review() should set awaiting_human=True."""
        from agent import human_review

        result = human_review({"newsletter": "Draft content here."})

        assert result["awaiting_human"] is True

    def test_human_review_preserves_newsletter(self):
        """human_review() should pass newsletter content through unchanged."""
        from agent import human_review

        draft = "# AI Weekly\n\nThis is the draft."
        result = human_review({"newsletter": draft})

        assert result["newsletter"] == draft

    def test_human_review_handles_missing_newsletter(self):
        """human_review() should not crash if newsletter key is missing."""
        from agent import human_review

        result = human_review({})

        assert result["awaiting_human"] is True
        assert result["newsletter"] is None


class TestSendNode:
    """Tests for the send() node function."""

    def test_send_saves_newsletter_successfully(self):
        """send() should call save_newsletter and return result."""
        from agent import send

        with patch("agent.save_newsletter", return_value="Newsletter saved as newsletter.md"):
            result = send({"newsletter": "# AI Weekly\n\nContent here."})

        assert "result" in result
        assert "saved" in result["result"].lower()

    def test_send_returns_error_on_empty_newsletter(self):
        """send() should return error when newsletter is empty string."""
        from agent import send

        result = send({"newsletter": ""})

        assert "error" in result

    def test_send_returns_error_on_missing_newsletter(self):
        """send() should return error when newsletter key is absent."""
        from agent import send

        result = send({})

        assert "error" in result


# ===========================================================
#  SECTION 2 — ROUTER TESTS
# ===========================================================

class TestReviewRouter:
    """Tests for the review_router() conditional edge function."""

    def test_router_returns_human_review_for_human_mode(self):
        """review_router() must return 'human_review' when mode is 'human'."""
        from agent import review_router

        result = review_router({"mode": "human"})
        assert result == "human_review"

    def test_router_returns_send_for_auto_mode(self):
        """review_router() must return 'send' when mode is 'auto'."""
        from agent import review_router

        result = review_router({"mode": "auto"})
        assert result == "send"

    def test_router_returns_send_when_mode_missing(self):
        """review_router() defaults to 'send' when mode key is absent."""
        from agent import review_router

        result = review_router({})
        assert result == "send"

    def test_router_returns_send_for_unknown_mode(self):
        """review_router() defaults to 'send' for any unrecognised mode."""
        from agent import review_router

        result = review_router({"mode": "something_else"})
        assert result == "send"


# ===========================================================
#  SECTION 3 — SAFE LLM CALL TESTS
# ===========================================================

class TestSafeLlmCall:
    """
    Tests for the safe_llm_call() helper.

    Patching strategy:
      ChatOllama is a Pydantic v2 model. Pydantic v2 blocks setattr/delattr
      on undeclared fields, so both patch("agent.llm.invoke") and
      patch.object(instance, "invoke") fail.

      Solution: patch at the CLASS level —
        patch("langchain_ollama.chat_models.ChatOllama.invoke")
      Class-level patching replaces the method on the class itself, which
      Pydantic does not block, and every instance (including agent.llm) picks
      up the mock via normal method resolution order.
    """

    LLM_PATH = "langchain_ollama.chat_models.ChatOllama.invoke"

    def test_returns_stripped_content(self):
        """safe_llm_call() should strip whitespace from LLM response."""
        from agent import safe_llm_call

        mock_response = MagicMock()
        mock_response.content = "  Hello World  "

        with patch(self.LLM_PATH, return_value=mock_response):
            result = safe_llm_call("test prompt")

        assert result == "Hello World"

    def test_raises_on_empty_content(self):
        """safe_llm_call() should raise ValueError on empty response."""
        from agent import safe_llm_call

        mock_response = MagicMock()
        mock_response.content = ""

        with patch(self.LLM_PATH, return_value=mock_response):
            with pytest.raises(ValueError, match="Empty response"):
                safe_llm_call("test prompt")

    def test_raises_on_none_content(self):
        """safe_llm_call() should raise when response.content is None."""
        from agent import safe_llm_call

        mock_response = MagicMock()
        mock_response.content = None

        with patch(self.LLM_PATH, return_value=mock_response):
            with pytest.raises(Exception):
                safe_llm_call("test prompt")

    def test_re_raises_llm_exception(self):
        """safe_llm_call() should propagate LLM exceptions."""
        from agent import safe_llm_call

        with patch(self.LLM_PATH, side_effect=ConnectionError("No connection")):
            with pytest.raises(ConnectionError):
                safe_llm_call("test prompt")


# ===========================================================
#  SECTION 4 — DATABASE TESTS
# ===========================================================

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """
    Creates a fresh temporary SQLite database for each test.
    Monkeypatches database.DB_NAME so tests never touch the real DB.
    """
    db_file = str(tmp_path / "test_newsletters.db")
    monkeypatch.setattr("database.DB_NAME", db_file)
    # Also patch in the module's namespace used at call time
    import database
    database.DB_NAME = db_file
    yield db_file


class TestDatabase:
    """Tests for database.py functions."""

    def test_init_db_creates_table(self, temp_db):
        """init_db() should create the newsletters table."""
        from database import init_db

        init_db()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='newsletters'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None

    def test_init_db_is_idempotent(self, temp_db):
        """init_db() can be called multiple times without error."""
        from database import init_db

        init_db()
        init_db()   # second call should not raise

    def test_save_newsletter_inserts_row(self, temp_db):
        """save_newsletter() should insert a row into the DB."""
        from database import init_db, save_newsletter

        init_db()
        save_newsletter("Weekly AI newsletter", "# AI Weekly\n\nContent here.")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT goal, content FROM newsletters")
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "Weekly AI newsletter"
        assert "AI Weekly" in row[1]

    def test_get_all_newsletters_returns_rows(self, temp_db):
        """get_all_newsletters() should return saved rows newest first."""
        from database import init_db, save_newsletter, get_all_newsletters

        init_db()
        save_newsletter("First goal",  "First content")
        save_newsletter("Second goal", "Second content")

        rows = get_all_newsletters()

        assert len(rows) == 2
        assert rows[0][1] == "Second goal"   # newest first

    def test_get_all_newsletters_returns_empty_list(self, temp_db):
        """get_all_newsletters() should return empty list on fresh DB."""
        from database import init_db, get_all_newsletters

        init_db()
        rows = get_all_newsletters()

        assert rows == []

    def test_get_newsletter_returns_content(self, temp_db):
        """get_newsletter() should return content for a valid id."""
        from database import init_db, save_newsletter, get_newsletter

        init_db()
        save_newsletter("My goal", "My newsletter content.")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM newsletters LIMIT 1")
        newsletter_id = cursor.fetchone()[0]
        conn.close()

        content = get_newsletter(newsletter_id)
        assert content == "My newsletter content."

    def test_get_newsletter_returns_not_found_for_invalid_id(self, temp_db):
        """get_newsletter() should return 'Not found' for a missing id."""
        from database import init_db, get_newsletter

        init_db()
        result = get_newsletter(9999)

        assert result == "Not found"

    def test_multiple_saves_increment_ids(self, temp_db):
        """Each save_newsletter() call should get its own auto-increment id."""
        from database import init_db, save_newsletter, get_all_newsletters

        init_db()
        save_newsletter("Goal 1", "Content 1")
        save_newsletter("Goal 2", "Content 2")
        save_newsletter("Goal 3", "Content 3")

        rows = get_all_newsletters()
        ids = [r[0] for r in rows]

        assert len(set(ids)) == 3  # all ids are unique


# ===========================================================
#  SECTION 5 — TOOLS TESTS
# ===========================================================

class TestTools:
    """Tests for tools.py functions."""

    def test_search_ai_news_formats_results(self):
        """search_ai_news() should format Tavily results into a string."""
        from tools import search_ai_news

        with patch("tools.tavily.search", return_value={
            "results": [
                {"title": "Story 1", "url": "http://a.com", "content": "Content A"},
                {"title": "Story 2", "url": "http://b.com", "content": "Content B"},
            ]
        }):
            result = search_ai_news("AI news")

        assert "Story 1" in result
        assert "Story 2" in result
        assert "http://a.com" in result

    def test_search_ai_news_handles_empty_results(self):
        """search_ai_news() should return empty string when no results."""
        from tools import search_ai_news

        with patch("tools.tavily.search", return_value={"results": []}):
            result = search_ai_news("AI news")

        assert result == ""

    def test_search_ai_news_handles_exception(self):
        """search_ai_news() should return error string on exception."""
        from tools import search_ai_news

        with patch("tools.tavily.search", side_effect=Exception("API error")):
            result = search_ai_news("AI news")

        assert "Error occurred" in result

    def test_save_newsletter_writes_file(self, tmp_path):
        """save_newsletter() should write content to newsletter.md."""
        from tools import save_newsletter

        content = "# AI Weekly\n\nThis is the newsletter."
        filepath = str(tmp_path / "newsletter.md")

        with patch("builtins.open", mock_open()) as mocked_file:
            result = save_newsletter(content)

        mocked_file.assert_called_once_with("newsletter.md", "w", encoding="utf-8")
        assert "saved" in result.lower() or "newsletter" in result.lower()

    def test_save_newsletter_handles_write_error(self):
        """save_newsletter() should return error string on IOError."""
        from tools import save_newsletter

        with patch("builtins.open", side_effect=IOError("Disk full")):
            result = save_newsletter("content")

        assert "Failed" in result


# ===========================================================
#  SECTION 6 — FLASK API TESTS
# ===========================================================

@pytest.fixture
def flask_client(temp_db):
    """
    Creates a Flask test client.
    Patches the agent functions so tests don't actually invoke the LLM.
    """
    import database
    database.DB_NAME = temp_db
    from database import init_db
    init_db()

    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"

    with flask_app.test_client() as client:
        yield client


class TestFlaskRoutes:
    """Tests for all Flask API endpoints."""

    def test_home_returns_200(self, flask_client):
        """GET / should return the index.html page."""
        response = flask_client.get("/")
        assert response.status_code == 200

    def test_run_agent_returns_draft(self, flask_client):
        """POST /run-agent should return draft_newsletter and status."""
        with patch("app.start_newsletter_agent", return_value={
            "thread_id": "test-thread-123",
            "newsletter": "# AI Weekly Draft"
        }):
            response = flask_client.post(
                "/run-agent",
                json={"goal": "Write a newsletter"}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "PAUSED_FOR_HUMAN_REVIEW"
        assert "AI Weekly Draft" in data["draft_newsletter"]

    def test_run_agent_stores_thread_id_in_session(self, flask_client):
        """POST /run-agent should store thread_id in Flask session."""
        with patch("app.start_newsletter_agent", return_value={
            "thread_id": "my-thread-id",
            "newsletter": "Draft"
        }):
            with flask_client.session_transaction() as sess:
                pass   # open session

            flask_client.post("/run-agent", json={"goal": "Test goal"})

            with flask_client.session_transaction() as sess:
                assert sess.get("thread_id") == "my-thread-id"

    def test_run_agent_returns_400_without_goal(self, flask_client):
        """POST /run-agent should return 400 when goal is missing."""
        response = flask_client.post("/run-agent", json={})
        assert response.status_code == 400

    def test_approve_returns_newsletter_sent(self, flask_client):
        """POST /approve should resume agent and return final newsletter."""
        # First, set thread_id in session manually
        with flask_client.session_transaction() as sess:
            sess["thread_id"] = "test-thread-123"
            sess["goal"] = "Write a newsletter"

        with patch("app.resume_newsletter_agent", return_value={
            "newsletter": "# AI Weekly Final"
        }):
            response = flask_client.post("/approve", json={})

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "NEWSLETTER_SENT"
        assert "AI Weekly Final" in data["newsletter"]

    def test_approve_returns_400_without_session(self, flask_client):
        """POST /approve should return 400 when no session exists."""
        response = flask_client.post("/approve", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_approve_clears_session_after_success(self, flask_client):
        """POST /approve should clear thread_id from session after completion."""
        with flask_client.session_transaction() as sess:
            sess["thread_id"] = "test-thread-123"
            sess["goal"] = "Test goal"

        with patch("app.resume_newsletter_agent", return_value={"newsletter": "Final"}):
            flask_client.post("/approve", json={})

        with flask_client.session_transaction() as sess:
            assert "thread_id" not in sess

    def test_get_newsletter_file_returns_content(self, flask_client, tmp_path):
        """GET /get-newsletter-file should return file content."""
        with patch("builtins.open", mock_open(read_data="# AI Weekly\n\nContent.")):
            response = flask_client.get("/get-newsletter-file")

        assert response.status_code == 200
        data = response.get_json()
        assert "AI Weekly" in data["file"]

    def test_get_newsletter_file_returns_fallback(self, flask_client):
        """GET /get-newsletter-file should return fallback when file missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = flask_client.get("/get-newsletter-file")

        assert response.status_code == 200
        data = response.get_json()
        assert "not created yet" in data["file"].lower()

    def test_history_returns_list(self, flask_client, temp_db):
        """GET /history should return list of saved newsletters."""
        import database
        database.DB_NAME = temp_db
        database.save_newsletter("Test goal", "Test content")

        response = flask_client.get("/history")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_history_returns_empty_list_on_fresh_db(self, flask_client):
        """GET /history should return empty list when DB has no newsletters."""
        response = flask_client.get("/history")

        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_open_newsletter_returns_content(self, flask_client, temp_db):
        """GET /newsletter/<id> should return newsletter content by id."""
        import database
        database.DB_NAME = temp_db
        database.save_newsletter("My goal", "My full newsletter content.")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM newsletters LIMIT 1")
        nid = cursor.fetchone()[0]
        conn.close()

        response = flask_client.get(f"/newsletter/{nid}")

        assert response.status_code == 200
        data = response.get_json()
        assert "My full newsletter content." in data["content"]

    def test_open_newsletter_returns_not_found(self, flask_client):
        """GET /newsletter/<id> should return 'Not found' for bad id."""
        response = flask_client.get("/newsletter/9999")

        assert response.status_code == 200
        data = response.get_json()
        assert data["content"] == "Not found"