# PR Guard Installer for Windows
$ErrorActionPreference = "Stop"

Write-Host "🛡️  PR Guard: AI-Powered PR Reviewer" -ForegroundColor Cyan
Write-Host "---------------------------------------"

# 1. Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.12+ first." -ForegroundColor Red
    return
}

# 2. Check for UV
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing UV (Modern Python Package Manager)..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH += ";$HOME\.cargo\bin"
}

# 2.5 Check for Node.js (required for VS Code extension)
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Node.js not found. Installing Node.js..." -ForegroundColor Yellow
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        winget install OpenJS.NodeJS --source winget --accept-package-agreements --accept-source-agreements
        # Refresh common paths for Node
        $env:PATH += ";C:\Program Files\nodejs"
    } else {
        Write-Host "⚠️  winget not found. Please install Node.js manually to use the VS Code extension." -ForegroundColor Yellow
    }
}

# 3. Clone or Update
$InstallDir = "$HOME\.pr_guard"
if (Test-Path $InstallDir) {
    Write-Host "🔄 Updating existing installation in $InstallDir..." -ForegroundColor Yellow
    cd $InstallDir
    git pull
} else {
    Write-Host "📥 Cloning PR Guard into $InstallDir..." -ForegroundColor Yellow
    git clone https://github.com/fahim-muntasir-niloy/pr_guard.git $InstallDir
}

# 4. Install Dependencies
Write-Host "🛠️  Setting up environment..." -ForegroundColor Yellow
cd $InstallDir
uv sync

# 5. Link CLI
Write-Host "🔗 Linking CLI..." -ForegroundColor Yellow
# Add alias to profile if not exists
$ProfilePath = $PROFILE
if (-not (Test-Path $ProfilePath)) {
    New-Item -Path $ProfilePath -ItemType File -Force
}

$AliasLine = "function pr-guard { & '$InstallDir\.venv\Scripts\pr-guard.exe' @args }"
if (-not (Select-String -Path $ProfilePath -Pattern "function pr-guard")) {
    Add-Content -Path $ProfilePath -Value "`n$AliasLine"
    Write-Host "✅ Added 'pr-guard' command to your PowerShell profile." -ForegroundColor Green
}

# 6. Install VS Code Extension
if (Get-Command "code" -ErrorAction SilentlyContinue) {
    Write-Host "`n🎨 VS Code detected! Installing PR Guard extension..." -ForegroundColor Yellow
    if (Get-Command "npm" -ErrorAction SilentlyContinue) {
        try {
            cd "$InstallDir\vsc-extension"
            Write-Host "📦 Building extension..." -ForegroundColor Yellow
            npm install --silent
            npm run compile --silent
            
            Write-Host "🍱 Packaging extension..." -ForegroundColor Yellow
            # Use npx to avoid requiring global vsce, and --no-git-check to avoid repo errors
            npx -y @vscode/vsce package --out pr-guard.vsix --no-git-check
            
            if (Test-Path "pr-guard.vsix") {
                code --install-extension pr-guard.vsix --force
                Write-Host "✅ VS Code extension installed successfully!" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Could not create VSIX package." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Failed to install VS Code extension: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        cd $InstallDir
    } else {
        Write-Host "ℹ️  npm not found. skipping VS Code extension. Install Node.js to use it." -ForegroundColor Gray
    }
}

Write-Host "`n🎉 PR Guard is ready! Restart your terminal and run 'pr-guard review'." -ForegroundColor Green
Write-Host "Don't forget to set your .env file in $InstallDir" -ForegroundColor Cyan
