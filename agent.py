
import os
import logging
from typing import TypedDict, Optional, Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
#from langchain_ollama import ChatOllama

from tools import search_ai_news, save_newsletter
from prompts import (
    PLAN_PROMPT,
    SUMMARIZE_PROMPT,
    NEWSLETTER_PROMPT,
    CRITIC_PROMPT,
)

from langgraph.checkpoint.memory import MemorySaver
import uuid

from langchain_groq import ChatGroq

""" ---> no need of google api as we are using local ollama llama 3.2 llm
#=========================
# Load environment variables
#=========================

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in .env file")
"""

#=====================
# Logging Configuration
#=====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


#===================
# LLM Initialization
#===================
""" 
llm = ChatOllama(
    model="llama3.2",
    temperature=0.3,
)
""" 
## -----> now i am using grok api
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in .env file")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=GROQ_API_KEY,
)


#============
# Agent State
#============

class AgentState(TypedDict, total=False):
    goal: str
    mode: str

    plan: str
    news: str
    summary: str
    newsletter: str

    # HITL Fields
    awaiting_human: bool
    approved: bool
    human_feedback: str

    error: Optional[str]


#==============
# Helper Function
#==============

def safe_llm_call(prompt: str) -> str:
    try:
        response = llm.invoke(prompt)

        if not response or not response.content:
            raise ValueError("Empty response from LLM")

        return response.content.strip()

    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        raise


#===============
# Step 1: Planner
#===============

def planner(state: AgentState):
    logger.info("Running Planner Node")

    try:
        goal = state.get("goal", "").strip()

        if not goal:
            raise ValueError("Goal is required")

        plan = safe_llm_call(PLAN_PROMPT.format(goal=goal))
        return {"plan": plan}

    except Exception as e:
        logger.error(f"Planner failed: {e}")
        return {"error": str(e)}


#===============
# Step 2: Research
#===============

def research(state: AgentState):
    logger.info("Running Research Node")

    try:
        news = search_ai_news("latest AI agents news 2025")

        if not news:
            raise ValueError("No news found")

        return {"news": news}

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return {"error": str(e)}


#===============
# Step 3: Summarize
#===============

def summarize(state: AgentState):
    logger.info("Running Summarization Node")

    try:
        news = state.get("news", "")
        summary = safe_llm_call(SUMMARIZE_PROMPT.format(news=news))
        return {"summary": summary}

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return {"error": str(e)}


#===============
# Step 4: Write Newsletter
#===============

def write_newsletter(state: AgentState):
    logger.info("Running Newsletter Writer Node")

    try:
        summary = state.get("summary", "")
        newsletter = safe_llm_call(NEWSLETTER_PROMPT.format(summary=summary))
        return {"newsletter": newsletter}

    except Exception as e:
        logger.error(f"Newsletter writing failed: {e}")
        return {"error": str(e)}


#===============
# Step 5: Critic
#===============

def critic(state: AgentState):
    logger.info("Running Critic Node")

    try:
        newsletter = state.get("newsletter", "")
        improved_newsletter = safe_llm_call(CRITIC_PROMPT.format(newsletter=newsletter))
        return {"newsletter": improved_newsletter}

    except Exception as e:
        logger.error(f"Critic failed: {e}")
        return {"error": str(e)}


#===============
# Human Review Node
#===============

def human_review(state: AgentState):
    logger.info("Human review required — pausing graph")
    return {
        "awaiting_human": True,
        "newsletter": state.get("newsletter")
    }


#===============
# Step 6: Send
#===============

def send(state: AgentState):
    logger.info("Running Send Node")

    try:
        newsletter = state.get("newsletter", "")

        if not newsletter:
            raise ValueError("Newsletter content is empty")

        result = save_newsletter(newsletter)
        return {"result": result}

    except Exception as e:
        logger.error(f"Send failed: {e}")
        return {"error": str(e)}


#===============
# Router
#===============

def review_router(state: AgentState) -> Literal["human_review", "send"]:
    if state.get("mode") == "human":
        return "human_review"
    return "send"


#===============
# Build Graph
#===============

memory = MemorySaver()

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner)
    graph.add_node("research", research)
    graph.add_node("summarize", summarize)
    graph.add_node("write", write_newsletter)
    graph.add_node("critic", critic)
    graph.add_node("human_review", human_review)
    graph.add_node("send", send)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "research")
    graph.add_edge("research", "summarize")
    graph.add_edge("summarize", "write")
    graph.add_edge("write", "critic")

    graph.add_conditional_edges(
        "critic",
        review_router,
        {
            "human_review": "human_review",
            "send": "send"
        }
    )

    graph.add_edge("human_review", "send")
    graph.add_edge("send", END)

    compiled = graph.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]
    )

    return compiled


app = build_graph()


#==============================================
# PUBLIC FUNCTIONS
#==============================================

def start_newsletter_agent(goal: str) -> dict:
    """
    Run the agent in human mode.
    Pauses before human_review and returns the draft + thread_id.
    """
    logger.info("Starting Newsletter Agent (human mode)")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(
        {
            "goal": goal,
            "mode": "human",
            "approved": False
        },
        config=config
    )

    return {
        "thread_id": thread_id,
        "newsletter": result.get("newsletter", "")
    }


def resume_newsletter_agent(thread_id: str) -> dict:
    """
    Resume the paused graph on the same thread after human approval.
    Passes None as input since state is already stored in memory.
    """
    logger.info(f"Resuming Newsletter Agent — thread: {thread_id}")

    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(None, config=config)

    return result


if __name__ == "__main__":
    # Test full flow
    started = start_newsletter_agent("Create a weekly AI Agents newsletter")
    print("DRAFT:\n", started["newsletter"])

    print("\nResuming with approval...\n")
    final = resume_newsletter_agent(started["thread_id"])
    print("FINAL:\n", final)