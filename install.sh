#!/bin/bash

# PR Guard Installer for macOS/Linux
set -e

echo -e "\033[0;36m🛡️  PR Guard: AI-Powered PR Reviewer\033[0m"
echo "---------------------------------------"

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31m❌ python3 not found. Please install Python 3.13+ first.\033[0m"
    exit 1
fi

# 2. Check for UV
if ! command -v uv &> /dev/null; then
    echo -e "\033[0;33m📦 Installing UV (Modern Python Package Manager)...\033[0m"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# 2.5 Check for Node.js (required for VS Code extension)
if ! command -v npm &> /dev/null; then
    echo -e "\033[0;33m📦 Node.js not found. Installing Node.js...\033[0m"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install node
        else
             echo -e "\033[0;31m⚠️  Homebrew not found. Please install Node.js manually to use the extension.\033[0m"
        fi
    else
        # Linux: Use fnm (Fast Node Manager)
        curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
        export PATH="$HOME/.local/share/fnm:$PATH"
        if command -v fnm &> /dev/null; then
            eval "$(fnm env)"
            fnm install --lts
            fnm use lts
        else
            echo -e "\033[0;31m⚠️  Failed to install fnm. Please install Node.js manually.\033[0m"
        fi
    fi
fi

# 3. Clone or Update
INSTALL_DIR="$HOME/.pr_guard"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "\033[0;33m🔄 Updating existing installation in $INSTALL_DIR...\033[0m"
    cd "$INSTALL_DIR"
    git pull
else
    echo -e "\033[0;33m📥 Cloning PR Guard into $INSTALL_DIR...\033[0m"
    git clone https://github.com/fahim-muntasir-niloy/pr_guard.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 4. Install Dependencies
echo -e "\033[0;33m🛠️  Setting up environment...\033[0m"
uv sync

# 5. Link CLI
echo -e "\033[0;33m🔗 Linking CLI...\033[0m"

# Detect shell profile
if [[ "$SHELL" == */zsh ]]; then
    PROFILE="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    PROFILE="$HOME/.bashrc"
    if [ ! -f "$PROFILE" ]; then
        PROFILE="$HOME/.bash_profile"
    fi
else
    PROFILE="$HOME/.profile"
fi

ALIAS_LINE="alias pr-guard='$INSTALL_DIR/.venv/bin/pr-guard'"

if ! grep -q "alias pr-guard" "$PROFILE" 2>/dev/null; then
    echo "" >> "$PROFILE"
    echo "$ALIAS_LINE" >> "$PROFILE"
    echo -e "\033[0;32m✅ Added 'pr-guard' alias to $PROFILE\033[0m"
fi

# 6. Install VS Code Extension
if command -v code &> /dev/null; then
    echo -e "\n\033[0;33m🎨 VS Code detected! Installing PR Guard extension...\033[0m"
    if command -v npm &> /dev/null; then
        (
            cd "$INSTALL_DIR/vsc-extension"
            echo -e "\033[0;33m📦 Building extension...\033[0m"
            npm install --quiet
            npm run compile --quiet
            
            echo -e "\033[0;33m🍱 Packaging extension...\033[0m"
            npx -y @vscode/vsce package --out pr-guard.vsix --no-git-check
            
            if [ -f "pr-guard.vsix" ]; then
                code --install-extension pr-guard.vsix --force
                echo -e "\033[0;32m✅ VS Code extension installed successfully!\033[0m"
            else
                echo -e "\033[0;31m⚠️  Could not create VSIX package.\033[0m"
            fi
        )
    else
        echo -e "\033[0;90mℹ️  npm not found. skipping VS Code extension. Install Node.js to use it.\033[0m"
    fi
fi

echo -e "\n\033[0;32m🎉 PR Guard is ready! Restart your terminal or run 'source $PROFILE'.\033[0m"
echo -e "\033[0;36mDon't forget to set your .env file in $INSTALL_DIR\033[0m"
