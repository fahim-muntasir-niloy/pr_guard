import httpx
import sys
from typing import Any, Dict, List, Tuple


async def post_github_review(
    repo: str,
    pr_number: int,
    token: str,
    review_payload: Dict[str, Any],
    file_comments: List[Dict[str, Any]],
):
    """
    Posts a review to a GitHub PR.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    base_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    async with httpx.AsyncClient() as client:
        # 1. Post the main review (summary + inline comments)
        print(f" Posting PR review to {repo} #{pr_number}...")
        res = await client.post(
            f"{base_url}/reviews", headers=headers, json=review_payload
        )
        if res.status_code not in (200, 201):
            print(
                f"Error posting review: {res.status_code} - {res.text}", file=sys.stderr
            )
        else:
            print("Main review posted successfully.")

        # 2. Post file-level comments (if any)
        if file_comments:
            print(f" Posting {len(file_comments)} file-level comments...")
            for comment in file_comments:
                comment_body = (
                    f"**File: {comment.get('path')}**\n\n{comment.get('body')}"
                )
                res = await client.post(
                    f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
                    headers=headers,
                    json={"body": comment_body},
                )
                if res.status_code not in (200, 201):
                    print(
                        f"Error posting comment for {comment.get('path')}: {res.status_code} - {res.text}",
                        file=sys.stderr,
                    )


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
