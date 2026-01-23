import * as vscode from 'vscode';
import { getNonce } from '../utils/common';

export class WebviewContent {
    public static getHtml(webview: vscode.Webview, extensionUri: vscode.Uri): string {
        const cssUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.css'));
        const jsUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'view', 'webview.js'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'resources', 'marked.min.js'));
        const codiconsUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'node_modules', '@vscode/codicons', 'dist', 'codicon.css'));
        const nonce = getNonce();

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
        <button id="tab-settings" class="tab">Settings</button>
    </div>

    <div class="main-content">
        <div id="commands-tab" class="tab-content active">
            <div class="actions-group minimalist">
                <div class="action-item collapsible active">
                    <div class="collapsible-header">
                        <i class="codicon codicon-rocket"></i>
                        <span>One Click PR</span>
                    </div>
                    <div class="collapsible-content">
                        <div class="input-group">
                            <label class="input-label">User Instructions</label>
                            <input type="text" id="pr-instructions" class="input" placeholder="e.g., Add new feature">
                        </div>
                        <div class="input-row">
                            <div class="input-group half">
                                <label class="input-label">Base</label>
                                <select id="pr-base" class="input">
                                    <option value="master">master</option>
                                    <option value="main">main</option>
                                </select>
                            </div>
                            <div class="input-group half">
                                <label class="input-label">Head <a href="#" id="refresh-branches" title="Refresh Branches"><i class="codicon codicon-refresh"></i></a></label>
                                <select id="pr-head" class="input">
                                    <option value="HEAD">HEAD</option>
                                </select>
                            </div>
                        </div>
                        <button id="one-click-pr-btn" class="button">
                            <span class="btn-text">Create Pull Request</span>
                            <div class="btn-loader hidden"><i class="codicon codicon-loading codicon-modifier-spin"></i></div>
                        </button>
                    </div>
                </div>
            </div>

            <div class="output-container">
                 <div class="output-header">
                    <span>Activity Log</span>
                    <div>
                        <span id="system-status-btn" class="action-icon" title="System Status"><i class="codicon codicon-pulse"></i></span>
                        <span id="save-report-btn" class="action-icon" title="Save Report"><i class="codicon codicon-save"></i></span>
                        <span id="clear-output-btn" class="action-icon" title="Clear Output"><i class="codicon codicon-trash"></i></span>
                    </div>
                </div>
                <div id="commands-output">
                    <div class="placeholder">Command output will appear here.</div>
                </div>
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

        <div id="settings-tab" class="tab-content">
            <div class="settings-container">
                <div class="settings-section">
                    <h3 class="section-title">LLM Configuration</h3>
                    
                    <div class="input-group">
                        <label class="input-label">Provider</label>
                        <select id="settings-provider" class="input">
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="google_genai">Google GenAI</option>
                            <option value="xai">XAI (Grok)</option>
                        </select>
                    </div>

                    <div class="input-group">
                        <label class="input-label">Model Name</label>
                        <input type="text" id="settings-model" class="input" placeholder="e.g. gpt-4o">
                    </div>

                    <div class="input-group">
                        <label class="input-label">API Key</label>
                        <div class="key-input-wrapper">
                            <input type="password" id="settings-key" class="input" placeholder="Enter your API key">
                            <button id="toggle-key-visibility" class="icon-button"><i class="codicon codicon-eye"></i></button>
                        </div>
                    </div>
                    <p id="save-settings-response"></p>
                    <button id="save-settings-btn" class="button">Save Settings</button>
                </div>

                <div class="settings-info">
                    <p><i class="codicon codicon-info"></i> Changes require a server restart to take effect.</p>
                </div>
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
