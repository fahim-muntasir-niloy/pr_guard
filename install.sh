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

echo -e "\n\033[0;32m🎉 PR Guard is ready! Restart your terminal or run 'source $PROFILE'.\033[0m"
echo -e "\033[0;36mDon't forget to set your .env file in $INSTALL_DIR\033[0m"
