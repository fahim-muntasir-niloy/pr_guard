"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebviewContent = void 0;
const vscode = require("vscode");
const common_1 = require("../utils/common");
class WebviewContent {
    static getHtml(webview, extensionUri) {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'resources', 'marked.min.js'));
        const nonce = (0, common_1.getNonce)();
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src http://127.0.0.1:8000;">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script nonce="${nonce}" src="${scriptUri}"></script>
                <style>
                    :root {
                        --padding: 16px;
                        --border-radius: 6px;
                        --bg-user: var(--vscode-editor-background);
                        --bg-assistant: var(--vscode-editor-background);
                        --border-color: var(--vscode-editorGroup-border);
                        --accent: var(--vscode-textLink-foreground);
                        --text-secondary: var(--vscode-descriptionForeground);
                    }
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: var(--vscode-font-family), system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        color: var(--vscode-editor-foreground);
                        background-color: var(--vscode-editor-background);
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                        overflow: hidden;
                        font-size: 13px;
                        line-height: 1.5;
                    }
                    
                    /* Modern Tabs */
                    .tabs {
                        display: flex;
                        padding: 0 8px;
                        margin-top: 8px;
                        gap: 16px;
                        border-bottom: 1px solid var(--vscode-widget-border);
                    }
                    .tab {
                        padding: 8px 4px;
                        background: transparent;
                        border: none;
                        color: var(--text-secondary);
                        cursor: pointer;
                        font-size: 12px;
                        font-weight: 500;
                        border-bottom: 2px solid transparent;
                        transition: color 0.2s, border-bottom 0.2s;
                    }
                    .tab:hover {
                        color: var(--vscode-foreground);
                    }
                    .tab.active {
                        color: var(--vscode-foreground);
                        border-bottom: 2px solid var(--accent);
                    }

                    .main-content {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        min-height: 0;
                        position: relative;
                    }

                    .tab-content { display: none; flex: 1; flex-direction: column; min-height: 0; padding: 0; }
                    .tab-content.active { display: flex; }

                    /* Accordion/Sections for Commands */
                    #commands-tab { padding: 8px; overflow-y: auto; }
                    .collapsible {
                        background: transparent;
                        color: var(--vscode-sideBarTitle-foreground);
                        cursor: pointer;
                        padding: 10px 0;
                        width: 100%;
                        border: none;
                        text-align: left;
                        outline: none;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        letter-spacing: 0.5px;
                        opacity: 0.8;
                    }
                    .collapsible:hover { opacity: 1; }
                    .collapsible:after {
                        content: '\\203A'; /* Chevron */
                        font-size: 14px;
                        margin-left: auto;
                        transition: transform 0.2s;
                    }
                    .collapsible.active:after {
                        transform: rotate(90deg);
                    }
                    .content-section {
                        padding: 4px 0 16px 0;
                        display: block; 
                    }

                    /* Minimal Form Elements */
                    .input-group { margin-bottom: 12px; }
                    .input-label { display: block; font-size: 11px; margin-bottom: 6px; color: var(--text-secondary); }
                    input[type="text"] {
                        width: 100%;
                        padding: 8px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 12px;
                    }
                    input[type="text"]:focus {
                        outline: 1px solid var(--vscode-focusBorder);
                        border-color: var(--vscode-focusBorder);
                    }

                    .button {
                        width: 100%;
                        padding: 8px;
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        cursor: pointer;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: 500;
                        transition: opacity 0.2s;
                    }
                    .button:hover { opacity: 0.9; }
                    .button:disabled { opacity: 0.5; cursor: not-allowed; }
                    .button.secondary {
                        background-color: var(--vscode-button-secondaryBackground);
                        color: var(--vscode-button-secondaryForeground);
                        margin-top: 6px;
                    }

                    /* Clean Interface Chat */
                    .messages-container {
                        flex: 1;
                        overflow-y: auto;
                        padding: 16px;
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                    }
                    
                    .message { 
                        font-size: 13px; 
                        line-height: 1.6; 
                        word-wrap: break-word; 
                        overflow-wrap: break-word; 
                        max-width: 100%;
                        position: relative;
                        animation: fadeIn 0.3s ease;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(5px); }
                        to { opacity: 1; transform: translateY(0); }
                    }

                    .message img { max-width: 100%; height: auto; border-radius: 4px; }
                    
                    /* User Message - Minimal, Right aligned or distinct */
                    .message.user { 
                        align-self: flex-end; /* If we want bubble style */
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        color: var(--vscode-editor-foreground);
                        padding: 8px 12px;
                        border-radius: 8px; /* Softer rounded corners */
                        max-width: 85%;
                        border: 1px solid var(--vscode-widget-border);
                    }

                    /* Assistant Message - Clean, left aligned */
                    .message.assistant { 
                        align-self: flex-start;
                        color: var(--vscode-editor-foreground);
                        padding: 0 4px;
                        max-width: 100%;
                        /* No background for assistant, just clean text like Cursor/Antigravity */
                    }
                    
                    .message.system { 
                        align-self: center;
                        font-size: 11px; 
                        color: var(--text-secondary); 
                        margin: 8px 0;
                        text-align: center;
                        background: var(--vscode-textBlockQuote-background);
                        padding: 4px 12px;
                        border-radius: 12px;
                    }
                    
                    .message.tool {
                        font-family: var(--vscode-editor-font-family);
                        font-size: 11px;
                        color: var(--text-secondary);
                        margin: 0;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        opacity: 0.8;
                    }
                    .message.tool::before {
                        content: '⚡';
                        font-size: 10px;
                    }

                    /* Markdown Overrides */
                    .message pre { 
                        background: var(--vscode-textCodeBlock-background); 
                        padding: 12px; 
                        border-radius: 6px; 
                        overflow-x: auto; 
                        margin: 8px 0; 
                        width: 100%;
                        border: 1px solid var(--vscode-widget-border);
                    }
                    .message code { 
                        font-family: var(--vscode-editor-font-family); 
                        font-size: 12px;
                        background: var(--vscode-textBlockQuote-background);
                        padding: 2px 4px;
                        border-radius: 3px;
                    }
                    .message pre code {
                        background: transparent;
                        padding: 0;
                    }

                    .message ul, .message ol { padding-left: 1.5rem; margin: 8px 0; }
                    .message li { margin-bottom: 4px; }
                    .message p { margin-bottom: 8px; }
                    .message p:last-child { margin-bottom: 0; }


                    /* Aesthetic Thinking Bubble */

                    /* Minimal Thinking UI */
                    .thinking-bubble {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 0;
                        margin: 4px 0;
                        color: var(--text-secondary);
                        font-family: var(--vscode-font-family);
                        font-size: 11px;
                        font-style: italic;
                        opacity: 0.8;
                    }

                    .thinking-dots {
                        display: flex;
                        gap: 3px;
                    }
                    
                    .dot {
                        width: 4px;
                        height: 4px;
                        background: var(--text-secondary);
                        border-radius: 50%;
                        animation: wave 1.4s infinite ease-in-out both;
                        opacity: 0.6;
                    }

                    .dot:nth-child(1) { animation-delay: -0.32s; }
                    .dot:nth-child(2) { animation-delay: -0.16s; }
                    
                    @keyframes wave {
                        0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                        40% { transform: scale(1); opacity: 1; }
                    }

                    .thinking-text {
                        transition: opacity 0.2s;
                    }

                    /* Input Area - Fixed at bottom */
                    .chat-footer { 
                        padding: 16px; 
                        background: var(--vscode-editor-background);
                        border-top: 1px solid var(--vscode-widget-border);
                    }
                    .input-wrapper {
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                        position: relative;
                    }
                    .chat-input {
                        width: 100%;
                        padding: 12px;
                        padding-right: 40px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 6px;
                        font-family: inherit;
                        font-size: 13px;
                        resize: none;
                        outline: none;
                    }
                    .chat-input:focus {
                        border-color: var(--vscode-focusBorder);
                    }
                    .send-icon-btn {
                        position: absolute;
                        right: 8px;
                        top: 8px; /* Adjusted for alignment */
                        background: transparent;
                        border: none;
                        color: var(--accent);
                        cursor: pointer;
                        padding: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .send-icon-btn:disabled {
                        color: var(--text-secondary);
                        cursor: default;
                    }
                    
                    .status-bar {
                        padding: 4px 12px;
                        font-size: 10px;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: var(--vscode-statusBar-background);
                        color: var(--vscode-statusBar-foreground);
                        border-top: 1px solid var(--vscode-panel-border);
                    }
                    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #666; }
                    .status-dot.online { background: #0dbc79; box-shadow: 0 0 4px #0dbc79; }
                    .status-dot.offline { background: #cd3131; }
                    .placeholder { 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        height: 100%; 
                        color: var(--text-secondary); 
                        font-size: 13px; 
                        opacity: 0.7;
                    }
                    
                    /* Hide old loader */
                    .loading-container { display: none; }
                </style>
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
                                    <button id="diff-btn" class="button secondary">Show Diff</button>
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

                <script nonce="${nonce}">
                    (function() {
                        const vscode = acquireVsCodeApi();
                        let isOnline = false;
                        let currentTab = 'commands';
                        let loadingInterval = null;

                        marked.setOptions({ gfm: true, breaks: true });

                        const switchTab = (tabName) => {
                            currentTab = tabName;
                            document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.id === 'tab-'+tabName));
                            document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === tabName+'-tab'));
                        };

                        const runCommand = (command, params = {}) => {
                            vscode.postMessage({ type: 'runCommand', command, params });
                        };

                        const runTreeWithParams = () => {
                            const path = document.getElementById('tree-path').value;
                            runCommand('getTree', { path });
                        };

                        const runChangedWithParams = () => {
                            const base = document.getElementById('ref-base').value;
                            const head = document.getElementById('ref-head').value;
                            runCommand('getChanged', { base, head });
                        };

                        const runDiffWithParams = () => {
                            const base = document.getElementById('ref-base').value;
                            const head = document.getElementById('ref-head').value;
                            runCommand('getDiff', { base, head });
                        };

                        const startChat = () => {
                            vscode.postMessage({ type: 'startChat' });
                        };
                        
                        const reconnect = () => {
                             vscode.postMessage({ type: 'onLoad' });
                        };

                        const sendMessage = () => {
                            const input = document.getElementById('chat-input');
                            if (input.value.trim()) {
                                vscode.postMessage({ type: 'sendChatMessage', message: input.value.trim() });
                                input.value = '';
                            }
                        };

                        const clearMessages = (id) => {
                            const container = document.getElementById(id);
                            if (container) container.innerHTML = '<div class="placeholder">Cleared.</div>';
                        };

                        const setLoading = (isLoading) => {
                            const container = document.getElementById('chat-messages');
                            const existingLoader = document.getElementById('active-thinking');
                            
                            if (isLoading) {
                                if (!existingLoader) {
                                    const loaderDiv = document.createElement('div');
                                    loaderDiv.id = 'active-thinking';
                                    loaderDiv.className = 'thinking-bubble';
                                    
                                    loaderDiv.innerHTML = \`
                                        <div class="thinking-dots">
                                            <div class="dot"></div>
                                            <div class="dot"></div>
                                            <div class="dot"></div>
                                        </div>
                                        <div class="thinking-text">Thinking...</div>
                                    \`;
                                    
                                    container.appendChild(loaderDiv);
                                    container.scrollTop = container.scrollHeight;

                                    // Rotate text
                                    const words = ['Thinking...', 'Reviewing...', 'Analysing...', 'Tinkering...', 'Blending...', 'Making...', 'Mixing...'];
                                    let wordIndex = 0;
                                    const textEl = loaderDiv.querySelector('.thinking-text');
                                    
                                    if (loadingInterval) clearInterval(loadingInterval);
                                    
                                    loadingInterval = setInterval(() => {
                                        wordIndex = (wordIndex + 1) % words.length;
                                        // Fade out
                                        textEl.style.opacity = '0';
                                        setTimeout(() => {
                                            textEl.innerText = words[wordIndex];
                                            textEl.style.opacity = '1';
                                        }, 200);
                                    }, 2500);

                                } else {
                                     // Move to bottom
                                     container.appendChild(existingLoader);
                                }
                            } else {
                                if (existingLoader) {
                                    existingLoader.remove();
                                }
                                if (loadingInterval) {
                                    clearInterval(loadingInterval);
                                    loadingInterval = null;
                                }
                            }
                        };

                        // Event Listeners
                        document.getElementById('tab-commands').addEventListener('click', () => switchTab('commands'));
                        document.getElementById('tab-chat').addEventListener('click', () => switchTab('chat'));
                        
                        document.querySelectorAll('.collapsible').forEach(btn => {
                            btn.addEventListener('click', function() {
                                this.classList.toggle("active");
                                const content = this.nextElementSibling;
                                if (content) {
                                    content.style.display = content.style.display === "none" ? "block" : "none";
                                }
                            });
                        });

                        document.getElementById('review-btn').addEventListener('click', () => runCommand('review'));
                        document.getElementById('tree-btn').addEventListener('click', runTreeWithParams);
                        document.getElementById('changed-btn').addEventListener('click', runChangedWithParams);
                        document.getElementById('diff-btn').addEventListener('click', runDiffWithParams);
                        document.getElementById('status-btn').addEventListener('click', () => runCommand('status'));
                        document.getElementById('clear-output-btn').addEventListener('click', () => clearMessages('commands-output'));
                        document.getElementById('send-btn').addEventListener('click', sendMessage);
                        document.getElementById('new-session-btn').addEventListener('click', startChat);
                        document.getElementById('reconnect-btn').addEventListener('click', reconnect);


                        function addMessage(type, content, context) {
                            // If context is provided, use it to select container. 
                            // Fallback to current behavior command/chat split logic or user inference.
                            
                            let containerId;
                            if (context === 'chat') {
                                containerId = 'chat-messages';
                            } else if (context === 'command') {
                                containerId = 'commands-output';
                            } else {
                                // Legacy fallback
                                containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            }
                            
                            // User messages always go to Chat, just to be safe, if context wasn't passed correctly
                            if (type === 'user') containerId = 'chat-messages';

                            const container = document.getElementById(containerId);
                            if (!container) return;
                            
                            // If this is a historical restore (no setLoading needed if we are just bulk adding?)
                            // But usually addMessage is for live stuff too.
                            
                            if (type === 'user') {
                                // User message triggers loading, BUT we must append user message first
                            } else if (type === 'assistant' || type === 'system') {
                                setLoading(false);
                            } else if (type === 'tool') {
                                setLoading(false);
                            }

                            const placeholder = container.querySelector('.placeholder');
                            if (placeholder) placeholder.remove();

                            const div = document.createElement('div');
                            div.className = 'message ' + type;
                            
                            if (type === 'tool') {
                                div.innerHTML = "<span>Exec:</span> <code>" + content + "</code>";
                            } else if (type === 'assistant' || type === 'system') {
                                div.setAttribute('data-raw', content);
                                div.innerHTML = marked.parse(content);
                            } else {
                                div.innerText = content;
                            }
                            
                            container.appendChild(div);
                            container.scrollTop = container.scrollHeight;
                            
                            // Handle Loading State AFTER appending message
                            if (type === 'user') {
                                setLoading(true); // Now loader will be at bottom, AFTER user message
                            } else if (type === 'tool') {
                                setLoading(true); // Re-show loader after tool message
                            }
                        }

                        function appendToLastMessage(content, context) {
                            let containerId;
                            if (context === 'chat') {
                                containerId = 'chat-messages';
                            } else if (context === 'command') {
                                containerId = 'commands-output';
                            } else {
                                containerId = currentTab === 'chat' ? 'chat-messages' : 'commands-output';
                            }

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
                                addMessage('assistant', content, context);
                            }
                            container.scrollTop = container.scrollHeight;
                        }

                        window.addEventListener('message', event => {
                            const m = event.data;
                            switch (m.type) {
                                case 'addMessage':
                                    addMessage(m.messageType, m.content, m.context);
                                    break;
                                case 'appendToLastMessage':
                                    appendToLastMessage(m.content, m.context);
                                    break;
                                case 'setChatActive':
                                    isOnline = m.active;
                                    document.getElementById('chat-input').disabled = !isOnline;
                                    document.getElementById('send-btn').disabled = !isOnline;
                                    document.getElementById('status-dot').className = 'status-dot ' + (isOnline ? 'online' : 'offline');
                                    document.getElementById('status-text').innerText = isOnline ? 'Ready' : 'Offline';
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

                        vscode.postMessage({ type: 'onLoad' });
                    })();
                </script>
            </body>
            </html>`;
    }
}
exports.WebviewContent = WebviewContent;
//# sourceMappingURL=WebviewContent.js.map