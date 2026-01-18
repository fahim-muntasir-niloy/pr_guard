"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const vscode = require("vscode");
const util_1 = require("util");
const ServerManager_1 = require("./services/ServerManager");
const ApiClient_1 = require("./api/ApiClient");
const WebviewContent_1 = require("./view/WebviewContent");
class SidebarProvider {
    constructor(_extensionUri, _getCliCommand) {
        this._extensionUri = _extensionUri;
        this._getCliCommand = _getCliCommand;
        this._chatHistory = [];
        this._currentContext = 'chat';
        this._serverManager = new ServerManager_1.ServerManager(_getCliCommand, (type, msg) => this._addMessage(type, msg), () => this._setChatActive(true));
        this._apiClient = new ApiClient_1.ApiClient(this._serverManager.apiBaseUrl, {
            onMessage: (type, content) => this._addMessage(type, content),
            onAppend: (content) => this._appendToLastMessage(content)
        });
    }
    resolveWebviewView(webviewView, context, _token) {
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
                        }
                        else {
                            this._addMessage('system', '✅ Restored connection to PR Guard Server.');
                        }
                    }
                    break;
                }
                case 'runCommand': {
                    this._currentContext = 'command';
                    await this._runCommand(data.command, data.params);
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
        webviewView.webview.html = WebviewContent_1.WebviewContent.getHtml(webviewView.webview, this._extensionUri);
        this._serverManager.startServer();
    }
    revive(panel) {
        this._view = panel;
    }
    async restartServer() {
        await this._serverManager.restartServer();
    }
    async startServer() {
        await this._serverManager.startServer();
    }
    stopServer() {
        this._serverManager.stopServer();
    }
    async _runCommand(subCommand, params) {
        if (subCommand === 'review') {
            await this._apiClient.runReview();
            return;
        }
        if (subCommand === 'status') {
            await this._apiClient.runStatus();
            return;
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
    _addMessage(type, content) {
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
    _appendToLastMessage(content) {
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
    _clearMessages() {
        this._chatHistory = [];
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
    async _saveReport(content) {
        if (vscode.workspace.workspaceFolders) {
            const uri = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.joinPath(vscode.workspace.workspaceFolders[0].uri, 'pr-guard-report.md'),
                filters: {
                    'Markdown': ['md']
                }
            });
            if (uri) {
                await vscode.workspace.fs.writeFile(uri, new util_1.TextEncoder().encode(content));
                vscode.window.showInformationMessage('Report saved successfully!');
            }
        }
        else {
            vscode.window.showErrorMessage('Please open a workspace to save the report.');
        }
    }
}
exports.SidebarProvider = SidebarProvider;
//# sourceMappingURL=SidebarProvider.js.map