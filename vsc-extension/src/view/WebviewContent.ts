import * as vscode from 'vscode';
import { getNonce } from '../utils/common';

export class WebviewContent {
    public static getHtml(webview: vscode.Webview, extensionUri: vscode.Uri): string {
        const cssUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.css'));
        const jsUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.js'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'resources', 'marked.min.js'));
        const nonce = getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src http://127.0.0.1:8000;">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="${cssUri}">
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
            <button class="collapsible active">Quick Actions</button>
            <div class="content-section">
                <button id="review-btn" class="button">Start Code Review</button>
                <div class="collapsible" id="one-click-pr-toggle">One Click PR</div>
                <div class="content-section" id="one-click-pr-content" style="display: none;">
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

            <button class="collapsible active">Repository Analysis</button>
            <div class="content-section">
                <div class="input-group">
                    <label class="input-label">Project Tree Path</label>
                    <input type="text" id="tree-path" value="." placeholder="path/to/folder" />
                    <button id="tree-btn" class="button secondary">Show Structure</button>
                </div>
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
                <button id="status-btn" class="button secondary">System Status</button>
            </div>

            <div class="messages-container" id="commands-output" style="border-top: 1px solid var(--vscode-widget-border); padding-top: 16px;">
                 <div class="input-label" style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span>Output</span>
                    <span id="clear-output-btn" style="cursor:pointer; opacity:0.7;">Clear</span>
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
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z"/>
                        </svg>
                    </button>
                </div>
                <button id="new-session-btn" class="button secondary" style="font-size: 11px; margin-top:8px; opacity:0.8;">New Chat Session</button>
            </div>
        </div>
    </div>

    <div class="status-bar">
        <div id="status-dot" class="status-dot"></div>
        <span id="status-text">Connecting...</span>
        <!-- Simplified Reconnect -->
        <span id="reconnect-btn" style="cursor:pointer; margin-left:auto; opacity:0.8;">Refresh</span>
    </div>

    <script nonce="${nonce}" src="${jsUri}"></script>
</body>
</html>`;
    }
}
