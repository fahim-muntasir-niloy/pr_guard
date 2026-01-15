# 🛡️ PR Guard: AI-Powered Pull Request Reviewer

**PR Guard** is an advanced, AI-driven code review agent designed to accelerate your development workflow by providing intelligent, automated feedback directly on your Pull Requests. Built for speed, accuracy, and developer happiness.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start (One-Liner)
Automate your setup—this command installs the **CLI tool**, sets up your environment, and installs the **VS Code Extension**. It even handles **Node.js** and **UV** installation for you if they are missing.

### For Windows (PowerShell):
```powershell
iex (iwr -useb https://raw.githubusercontent.com/fahim-muntasir-niloy/pr_guard/master/install.ps1).Content
```

### For macOS/Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/fahim-muntasir-niloy/pr_guard/master/install.sh | bash
```

---

## ✨ Features

- **🤖 AI-Powered Analysis**: Beyond linting—understands logic, security vulnerabilities, and architectural patterns.
- **💡 Smart Suggestions**: Provides GitHub-style suggested changes that can be applied with a single click.
- **⚡ Seamless Integration**: Works as a CLI tool for local checks or a GitHub Action for team-wide automation.
- **🎨 Rich CLI Output**: Beautiful terminal feedback using the `rich` library.
- **🔒 Secure & Private**: Configurable to your organization's security standards.

---

## 🛠️ Installation

### 1. Requirements
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Recommended for speed)

### 2. Standard Installation
```bash
git clone https://github.com/fahim-muntasir-niloy/pr_guard.git
cd pr_guard
uv sync
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here
```

---

## 📖 Usage

### CLI Commands
Review the latest changes in your current branch:
```bash
pr-guard review
```

For help with the CLI, run:
```bash
pr-guard --help
```

### GitHub Action
The easiest way to set up automated reviews is with the `init` command:
```bash
pr-guard init
```
This will create a `.github/workflows/pr_review.yml` file for you. PR Guard will then automatically review every pull request.

---

## 🚢 Distribution for Your Office

To roll this out to everyone, we've provided several entry points:

1. **The CLI**: Best for local pre-commit reviews.
2. **VS Code Extension**: A premium IDE experience for chat and inline reviews (installed automatically via the one-liner).
3. **The Portal**: Run the internal dashboard to see all PR stats.
4. **The Action**: Enforce code quality across all repositories.

> **Note**: For the best experience, ensure your team has [Node.js](https://nodejs.org/) installed so the VS Code extension can be built and installed during the one-liner setup.

---

## 🏗️ Technical Stack
- **Framework**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **CLI**: [Typer](https://typer.tiangolo.com/) & [Rich](https://rich.readthedocs.io/)
- **API**: [FastAPI](https://fastapi.tiangolo.com/)
- **Build System**: [uv](https://github.com/astral-sh/uv) + [Hatchling](https://hatchling.pypa.io/)

---

*Built with ❤️ by the AI Engineering Team.*
