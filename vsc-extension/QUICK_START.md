# PR Guard Extension - Quick Start Guide

## Opening the Extension

1. Click the PR Guard icon in the VS Code Activity Bar (left sidebar)
2. The PR Guard sidebar will open with two tabs: **Commands** and **💬 Chat**

## Using Commands

### Quick Actions
- **📝 Start Review**: Analyzes your current PR/changes and provides AI-powered code review
- **📊 Check Status**: Shows your current git status and PR Guard configuration
- **⚙️ Run Init**: Initializes GitHub Actions workflow for automated PR reviews

### Viewing Output
- All command output appears in the "Output" section below the buttons
- ANSI colors from the CLI are preserved (green for success, red for errors, cyan for info, etc.)
- Click **Clear** to reset the output area

## Using Interactive Chat

### Starting a Chat Session
1. Click the **💬 Chat** tab
2. Click **Start Chat** button
3. Wait for the chat session to initialize (you'll see the welcome message)

### Chatting with PR Guard
1. Type your question or command in the input field at the bottom
2. Press **Enter** or click **Send**
3. Your message appears on the right (blue bubble)
4. The AI response streams in on the left with proper formatting

### Available Chat Commands
You can use any of these commands in the chat:
- `help` - Show available commands
- `review` - Run a code review
- `status` - Check status
- `tree [path]` - Show directory tree
- `changed [base] [head]` - List changed files
- `diff [base] [head]` - Show git diff
- `log [limit]` - Show git log
- `cat <file>` - Read file content
- `version` - Show PR Guard version
- Or just ask questions naturally!

### Stopping Chat
- Click the **Stop** button to end the chat session
- The chat process will terminate gracefully

## Tips & Tricks

### Rich Output Rendering
- The extension automatically converts ANSI escape codes to HTML
- Colors, bold text, and other formatting from Python Rich library are preserved
- This works in both the Commands output and Chat messages

### Keyboard Shortcuts
- **Enter** in chat input: Send message
- **Ctrl+C** in chat: Stop current operation (if supported by CLI)

### Troubleshooting

**Chat not starting?**
- Ensure `pr-guard` is installed and accessible from your PATH
- Check the extension settings: `prGuard.executablePath`
- Try running `pr-guard --version` in your terminal

**Output not showing colors?**
- This is expected for Commands tab (colors disabled for non-interactive mode)
- Chat tab should show full ANSI color support
- If colors aren't showing in chat, check your VS Code theme

**Extension not finding pr-guard?**
- Go to Settings → Extensions → PR Guard
- Set `prGuard.executablePath` to your pr-guard installation path
- Example: `C:\Users\YourName\.pr_guard\.venv\Scripts\pr-guard.exe`

## Configuration

### Extension Settings
Access via: File → Preferences → Settings → Extensions → PR Guard

- **prGuard.executablePath**: Custom path to pr-guard executable (optional)
  - Leave empty to use system PATH
  - Set if pr-guard is installed in a non-standard location

## Next Steps

- Try asking the chat: "What files changed in my last commit?"
- Run a review to see AI-powered code analysis
- Set up GitHub Actions with the Init command for automated PR reviews

---

For more information, visit: https://github.com/fahim-muntasir-niloy/pr_guard
