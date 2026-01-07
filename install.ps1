# PR Guard Installer for Windows
$ErrorActionPreference = "Stop"

Write-Host "🛡️  PR Guard: AI-Powered PR Reviewer" -ForegroundColor Cyan
Write-Host "---------------------------------------"

# 1. Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.13+ first." -ForegroundColor Red
    return
}

# 2. Check for UV
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing UV (Modern Python Package Manager)..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH += ";$HOME\.cargo\bin"
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

Write-Host "`n🎉 PR Guard is ready! Restart your terminal and run 'pr-guard review'." -ForegroundColor Green
Write-Host "Don't forget to set your .env file in $InstallDir" -ForegroundColor Cyan
