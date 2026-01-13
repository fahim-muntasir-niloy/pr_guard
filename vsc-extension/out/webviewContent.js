"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getWebviewContent = getWebviewContent;
const MarkdownIt = require("markdown-it");
const md = new MarkdownIt();
function getWebviewContent(content, isLoading = false) {
    const bodyContent = isLoading
        ? '<div class="loading">Generating AI Review... <span class="loader"></span></div>'
        : md.render(content);
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR Guard Review</title>
    <style>
        body {
            font-family: var(--vscode-editor-font-family);
            padding: 20px;
            color: var(--vscode-editor-foreground);
            background-color: var(--vscode-editor-background);
        }
        h1, h2, h3 {
            color: var(--vscode-textLink-foreground);
        }
        code {
            font-family: var(--vscode-editor-font-family);
            background-color: var(--vscode-textBlockQuote-background);
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            background-color: var(--vscode-textBlockQuote-background);
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            font-size: 1.5em;
            color: var(--vscode-descriptionForeground);
        }
        .loader {
            border: 4px solid var(--vscode-panel-border);
            border-top: 4px solid var(--vscode-progressBar-background);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    ${bodyContent}
</body>
</html>`;
}
//# sourceMappingURL=webviewContent.js.map