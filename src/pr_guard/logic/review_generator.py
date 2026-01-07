import asyncio
import os
import json
import sys
from typing import Any, Dict
from pr_guard.agent import init_agent
from pr_guard.config import settings


def setup_env():
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def generate_github_review_payload() -> Dict[str, Any]:
    """Runs the AI agent and formats the response for the GitHub Reviews API."""
    sys.stderr.write("Generating review payload...\n")
    setup_env()
    agent = await init_agent()
    res = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Execute a pre-merge code review for the latest git commits.",
                }
            ]
        }
    )

    # Extract the structured response
    review_data = res["structured_response"]

    # Map comments to include suggestions if present
    formatted_comments = []
    review_dict = review_data.model_dump()
    for comment in review_dict.get("comments", []):
        body = comment["body"]
        if comment.get("suggestion"):
            # Wrap suggestion in ```suggestion ... ``` as GitHub expects
            body += f"\n\n```suggestion\n{comment['suggestion']}\n```"

        c_entry = {
            "path": comment["path"],
            "side": comment.get("side", "RIGHT"),
            "body": body,
        }
        if comment.get("line"):
            c_entry["line"] = comment["line"]

        formatted_comments.append(c_entry)

    github_review = {
        "event": review_dict["event"],
        "body": review_dict["body"],
        "comments": formatted_comments,
    }
    return github_review


async def main():
    payload = await generate_github_review_payload()
    print(json.dumps(payload, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
