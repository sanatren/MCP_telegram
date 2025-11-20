#!/bin/bash
# Gemma Voice Assistant Background Launcher

# Get script directory and go to project root
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/.."

# Check if already running
if pgrep -f "auto_voice_assistant.py" > /dev/null; then
    echo "Gemma Voice Assistant is already running!"
    exit 0
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    # Try to start Ollama if not running
    if command -v ollama &> /dev/null; then
        echo "Starting Ollama..."
        ollama serve &
        sleep 3
    else
        echo "❌ Ollama not found. Please install Ollama first."
        exit 1
    fi
fi

# Start voice assistant in background with logging
echo "🚀 Starting Gemma Voice Assistant in background..."

# Use conda/pip environment
export PATH="/opt/homebrew/Caskroom/miniconda/base/bin:$PATH"
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate base

nohup python main.py > logs/gemma.log 2>&1 &

# Get PID
GEMMA_PID=$!
echo $GEMMA_PID > logs/gemma.pid

echo "✅ Gemma Voice Assistant started!"
echo "📋 Process ID: $GEMMA_PID"
echo "📝 Logs: logs/gemma.log"
echo "🎤 Say activation word to activate!"
echo ""
echo "To stop: ./scripts/stop_gemma.sh"