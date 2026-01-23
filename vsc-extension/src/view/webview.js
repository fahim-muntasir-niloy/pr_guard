(function() {
    const vscode = acquireVsCodeApi();
    let isOnline = false;
    let currentTab = 'commands';
    let loadingInterval = null;

    marked.setOptions({ gfm: true, breaks: true });

    const switchTab = (tabName) => {
        currentTab = tabName;
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.id === 'tab-' + tabName));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === tabName + '-tab'));
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

    const runOneClickPRWithParams = () => {
        const userInstructions = document.getElementById('pr-instructions').value;
        const base = document.getElementById('pr-base').value;
        const head = document.getElementById('pr-head').value;

        // Show loader
        const btn = document.getElementById('one-click-pr-btn');
        const loader = btn.querySelector('.btn-loader');
        const text = btn.querySelector('.btn-text');
        
        btn.disabled = true;
        loader.classList.remove('hidden');
        text.style.opacity = '0.5';

        runCommand('oneClickPR', { userInstructions, base, head });
    };

    const saveSettings = () => {
        const provider = document.getElementById('settings-provider').value;
        const model = document.getElementById('settings-model').value;
        const key = document.getElementById('settings-key').value;
        console.log(provider)
        if(!provider || !model || !key) {
            const response = document.getElementById('save-settings-response');
            response.innerText = 'Provider, Model Name & API Key are required.';
            response.style.color = 'red';
            return;
        }

        const params = {
            llm_provider: provider,
            llm_model: model
        };

        // Map provider to specific key field
        if (key) {
            if (provider === 'openai') params.openai_api_key = key;
            else if (provider === 'xai') params.xai_api_key = key;
            else if (provider === 'anthropic') params.anthropic_api_key = key;
            else if (provider === 'google_genai') params.google_api_key = key;
        }

        vscode.postMessage({ type: 'runCommand', command: 'updateConfig', params });
        
        const saveBtn = document.getElementById('save-settings-btn');
        saveBtn.innerText = 'Saving...';
        saveBtn.disabled = true;
        
        setTimeout(() => {
            saveBtn.innerText = 'Save Settings';
            saveBtn.disabled = false;
        }, 2000);
    };

    const toggleKeyVisibility = () => {
        const keyInput = document.getElementById('settings-key');
        const icon = document.querySelector('#toggle-key-visibility i');
        if (keyInput.type === 'password') {
            keyInput.type = 'text';
            icon.classList.replace('codicon-eye', 'codicon-eye-closed');
        } else {
            keyInput.type = 'password';
            icon.classList.replace('codicon-eye-closed', 'codicon-eye');
        }
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

                loaderDiv.innerHTML = `
                    <div class="thinking-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                    <div class="thinking-text">Thinking...</div>
                `;

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

    const updateBranchSelects = (branches) => {
        const base = document.getElementById('pr-base');
        const head = document.getElementById('pr-head');
        
        // Preserve current selections if possible
        const baseVal = base.value;
        const headVal = head.value;

        [base, head].forEach(sel => {
            sel.innerHTML = '';
            // Add HEAD option manually for head branch selection (common use case)
            if (sel.id === 'pr-head') {
                 const optHead = document.createElement('option');
                 optHead.value = 'HEAD';
                 optHead.innerText = 'HEAD (Current)';
                 sel.appendChild(optHead);
            }

            branches.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.innerText = b;
                sel.appendChild(opt);
            });
        });

        if (baseVal && Array.from(base.options).some(o => o.value === baseVal)) base.value = baseVal;
        else {
            if (branches.includes('main')) base.value = 'main';
            else if (branches.includes('master')) base.value = 'master';
        }

         if (headVal && Array.from(head.options).some(o => o.value === headVal)) head.value = headVal;
    };

    const loadBranches = async () => {
        try {
            const res = await fetch('http://127.0.0.1:8000/branches');
            if (res.ok) {
                const data = await res.json();
                if (data.branches) {
                    updateBranchSelects(data.branches);
                }
            }
        } catch (e) {
            console.log('Server not ready for branches yet', e);
        }
    };

    // Event Listeners
    document.getElementById('tab-commands').addEventListener('click', () => switchTab('commands'));
    document.getElementById('tab-chat').addEventListener('click', () => switchTab('chat'));
    document.getElementById('tab-settings').addEventListener('click', () => {
        switchTab('settings');
        // Fetch current status to prepopulate settings
        runCommand('status');
    });

    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', function() {
            this.parentElement.classList.toggle("active");
        });
    });

    document.getElementById('one-click-pr-btn').addEventListener('click', runOneClickPRWithParams);
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
    window.addEventListener('message', event => {
    const msg = event.data;
    console.log('Received message:', msg);
        if (msg.type === 'commandResponse' && msg.command === 'updateConfig') {
            const response = document.getElementById('save-settings-response');
            response.innerText = msg.data.message;
            response.style.color = msg.data.success ? 'green' : 'red';
            
            setTimeout(() => {
                response.innerText = '';
            }, 2000);
        }
    });
    document.getElementById('toggle-key-visibility').addEventListener('click', toggleKeyVisibility);
    document.getElementById('clear-output-btn').addEventListener('click', () => clearMessages('commands-output'));
    document.getElementById('system-status-btn').addEventListener('click', () => runCommand('status'));
    document.getElementById('save-report-btn').addEventListener('click', () => {
        const reportMessages = document.querySelectorAll('#commands-output .message.assistant');
        const reportContent = Array.from(reportMessages).map(msg => msg.getAttribute('data-raw')).join('\n\n');
        vscode.postMessage({ type: 'saveReport', content: reportContent });
    });
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('new-session-btn').addEventListener('click', startChat);
    document.getElementById('reconnect-btn').addEventListener('click', reconnect);
    
    const refreshBtn = document.getElementById('refresh-branches');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loadBranches();
        });
    }

    // Initial load
    setTimeout(loadBranches, 1000); // Wait a sec for server to potentially start
    setInterval(loadBranches, 10000); // Poll occasionally

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
        } else if (type === 'assistant') {
            setLoading(false);
            // Reset PR button state when assistant starts responding
            const btn = document.getElementById('one-click-pr-btn');
            const loader = btn.querySelector('.btn-loader');
            const text = btn.querySelector('.btn-text');
            btn.disabled = false;
            loader.classList.add('hidden');
            text.style.opacity = '1';
        } else if (type === 'system') {
            setLoading(false);
            // Only reset PR button on errors or completion messages
            if (content.includes('Error') || content.includes('completed') || content.includes('success')) {
                const btn = document.getElementById('one-click-pr-btn');
                const loader = btn.querySelector('.btn-loader');
                const text = btn.querySelector('.btn-text');
                btn.disabled = false;
                loader.classList.add('hidden');
                text.style.opacity = '1';
            }
        } else if (type === 'tool') {
            setLoading(false);
        }

        const placeholder = container.querySelector('.placeholder');
        if (placeholder) placeholder.remove();

        const div = document.createElement('div');
        div.className = 'message ' + type;

        if (type === 'tool') {
            // Map common tools to nice icons
            const toolMap = {
                'execute_git_operations': { icon: 'git-branch', label: 'Git Operation' },
                'execute_github_command': { icon: 'github', label: 'GitHub CLI' },
                'read_file_cat': { icon: 'file-code', label: 'Read File' },
                'list_files_tree': { icon: 'list-tree', label: 'List Files' },
                'search_code_grep': { icon: 'search', label: 'Search Code' },
                'get_diff_of_single_file': { icon: 'diff', label: 'Diff File' },
                'default': { icon: 'tools', label: 'Tool Call' }
            };

            // Content is now a JSON string: { name: "ToolName", args: {...} }
            let toolName = 'Unknown';
            let toolArgsObj = {};
            let toolArgsPretty = '{}';

            try {
                const payload = JSON.parse(content);
                toolName = payload.name || 'Unknown';
                toolArgsObj = payload.args || {};
                toolArgsPretty = JSON.stringify(toolArgsObj, null, 2);
            } catch (e) {
                // Fallback for legacy format or error
                toolName = 'Error parsing tool';
                toolArgsPretty = content;
            }

            const info = toolMap[toolName] || toolMap['default'];
            
            div.innerHTML = `
                <div class="tool-card">
                    <div class="tool-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <div class="tool-icon"><i class="codicon codicon-${info.icon}"></i></div>
                        <div class="tool-info-row" style="flex:1; display:flex; align-items:baseline; gap:8px; overflow:hidden;">
                            <div class="tool-name">${info.label}</div>
                            <div class="tool-summary-text" style="font-family:monospace; font-size:10px; color:var(--text-secondary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; opacity: 0.7;">
                                ${toolName}
                            </div>
                        </div>
                        <div class="tool-status">
                            <i class="codicon codicon-chevron-right tool-toggle-icon"></i>
                        </div>
                    </div>
                    <div class="tool-details">
                        <div class="tool-args-block">${toolArgsPretty}</div>
                    </div>
                </div>
            `;
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
        for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].classList.contains('assistant')) {
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
                if (isOnline) loadBranches();
                break;
            case 'updateSettings':
                if (m.config) {
                    document.getElementById('settings-provider').value = m.config.llm_provider || 'openai';
                    document.getElementById('settings-model').value = m.config.llm_model || '';
                    // We don't populate keys for security, but we show masked key in info if needed
                }
                break;
            case 'clearMessages':
                clearMessages('commands-output');
                clearMessages('chat-messages');
                break;
        }
    });

    document.getElementById('chat-input').addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });

    vscode.postMessage({ type: 'onLoad' });
})();