import asyncio
import os
import json
import sys
from typing import Any, Dict
from pr_guard.agent import init_review_agent
from pr_guard.config import settings
from pr_guard.utils.github_utils import (
    build_github_review_payload,
    get_pr_diff,
    parse_diff_for_valid_lines,
)


def setup_env():
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def generate_github_review_payload() -> Dict[str, Any]:
    """
    Runs the AI agent and prepares GitHub-ready payloads:
    - PR review payload (summary + inline comments with line+side)
    - File-level fallback comments
    """

    setup_env()
    agent = await init_review_agent()

    # Get PR info from environment
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER", "0"))
    token = os.getenv("GITHUB_TOKEN")

    # Fetch and parse diff to get valid line numbers
    valid_lines = None
    if repo and pr_number and token:
        try:
            diff_text = await get_pr_diff(repo, pr_number, token)
            valid_lines = parse_diff_for_valid_lines(diff_text)
            print(f"Parsed valid lines from diff: {valid_lines}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not fetch diff for validation: {e}", file=sys.stderr)

    res = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": """
                    You are a senior code reviewer. Analyze the git diff of this pull request and provide:

1. **Summary Review**: Concise overall assessment (2-3 sentences) for this PR only. Include whether it should be APPROVED, REQUEST_CHANGES, or COMMENT.

2. **Inline Comments**: For each issue:
   - **CRITICAL**: Only comment on lines that are visible in the diff below (lines starting with + or -)
   - For additions/modifications, use side="RIGHT" and the line number from the NEW file (after the change)
   - For deletions, use side="LEFT" and the line number from the OLD file (before the change)
   - Give clear, actionable feedback
   - Include code suggestion if applicable
   - Rate severity: blocker, major, minor, nit

3. **Focus Areas**:
   - Logic correctness and potential bugs
   - Code quality, maintainability, style
   - Performance implications
   - Security vulnerabilities
   - Missing error handling
   - Incomplete or inconsistent implementations

Be specific, constructive, and cite code references. Prioritize critical issues.
                    """,
                }
            ]
        }
    )

    review_data = res["structured_response"]
    review_dict = review_data.model_dump()

    review_payload, file_level_comments = build_github_review_payload(
        review_dict, valid_lines
    )

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
