#!/bin/bash

# ShellQuest Installation Script

echo "🚀 Installing ShellQuest..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -q rich pyyaml click prompt-toolkit

# Install in editable mode
echo "🔧 Installing ShellQuest..."
pip3 install -q -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run 'shellquest' to start the game"
echo "Or use: python3 -m shellquest"
echo ""
