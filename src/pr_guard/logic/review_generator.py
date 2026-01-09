import asyncio
import os
import json
import sys
from typing import Any, Dict
from pr_guard.agent import init_review_agent
from pr_guard.config import settings
from pr_guard.utils.github_utils import build_github_review_payload


def setup_env():
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def generate_github_review_payload() -> Dict[str, Any]:
    """
    Runs the AI agent and prepares GitHub-ready payloads:
    - PR review payload (summary + inline comments)
    - File-level fallback comments
    """

    setup_env()
    agent = await init_review_agent()

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

    review_data = res["structured_response"]
    review_dict = review_data.model_dump()

    review_payload, file_level_comments = build_github_review_payload(review_dict)

    return {
        "review": review_payload,
        "file_comments": file_level_comments,
    }


async def main():
    try:
        payload = await generate_github_review_payload()

        # stdout MUST be pure JSON (GitHub Action contract)
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")

    except Exception as e:
        # stderr for logs so JSON is not corrupted
        print(f"[pr-guard] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
