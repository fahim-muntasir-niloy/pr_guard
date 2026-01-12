# ⚙️ PR Guard Setup Guide

This guide will walk you through setting up PR Guard to be available globally on your system.

## Prerequisites
- **Python**: Version 3.13 or higher.
- **Git**: Installed and configured.
- **GitHub CLI (gh)**: Required for interactive features. [Download here](https://cli.github.com/).
- **OpenAI API Key**: Required for AI analysis.

---

## Quick Start: Global Installation (Recommended)

To make `pr-guard` available globally as a command, run the installer script for your operating system. These scripts will clone the repository, install dependencies, and configure your terminal profile.

### One-Liner (Fastest)

**Windows (PowerShell):**
```powershell
iex (iwr -useb https://raw.githubusercontent.com/fahim-muntasir-niloy/pr_guard/master/install.ps1).Content
```

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/fahim-muntasir-niloy/pr_guard/master/install.sh | bash
```

### Alternative: Local script execution
If you have already cloned the repo:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -File .\install.ps1
```

**Linux / macOS (Bash/Zsh):**
```bash
chmod +x install.sh
./install.sh
```

---

## Environment Configuration
After installation, navigate to the installation directory (default is `~/.pr_guard`) and create/edit the `.env` file:
```bash
cd ~/.pr_guard
# Edit .env
OPENAI_API_KEY=your_openai_key_here
LANGSMITH_API_KEY=your_optional_langsmith_key # Optional for tracing
```

---

## Verifying the Setup
Restart your terminal and run the status command from anywhere:
```bash
pr-guard status
```
You should see "Configured" for the OpenAI API Key and "Git Branch" information.

---

## Manual Installation (Alternative)
If you prefer to manage the installation manually:
1. **Clone**: `git clone https://github.com/fahim-muntasir-niloy/pr_guard.git`
2. **Install**: `uv sync`
3. **Run**: Use `uv run pr-guard` or link the venv binary manually.
