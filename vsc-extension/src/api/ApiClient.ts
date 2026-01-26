import { uuidv4 } from '../utils/common';

export class ApiClient {
    private _threadId?: string;

    constructor(
        private readonly _apiBaseUrl: string,
        private readonly _callbacks: {
            onMessage: (type: 'user' | 'assistant' | 'system' | 'tool', content: string) => void,
            onAppend: (content: string) => void
        }
    ) {
        this.resetThreadId();
    }

    public resetThreadId() {
        this._threadId = uuidv4();
    }

    public getThreadId() {
        return this._threadId;
    }

    public async runStatus() {
        this._callbacks.onMessage('system', '📊 Checking Status via API...');
        try {
            const response = await fetch(`${this._apiBaseUrl}/status`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json() as any;
            
            let gitInfo = '';
            if (typeof data.git === 'object') {
                gitInfo = `Branch: ${data.git.branch}\nLast Commit: ${data.git.last_commit}`;
            } else {
                gitInfo = data.git;
            }

            const statusText = `**Git Status**\n${gitInfo}\n\n**Configuration**\n- Provider: ${data.llm_provider}\n- Model: ${data.llm_model}\n- LangSmith Tracing: ${data.langsmith_tracing ? 'Enabled' : 'Disabled'}`;

            this._callbacks.onMessage('assistant', statusText);
            
            // Return raw data for webview to prepopulate settings
            return data;
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async updateConfig(params: any) {
        this._callbacks.onMessage('system', '⚙️ Updating Configuration via API...');
        try {
            const response = await fetch(`${this._apiBaseUrl}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            this._callbacks.onMessage('system', '✅ Configuration updated successfully.');
            this._callbacks.onMessage('assistant', 'Configuration saved! Please restart the server for changes to take effect.');
            
            return {
                success: true,
                message: 'Configuration updated successfully'
            };
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error mapping config: ${error.message}`);
            
            return {
                success: false,
                message: error.message
            };
        }
    }

    public async runTree(params: any) {
        const path = params?.path || '.';
        this._callbacks.onMessage('system', `🌲 Getting Project Tree for "${path}" via API...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/tree?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json() as any;
            
            this._callbacks.onMessage('assistant', `**Project Structure (${path})**\n\n\`\`\`\n${data.tree}\n\`\`\``);
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async runChanged(params: any) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._callbacks.onMessage('system', `📝 Listing changed files between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/changed?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json() as any;
            
            if (data.files && data.files.length > 0) {
                this._callbacks.onMessage('assistant', `**Changed Files (${base}...${head})**\n\n${data.files.map((f: string) => `- ${f}`).join('\n')}`);
            } else {
                this._callbacks.onMessage('assistant', `**Changed Files (${base}...${head})**\n\nNo changes found.`);
            }
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async runDiff(params: any) {
        const base = params?.base || 'master';
        const head = params?.head || 'HEAD';
        this._callbacks.onMessage('system', `🔍 Getting diff between ${base} and ${head}...`);
        try {
            const response = await fetch(`${this._apiBaseUrl}/diff?base=${encodeURIComponent(base)}&head=${encodeURIComponent(head)}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            const data = await response.json() as any;
            
            this._callbacks.onMessage('assistant', `**Diff (${base}...${head})**\n\n\`\`\`diff\n${data.diff}\n\`\`\``);
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async runReview() {
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
                if (done) break;

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
                            } else if (data.type === 'report') {
                                const reportHtml = this._formatReviewReport(data.content);
                                this._callbacks.onMessage('assistant', reportHtml);
                            } else if (data.type === 'status') {
                                this._callbacks.onMessage('system', data.message);
                            } else if (data.type === 'error') {
                                this._callbacks.onMessage('system', `❌ AI Error: ${data.content}`);
                            }
                        } catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
            this._callbacks.onMessage('system', '✅ Review completed.');
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async sendChat(message: string) {
        if (!message) return;

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
                if (done) break;

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
                                } else {
                                    this._callbacks.onAppend(data.content);
                                }
                            } else if (data.type === 'tool_call') {
                                const toolPayload = JSON.stringify({ 
                                    name: data.name, 
                                    args: data.args || {} 
                                });
                                this._callbacks.onMessage('tool', toolPayload);
                            } else if (data.type === 'error') {
                                this._callbacks.onMessage('system', `❌ AI Error: ${data.content}`);
                            }
                        } catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    public async createOneClickPR(userInstructions: string, base: string = 'master', head: string = 'HEAD') {
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
                if (done) break;

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
                                } else {
                                    this._callbacks.onAppend(data.content);
                                }
                            } else if (data.type === 'tool_call') {
                                const toolPayload = JSON.stringify({ 
                                    name: data.name, 
                                    args: data.args || {} 
                                });
                                this._callbacks.onMessage('tool', toolPayload);
                            } else if (data.type === 'error') {
                                this._callbacks.onMessage('system', `❌ AI Error: ${data.content}`);
                            }
                        } catch (e) {
                            // Invalid JSON
                        }
                    }
                }
            }
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
        }
    }

    private _formatReviewReport(content: any): string {
        if (typeof content === 'string') return content;

        try {
            const report = content;
            let md = `# 🤖 AI Code Review Report\n\n`;
            md += `## 📊 Summary\n\n`;
            md += `**Status:** ${report.event || 'COMPLETED'}\n\n`;
            md += `${report.body || 'Review completed successfully.'}\n\n`;

            if (report.comments && Array.isArray(report.comments) && report.comments.length > 0) {
                md += `## 🔍 Detailed Findings\n\n`;
                report.comments.forEach((c: any, index: number) => {
                    const severityIcon = c.severity === 'error' ? '❌' : c.severity === 'warning' ? '⚠️' : 'ℹ️';
                    md += `### ${index + 1}. ${severityIcon} ${c.path} (line ${c.position})\n\n`;
                    md += `**Severity:** ${c.severity || 'info'}\n\n`;
                    md += `${c.body}\n\n`;
                    if (c.suggestion) {
                        md += `**💡 Suggested Fix:**\n\`\`\`\n${c.suggestion}\n\`\`\`\n\n`;
                    }
                    md += `---\n\n`;
                });
            } else {
                md += `## ✅ No Issues Found\n\n`;
                md += `Great job! No critical issues were identified in this review.\n\n`;
            }

            md += `---\n\n*Generated by PR Guard AI Assistant*`;
            return md;
        } catch (e) {
            return `## 🤖 AI Review Report\n\n${JSON.stringify(content, null, 2)}`;
        }
    }
}
