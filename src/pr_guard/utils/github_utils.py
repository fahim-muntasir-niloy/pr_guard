import httpx
import sys
from typing import Any, Dict, List, Tuple, Set
import os
import re


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


def parse_diff_for_valid_lines(diff_text: str) -> Dict[str, Set[int]]:
    """
    Parse a unified diff and return valid line numbers per file.
    Returns: {"path/to/file.py": {10, 11, 12, ...}}
    """
    valid_lines = {}
    current_file = None
    current_line = 0

    for line in diff_text.split("\n"):
        # New file marker
        if line.startswith("+++ b/"):
            current_file = line[6:]  # Remove '+++ b/'
            valid_lines[current_file] = set()
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                current_line = int(match.group(1))
            continue

        if current_file is None:
            continue

        # Track line numbers for additions and context
        if line.startswith("+") and not line.startswith("+++"):
            valid_lines[current_file].add(current_line)
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            # Deletions don't increment new file line numbers
            pass
        elif not line.startswith("\\"):  # Context line (not "\ No newline")
            valid_lines[current_file].add(current_line)
            current_line += 1

    return valid_lines


async def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """Fetch the PR diff from GitHub."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.diff",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers
        )
        resp.raise_for_status()
        return resp.text


def build_github_review_payload(
    review_dict: Dict[str, Any],
    valid_lines: Dict[str, Set[int]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Builds:
    1) A PR review payload (summary + inline diff comments)
    2) A list of file-level PR comments (fallback for comments without line info)

    If valid_lines is provided, filters out comments on lines not in the diff.
    """

    inline_comments: List[Dict[str, Any]] = []
    file_level_comments: List[Dict[str, Any]] = []

    for comment in review_dict.get("comments", []):
        body = comment["body"]

        if comment.get("suggestion"):
            body += f"\n\n```suggestion\n{comment['suggestion']}\n```"

        path = comment["path"]
        line = comment.get("line")

        # Check if line is valid (in the diff)
        if line is not None:
            is_valid = valid_lines is None or (
                path in valid_lines and line in valid_lines[path]
            )

            if is_valid:
                inline_comments.append(
                    {
                        "path": path,
                        "line": line,
                        "side": comment.get("side", "RIGHT"),
                        "body": body,
                    }
                )
            else:
                # Convert to file-level comment if line not in diff
                file_level_comments.append(
                    {
                        "path": path,
                        "body": f"**Line {line}**\n\n{body}",
                    }
                )
        else:
            file_level_comments.append(
                {
                    "path": path,
                    "body": body,
                }
            )

    review_payload = {
        "event": review_dict["event"],
        "body": review_dict["body"],
        "comments": inline_comments,
        "commit_id": os.getenv("GITHUB_SHA"),
    }

    return review_payload, file_level_comments
