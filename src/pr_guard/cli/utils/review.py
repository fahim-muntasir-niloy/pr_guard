import os
import json
from rich.panel import Panel
from rich.syntax import Syntax
from pr_guard.agent import init_review_agent
from pr_guard.cli.utils.terminal import console
from pr_guard.cli.utils.env import setup_env
from pr_guard.utils.github_utils import post_github_review, build_github_review_payload


async def run_review(plain: bool = False, github: bool = False):
    console.print("\n")
    console.print(
        "[bold blue]🛡️ PR Guard[/bold blue] - [dim]Advanced AI Code Reviewer[/dim]"
    )
    console.print("\n")
    setup_env()

    agent = await init_review_agent()

    # Determine branch context for the prompt
    base_ref = os.getenv("GITHUB_BASE_REF")
    head_ref = os.getenv("GITHUB_HEAD_REF")

    user_content = "Execute a full code review for the latest git commits. Call the tools needed to understand the scope and diff."
    if base_ref and head_ref:
        user_content = f"Execute a full code review for changes from branch `{head_ref}` into `{base_ref}`. Focus on the diff between `{base_ref}` and `{head_ref}`."

    # Track the result for the final report
    final_structured_res = None

    # Use modern astream with "updates" mode
    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_content,
                }
            ]
        },
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            # 1. Stream the "Steps" (Detect tool calls in the message history)
            if "messages" in update:
                last_msg = update["messages"][-1]
                # Check for tool calls in the message
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        # Format the arguments as a clean string
                        args_json = json.dumps(tc["args"])

                        if not plain:
                            console.print(
                                f"🔧 [bold dim]Calling tool:[/bold dim] [cyan]{tc['name']}[/cyan]"
                            )
                            console.print(f"[dim]   Input: {args_json}[/dim]")
                        else:
                            print(f"Calling tool: {tc['name']} with {args_json}")

            # 2. Capture the structured response if this node provides it
            if "structured_response" in update:
                final_structured_res = update["structured_response"]

    if not final_structured_res:
        return

    # --- REPORT DATA ---
    review_dict = final_structured_res.model_dump()

    # --- GITHUB POSTING ---
    if github:
        repo = os.getenv("GITHUB_REPOSITORY")
        pr_number = os.getenv("GITHUB_PR_NUMBER")
        token = os.getenv("GITHUB_TOKEN")

        if not all([repo, pr_number, token]):
            console.print(
                "[red]Error: GITHUB_REPOSITORY, GITHUB_PR_NUMBER, and GITHUB_TOKEN must be set for --github mode.[/red]"
            )
            return

        review_payload, file_comments = build_github_review_payload(review_dict)
        await post_github_review(
            repo=repo,
            pr_number=int(pr_number),
            token=token,
            review_payload=review_payload,
            file_comments=file_comments,
        )
        console.print("[bold green]✅ Review posted to GitHub![/bold green]")
        return

    # --- BEUTIFUL RICH REPORT ---

    if plain:
        print(json.dumps(review_dict, indent=4))
        return

    event = review_dict.get("event", "COMMENT")
    event_color = (
        "green"
        if event == "APPROVE"
        else "red"
        if event == "REQUEST_CHANGES"
        else "yellow"
    )

    console.print("\n")
    console.print(
        Panel(
            f"[bold {event_color}]{event}[/bold {event_color}]\n\n{review_dict.get('body', '')}",
            title="🏁 Review Result",
            border_style=event_color,
            padding=(1, 2),
        )
    )

    if not review_dict.get("comments"):
        console.print(
            "\n✨ [bold green]No issues found! Your code looks great.[/bold green]"
        )
        return

    console.print(
        f"\n[bold]🔍 Found {len(review_dict['comments'])} items to address:[/bold]\n"
    )

    for comment in review_dict["comments"]:
        severity = comment.get("severity", "nit").lower()
        sev_color = (
            "red"
            if severity == "blocker"
            else "orange3"
            if severity == "major"
            else "yellow"
            if severity == "minor"
            else "dim"
        )

        line_info = f":{comment.get('line', '')}" if comment.get("line") else ""
        info = f"[bold cyan]{comment['path']}{line_info}[/bold cyan]"
        sev_badge = f"[{sev_color}]▐ {severity.upper()}[/{sev_color}]"

        console.print(
            Panel(
                f"{comment['body']}",
                title=f"{sev_badge} {info}",
                title_align="left",
                border_style=sev_color,
                padding=(0, 1),
            )
        )

        if comment.get("suggestion"):
            syntax = Syntax(
                comment["suggestion"],
                os.path.splitext(comment["path"])[1].lstrip(".") or "python",
                theme="monokai",
                line_numbers=True,
            )
            console.print(Panel(syntax, title="💡 Suggested Fix", border_style="green"))
        console.print("")
