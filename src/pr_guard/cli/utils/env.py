import os
import dotenv
from pr_guard.config import settings
from pr_guard.cli.utils.terminal import console
from rich.panel import Panel


def setup_env(strict: bool = True):
    """Setup environment variables and check for required API keys."""
    # Check key based on provider
    provider = settings.LLM_PROVIDER.lower().strip() if settings.LLM_PROVIDER else "xai"

    # If explicitly set provider is invalid/empty, try to guess from available keys
    if not provider:
        if settings.XAI_API_KEY:
            provider = "xai"
        elif settings.OPENAI_API_KEY:
            provider = "openai"
        elif settings.ANTHROPIC_API_KEY:
            provider = "anthropic"
        elif settings.GOOGLE_API_KEY:
            provider = "google_genai"
        else:
            provider = "openai"  # Ultimate fallback for error message

    has_key = False

    if provider == "openai" and settings.OPENAI_API_KEY:
        has_key = True
    elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        has_key = True
    elif provider == "google_genai" and settings.GOOGLE_API_KEY:
        has_key = True
    elif provider == "xai" and settings.XAI_API_KEY:
        has_key = True

    if not has_key and strict:
        is_ci = os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true"
        console.print("\n[bold red]❌ Environment Error:[/bold red]")
        if is_ci:
            console.print(
                f"[yellow]{provider.upper()}_API_KEY is missing. Please ensure you have added it to your GitHub Repository Secrets.[/yellow]\n"
            )
        else:
            console.print(
                f"[yellow]{provider.upper()}_API_KEY is missing. Please create a .env file or run 'pr-guard config' to set your keys.[/yellow]\n"
            )
        import sys

        sys.exit(1)

    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = "pr-agent"


def update_env_file(key: str, value: str):
    """
    Updates a key in the global .env file (~/.pr_guard/.env).
    """
    env_path = os.path.join(os.path.expanduser("~"), ".pr_guard", ".env")

    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("")

    dotenv.set_key(env_path, key, value)


async def run_config():
    """
    ⚙️ Interactive configuration for PR Guard.
    """
    console.print(
        Panel("⚙️ [bold white]PR Guard Configuration[/bold white]", border_style="blue")
    )

    # 1. Choose Provider
    providers = ["openai", "anthropic", "google_genai", "xai"]
    console.print("\n[bold cyan]Supported Providers:[/bold cyan]")
    for i, p in enumerate(providers, 1):
        console.print(f" {i}. [green]{p}[/green]")

    provider_choice = (
        console.input(
            f"\n[bold green]Select LLM Provider[/bold green] (enter 1-4 or name, current: [cyan]{settings.LLM_PROVIDER}[/cyan]): "
        )
        .strip()
        .lower()
    )

    if not provider_choice:
        provider = settings.LLM_PROVIDER
    elif provider_choice in ["1", "openai"]:
        provider = "openai"
    elif provider_choice in ["2", "anthropic"]:
        provider = "anthropic"
    elif provider_choice in ["3", "google_genai"]:
        provider = "google_genai"
    elif provider_choice in ["4", "xai"]:
        provider = "xai"
    else:
        console.print(
            f"[red]Error: Invalid choice. Using current: '{settings.LLM_PROVIDER}'.[/red]"
        )
        provider = settings.LLM_PROVIDER

    # 2. Choose Model
    default_models = {
        "openai": "gpt-5",
        "anthropic": "claude-4-5-sonnet-latest",
        "google_genai": "gemini-3-flash",
        "xai": "grok-4-1-fast-reasoning",
    }
    suggested_model = default_models.get(provider, "gpt-5")

    model = console.input(
        f"[bold green]Enter LLM Model[/bold green] (suggested for {provider}: [cyan]{suggested_model}[/cyan], current: [cyan]{settings.LLM_MODEL}[/cyan]): "
    ).strip()
    if not model:
        model = (
            settings.LLM_MODEL if provider == settings.LLM_PROVIDER else suggested_model
        )

    # 3. API Keys
    key_mapping = {
        "openai": ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
        "anthropic": ("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY),
        "google_genai": ("GOOGLE_API_KEY", settings.GOOGLE_API_KEY),
        "xai": ("XAI_API_KEY", settings.XAI_API_KEY),
    }

    key_name, current_key = key_mapping.get(
        provider, ("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    )

    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if current_key else "None"
    api_key = console.input(
        f"[bold green]Enter {key_name}[/bold green] (current: [cyan]{masked_key}[/cyan]): "
    ).strip()

    # Save settings
    update_env_file("LLM_PROVIDER", provider)
    update_env_file("LLM_MODEL", model)
    if api_key:
        update_env_file(key_name, api_key)

    console.print("\n[bold green]✅ Configuration saved![/bold green]")
    console.print(f"Provider: [cyan]{provider}[/cyan]")
    console.print(f"Model: [cyan]{model}[/cyan]")
    console.print("[dim]Changes will take effect on next restart.[/dim]\n")
