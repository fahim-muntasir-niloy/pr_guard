import * as vscode from 'vscode';
import * as cp from 'child_process';

export class ServerManager {
    private _serverProcess?: cp.ChildProcess;
    private _isServerStarting = false;
    public readonly apiBaseUrl = 'http://127.0.0.1:8900';

    constructor(
        private readonly _getCliCommand: () => Promise<string | null>,
        private readonly _onMessage: (type: 'system', message: string) => void,
        private readonly _onReady: () => void
    ) {}

    public async restartServer() {
        await this.stopServer();
        // Give it a moment to release resources
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.startServer();
    }

    public stopServer() {
        if (this._serverProcess) {
            this._serverProcess.kill();
            this._serverProcess = undefined;
        }
    }

    public get isRunning(): boolean {
        return !!this._serverProcess;
    }

    public async startServer() {

        if (this._serverProcess || this._isServerStarting) {
            return;
        }

        this._isServerStarting = true;

        // Ensure port 8000 is free before starting
        try {
            await this._killPort(8000);
        } catch(e) {
            // Ignore if we couldn't kill or nothing was running
        }

        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceFolder) {
            this._onMessage('system', '❌ Error: No workspace folder open.');
            this._isServerStarting = false;
            return;
        }

        const commandBase = await this._getCliCommand();
        if (!commandBase) {
            this._onMessage('system', '❌ Error: pr-guard command not found.');
            this._isServerStarting = false;
            return;
        }

        // Create the full command string
        // Force port 8000 to be explicit
        let fullCommand = `${commandBase} serve --port 8000`.trim();
        
        // On Windows, if the command has spaces or quotes, PowerShell needs the call operator '&'
        if (process.platform === 'win32') {
            const needsCallOperator = commandBase.includes(' ') || commandBase.includes('"') || commandBase.includes("'");
            if (needsCallOperator && !fullCommand.startsWith('&')) {
                // Wrap in quotes if not already and prepend &
                const quotedCmd = commandBase.startsWith('"') ? commandBase : `"${commandBase}"`;
                fullCommand = `& ${quotedCmd} serve --port 8000`;
            }
        }
        
        const shellStr = process.platform === 'win32' ? await this._getBestShell() : true;

        this._onMessage('system', `🚀 Starting PR Guard Server...`);

        const child = cp.spawn(fullCommand, [], {
            cwd: workspaceFolder,
            shell: shellStr,
            env: { ...process.env, FORCE_COLOR: '0', PYTHONIOENCODING: 'utf-8' },
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
                this._onMessage('system', `⚠️ Server: ${errOutput.substring(0, 100)}...`);
            }
        });

        child.on('error', (err) => {
            this._onMessage('system', `❌ Failed to spawn server: ${err.message}`);
        });

        child.on('close', (code) => {
            console.log(`Server process exited with code ${code}`);
            this._serverProcess = undefined;
            // Only set starting to false here if we haven't succeeded yet
            if (this._isServerStarting) {
                this._isServerStarting = false;
                this._onMessage('system', `⚠️ Server stopped (Code ${code}).`);
            }
        });

        // Wait for server to be ready
        let attempts = 0;
        const maxAttempts = 15;
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/status`);
                if (response.ok) {
                    this._onMessage('system', '✅ PR Guard Server is ready!');
                    this._isServerStarting = false;
                    this._onReady();
                    return;
                }
            } catch (e) {
                // Not ready yet
            }
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        this._onMessage('system', '❌ Failed to connect to PR Guard Server after startup.');
        this._isServerStarting = false;
    }

    private async _killPort(port: number): Promise<void> {
        return new Promise((resolve) => {
            const cmd = process.platform === 'win32' 
                ? `netstat -ano | findstr :${port}`
                : `lsof -i :${port} -t`;
            
            cp.exec(cmd, (err, stdout) => {
                if (err || !stdout) {
                    resolve(); // Nothing to kill
                    return;
                }

                const pids = new Set<string>();
                if (process.platform === 'win32') {
                    stdout.split('\n').forEach(line => {
                        const parts = line.trim().split(/\s+/);
                        // Protocol Local Address Foreign Address State PID
                        const pid = parts[parts.length - 1];
                        if (pid && /^\d+$/.test(pid) && pid !== '0') {
                            pids.add(pid);
                        }
                    });
                } else {
                    stdout.split('\n').forEach(pid => {
                        if (pid.trim()) pids.add(pid.trim());
                    });
                }

                if (pids.size === 0) {
                    resolve();
                    return;
                }

                const killCmd = process.platform === 'win32'
                    ? `taskkill /F /PID ${Array.from(pids).join(' /PID ')}`
                    : `kill -9 ${Array.from(pids).join(' ')}`;
                
                cp.exec(killCmd, () => resolve());
            });
        });
    }

    private async _getBestShell(): Promise<string | boolean> {
        if (process.platform !== 'win32') return true;
        
        return new Promise((resolve) => {
            cp.exec('pwsh -Command "$PSVersionTable.PSVersion.Major"', (err) => {
                if (!err) {
                    resolve('pwsh.exe');
                } else {
                    resolve('powershell.exe');
                }
            });
        });
    }
}
