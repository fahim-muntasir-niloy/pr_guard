# 🛡️ PR Guard Handoff Deck

## Project Overview
PR Guard is an AI-powered code review assistant that integrates with GitHub and local development environments. It helps developers maintain code quality by providing automated reviews, suggestions, and an interactive chat interface.

---

## Core Features
- 🤖 **AI Code Review**: Automated analysis of PR changes using LLMs.
- 💬 **Interactive Chat**: A CLI-based chat assistant for codebase exploration and review discussions.
- 📁 **Repository Tools**: Built-in tools for viewing file trees, diffs, and commit logs.
- 🚀 **GitHub Integration**: Automated reviews via GitHub Actions and posting comments directly to PRs.

---

## Technology Stack
- **Language**: Python 3.13+
- **Agent Framework**: LangChain / LangGraph
- **CLI Framework**: Typer / Rich
- **Git Integration**: GitHub CLI (gh)
- **Dependency Management**: UV

---

## Project Structure
- `src/pr_guard/cli/`: CLI entry points and loop logic.
- `src/pr_guard/agent.py`: LangGraph agent definitions.
- `src/pr_guard/tools.py`: Custom tools for file system and git operations.
- `src/pr_guard/model.py`: LLM configuration.
- `src/pr_guard/schema/`: Pydantic models for structured output.

---

## How it Works
1. **User Input**: CLI command (e.g., `pr-guard review`) or chat message.
2. **Agent Initialization**: LangGraph agent loaded with specific prompts and tools.
3. **Tool Execution**: Agent calls tools to fetch git diffs, file content, etc.
4. **AI Analysis**: LLM processes the gathered data and generates a review.
5. **Output**: Results displayed in a rich CLI format or posted to GitHub.
