import * as vscode from 'vscode';
import { TextEncoder } from 'util';
import { ServerManager } from './services/ServerManager';
import { ApiClient } from './api/ApiClient';
import { WebviewContent } from './view/WebviewContent';

export class SidebarProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    private _serverManager: ServerManager;
    private _apiClient: ApiClient;

    private _chatHistory: Array<{type: string, content: string, context: string}> = [];
    private _currentContext: 'chat' | 'command' = 'chat';

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _getCliCommand: () => Promise<string | null>
    ) {
        this._serverManager = new ServerManager(
            _getCliCommand,
            (type, msg) => this._addMessage(type, msg),
            () => this._setChatActive(true)
        );

        this._apiClient = new ApiClient(
            this._serverManager.apiBaseUrl,
            {
                onMessage: (type, content) => this._addMessage(type as any, content),
                onAppend: (content) => this._appendToLastMessage(content)
            }
        );
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };

        const eventListener = webviewView.webview.onDidReceiveMessage(async (data) => {
            console.log('Received message from webview:', data);
            switch (data.type) {
                case 'onLoad': {
                    if (this._serverManager.isRunning) {
                        this._setChatActive(true);
                        // Restore history
                        if (this._chatHistory.length > 0) {
                             // If the last context was chat, switch to it? 
                             // Or just restore messages to their respective places.
                             // For now, let's just restore data. The webview stays on default tab unless we switch it.
                             
                             for (const msg of this._chatHistory) {
                                 webviewView.webview.postMessage({
                                     type: 'addMessage',
                                     messageType: msg.type,
                                     content: msg.content,
                                     context: msg.context
                                 });
                             }
                        } else {
                            this._addMessage('system', '✅ Restored connection to PR Guard Server.');
                        }
                    }
                    break;
                }
                case 'runCommand': {
                    this._currentContext = 'command';
                    var result = await this._runCommand(data.command, data.params);
                    
                    webviewView.webview.postMessage({
                        type: 'commandResponse',
                        command: data.command,
                        data: result
                    });
                    
                    break;
                }
                case 'clearOutput': {
                    this._clearMessages();
                    break;
                }
                case 'startChat': {
                    this._currentContext = 'chat';
                    this._apiClient.resetThreadId();
                    this._clearMessages();
                    this._addMessage('system', '🆕 New chat session started.');
                    this._setChatActive(true);
                    break;
                }
                case 'sendChatMessage': {
                    this._currentContext = 'chat';
                    await this._apiClient.sendChat(data.message);
                    break;
                }
                case 'stopChat': {
                    this._setChatActive(false);
                    break;
                }
                case 'saveReport': {
                    this._saveReport(data.content);
                    break;
                }
            }
        });

        webviewView.webview.html = WebviewContent.getHtml(webviewView.webview, this._extensionUri);
        this._serverManager.startServer();
    }

    public revive(panel: vscode.WebviewView) {
        this._view = panel;
    }

    public async restartServer() {
        await this._serverManager.restartServer();
    }

    public async startServer() {
        await this._serverManager.startServer();
    }

    public stopServer() {
        this._serverManager.stopServer();
    }

    private async _runCommand(subCommand: string, params: any) {
        if (subCommand === 'review') {
            await this._apiClient.runReview();
            return;
        }
        if (subCommand === 'status') {
            const config = await this._apiClient.runStatus();
            if (config && this._view) {
                this._view.webview.postMessage({
                    type: 'updateSettings',
                    config
                });
            }
            return;
        }
        if (subCommand === 'updateConfig') {
            const result = await this._apiClient.updateConfig(params);
            return result;
        }
        if (subCommand === 'getTree') {
            await this._apiClient.runTree(params);
            return;
        }
        if (subCommand === 'getChanged') {
            await this._apiClient.runChanged(params);
            return;
        }
        if (subCommand === 'getDiff') {
            await this._apiClient.runDiff(params);
            return;
        }
        if (subCommand === 'oneClickPR') {
            await this._apiClient.createOneClickPR(params.userInstructions, params.base, params.head);
            return;
        }

        console.log(`Running generic command: ${subCommand}`);
    }

    private _addMessage(type: 'user' | 'assistant' | 'system' | 'tool', content: string) {
        // Store in history
        this._chatHistory.push({ type, content, context: this._currentContext });

        if (this._view) {
            this._view.webview.postMessage({
                type: 'addMessage',
                messageType: type,
                content: content,
                context: this._currentContext
            });
        }
    }

    private _appendToLastMessage(content: string) {
        // Update history
        if (this._chatHistory.length > 0) {
            this._chatHistory[this._chatHistory.length - 1].content += content;
        }

        if (this._view) {
            this._view.webview.postMessage({
                type: 'appendToLastMessage',
                content: content,
                context: this._currentContext
            });
        }
    }

    private _clearMessages() {
        this._chatHistory = [];
        if (this._view) {
            this._view.webview.postMessage({
                type: 'clearMessages'
            });
        }
    }

    private _setChatActive(active: boolean) {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'setChatActive',
                active: active
            });
        }
    }

    private async _saveReport(content: string) {
        if (vscode.workspace.workspaceFolders) {
            const uri = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.joinPath(vscode.workspace.workspaceFolders[0].uri, 'pr-guard-report.md'),
                filters: {
                    'Markdown': ['md']
                }
            });

            if (uri) {
                await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(content));
                vscode.window.showInformationMessage('Report saved successfully!');
            }
        } else {
            vscode.window.showErrorMessage('Please open a workspace to save the report.');
        }
    }
}
