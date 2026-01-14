"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const webviewContent_1 = require("./webviewContent");
const SidebarProvider_1 = require("./SidebarProvider");
let outputChannel;
let sidebarProvider;
function activate(context) {
    console.log('PR Guard Extension is now active!');
    outputChannel = vscode.window.createOutputChannel("PR Guard");
    context.subscriptions.push(outputChannel);
    // Register Sidebar Provider
    sidebarProvider = new SidebarProvider_1.SidebarProvider(context.extensionUri, getCliCommand);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider("pr-guard.sidebarView", sidebarProvider));
    // Command: Review
    let reviewDisposable = vscode.commands.registerCommand('pr-guard.review', async () => {
        const panel = vscode.window.createWebviewPanel('prGuardReview', 'PR Guard Review', vscode.ViewColumn.One, { enableScripts: true });
        panel.webview.html = (0, webviewContent_1.getWebviewContent)("", true);
        const commandBase = await getCliCommand();
        if (!commandBase) {
            panel.webview.html = (0, webviewContent_1.getWebviewContent)("Error: Could not determine PR Guard command.", false);
            return;
        }
        const fullCommand = `${commandBase} review --plain`.trim();
        const finalCommand = (process.platform === 'win32' && fullCommand.startsWith('"'))
            ? `& ${fullCommand}`
            : fullCommand;
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder open.');
            panel.webview.html = (0, webviewContent_1.getWebviewContent)("Error: No workspace folder open.", false);
            return;
        }
        cp.exec(finalCommand, {
            cwd: workspaceFolder,
            shell: process.platform === 'win32' ? 'powershell.exe' : '/bin/sh'
        }, (err, stdout, stderr) => {
            if (err) {
                vscode.window.showErrorMessage(`PR Guard error: ${err.message}`);
                panel.webview.html = (0, webviewContent_1.getWebviewContent)(`### Error\n\n\`\`\`\n${stderr || err.message}\n\`\`\``, false);
                return;
            }
            panel.webview.html = (0, webviewContent_1.getWebviewContent)(stdout, false);
        });
    });
    // Command: Status
    let statusDisposable = vscode.commands.registerCommand('pr-guard.status', async () => {
        runCommandInOutputChannel('status', 'Checking Status...');
    });
    context.subscriptions.push(reviewDisposable);
    context.subscriptions.push(statusDisposable);
}
function deactivate() {
    if (sidebarProvider) {
        sidebarProvider.stopServer();
    }
}
async function runCommandInOutputChannel(subcommand, startMessage) {
    outputChannel.show();
    outputChannel.appendLine(startMessage);
    const commandBase = await getCliCommand();
    if (!commandBase) {
        outputChannel.appendLine("Error: Could not determine how to run PR Guard. Please install it or configure 'prGuard.executablePath' in settings.");
        return;
    }
    const fullCommand = `${commandBase} ${subcommand}`.trim();
    const finalCommand = (process.platform === 'win32' && fullCommand.startsWith('"'))
        ? `& ${fullCommand}`
        : fullCommand;
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder open.');
        return;
    }
    outputChannel.appendLine(`Executing: ${finalCommand}`);
    cp.exec(finalCommand, {
        cwd: workspaceFolder,
        shell: process.platform === 'win32' ? 'powershell.exe' : '/bin/sh'
    }, (err, stdout, stderr) => {
        if (err) {
            outputChannel.appendLine(`Error: ${err.message}`);
            if (stderr)
                outputChannel.appendLine(stderr);
            return;
        }
        if (stdout)
            outputChannel.append(stdout);
        outputChannel.appendLine("Done.");
    });
}
async function getCliCommand() {
    const config = vscode.workspace.getConfiguration('prGuard');
    const os = require('os');
    // User overrides
    const executablePath = config.get('executablePath');
    let commandBase = '';
    // 1. Explicit 'pr-guard' executable configuration
    if (executablePath && executablePath.trim().length > 0) {
        commandBase = `"${executablePath}"`;
    }
    // 2. Check workspace-local .venv (Windows)
    if (!commandBase && process.platform === 'win32') {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders) {
            const fs = require('fs');
            const localPath = path.join(workspaceFolders[0].uri.fsPath, '.venv', 'Scripts', 'pr-guard.exe');
            if (fs.existsSync(localPath)) {
                commandBase = `"${localPath}"`;
            }
        }
    }
    // 3. Check standard installation location (Windows)
    if (!commandBase && process.platform === 'win32') {
        const homeDir = os.homedir();
        const standardPath = path.join(homeDir, '.pr_guard', '.venv', 'Scripts', 'pr-guard.exe');
        const fs = require('fs');
        if (fs.existsSync(standardPath)) {
            commandBase = `"${standardPath}"`;
        }
    }
    // 4. Fallback: try global command
    if (!commandBase && await checkCommand(process.platform === 'win32' ? 'powershell -Command "pr-guard --version"' : 'pr-guard --version')) {
        commandBase = 'pr-guard';
    }
    // 5. Fallback: try as Python module
    if (!commandBase && await checkCommand('python -m pr_guard --version')) {
        commandBase = 'python -m pr_guard';
    }
    // 5. Last resort: return null to show error
    if (!commandBase) {
        return null;
    }
    // Return the base command
    return commandBase;
}
function checkCommand(cmd) {
    return new Promise((resolve) => {
        cp.exec(cmd, (err) => {
            resolve(!err);
        });
    });
}
//# sourceMappingURL=extension.js.map