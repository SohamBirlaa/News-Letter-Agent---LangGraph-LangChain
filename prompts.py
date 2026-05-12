PLAN_PROMPT = """
You are an expert AI workflow planner.

Goal:
{goal}

Create a concise step-by-step execution plan.

Rules:
- Keep steps short and actionable
- Use numbered points
- Avoid unnecessary explanation
- Focus on practical execution
- Maximum 7 steps
"""


SUMMARIZE_PROMPT = """
You are an AI news analyst.

Task:
Summarize the following AI news into 5-7 concise bullet points.

Requirements:
- Highlight only the most important updates
- Keep each point under 25 words
- Use simple and engaging language
- Avoid repetition
- Focus on trends, launches, funding, research, and AI agents

News:
{news}
"""


NEWSLETTER_PROMPT = """
You are a professional tech newsletter writer.

Create a polished weekly AI Agents newsletter in Markdown format.

Structure:
# Title

## Intro
Short engaging introduction (2-3 lines)

## Top AI Stories
Use bullet points with short explanations

## Why It Matters
Brief insight on industry impact

## Closing
Friendly closing statement

Requirements:
- Make it visually clean
- Use markdown formatting properly
- Keep tone modern and engaging
- Avoid hype or fake claims
- Keep total length under 700 words

Content:
{summary}
"""


CRITIC_PROMPT = """
You are an expert editor.

Review and improve the following newsletter.

Focus on:
- Clarity
- Readability
- Formatting
- Grammar
- Engagement
- Flow between sections

Rules:
- Preserve original meaning
- Improve markdown structure
- Remove repetitive lines
- Make transitions smoother
- Return ONLY the improved newsletter

Newsletter:
{newsletter}
"""

