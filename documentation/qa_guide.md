# 🧪 PR Guard QA Guide

This guide outlines the scenarios and steps for testing PR Guard.

## 1. Testing CLI Commands
Verify that each command produces the expected output.

| Command | Expected Result |
| :--- | :--- |
| `pr-guard version` | Displays current version (e.g., 0.1.0). |
| `pr-guard status` | Shows git branch and API key configuration status. |
| `pr-guard tree` | Displays a visual tree of the current directory. |
| `pr-guard changed` | Lists files changed against the default branch (master/main). |
| `pr-guard diff` | Shows the colorized git diff of changes. |
| `pr-guard review` | Runs AI review and displays a rich report of suggestions. |

---

## 2. Testing the Interactive Chat
Run `pr-guard chat` and verify:
- [ ] **Real-time Streaming**: Text appears as it's being generated.
- [ ] **Tool Usage**: Ask "What files changed?" and verify the agent calls the `changed` tool.
- [ ] **Context Awareness**: Ask follow-up questions about specific files or diffs.
- [ ] **Commands inside Chat**: Type `help`, `tree`, or `review` inside the chat loop.

---

## 3. GitHub Action Integration
To test the GitHub Action:
1. Run `pr-guard init` in a repository.
2. Verify `.github/workflows/pr_review.yml` is created.
3. Push the changes to a branch.
4. Create a Pull Request on GitHub.
5. Check the "Actions" tab to see the review running.
6. Verify the AI posts comments directly to the PR files.

---

## 4. Edge Cases to Consider
- [ ] **Missing API Key**: Verify the tool provides a clear error message.
- [ ] **Large Diffs**: Test how the agent handles very large changes.
- [ ] **No Git Repo**: Run commands in a non-git directory and check for graceful failure.
- [ ] **GitHub CLI Not Logged In**: Run `pr-guard chat` without `gh auth login`.
