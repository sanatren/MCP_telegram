#!/bin/bash
# Stop Gemma Voice Assistant

# Get script directory and go to project root
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/.."

echo "🛑 Stopping Gemma Voice Assistant..."

# Kill by PID if exists
if [ -f "logs/gemma.pid" ]; then
    PID=$(cat logs/gemma.pid)
    if kill "$PID" 2>/dev/null; then
        echo "✅ Stopped process $PID"
    fi
    rm -f logs/gemma.pid
fi

# Kill any remaining processes
pkill -f "main.py" 2>/dev/null
pkill -f "auto_voice_assistant.py" 2>/dev/null

echo "🔇 Gemma Voice Assistant stopped!"