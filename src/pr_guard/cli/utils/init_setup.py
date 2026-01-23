import os
from pr_guard.cli.utils.terminal import console


async def run_init():
    """
    🚀 Initialize GitHub Actions for automated PR review.
    """
    workflow_path = ".github/workflows/pr_review.yml"
    os.makedirs(os.path.dirname(workflow_path), exist_ok=True)

    workflow_content = """name: PR Review Guard

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          python-version: '3.13'


      - name: Run PR Guard Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} # Optional
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }} # Optional
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }} # Optional
          XAI_API_KEY: ${{ secrets.XAI_API_KEY }} # Optional
          LLM_PROVIDER: ${{ secrets.LLM_PROVIDER }} # Optional
          LLM_MODEL: ${{ secrets.LLM_MODEL }} # Optional
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }} # Optional
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_BASE_REF: ${{ github.base_ref }}
          GITHUB_HEAD_REF: ${{ github.head_ref }}
          GITHUB_SHA: ${{ github.event.pull_request.head.sha }}
        run: uvx --from git+https://github.com/fahim-muntasir-niloy/pr_guard.git pr-guard review --github
"""

    if os.path.exists(workflow_path):
        console.print(
            f"[yellow]⚠️ Workflow file already exists at {workflow_path}[/yellow]"
        )
        import typer

        overwrite = typer.confirm(
            "Do you want to overwrite it with the latest template?"
        )
        if not overwrite:
            console.print("[red]✖ Setup aborted.[/red]")
            return

    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(workflow_content)

    console.print("\n[bold green]✨ PR Guard successfully initialized![/bold green]")
    console.print(f"📍 Created: [cyan]{workflow_path}[/cyan]\n")

    console.print("[bold]Next Steps to Activate Your AI Sentinel:[/bold]")
    console.print(
        "  1. [bold blue]Push[/bold blue] this file to your repository's default branch."
    )
    console.print(
        "  2. [bold blue]Add Secrets[/bold blue]: Navigate to [dim]Settings > Secrets and variables > Actions[/dim]."
    )
    console.print(
        "     - Add [bold]OPENAI_API_KEY[/bold] (or your preferred provider's key)."
    )
    console.print(
        "     - (Optional) Add [bold]LLM_PROVIDER[/bold] if not using OpenAI."
    )
    console.print(
        "  3. [bold blue]Watch the Magic[/bold blue]: Every new PR will now be automatically vetted by PR Guard! 🛡️\n"
    )
