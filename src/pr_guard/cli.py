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


async def run_review():
    console.print(Panel("[bold blue]PR Guard[/bold blue] - Initialized", expand=False))
    try:
        setup_env()
        with console.status(
            "[bold green]Agent is working...", spinner="dots"
        ) as status:
            agent = await init_agent()

            async for mode, data in agent.astream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": """Execute a pre-merge code review for the latest git commit.

                                            You must:
                                            - Use git tools to identify changed files
                                            - Review only modified lines and their immediate context
                                            - Produce GitHub-style diff comments
                                            - Assign severity to each issue
                                            - Output only valid `pr_agent_response` JSON

                                            Do not explain your process.
                                            """,
                        }
                    ]
                },
                stream_mode=["messages", "updates"],
            ):
                # 1. Capture incremental "steps" (Tool names and inputs)
                if mode == "messages":
                    status.stop()  # Stop spinner while printing tool info
                    message_chunk, metadata = data
                    if (
                        hasattr(message_chunk, "tool_call_chunks")
                        and message_chunk.tool_call_chunks
                    ):
                        for chunk in message_chunk.tool_call_chunks:
                            if chunk.get("name"):
                                console.print(
                                    f"\n[bold blue]Calling Tool:[/bold blue] {chunk['name']}"
                                )
                            # if chunk.get("args"):
                            #     console.print(f"[dim]{chunk['args']}[/dim]", end="")
                    status.start()  # Resume spinner

                # 2. Capture the final "structured_response"
                if mode == "updates":
                    for node_name, update in data.items():
                        if "structured_response" in update:
                            status.stop()  # Stop spinner for final output
                            console.print(
                                "\n\n[bold green]Final Structured Review:[/bold green]"
                            )
                            console.print("-" * 80)
                            console.print("\n")
                            console.print(update["structured_response"])
                            console.print("\n")
                            console.print("-" * 80)
                            console.print("\n")
                            status.start()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def review():
    """
    Review the current git changes.
    """
    asyncio.run(run_review())


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
