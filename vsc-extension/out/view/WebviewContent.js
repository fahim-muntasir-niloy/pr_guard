"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebviewContent = void 0;
const vscode = require("vscode");
const common_1 = require("../utils/common");
class WebviewContent {
    static getHtml(webview, extensionUri) {
        const cssUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.css'));
        const jsUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.js'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'resources', 'marked.min.js'));
        const codiconsUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'node_modules', '@vscode/codicons', 'dist', 'codicon.css'));
        const nonce = (0, common_1.getNonce)();
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; font-src ${webview.cspSource}; script-src 'nonce-${nonce}'; connect-src http://127.0.0.1:8000;">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="${cssUri}">
    <link rel="stylesheet" href="${codiconsUri}">
    <script nonce="${nonce}" src="${scriptUri}"></script>
    <title>PR Guard</title>
</head>
<body>
    <div class="tabs">
        <button id="tab-commands" class="tab active">Actions</button>
        <button id="tab-chat" class="tab">Chat</button>
    </div>

    <div class="main-content">
        <div id="commands-tab" class="tab-content active">
            <div class="actions-group">
                <div class="action-item">
                    <button id="review-btn" class="button">Start Code Review</button>
                </div>
                <div class="action-item collapsible">
                    <button class="button collapsible-toggle">One Click PR</button>
                    <div class="collapsible-content">
                        <div class="input-group">
                            <label class="input-label">User Instructions</label>
                            <input type="text" id="pr-instructions" class="input" placeholder="e.g., Add new feature">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Base Branch</label>
                            <input type="text" id="pr-base" class="input" value="master">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Head Branch</label>
                            <input type="text" id="pr-head" class="input" value="HEAD">
                        </div>
                        <button id="one-click-pr-btn" class="button">Create PR</button>
                    </div>
                </div>
            </div>

            <div class="actions-group">
                <div class="action-item">
                    <div class="input-group">
                        <label class="input-label">Project Tree Path</label>
                        <input type="text" id="tree-path" value="." placeholder="path/to/folder" />
                        <button id="tree-btn" class="button secondary">Show Structure</button>
                    </div>
                </div>
                <div class="action-item">
                    <div class="input-group">
                        <label class="input-label">Compare Refs</label>
                        <div style="display:flex; gap:8px; margin-bottom:8px;">
                            <input type="text" id="ref-base" value="master" placeholder="base" />
                            <input type="text" id="ref-head" value="HEAD" placeholder="head" />
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button id="changed-btn" class="button secondary">Changed Files</button>
                        </div>
                    </div>
                </div>
                <div class="action-item">
                    <button id="status-btn" class="button secondary">System Status</button>
                </div>
            </div>

            <div class="output-container" id="commands-output">
                 <div class="output-header">
                    <span>Output</span>
                    <div>
                        <span id="save-report-btn" class="action-icon" title="Save Report"><i class="codicon codicon-save"></i></span>
                        <span id="clear-output-btn" class="action-icon" title="Clear Output"><i class="codicon codicon-trash"></i></span>
                    </div>
                </div>
                <div class="placeholder">Results will appear here.</div>
            </div>
        </div>

        <div id="chat-tab" class="tab-content">
            <div class="messages-container" id="chat-messages">
                <div class="placeholder">
                    <div style="text-align:center;">
                        <p>How can I help you today?</p>
                        <p style="font-size:11px; margin-top:8px;">Try asking about your code changes.</p>
                    </div>
                </div>
            </div>
            <div class="chat-footer">
                <div class="input-wrapper">
                    <input type="text" id="chat-input" class="chat-input" placeholder="Ask a question..." disabled />
                    <button id="send-btn" class="send-icon-btn" disabled>
                        <i class="codicon codicon-send"></i>
                    </button>
                </div>
                <button id="new-session-btn" class="button secondary" style="font-size: 11px; margin-top:8px; opacity:0.8;">New Chat Session</button>
            </div>
        </div>
    </div>

    <div class="status-bar">
        <div id="status-dot" class="status-dot"></div>
        <span id="status-text">Connecting...</span>
        <span id="reconnect-btn" class="action-icon" style="margin-left:auto;"><i class="codicon codicon-sync"></i></span>
    </div>

    <script nonce="${nonce}" src="${jsUri}"></script>
</body>
</html>`;
    }
}
exports.WebviewContent = WebviewContent;
//# sourceMappingURL=WebviewContent.js.map