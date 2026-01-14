"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const vscode = require("vscode");
const cp = require("child_process");
class SidebarProvider {
    constructor(_extensionUri, _getCliCommand) {
        this._extensionUri = _extensionUri;
        this._getCliCommand = _getCliCommand;
        this._apiBaseUrl = 'http://127.0.0.1:8000';
        this._isServerStarting = false;
        this._generateNewThreadId();
    }
    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        // Start the server when sidebar is opened
        this._startServer();
        webviewView.webview.onDidReceiveMessage(async (data) => {
            console.log('Received message from webview:', data);
            switch (data.type) {
                case 'runCommand': {
                    await this._runCommand(data.command, data.params);
                    break;
                }
                case 'clearOutput': {
                    this._clearMessages();
                    break;
                }
                case 'startChat': {
                    this._generateNewThreadId();
                    this._addMessage('system', '🆕 New chat session started.');
                    this._setChatActive(true);
                    break;
                }
                case 'sendChatMessage': {
                    await this._sendChatToApi(data.message);
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
    async _startServer() {
        if (this._serverProcess || this._isServerStarting) {
            return;
        }
        // First check if a server is already running
        try {
            const checkResponse = await fetch(`${this._apiBaseUrl}/status`);
            if (checkResponse.ok) {
                this._addMessage('system', '✅ Connected to existing PR Guard Server.');
                this._setChatActive(true);
                return;
            }
        }
        catch (e) {
            // Server not running, proceed to start
        }
        this._isServerStarting = true;
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceFolder) {
            this._addMessage('system', '❌ Error: No workspace folder open.');
            this._isServerStarting = false;
            return;
        }
        const commandBase = await this._getCliCommand();
        if (!commandBase) {
            this._addMessage('system', '❌ Error: pr-guard command not found.');
            this._isServerStarting = false;
            return;
        }
        // Command to run: pr-guard serve
        let fullCommand = `${commandBase} serve`;
        if (process.platform === 'win32' && fullCommand.startsWith('"')) {
            fullCommand = `& ${fullCommand}`;
        }
        this._addMessage('system', `🚀 Starting PR Guard Server with: ${fullCommand}`);
        console.log(`Starting server with command: ${fullCommand}`);
        const shell = process.platform === 'win32' ? 'powershell.exe' : true;
        // Ensure command is a single string for shell
        const spawnCommand = process.platform === 'win32' ? fullCommand : commandBase;
        const spawnArgs = process.platform === 'win32' ? [] : ['serve'];
        const child = cp.spawn(spawnCommand, spawnArgs, {
            cwd: workspaceFolder,
            shell: shell,
            env: { ...process.env, FORCE_COLOR: '0' },
            detached: false
        });
        this._serverProcess = child;
        child.stdout?.on('data', (data) => {
            console.log(`Server STDOUT: ${data}`);
        });
        child.stderr?.on('data', (data) => {
            const errOutput = data.toString();
            console.error(`Server STDERR: ${errOutput}`);
            // Report major errors to UI
            if (errOutput.toLowerCase().includes('error') || errOutput.toLowerCase().includes('fail')) {
                this._addMessage('system', `⚠️ Server: ${errOutput.substring(0, 100)}...`);
            }
        });
        child.on('error', (err) => {
            this._addMessage('system', `❌ Failed to spawn server: ${err.message}`);
        });
        child.on('close', (code) => {
            console.log(`Server process exited with code ${code}`);
            this._serverProcess = undefined;
            // Only set starting to false here if we haven't succeeded yet
            if (this._isServerStarting) {
                this._isServerStarting = false;
                this._addMessage('system', `⚠️ Server stopped (Code ${code}).`);
            }
        });
        // Wait for server to be ready
        let attempts = 0;
        const maxAttempts = 15;
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`${this._apiBaseUrl}/status`);
                if (response.ok) {
                    this._addMessage('system', '✅ PR Guard Server is ready!');
                    this._isServerStarting = false;
                    this._setChatActive(true);
                    return;
                }
            }
            catch (e) {
                // Not ready yet
            }
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        this._addMessage('system', '❌ Failed to connect to PR Guard Server after startup.');
        this._isServerStarting = false;
    }
    _generateNewThreadId() {
        this._threadId = this._uuidv4();
    }
    _uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    stopServer() {
        if (this._serverProcess) {
            this._serverProcess.kill();
            this._serverProcess = undefined;
        }
    }
    async _runStatusViaApi() {
        this._addMessage('system', '📊 Checking Status via API...');
        try {
            const response = await fetch(`${this._apiBaseUrl}/status`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            let gitInfo = '';
            if (typeof data.git === 'object') {
                gitInfo = `Branch: ${data.git.branch}\nLast Commit: ${data.git.last_commit}`;
            }
            else {
                gitInfo = data.git;
            }
            const statusText = `**Git Status**\n${gitInfo}\n\n**Configuration**\n- OpenAI API Key: ${data.openai_api_key}\n- LangSmith Tracing: ${data.langsmith_tracing ? 'Enabled' : 'Disabled'}`;
            this._addMessage('assistant', statusText);
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async _runTreeViaApi(params) {
        const path = params?.path || '.';
        this._addMessage('system', `🌲 Getting Project Tree for "${path}" via API...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/tree?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            this._addMessage('assistant', `**Project Structure (${path})**\n\n\`\`\`\n${data.tree}\n\`\`\``);
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async _runChangedViaApi(params) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._addMessage('system', `📝 Listing changed files between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/changed?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            if (data.files && data.files.length > 0) {
                this._addMessage('assistant', `**Changed Files (${base}...${head})**\n\n${data.files.map((f) => `- ${f}`).join('\n')}`);
            }
            else {
                this._addMessage('assistant', `**Changed Files (${base}...${head})**\n\nNo changes found.`);
            }
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async _runDiffViaApi(params) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._addMessage('system', `🔍 Getting diff between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/diff?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            this._addMessage('assistant', `**Diff (${base}...${head})**\n\n\`\`\`diff\n${data.diff}\n\`\`\``);
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async _runReviewViaApi() {
        this._addMessage('system', '🤖 Starting AI Review via API...');
        try {
            const response = await fetch(`${this._apiBaseUrl}/review`, {
                method: 'POST'
            });
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            if (!response.body) {
                throw new Error('No response body');
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedData = '';
            this._addMessage('assistant', 'Starting review...');
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                accumulatedData += chunk;
                const lines = accumulatedData.split('\n');
                accumulatedData = lines.pop() || '';
                for (const line of lines) {
                    const cleanLine = line.trim();
                    if (cleanLine.startsWith('data: ')) {
                        const dataStr = cleanLine.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'tool_call') {
                                this._addMessage('tool', data.name);
                            }
                            else if (data.type === 'report') {
                                const reportHtml = this._formatReviewReport(data.content);
                                this._addMessage('assistant', reportHtml);
                            }
                            else if (data.type === 'status') {
                                this._addMessage('system', data.message);
                            }
                        }
                        catch (e) {
                            // Partial JSON
                        }
                    }
                }
            }
            this._addMessage('system', '✅ Review completed.');
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    _formatReviewReport(content) {
        if (typeof content === 'string')
            return content;
        try {
            const report = content;
            let md = `## AI Review Report\n\n`;
            md += `**Result:** ${report.event || 'COMPLETED'}\n\n`;
            md += `${report.body || ''}\n\n`;
            if (report.comments && Array.isArray(report.comments)) {
                md += `### Detailed Comments\n\n`;
                report.comments.forEach((c) => {
                    md += `#### 📝 ${c.path} (line ${c.position})\n`;
                    md += `**Severity:** ${c.severity || 'info'}\n\n`;
                    md += `${c.body}\n\n`;
                    if (c.suggestion) {
                        md += `**Suggestion:**\n\`\`\`\n${c.suggestion}\n\`\`\`\n\n`;
                    }
                    md += `---\n\n`;
                });
            }
            return md;
        }
        catch (e) {
            return JSON.stringify(content, null, 2);
        }
    }
    async _sendChatToApi(message) {
        if (!message)
            return;
        this._addMessage('user', message);
        try {
            const response = await fetch(`${this._apiBaseUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    thread_id: this._threadId
                })
            });
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            if (!response.body) {
                throw new Error('No response body');
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedData = '';
            let started = false;
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                accumulatedData += chunk;
                const lines = accumulatedData.split('\n');
                accumulatedData = lines.pop() || '';
                for (const line of lines) {
                    const cleanLine = line.trim();
                    if (cleanLine.startsWith('data: ')) {
                        const dataStr = cleanLine.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'token') {
                                if (!started) {
                                    this._addMessage('assistant', data.content);
                                    started = true;
                                }
                                else {
                                    this._appendToLastMessage(data.content);
                                }
                            }
                            else if (data.type === 'tool_call') {
                                this._addMessage('tool', data.name);
                            }
                        }
                        catch (e) {
                            // Partial JSON
                        }
                    }
                }
            }
        }
        catch (error) {
            this._addMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async _runCommand(subCommand, params) {
        if (subCommand === 'review') {
            await this._runReviewViaApi();
            return;
        }
        if (subCommand === 'status') {
            await this._runStatusViaApi();
            return;
        }
        if (subCommand === 'getTree') {
            await this._runTreeViaApi(params);
            return;
        }
        if (subCommand === 'getChanged') {
            await this._runChangedViaApi(params);
            return;
        }
        if (subCommand === 'getDiff') {
            await this._runDiffViaApi(params);
            return;
        }
        console.log(`Running generic command: ${subCommand}`);
        // Fallback for any other command...
    }
    _stopChat() {
        this._setChatActive(false);
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
                <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                <style>
                    :root {
                        --padding: 12px;
                        --border-radius: 4px;
                    }
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: var(--vscode-font-family);
                        color: var(--vscode-foreground);
                        background-color: var(--vscode-editor-background);
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                        overflow: hidden;
                    }
                    
                    /* VS Code Header Look */
                    .header {
                        padding: 8px 12px;
                        text-transform: uppercase;
                        font-size: 11px;
                        font-weight: bold;
                        color: var(--vscode-descriptionForeground);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        background: var(--vscode-sideBar-background);
                    }

                    .tabs {
                        display: flex;
                        background: var(--vscode-sideBar-background);
                        border-bottom: 1px solid var(--vscode-panel-border);
                        padding: 0 4px;
                    }
                    .tab {
                        padding: 8px 12px;
                        background: transparent;
                        border: none;
                        color: var(--vscode-tab-inactiveForeground);
                        cursor: pointer;
                        font-size: 12px;
                        border-bottom: 1px solid transparent;
                    }
                    .tab.active {
                        color: var(--vscode-tab-activeForeground);
                        border-bottom: 1px solid var(--vscode-tab-activeForeground);
                        font-weight: 600;
                    }

                    .main-content {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        min-height: 0;
                        padding: 8px;
                    }

                    .tab-content { display: none; flex: 1; flex-direction: column; min-height: 0; }
                    .tab-content.active { display: flex; }

                    /* Accordion/Sections */
                    .collapsible {
                        background: var(--vscode-sideBarSectionHeader-background);
                        color: var(--vscode-sideBarSectionHeader-foreground);
                        cursor: pointer;
                        padding: 6px 8px;
                        width: 100%;
                        border: none;
                        text-align: left;
                        outline: none;
                        font-size: 11px;
                        font-weight: bold;
                        text-transform: uppercase;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }
                    .collapsible:after {
                        content: '\\u25B6';
                        font-size: 8px;
                        margin-left: auto;
                        transition: transform 0.2s;
                    }
                    .collapsible.active:after {
                        transform: rotate(90deg);
                    }
                    .content-section {
                        padding: 12px 8px;
                        display: block; /* Modified by JS */
                        background: var(--vscode-sideBar-background);
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    /* Form Elements */
                    .input-group { margin-bottom: 10px; }
                    .input-label { display: block; font-size: 11px; margin-bottom: 4px; color: var(--vscode-descriptionForeground); }
                    input[type="text"] {
                        width: 100%;
                        padding: 6px 8px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 2px;
                        font-family: inherit;
                        font-size: 12px;
                    }
                    input[type="text"]:focus {
                        outline: 1px solid var(--vscode-focusBorder);
                        border-color: var(--vscode-focusBorder);
                    }

                    .button {
                        width: 100%;
                        padding: 6px;
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        cursor: pointer;
                        border-radius: 2px;
                        font-size: 12px;
                    }
                    .button:hover { background-color: var(--vscode-button-hoverBackground); }
                    .button:disabled { opacity: 0.5; cursor: not-allowed; }
                    .button.secondary {
                        background-color: var(--vscode-button-secondaryBackground);
                        color: var(--vscode-button-secondaryForeground);
                        margin-top: 4px;
                    }

                    /* Messages Area */
                    .messages-container {
                        flex: 1;
                        overflow-y: auto;
                        padding: 8px;
                        background: var(--vscode-editor-background);
                        border: 1px solid var(--vscode-panel-border);
                        margin-top: 8px;
                        border-radius: 4px;
                    }
                    .message { margin-bottom: 12px; font-size: 13px; line-height: 1.4; border-radius: 4px; padding: 8px; }
                    .message.user { background: var(--vscode-button-background); color: var(--vscode-button-foreground); margin-left: 20px; }
                    .message.assistant { background: var(--vscode-editor-lineHighlightBackground); border-left: 3px solid var(--vscode-button-background); }
                    .message.system { font-size: 11px; opacity: 0.7; border-top: 1px solid var(--vscode-panel-border); padding-top: 4px; color: var(--vscode-descriptionForeground); margin-top: 8px; }
                    
                    /* Tool Call Styling - Outside AI message */
                    .message.tool {
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        border: 1px dashed var(--vscode-panel-border);
                        font-family: var(--vscode-editor-font-family);
                        font-size: 11px;
                        padding: 4px 8px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin: 4px 0;
                        opacity: 0.9;
                    }
                    .message.tool code { color: var(--vscode-textLink-foreground); }

                    /* Markdown Overrides */
                    .message pre { background: var(--vscode-textCodeBlock-background); padding: 8px; border-radius: 4px; overflow-x: auto; margin: 6px 0; width: 100%; }
                    .message code { font-family: var(--vscode-editor-font-family); font-size: 12px; }

                    .status-bar {
                        padding: 4px 12px;
                        font-size: 10px;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: var(--vscode-sideBarSectionHeader-background);
                        border-top: 1px solid var(--vscode-panel-border);
                    }
                    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #666; }
                    .status-dot.online { background: #0dbc79; box-shadow: 0 0 4px #0dbc79; }
                    .status-dot.offline { background: #cd3131; }
                    .placeholder { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--vscode-descriptionForeground); font-size: 12px; font-style: italic; }
                    
                    .chat-footer { padding: 8px; border-top: 1px solid var(--vscode-panel-border); }
                    .input-row { display: flex; gap: 4px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <span>PR Guard Assistant</span>
                </div>
                
                <div class="tabs">
                    <button id="tab-commands" class="tab active" onclick="switchTab('commands')">COMMANDS</button>
                    <button id="tab-chat" class="tab" onclick="switchTab('chat')">CHAT</button>
                </div>
                
                <div class="main-content">
                    <div id="commands-tab" class="tab-content active" style="overflow-y: auto;">
                        <button class="collapsible active" onclick="toggleCollapsible(this)">AI Actions</button>
                        <div class="content-section">
                            <button class="button" onclick="runCommand('review')">Start Full Code Review</button>
                        </div>

                        <button class="collapsible active" onclick="toggleCollapsible(this)">Repository Analysis</button>
                        <div class="content-section">
                            <div class="input-group">
                                <label class="input-label">Project Tree Path</label>
                                <input type="text" id="tree-path" value="." placeholder="path/to/folder" />
                                <button class="button secondary" onclick="runTreeWithParams()">Show Structure</button>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Compare Refs (Base...Head)</label>
                                <div style="display:flex; gap:4px; margin-bottom:4px;">
                                    <input type="text" id="ref-base" value="master" placeholder="base" />
                                    <input type="text" id="ref-head" value="HEAD" placeholder="head" />
                                </div>
                                <div style="display:flex; gap:4px;">
                                    <button class="button secondary" onclick="runChangedWithParams()">Changed Files</button>
                                    <button class="button secondary" onclick="runDiffWithParams()">Show Diff</button>
                                </div>
                            </div>
                            <button class="button secondary" onclick="runCommand('status')">System Status</button>
                        </div>

                        <div class="header" style="margin-top:12px; background:transparent;">
                            <span>Output</span>
                            <span style="cursor:pointer; text-decoration:underline;" onclick="clearMessages('commands-output')">Clear</span>
                        </div>
                        <div class="messages-container" id="commands-output">
                            <div class="placeholder">Command output will appear here.</div>
                        </div>
                    </div>

                    <div id="chat-tab" class="tab-content">
                        <div class="messages-container" id="chat-messages">
                            <div class="placeholder">How can I help you?</div>
                        </div>
                        <div class="chat-footer">
                            <div class="input-row">
                                <input type="text" id="chat-input" placeholder="Message PR Guard..." disabled />
                                <button class="button" id="send-btn" onclick="sendMessage()" style="width: auto;" disabled>Send</button>
                            </div>
                            <button class="button secondary" onclick="startChat()" style="font-size: 11px; margin-top:8px;">New Session</button>
                        </div>
                    </div>
                </div>

                <div class="status-bar">
                    <div id="status-dot" class="status-dot"></div>
                    <span id="status-text">Connecting...</span>
                    <!-- Simplified Reconnect -->
                    <span onclick="reconnect()" style="color:var(--vscode-textLink-foreground); cursor:pointer; margin-left:auto;">Refresh</span>
                </div>

                <script>
                    (function() {
                        const vscode = acquireVsCodeApi();
                        let isOnline = false;
                        let currentTab = 'commands';

                        marked.setOptions({ gfm: true, breaks: true });

                        window.toggleCollapsible = function(el) {
                            el.classList.toggle("active");
                            const content = el.nextElementSibling;
                            if (content.style.display === "none") {
                                content.style.display = "block";
                            } else {
                                content.style.display = "none";
                            }
                        };

                        window.switchTab = function(tabName) {
                            currentTab = tabName;
                            document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.id === 'tab-'+tabName));
                            document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === tabName+'-tab'));
                        };

                        window.runCommand = function(command, params = {}) {
                            vscode.postMessage({ type: 'runCommand', command, params });
                        };

                        window.runTreeWithParams = function() {
                            const path = document.getElementById('tree-path').value;
                            runCommand('getTree', { path });
                        };

                        window.runChangedWithParams = function() {
                            const base = document.getElementById('ref-base').value;
                            const head = document.getElementById('ref-head').value;
                            runCommand('getChanged', { base, head });
                        };

                        window.runDiffWithParams = function() {
                            const base = document.getElementById('ref-base').value;
                            const head = document.getElementById('ref-head').value;
                            runCommand('getDiff', { base, head });
                        };

                        window.startChat = function() {
                            vscode.postMessage({ type: 'startChat' });
                        };
                        
                        window.reconnect = function() {
                             vscode.postMessage({ type: 'startChat' }); // Trigger re-check
                        };

                        window.sendMessage = function() {
                            const input = document.getElementById('chat-input');
                            if (input.value.trim()) {
                                vscode.postMessage({ type: 'sendChatMessage', message: input.value.trim() });
                                input.value = '';
                            }
                        };

                        window.clearMessages = function(id) {
                            document.getElementById(id).innerHTML = '<div class="placeholder">Cleared.</div>';
                        };

                        function addMessage(type, content) {
                            const containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            const container = document.getElementById(containerId);
                            if (!container) return;
                            
                            const placeholder = container.querySelector('.placeholder');
                            if (placeholder) placeholder.remove();

                            const div = document.createElement('div');
                            div.className = 'message ' + type;
                            
                            if (type === 'tool') {
                                div.innerHTML = "<span>🔧 Executing tool:</span> <code>" + content + "</code>";
                            } else if (type === 'assistant' || type === 'system') {
                                div.setAttribute('data-raw', content);
                                div.innerHTML = marked.parse(content);
                            } else {
                                div.innerText = content;
                            }
                            
                            container.appendChild(div);
                            container.scrollTop = container.scrollHeight;
                        }

                        function appendToLastMessage(content) {
                            const containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            const container = document.getElementById(containerId);
                            if (!container) return;
                            
                            const messages = container.querySelectorAll('.message');
                            let last = null;
                            for(let i = messages.length-1; i>=0; i--) {
                                if(messages[i].classList.contains('assistant')) {
                                    last = messages[i];
                                    break;
                                }
                            }

                            if (last) {
                                const raw = (last.getAttribute('data-raw') || '') + content;
                                last.setAttribute('data-raw', raw);
                                last.innerHTML = marked.parse(raw);
                            } else {
                                addMessage('assistant', content);
                            }
                            container.scrollTop = container.scrollHeight;
                        }

                        window.addEventListener('message', event => {
                            const m = event.data;
                            switch (m.type) {
                                case 'addMessage':
                                    addMessage(m.messageType, m.content);
                                    break;
                                case 'appendToLastMessage':
                                    appendToLastMessage(m.content);
                                    break;
                                case 'setChatActive':
                                    isOnline = m.active;
                                    document.getElementById('chat-input').disabled = !isOnline;
                                    document.getElementById('send-btn').disabled = !isOnline;
                                    document.getElementById('status-dot').className = 'status-dot ' + (isOnline ? 'online' : 'offline');
                                    document.getElementById('status-text').innerText = isOnline ? 'Server Online' : 'Server Offline';
                                    break;
                                case 'clearMessages':
                                    window.clearMessages('commands-output');
                                    window.clearMessages('chat-messages');
                                    break;
                            }
                        });

                        document.getElementById('chat-input').addEventListener('keypress', e => {
                            if (e.key === 'Enter') sendMessage();
                        });
                    })();
                </script>
            </body>
            </html>`;
    }
}
exports.SidebarProvider = SidebarProvider;
//# sourceMappingURL=SidebarProvider.js.map