# PR Guard VS Code Extension

A powerful VS Code extension that brings AI-powered code review capabilities directly into your editor. Integrates seamlessly with the PR Guard CLI tool.

## Features

### 🎯 Interactive Chat
- Chat directly with the PR Guard AI assistant in the sidebar
- Ask questions about your codebase
- Get instant code analysis and suggestions
- Full ANSI color support for rich terminal output

### 📝 Quick Commands
- **Start Review**: Run AI-powered code reviews on your changes
- **Check Status**: View git status and PR Guard configuration
- **Run Init**: Set up GitHub Actions for automated PR reviews

### 🎨 Rich Output Rendering
- Proper ANSI escape code rendering
- Preserves colors, bold, italic, and other formatting from Python Rich library
- Clean, modern UI that matches VS Code's theme

## Installation

### Prerequisites
1. Install PR Guard CLI:
   ```bash
   pip install pr-guard
   # or
   uvx pr-guard
   ```

2. Configure your API keys (if needed):
   ```bash
   pr-guard init
   ```

### Installing the Extension

#### From Source (Development)
1. Clone the repository
2. Navigate to the extension directory:
   ```bash
   cd vsc-extension
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Compile the extension:
   ```bash
   npm run compile
   ```
5. Press F5 in VS Code to launch Extension Development Host

#### From VSIX (Coming Soon)
- Download the `.vsix` file from releases
- Install via: Extensions → ... → Install from VSIX

## Usage

See [QUICK_START.md](./QUICK_START.md) for detailed usage instructions.

### Quick Start

1. **Open PR Guard Sidebar**
   - Click the PR Guard icon in the Activity Bar

2. **Run a Review**
   - Click "📝 Start Review" in the Commands tab
   - View the AI-generated code review in the output area

3. **Chat with AI**
   - Switch to the "💬 Chat" tab
   - Click "Start Chat"
   - Ask questions like: "What files changed in my last commit?"

## Configuration

### Extension Settings

- `prGuard.executablePath`: Path to pr-guard executable
  - Default: Uses system PATH
  - Set this if pr-guard is installed in a custom location

### Example Configuration

```json
{
  "prGuard.executablePath": "C:\\Users\\YourName\\.pr_guard\\.venv\\Scripts\\pr-guard.exe"
}
```

## Development

### Project Structure

```
vsc-extension/
├── src/
│   ├── extension.ts          # Main extension entry point
│   ├── SidebarProvider.ts    # Sidebar webview provider
│   └── webviewContent.ts     # Review panel content
├── out/                      # Compiled JavaScript
├── package.json              # Extension manifest
└── tsconfig.json            # TypeScript configuration
```

### Building

```bash
npm run compile    # Compile TypeScript
npm run watch      # Watch mode for development
```

### Debugging

1. Open the extension folder in VS Code
2. Press F5 to launch Extension Development Host
3. Set breakpoints in TypeScript files
4. Test the extension in the new window

## Architecture

### Chat Integration

The chat feature uses a persistent process model:

```
VS Code Extension
    ↓
SidebarProvider (TypeScript)
    ↓ spawn
pr-guard chat (Python CLI)
    ↓ stdout/stderr
ANSI Output → HTML Conversion
    ↓
Webview Display
```

### ANSI Rendering

The extension includes a comprehensive ANSI-to-HTML converter that:
- Parses ANSI escape sequences (colors, styles)
- Converts to HTML with CSS classes
- Preserves formatting from Python Rich library
- Removes non-visual escape codes (cursor movement, etc.)

## Technical Details

### Supported ANSI Codes

- **Colors**: 30-37 (standard), 90-97 (bright)
- **Styles**: Bold (1), Dim (2), Italic (3), Underline (4)
- **Reset**: 0 (reset all styles)
- **Combined**: Multiple codes in one sequence (e.g., `\x1b[1;32m`)

### Message Types

- **User**: Messages sent by the user (blue, right-aligned)
- **Assistant**: Responses from PR Guard AI (gray, left-aligned)
- **System**: Status messages (blue, centered)

## Troubleshooting

### Common Issues

**Extension can't find pr-guard**
- Ensure pr-guard is in your PATH
- Or set `prGuard.executablePath` in settings

**Chat not starting**
- Check pr-guard is installed: `pr-guard --version`
- Verify workspace folder is open
- Check extension logs: View → Output → PR Guard

**Colors not rendering**
- Ensure you're using the Chat tab (Commands tab has colors disabled)
- Check your VS Code theme supports the color classes

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Changelog

### v0.0.1 (Current)
- ✅ Interactive chat in sidebar
- ✅ ANSI-to-HTML rendering
- ✅ Quick command buttons
- ✅ Tabbed interface (Commands/Chat)
- ✅ Real-time message streaming

## License

Same as PR Guard main project

## Links

- [PR Guard Repository](https://github.com/fahim-muntasir-niloy/pr_guard)
- [Quick Start Guide](./QUICK_START.md)
- [Chat Integration Details](./CHAT_INTEGRATION.md)

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review the Quick Start guide

---

Made with ❤️ by the PR Guard team
