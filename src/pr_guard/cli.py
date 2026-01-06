import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from pr_guard.agent import init_agent
from pr_guard.config import settings
import os
import json

app = typer.Typer(
    name="pr-guard",
    help="AI-powered Pull Request Reviewer and Guard.",
    add_completion=False,
)
console = Console()


def setup_env():
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def run_review(plain: bool = False):
    if not plain:
        console.print(
            Panel("[bold blue]PR Guard[/bold blue] - Initialized", expand=False)
        )
    try:
        setup_env()

        # Use a context manager for status if not in plain mode
        status_manager = (
            console.status("[bold green]Agent is working...", spinner="dots")
            if not plain
            else asyncio.Event()  # Dummy object for plain mode
        )

        async def _run():
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
            review_data = review_data.model_dump()
            for comment in review_data.get("comments", []):
                body = comment["body"]
                if comment.get("suggestion"):
                    # Wrap suggestion in ```suggestion ... ``` as GitHub expects
                    body += f"\n\n```suggestion\n{comment['suggestion']}\n```"

                formatted_comments.append(
                    {
                        "path": comment["path"],
line = comment.get("line")
if line is None:
    continue
formatted_comments.append(
    {
        "path": comment["path"],
        "line": line,
        "side": comment.get("side", "RIGHT"),
        "body": body,
    }
)
                        "side": comment.get("side", "RIGHT"),
                        "body": body,
                    }
                )

            github_review = {
                "event": review_data["event"],
                "body": review_data["body"],
                "comments": formatted_comments,
            }

            print(json.dumps(github_review, indent=4))

        if not plain:
            with status_manager:
                await _run()
        else:
            await _run()

    except Exception as e:
        if not plain:
            console.print(f"\n[red]Error:[/red] {e}")
        else:
            print(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def review(
    plain: bool = typer.Option(
        False, "--plain", help="Output plain Markdown without styling."
    ),
):
    """
    Review the current git changes.
    """
    asyncio.run(run_review(plain=plain))


async def run_comment():
    setup_env()
    agent = await init_agent()
    res = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Execute a pre-merge code review for the latest git commits (up to the last merge).\n\n"
                        "You must:\n"
                        "- Use git tools to identify changed files\n"
                        "- Review modified lines and their immediate context\n"
                        "- Produce GitHub-style diff comments\n"
                        "- Assign severity to each issue\n"
                        "- Never repeat all the changes in the diff; only suggest necessary improvements.\n\n"
                        "**Output Requirements:**\n"
                        "- Use `### 📄 File: filename` for each file.\n"
                        "- Use `> [!IMPORTANT]` or `> [!NOTE]` for comments depending on severity.\n"
                        "- ALWAYS wrap diffs in ```diff ... ``` blocks.\n"
                        "- Use bold text for labels like **Severity**, **Issue**, etc.\n"
                        "- Do not include explanatory conversational filler.\n\n"
                        "Output the review in structured, clean Markdown."
                    ),
                }
            ]
        }
    )
    return res


@app.command()
def comment():
    """
    Comment on the current git changes in github.
    """
    res = asyncio.run(run_comment())
    console.print(res["messages"][-1].content)


@app.command()
def version():
    """
    Show the version of PR Guard.
    """
    import importlib.metadata

    try:
        ver = importlib.metadata.version("pr-guard")
        console.print(f"PR Guard version: [bold cyan]{ver}[/bold cyan]")
    except importlib.metadata.PackageNotFoundError:
        console.print("PR Guard version: [bold cyan]0.1.0[/bold cyan] (local)")


if __name__ == "__main__":
    app()
