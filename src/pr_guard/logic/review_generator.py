import asyncio
import os
import json
import sys
from typing import Any, Dict
from pr_guard.agent import init_review_agent
from pr_guard.config import settings


def setup_env():
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = "pr-agent"


from typing import Any, Dict, List, Tuple


def build_github_review_payload(
    review_dict: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Builds:
    1) A PR review payload (summary + inline diff comments)
    2) A list of file-level PR comments (fallback)
    """

    inline_comments: List[Dict[str, Any]] = []
    file_level_comments: List[Dict[str, Any]] = []

    for comment in review_dict.get("comments", []):
        body = comment["body"]

        if comment.get("suggestion"):
            body += f"\n\n```suggestion\n{comment['suggestion']}\n```"

        if comment.get("position") is not None:
            inline_comments.append(
                {
                    "path": comment["path"],
                    "position": comment["position"],
                    "body": body,
                }
            )
        else:
            file_level_comments.append(
                {
                    "path": comment["path"],
                    "body": body,
                }
            )

    review_payload = {
        "event": review_dict["event"],  # APPROVE | REQUEST_CHANGES | COMMENT
        "body": review_dict["body"],
        "comments": inline_comments,  # may be empty, that's OK
    }

    return review_payload, file_level_comments


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
