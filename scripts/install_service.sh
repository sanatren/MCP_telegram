#!/bin/bash
# Install Gemma Voice Assistant as macOS service (auto-start)

echo "🔧 Installing Gemma Voice Assistant as system service..."

# Get current directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy service file to LaunchAgents
cp "$DIR/com.gemma.voiceassistant.plist" ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.gemma.voiceassistant.plist

echo "✅ Service installed!"
echo "🚀 Gemma will now start automatically when you log in"
echo ""
echo "Commands:"
echo "  Start manually: ./start_gemma_background.sh"
echo "  Stop manually: ./stop_gemma.sh"
echo "  Uninstall service: ./uninstall_service.sh"
echo ""
echo "🎤 Say 'Hey Gemma' anytime!"