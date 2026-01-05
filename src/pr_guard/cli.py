import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from pr_guard.agent import init_agent
from pr_guard.config import settings
import os

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

            async for mode, data in agent.astream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": """Execute a pre-merge code review for the latest git commits (up to the last merge).

                                            You must:
                                            - Use git tools to identify changed files
                                            - Review modified lines and their immediate context
                                            - Produce GitHub-style diff comments
                                            - Assign severity to each issue
                                            - Never repeat all the changes in the diff; only suggest necessary improvements.
                                            
                                            **Output Requirements:**
                                            - Use `### 📄 File: filename` for each file.
                                            - Use `> [!IMPORTANT]` or `> [!NOTE]` for comments depending on severity.
                                            - ALWAYS wrap diffs in ```diff ... ``` blocks.
                                            - Use bold text for labels like **Severity**, **Issue**, etc.
                                            - Do not include explanatory conversational filler.

                                            Output the review in structured, clean Markdown.""",
                        }
                    ]
                },
                stream_mode=["messages", "updates"],
            ):
                # 1. Capture and print plain text tokens in real-time
                if mode == "messages":
                    message_chunk, metadata = data

                    # Print the text content of the chunk
                    if message_chunk.content:
                        if not plain:
                            status.stop()
                            console.print(message_chunk.content, end="")
                            status.start()
                        else:
                            console.print(message_chunk.content, end="")

                    # Capture incremental tool names
                    if (
                        not plain
                        and hasattr(message_chunk, "tool_call_chunks")
                        and message_chunk.tool_call_chunks
                    ):
                        for chunk in message_chunk.tool_call_chunks:
                            if chunk.get("name"):
                                status.stop()
                                console.print(
                                    f"\n[bold blue]Calling Tool:[/bold blue] {chunk['name']}\n"
                                )
                                status.start()

                # 2. Handle final state updates
                if mode == "updates":
                    for node_name, update in data.items():
                        # If your graph adds the final result to the 'messages' key
                        if "messages" in update:
                            last_msg = update["messages"][-1]
                            # Only act if this is the final AI response (not a tool call)
                            if last_msg.type == "ai" and not last_msg.tool_calls:
                                if not plain:
                                    status.stop()
                                    console.print(
                                        "\n\n[bold green]Review Summary:[/bold green]"
                                    )
                                    console.print("-" * 80)
                                    # Optional: Print final collected content if streaming missed chunks
                                    # console.print(last_msg.content)
                                    console.print("-" * 80)
                                    status.start()

        if not plain:
            with status_manager as status:
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
