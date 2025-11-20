#!/usr/bin/env python3
"""
Gemma Voice Assistant with MCP Integration
Combines voice recognition with Telegram messaging via MCP
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.mcp_client import MCPClientSync
from src.core.command_parser import CommandParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceAssistantMCP:
    """Voice Assistant with MCP integration for Telegram"""

    def __init__(self):
        self.mcp_client = MCPClientSync()
        self.command_parser = CommandParser()

        # Connect to Telegram MCP server
        logger.info("🔌 Connecting to Telegram MCP server...")
        if self.mcp_client.connect_telegram():
            logger.info("✅ Telegram MCP connected!")
        else:
            logger.error("❌ Failed to connect to Telegram MCP")

    def process_voice_command(self, voice_input: str) -> str:
        """
        Process a voice command and execute via MCP

        Args:
            voice_input: The voice command from user

        Returns:
            Response message
        """
        logger.info(f"🎙️  Received voice command: '{voice_input}'")

        # Parse the command
        parsed = self.command_parser.parse(voice_input)

        if not parsed["success"]:
            return "Sorry, I didn't understand that command. Try saying 'send message to John saying hello'."

        # Execute via MCP
        logger.info(f"📞 Executing {parsed['action']} via MCP...")

        if parsed["action"] == "send_message":
            message = parsed["arguments"]["message"]
            result = self.mcp_client.send_telegram_message(message)

            if result and "successfully" in result:
                return f"Message sent to {parsed.get('recipient', 'recipient')}!"
            else:
                return f"Failed to send message: {result}"

        elif parsed["action"] == "send_photo":
            # Note: This is a placeholder - in real use, you'd specify the photo
            return "Photo sending not yet implemented in voice commands."

        else:
            return "Unknown action."

    def test_integration(self):
        """Test the MCP integration"""
        print("\n🧪 Testing Voice Assistant with MCP")
        print("=" * 50)

        test_commands = [
            "send message to John saying hello how are you",
            "tell Sarah the meeting is at 3pm",
            "message Mike can you call me back",
        ]

        for cmd in test_commands:
            print(f"\n🎙️  Voice: '{cmd}'")
            response = self.process_voice_command(cmd)
            print(f"🤖 Response: {response}")

        print("\n" + "=" * 50)
        print("✅ Integration test complete!")


if __name__ == "__main__":
    assistant = VoiceAssistantMCP()
    assistant.test_integration()
