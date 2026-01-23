import uuid
import json
from rich.live import Live
from rich.markdown import Markdown
from langchain.messages import AIMessageChunk
from pr_guard.agent import one_click_pr_agent
from pr_guard.cli.utils.terminal import console
from pr_guard.cli.utils.env import setup_env
from pr_guard.cli.utils.chat import token_processor


async def run_one_click_pr(
    user_instructions: str, base: str = "master", head: str = "HEAD"
):
    """
    Create a one-click pull request.
    """
    setup_env()

    agent = await one_click_pr_agent()

    message = f"""
    You are an automated GitHub Pull Request generator.

    Your task is to create a new pull request based ONLY on the provided commit history.

    Rules:
    - Take into account the user instructions provided -> {user_instructions}.
    - First take pull in both {base} and {head} branches
    - Summarize only the commits included in this pull request.
    - Ignore any commits that happened before the last merge commit.
    - Do not invent changes or features.
    - Be concise and technical.
    - Use clear bullet points for changes.
    - If no meaningful changes exist, say so explicitly.

    Output format:
    Title: <short, descriptive PR title>
    PR url: <url to the pull request>

    PR description:
    - <bullet point summary of changes>

    Breaking changes:
    - <bullet point summary of breaking changes>

    Do not include explanations, disclaimers, or markdown outside this format.
    """
    full_response = ""
    with Live(
        "[bold cyan]Creating PR...",
        console=console,
        refresh_per_second=5,
        vertical_overflow="visible",
    ) as live:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode=["updates", "messages"],
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        ):
            stream_mode_name, data = chunk

            if stream_mode_name == "updates":
                for step_name, step_data in data.items():
                    if step_data is None:
                        continue
                    messages = step_data.get("messages", [])
                    if messages:
                        latest_msg = messages[-1]
                        if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
                            for tool_call in latest_msg.tool_calls:
                                args_json = json.dumps(tool_call.get("args", {}))
                                console.print(
                                    f"🔧 [bold dim]Executing tool:[/bold dim] [cyan]{tool_call.get('name')}[/cyan]"
                                )
                                console.print(f"[dim]   Input: {args_json}[/dim]")

            elif stream_mode_name == "messages":
                msg, metadata = data
                if isinstance(msg, AIMessageChunk) and msg.content:
                    token = token_processor(msg.content)
                    if token:
                        full_response += token
                        live.update(Markdown(full_response))

    console.print("\n")
