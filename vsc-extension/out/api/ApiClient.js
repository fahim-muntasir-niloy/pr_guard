"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApiClient = void 0;
const common_1 = require("../utils/common");
class ApiClient {
    constructor(_apiBaseUrl, _callbacks) {
        this._apiBaseUrl = _apiBaseUrl;
        this._callbacks = _callbacks;
        this.resetThreadId();
    }
    resetThreadId() {
        this._threadId = (0, common_1.uuidv4)();
    }
    getThreadId() {
        return this._threadId;
    }
    async runStatus() {
        this._callbacks.onMessage('system', '📊 Checking Status via API...');
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
            this._callbacks.onMessage('assistant', statusText);
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async runTree(params) {
        const path = params?.path || '.';
        this._callbacks.onMessage('system', `🌲 Getting Project Tree for "${path}" via API...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/tree?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            this._callbacks.onMessage('assistant', `**Project Structure (${path})**\n\n\`\`\`\n${data.tree}\n\`\`\``);
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async runChanged(params) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._callbacks.onMessage('system', `📝 Listing changed files between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/changed?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            if (data.files && data.files.length > 0) {
                this._callbacks.onMessage('assistant', `**Changed Files (${base}...${head})**\n\n${data.files.map((f) => `- ${f}`).join('\n')}`);
            }
            else {
                this._callbacks.onMessage('assistant', `**Changed Files (${base}...${head})**\n\nNo changes found.`);
            }
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async runDiff(params) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._callbacks.onMessage('system', `🔍 Getting diff between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/diff?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json();
            this._callbacks.onMessage('assistant', `**Diff (${base}...${head})**\n\n\`\`\`diff\n${data.diff}\n\`\`\``);
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async runReview() {
        this._callbacks.onMessage('system', '🤖 Starting AI Review via API...');
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
            let buffer = '';
            this._callbacks.onMessage('assistant', 'Starting review...');
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                let endIndex;
                while ((endIndex = buffer.indexOf('\n\n')) !== -1) {
                    const message = buffer.substring(0, endIndex);
                    buffer = buffer.substring(endIndex + 2);
                    if (message.startsWith('data: ')) {
                        const dataStr = message.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'tool_call') {
                                const toolPayload = JSON.stringify({
                                    name: data.name,
                                    args: data.args || {}
                                });
                                this._callbacks.onMessage('tool', toolPayload);
                            }
                            else if (data.type === 'report') {
                                const reportHtml = this._formatReviewReport(data.content);
                                this._callbacks.onMessage('assistant', reportHtml);
                            }
                            else if (data.type === 'status') {
                                this._callbacks.onMessage('system', data.message);
                            }
                        }
                        catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
            this._callbacks.onMessage('system', '✅ Review completed.');
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async sendChat(message) {
        if (!message)
            return;
        this._callbacks.onMessage('user', message);
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
            let buffer = '';
            let started = false;
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                let endIndex;
                while ((endIndex = buffer.indexOf('\n\n')) !== -1) {
                    const message = buffer.substring(0, endIndex);
                    buffer = buffer.substring(endIndex + 2);
                    if (message.startsWith('data: ')) {
                        const dataStr = message.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'token') {
                                if (!started) {
                                    this._callbacks.onMessage('assistant', data.content);
                                    started = true;
                                }
                                else {
                                    this._callbacks.onAppend(data.content);
                                }
                            }
                            else if (data.type === 'tool_call') {
                                const toolPayload = JSON.stringify({
                                    name: data.name,
                                    args: data.args || {}
                                });
                                this._callbacks.onMessage('tool', toolPayload);
                            }
                        }
                        catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    async createOneClickPR(userInstructions, base = 'master', head = 'HEAD') {
        this._callbacks.onMessage('system', '🚀 Creating one-click PR via API...');
        try {
            const response = await fetch(`${this._apiBaseUrl}/one-click-pr`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_instructions: userInstructions,
                    base,
                    head
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
            let buffer = '';
            let started = false;
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                let endIndex;
                while ((endIndex = buffer.indexOf('\n\n')) !== -1) {
                    const message = buffer.substring(0, endIndex);
                    buffer = buffer.substring(endIndex + 2);
                    if (message.startsWith('data: ')) {
                        const dataStr = message.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'token') {
                                if (!started) {
                                    this._callbacks.onMessage('assistant', data.content);
                                    started = true;
                                }
                                else {
                                    this._callbacks.onAppend(data.content);
                                }
                            }
                            else if (data.type === 'tool_call') {
                                const toolPayload = JSON.stringify({
                                    name: data.name,
                                    args: data.args || {}
                                });
                                this._callbacks.onMessage('tool', toolPayload);
                            }
                        }
                        catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
        }
        catch (error) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }
    _formatReviewReport(content) {
        if (typeof content === 'string')
            return content;
        try {
            const report = content;
            let md = `# 🤖 AI Code Review Report\n\n`;
            md += `## 📊 Summary\n\n`;
            md += `**Status:** ${report.event || 'COMPLETED'}\n\n`;
            md += `${report.body || 'Review completed successfully.'}\n\n`;
            if (report.comments && Array.isArray(report.comments) && report.comments.length > 0) {
                md += `## 🔍 Detailed Findings\n\n`;
                report.comments.forEach((c, index) => {
                    const severityIcon = c.severity === 'error' ? '❌' : c.severity === 'warning' ? '⚠️' : 'ℹ️';
                    md += `### ${index + 1}. ${severityIcon} ${c.path} (line ${c.position})\n\n`;
                    md += `**Severity:** ${c.severity || 'info'}\n\n`;
                    md += `${c.body}\n\n`;
                    if (c.suggestion) {
                        md += `**💡 Suggested Fix:**\n\`\`\`\n${c.suggestion}\n\`\`\`\n\n`;
                    }
                    md += `---\n\n`;
                });
            }
            else {
                md += `## ✅ No Issues Found\n\n`;
                md += `Great job! No critical issues were identified in this review.\n\n`;
            }
            md += `---\n\n*Generated by PR Guard AI Assistant*`;
            return md;
        }
        catch (e) {
            return `## 🤖 AI Review Report\n\n${JSON.stringify(content, null, 2)}`;
        }
    }
}
exports.ApiClient = ApiClient;
//# sourceMappingURL=ApiClient.js.map