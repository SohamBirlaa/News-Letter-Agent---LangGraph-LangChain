from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_AP_KEY"))


# Tool 1 - search_ai_news(query) -->  [web search]

def search_ai_news(query: str):
    try:
        results = tavily.search(query=query, max_results=7)

        articles = []

        for result in results.get("results", []):
            title = result.get("title", "No Title")
            url = result.get("url", "")
            content = result.get("content", "")

            articles.append(f"{title} - {url}\n{content}")

        return "\n\n".join(articles)

    except Exception as e:
        return f"Error occurred: {e}"


# TOOL 2: Save newsletter (simulate sending email)

def save_newsletter(content: str):
    try:
        with open("newsletter.md", "w", encoding="utf-8") as f:
            f.write(content)
        return "Newsletter saved as a newsletter.md (email situmaled)"
    except Exception as e:
        return f"Failed to save newsletter: {e}"

