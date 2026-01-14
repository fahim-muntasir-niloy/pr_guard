"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const vscode = require("vscode");
const cp = require("child_process");
class SidebarProvider {
    constructor(_extensionUri, _getCliCommand) {
        this._extensionUri = _extensionUri;
        this._getCliCommand = _getCliCommand;
    }
    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        webviewView.webview.onDidReceiveMessage(async (data) => {
            console.log('Received message from webview:', data);
            switch (data.type) {
                case 'runCommand': {
                    await this._runCommand(data.command);
                    break;
                }
                case 'clearOutput': {
                    this._clearMessages();
                    break;
                }
                case 'startChat': {
                    await this._startChat();
                    break;
                }
                case 'sendChatMessage': {
                    this._sendChatMessage(data.message);
                    break;
                }
                case 'stopChat': {
                    this._stopChat();
                    break;
                }
            }
        });
    }
    revive(panel) {
        this._view = panel;
    }
    async _runCommand(subCommand) {
        console.log(`Running command: ${subCommand}`);
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceFolder) {
            this._addMessage('system', '❌ Error: No workspace folder open.');
            return;
        }
        const commandBase = await this._getCliCommand();
        if (!commandBase) {
            this._addMessage('system', '❌ Error: pr-guard command not found. Please install pr-guard or configure the executable path in settings.');
            return;
        }
        const fullCommand = `${commandBase} ${subCommand}`.trim();
        this._addMessage('system', `🔄 Running: ${fullCommand}`);
        const execOptions = {
            cwd: workspaceFolder,
            maxBuffer: 1024 * 1024 * 10, // 10MB buffer
            shell: process.platform === 'win32' ? 'powershell.exe' : '/bin/sh',
            env: { ...process.env, FORCE_COLOR: '0' }
        };
        // In PowerShell, if the command starts with quotes, you must use the call operator (&)
        const finalCommand = (process.platform === 'win32' && fullCommand.startsWith('"'))
            ? `& ${fullCommand}`
            : fullCommand;
        const childProcess = cp.exec(finalCommand, execOptions);
        childProcess.stdout?.on('data', (data) => {
            this._appendToLastMessage(data);
        });
        childProcess.stderr?.on('data', (data) => {
            this._appendToLastMessage(data);
        });
        childProcess.on('close', (code) => {
            if (code === 0) {
                this._addMessage('system', '✅ Command completed successfully');
            }
            else {
                this._addMessage('system', `❌ Command exited with code ${code}`);
            }
        });
        childProcess.on('error', (err) => {
            console.error('Command error:', err);
            this._addMessage('system', `❌ Error: ${err.message}`);
        });
    }
    async _startChat() {
        console.log('Starting chat session');
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceFolder) {
            this._addMessage('system', '❌ Error: No workspace folder open.');
            return;
        }
        const commandBase = await this._getCliCommand();
        if (!commandBase) {
            this._addMessage('system', '❌ Error: pr-guard command not found.');
            return;
        }
        this._clearMessages();
        this._setChatActive(true);
        this._addMessage('system', '🚀 Initializing PR Guard Chat...');
        const execOptions = {
            cwd: workspaceFolder,
            shell: process.platform === 'win32' ? 'powershell.exe' : true,
            env: { ...process.env, FORCE_COLOR: '1' } // Force color for chat
        };
        // Create final command string
        let finalCommand = `${commandBase} chat`;
        if (process.platform === 'win32' && finalCommand.startsWith('"')) {
            finalCommand = `& ${finalCommand}`;
        }
        this._chatProcess = cp.spawn(finalCommand, [], execOptions);
        let lastMessageFromAssistant = false;
        this._chatProcess.stdout?.on('data', (data) => {
            const text = data.toString();
            if (lastMessageFromAssistant) {
                this._appendToLastMessage(text);
            }
            else {
                this._addMessage('assistant', text);
                lastMessageFromAssistant = true;
            }
        });
        this._chatProcess.stderr?.on('data', (data) => {
            const text = data.toString();
            this._appendToLastMessage(text);
        });
        this._chatProcess.on('close', (code) => {
            console.log(`Chat process closed with code ${code}`);
            this._setChatActive(false);
            if (code !== 0 && code !== null) {
                this._addMessage('system', `Chat session ended (Code: ${code})`);
            }
            else {
                this._addMessage('system', 'Chat session ended');
            }
        });
        this._chatProcess.on('error', (err) => {
            console.error('Chat error:', err);
            this._addMessage('system', `❌ Error: ${err.message}`);
            this._setChatActive(false);
        });
    }
    _sendChatMessage(message) {
        if (!this._chatProcess || !this._chatProcess.stdin) {
            this._addMessage('system', '❌ Chat is not active');
            return;
        }
        this._addMessage('user', message);
        this._chatProcess.stdin.write(message + '\n');
    }
    _stopChat() {
        if (this._chatProcess) {
            this._chatProcess.kill();
            this._chatProcess = undefined;
        }
    }
    _addMessage(type, content) {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'addMessage',
                messageType: type,
                content: content
            });
        }
    }
    _appendToLastMessage(content) {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'appendToLastMessage',
                content: content
            });
        }
    }
    _clearMessages() {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'clearMessages'
            });
        }
    }
    _setChatActive(active) {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'setChatActive',
                active: active
            });
        }
    }
    _getHtmlForWebview(webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    body {
                        font-family: var(--vscode-editor-font-family);
                        padding: 12px;
                        color: var(--vscode-editor-foreground);
                        background-color: var(--vscode-editor-background);
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                    }
                    .tabs {
                        display: flex;
                        gap: 4px;
                        margin-bottom: 12px;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }
                    .tab {
                        padding: 8px 16px;
                        background: transparent;
                        border: none;
                        color: var(--vscode-descriptionForeground);
                        cursor: pointer;
                        font-size: 13px;
                        font-weight: 500;
                        border-bottom: 2px solid transparent;
                        transition: all 0.2s;
                    }
                    .tab:hover {
                        color: var(--vscode-foreground);
                    }
                    .tab.active {
                        color: var(--vscode-button-background);
                        border-bottom-color: var(--vscode-button-background);
                    }
                    .tab-content {
                        display: none;
                        flex: 1;
                        flex-direction: column;
                        min-height: 0;
                    }
                    .tab-content.active {
                        display: flex;
                    }
                    .button {
                        width: 100%;
                        padding: 10px;
                        margin-bottom: 8px;
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        text-align: center;
                        cursor: pointer;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: 500;
                        transition: background-color 0.2s;
                    }
                    .button:hover {
                        background-color: var(--vscode-button-hoverBackground);
                    }
                    .button:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }
                    .button.secondary {
                        background-color: var(--vscode-button-secondaryBackground);
                        color: var(--vscode-button-secondaryForeground);
                    }
                    .button.secondary:hover {
                        background-color: var(--vscode-button-secondaryHoverBackground);
                    }
                    .section {
                        margin-bottom: 16px;
                    }
                    h3 {
                        text-transform: uppercase;
                        font-size: 11px;
                        font-weight: 600;
                        opacity: 0.8;
                        margin-bottom: 10px;
                        letter-spacing: 0.5px;
                    }
                    .messages-container {
                        flex: 1;
                        overflow-y: auto;
                        padding: 10px;
                        border: 1px solid var(--vscode-panel-border);
                        background: var(--vscode-editor-background);
                        margin-bottom: 10px;
                        border-radius: 4px;
                    }
                    .message {
                        margin-bottom: 12px;
                        padding: 8px 12px;
                        border-radius: 6px;
                        line-height: 1.5;
                        font-size: 13px;
                    }
                    .message.user {
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        margin-left: 20px;
                    }
                    .message.assistant {
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        margin-right: 20px;
                        white-space: pre-wrap;
                        font-family: var(--vscode-editor-font-family);
                    }
                    .message.system {
                        background: var(--vscode-inputValidation-infoBackground);
                        color: var(--vscode-inputValidation-infoForeground);
                        text-align: center;
                        font-size: 12px;
                        opacity: 0.9;
                    }
                    .input-container {
                        display: flex;
                        gap: 8px;
                    }
                    .input-container input {
                        flex: 1;
                        padding: 8px 12px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 4px;
                        font-size: 13px;
                        font-family: var(--vscode-editor-font-family);
                    }
                    .input-container input:focus {
                        outline: none;
                        border-color: var(--vscode-focusBorder);
                    }
                    .input-container button {
                        padding: 8px 16px;
                        margin: 0;
                    }
                    .placeholder {
                        color: var(--vscode-descriptionForeground);
                        font-style: italic;
                        text-align: center;
                        padding: 40px 20px;
                    }
                    
                    .ansi-black { color: #000000; }
                    .ansi-red { color: #cd3131; }
                    .ansi-green { color: #0dbc79; }
                    .ansi-yellow { color: #e5e510; }
                    .ansi-blue { color: #2472c8; }
                    .ansi-magenta { color: #bc3fbc; }
                    .ansi-cyan { color: #11a8cd; }
                    .ansi-white { color: #e5e5e5; }
                    .ansi-bright-black { color: #666666; }
                    .ansi-bright-red { color: #f14c4c; }
                    .ansi-bright-green { color: #23d18b; }
                    .ansi-bright-yellow { color: #f5f543; }
                    .ansi-bright-blue { color: #3b8eea; }
                    .ansi-bright-magenta { color: #d670d6; }
                    .ansi-bright-cyan { color: #29b8db; }
                    .ansi-bright-white { color: #ffffff; }
                    .ansi-bold { font-weight: bold; }
                    .ansi-dim { opacity: 0.6; }
                    .ansi-italic { font-style: italic; }
                    .ansi-underline { text-decoration: underline; }
                </style>
                <script>
                    (function() {
                        const vscode = acquireVsCodeApi();
                        let chatActive = false;
                        let currentTab = 'commands';

                        window.switchTab = function(tabName) {
                            currentTab = tabName;
                            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                            
                            const tabBtn = document.getElementById('tab-' + tabName);
                            if (tabBtn) tabBtn.classList.add('active');
                            const tabContent = document.getElementById(tabName + '-tab');
                            if (tabContent) tabContent.classList.add('active');
                        };

                        window.runCommand = function(command) {
                            vscode.postMessage({ type: 'runCommand', command: command });
                        };

                        window.clearAllMessages = function() {
                            const cmdOutput = document.getElementById('commands-output');
                            if (cmdOutput) cmdOutput.innerHTML = '<div class="placeholder">Run a command to see output here...</div>';
                            const chatOutput = document.getElementById('chat-messages');
                            if (chatOutput) chatOutput.innerHTML = '<div class="placeholder">Click "Start Chat" to begin...</div>';
                        };

                        window.startChat = function() {
                            vscode.postMessage({ type: 'startChat' });
                        };

                        window.stopChat = function() {
                            vscode.postMessage({ type: 'stopChat' });
                        };

                        window.sendMessage = function() {
                            const input = document.getElementById('chat-input');
                            const message = input.value.trim();
                            if (message && chatActive) {
                                vscode.postMessage({ type: 'sendChatMessage', message: message });
                                input.value = '';
                            }
                        };

                        function convertAnsiToHtml(text) {
                            const esc = String.fromCharCode(27);
                            let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                            
                            // Simple ANSI split approach to avoid regex literals in template
                            const parts = html.split(esc + '[');
                            if (parts.length === 1) return html;
                            
                            let result = parts[0];
                            for (let i = 1; i < parts.length; i++) {
                                const m = parts[i].match(/^([0-9;]*)m/);
                                if (m) {
                                    const params = m[1];
                                    const rest = parts[i].substring(m[0].length);
                                    if (!params || params === '0') {
                                        result += '</span>' + rest;
                                    } else {
                                        const codes = params.split(';').map(Number);
                                        const classes = [];
                                        codes.forEach(code => {
                                            if (code === 1) classes.push('ansi-bold');
                                            else if (code === 2) classes.push('ansi-dim');
                                            else if (code >= 30 && code <= 37) classes.push('ansi-' + ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'][code - 30]);
                                            else if (code >= 90 && code <= 97) classes.push('ansi-bright-' + ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'][code - 90]);
                                        });
                                        result += '<span class="' + classes.join(' ') + '">' + rest;
                                    }
                                } else {
                                    result += parts[i];
                                }
                            }
                            return result;
                        }

                        function addMessage(type, content) {
                            const containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            const container = document.getElementById(containerId);
                            if (!container) return;
                            
                            const placeholder = container.querySelector('.placeholder');
                            if (placeholder) placeholder.remove();
                            
                            const div = document.createElement('div');
                            div.className = 'message ' + type;
                            div.innerHTML = convertAnsiToHtml(content);
                            container.appendChild(div);
                            container.scrollTop = container.scrollHeight;
                        }

                        function appendToLastMessage(content) {
                            const containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            const container = document.getElementById(containerId);
                            if (!container) return;
                            
                            const messages = container.querySelectorAll('.message');
                            if (messages.length > 0) {
                                messages[messages.length - 1].innerHTML += convertAnsiToHtml(content);
                            } else {
                                addMessage('assistant', content);
                            }
                            container.scrollTop = container.scrollHeight;
                        }

                        function setChatActive(active) {
                            chatActive = active;
                            const input = document.getElementById('chat-input');
                            if (input) input.disabled = !active;
                            const btn = document.getElementById('send-btn');
                            if (btn) btn.disabled = !active;
                            const startBtn = document.getElementById('start-chat-btn');
                            if (startBtn) startBtn.style.display = active ? 'none' : 'block';
                            const stopBtn = document.getElementById('stop-chat-btn');
                            if (stopBtn) stopBtn.style.display = active ? 'block' : 'none';
                        }

                        window.addEventListener('message', event => {
                            const m = event.data;
                            if (m.type === 'addMessage') addMessage(m.messageType, m.content);
                            else if (m.type === 'appendToLastMessage') appendToLastMessage(m.content);
                            else if (m.type === 'clearMessages') window.clearAllMessages();
                            else if (m.type === 'setChatActive') setChatActive(m.active);
                        });

                        document.addEventListener('DOMContentLoaded', () => {
                            const input = document.getElementById('chat-input');
                            if (input) {
                                input.addEventListener('keypress', (e) => {
                                    if (e.key === 'Enter') window.sendMessage();
                                });
                            }
                        });
                        
                        console.log('PR Guard Sidebar Loaded');
                    })();
                </script>
            </head>
            <body>
                <div class="tabs">
                    <button id="tab-commands" class="tab active" onclick="switchTab('commands')">Commands</button>
                    <button id="tab-chat" class="tab" onclick="switchTab('chat')">💬 Chat</button>
                </div>

                <div id="commands-tab" class="tab-content active">
                    <div class="section">
                        <h3>Quick Actions</h3>
                        <button class="button" onclick="runCommand('review')">📝 Start Review</button>
                        <button class="button" onclick="runCommand('status')">📊 Check Status</button>
                        <button class="button" onclick="runCommand('init')">⚙️ Run Init</button>
                    </div>

                    <div style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0;">Output</h3>
                            <button class="button secondary" onclick="clearAllMessages()" style="width: auto; padding: 4px 12px; margin: 0; font-size: 11px;">Clear</button>
                        </div>
                        <div class="messages-container" id="commands-output">
                            <div class="placeholder">Run a command to see output here...</div>
                        </div>
                    </div>
                </div>

                <div id="chat-tab" class="tab-content">
                    <div style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0;">Chat Session</h3>
                            <div style="display: flex; gap: 8px;">
                                <button id="start-chat-btn" class="button" onclick="startChat()" style="width: auto; padding: 4px 12px; margin: 0; font-size: 11px;">Start Chat</button>
                                <button id="stop-chat-btn" class="button secondary" onclick="stopChat()" style="width: auto; padding: 4px 12px; margin: 0; font-size: 11px; display: none;">Stop</button>
                            </div>
                        </div>
                        <div class="messages-container" id="chat-messages">
                            <div class="placeholder">Click "Start Chat" to begin...</div>
                        </div>
                        <div class="input-container">
                            <input type="text" id="chat-input" placeholder="Type message..." disabled />
                            <button class="button" onclick="sendMessage()" id="send-btn" disabled>Send</button>
                        </div>
                    </div>
                </div>
            </body>
            </html>`;
    }
}
exports.SidebarProvider = SidebarProvider;
//# sourceMappingURL=SidebarProvider.js.map