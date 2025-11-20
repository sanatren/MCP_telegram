#!/usr/bin/env python3
"""
Command Parser for Voice Assistant
Parses natural language voice commands into structured MCP tool calls
"""

import re
import logging

logger = logging.getLogger(__name__)


class CommandParser:
    """Parse voice commands into MCP tool calls"""

    def __init__(self):
        # Patterns for different command types
        self.patterns = {
            "send_message": [
                r"send (?:a )?(?:telegram )?message to (\w+) saying (.+)",
                r"send (?:a )?(?:telegram )?message to (\w+) (.+)",
                r"message (\w+) (?:saying )?(.+)",
                r"tell (\w+) (?:that )?(.+)",
                r"text (\w+) (.+)",
                r"notify (\w+) (?:that )?(.+)",
                r"let (\w+) know (?:that )?(.+)",
                r"inform (\w+) (?:that )?(.+)",
                r"tell (\w+) (.+)",
            ],
            "send_photo": [
                r"send (?:a )?(?:telegram )?photo to (\w+)",
                r"send (?:a )?picture to (\w+)",
            ],
        }

        logger.info("✅ Command parser initialized")

    def parse(self, command: str) -> dict:
        """
        Parse a voice command into structured data

        Args:
            command: Natural language command

        Returns:
            Dictionary with:
            - action: The action to perform
            - server: MCP server name
            - tool: Tool name
            - arguments: Tool arguments
            - success: Whether parsing succeeded
        """
        command_lower = command.lower().strip()

        logger.info(f"🔍 Parsing command: '{command}'")

        # Check for send message patterns
        for pattern in self.patterns["send_message"]:
            match = re.search(pattern, command_lower)
            if match:
                recipient = match.group(1)
                message = match.group(2)

                logger.info(f"✅ Parsed as send_message: to={recipient}, message={message}")

                return {
                    "action": "send_message",
                    "server": "telegram",
                    "tool": "send_telegram_message",
                    "arguments": {
                        "message": message.strip()
                    },
                    "recipient": recipient,
                    "success": True
                }

        # Check for send photo patterns
        for pattern in self.patterns["send_photo"]:
            match = re.search(pattern, command_lower)
            if match:
                recipient = match.group(1)

                logger.info(f"✅ Parsed as send_photo: to={recipient}")

                return {
                    "action": "send_photo",
                    "server": "telegram",
                    "tool": "send_telegram_photo",
                    "arguments": {
                        "photo_path": "/path/to/photo.jpg",  # Could be enhanced
                    },
                    "recipient": recipient,
                    "success": True
                }

        # No pattern matched
        logger.warning(f"⚠️ Could not parse command: '{command}'")

        return {
            "action": "unknown",
            "success": False,
            "error": "Could not understand command"
        }

    def extract_recipient(self, command: str) -> str:
        """Extract recipient name from command"""
        # Try various patterns to find recipient
        patterns = [
            r"to (\w+)",
            r"message (\w+)",
            r"tell (\w+)",
            r"text (\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                return match.group(1)

        return ""

    def extract_message(self, command: str) -> str:
        """Extract message content from command"""
        # Try various patterns to find message
        patterns = [
            r"saying (.+)",
            r"that (.+)",
            r"message to \w+ (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                return match.group(1)

        return ""


if __name__ == "__main__":
    # Test the parser
    print("🧪 Testing Command Parser")
    print("=" * 50)

    parser = CommandParser()

    test_commands = [
        "send a message to John saying hello how are you",
        "send message to Sarah I'll be late today",
        "message Mike we need to talk",
        "tell Emma the meeting is at 3pm",
        "text Alice can you call me",
        "send a photo to Bob",
        "this is not a valid command",
    ]

    for cmd in test_commands:
        print(f"\n📝 Command: '{cmd}'")
        result = parser.parse(cmd)

        if result["success"]:
            print(f"✅ Action: {result['action']}")
            print(f"   Tool: {result['tool']}")
            print(f"   Args: {result['arguments']}")
        else:
            print(f"❌ Failed to parse")

    print("\n" + "=" * 50)
    print("✅ Tests complete!")
