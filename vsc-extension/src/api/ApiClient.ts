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

            const statusText = `**Git Status**\n${gitInfo}\n\n**Configuration**\n- OpenAI API Key: ${data.openai_api_key}\n- LangSmith Tracing: ${data.langsmith_tracing ? 'Enabled' : 'Disabled'}`;

            this._callbacks.onMessage('assistant', statusText);
        } catch (error: any) {
            this._callbacks.onMessage('system', `❌ Error: ${error.message}`);
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
            let accumulatedData = '';

            this._callbacks.onMessage('assistant', 'Starting review...'); 

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

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
                                this._callbacks.onMessage('tool', data.name);
                            } else if (data.type === 'report') {
                                const reportHtml = this._formatReviewReport(data.content);
                                this._callbacks.onMessage('assistant', reportHtml);
                            } else if (data.type === 'status') {
                                this._callbacks.onMessage('system', data.message);
                            }
                        } catch (e) {
                            // Partial JSON
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
            let accumulatedData = '';
            let started = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

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
                                    this._callbacks.onMessage('assistant', data.content);
                                    started = true;
                                } else {
                                    this._callbacks.onAppend(data.content);
                                }
                            } else if (data.type === 'tool_call') {
                                this._callbacks.onMessage('tool', data.name);
                            }
                        } catch (e) {
                            // Partial JSON
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
            let md = `## AI Review Report\n\n`;
            md += `**Result:** ${report.event || 'COMPLETED'}\n\n`;
            md += `${report.body || ''}\n\n`;
            
            if (report.comments && Array.isArray(report.comments)) {
                md += `### Detailed Comments\n\n`;
                report.comments.forEach((c: any) => {
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
        } catch (e) {
            return JSON.stringify(content, null, 2);
        }
    }
}
