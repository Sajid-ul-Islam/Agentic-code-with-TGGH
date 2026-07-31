#!/bin/bash
# Quick start script for GitHub Telegram Bot

echo "🤖 GitHub Telegram Bot - Quick Start"
echo "===================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your tokens:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - GEMINI_API_KEY"
    echo ""
    read -p "Press Enter once you've added your tokens..."
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install it first."
    exit 1
fi

# Create virtual environment
if [ ! -d venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run bot
echo "✅ Starting bot..."
echo ""
python github_bot.py
