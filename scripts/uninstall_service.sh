#!/bin/bash
# Uninstall Gemma Voice Assistant service

echo "🗑️  Uninstalling Gemma Voice Assistant service..."

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.gemma.voiceassistant.plist 2>/dev/null

# Remove service file
rm -f ~/Library/LaunchAgents/com.gemma.voiceassistant.plist

# Stop any running processes
./stop_gemma.sh

echo "✅ Service uninstalled!"
echo "Gemma will no longer start automatically."