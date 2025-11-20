#!/usr/bin/env python3
"""
MCP Server for Telegram Integration
Exposes Telegram bot capabilities through MCP protocol
"""

import os
import sys
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.messaging.telethon_user_client import TelethonUserClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize MCP server
app = Server("telegram-server")

# Initialize Telethon user client
telegram_client = TelethonUserClient()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available Telegram tools
    """
    return [
        Tool(
            name="send_telegram_message",
            description="Send a text message from YOUR Telegram account (not a bot). Supports names from contacts.json, @usernames, or phone numbers with country code",
            inputSchema={
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Recipient: name (e.g., 'john'), @username (e.g., '@johndoe'), or phone with country code (e.g., '+919876543210')"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to send"
                    }
                },
                "required": ["recipient", "message"]
            }
        ),
        Tool(
            name="send_telegram_photo",
            description="Send a photo via Telegram bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_path": {
                        "type": "string",
                        "description": "Path to the photo file to send"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption for the photo"
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "Optional: Telegram chat ID"
                    }
                },
                "required": ["photo_path"]
            }
        ),
        Tool(
            name="send_telegram_document",
            description="Send a document/file via Telegram bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string",
                        "description": "Path to the document file to send"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption for the document"
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "Optional: Telegram chat ID"
                    }
                },
                "required": ["document_path"]
            }
        ),
        Tool(
            name="get_telegram_bot_info",
            description="Get information about the Telegram bot",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_telegram_chat_info",
            description="Get information about a Telegram chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Optional: Telegram chat ID. If not provided, uses default"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls from MCP clients
    """
    logger.info(f"📞 Tool called: {name} with args: {arguments}")

    try:
        if name == "send_telegram_message":
            recipient = arguments.get("recipient")
            message = arguments.get("message")

            if not recipient or not message:
                return [TextContent(
                    type="text",
                    text="Error: 'recipient' and 'message' parameters are required"
                )]

            result = await telegram_client.send_message(recipient, message)

            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"✅ Message sent successfully to {result['recipient']}!\nMessage ID: {result['message_id']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to send message: {result['error']}"
                )]

        elif name == "send_telegram_photo":
            photo_path = arguments.get("photo_path")
            caption = arguments.get("caption")
            chat_id = arguments.get("chat_id")

            if not photo_path:
                return [TextContent(
                    type="text",
                    text="Error: 'photo_path' parameter is required"
                )]

            result = await telegram_client.send_photo(photo_path, caption, chat_id)

            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"✅ Photo sent successfully!\nMessage ID: {result['message_id']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to send photo: {result['error']}"
                )]

        elif name == "send_telegram_document":
            document_path = arguments.get("document_path")
            caption = arguments.get("caption")
            chat_id = arguments.get("chat_id")

            if not document_path:
                return [TextContent(
                    type="text",
                    text="Error: 'document_path' parameter is required"
                )]

            result = await telegram_client.send_document(document_path, caption, chat_id)

            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"✅ Document sent successfully!\nMessage ID: {result['message_id']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to send document: {result['error']}"
                )]

        elif name == "get_telegram_bot_info":
            result = await telegram_client.get_bot_info()

            if result["success"]:
                return [TextContent(
                    type="text",
                    text=f"🤖 Bot Information:\n"
                         f"Name: {result['bot_name']}\n"
                         f"Username: @{result['bot_username']}\n"
                         f"ID: {result['bot_id']}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to get bot info: {result['error']}"
                )]

        elif name == "get_telegram_chat_info":
            chat_id = arguments.get("chat_id")
            result = await telegram_client.get_chat_info(chat_id)

            if result["success"]:
                chat_type = result.get('type', 'N/A')
                first_name = result.get('first_name', 'N/A')
                username = result.get('username', 'N/A')

                return [TextContent(
                    type="text",
                    text=f"💬 Chat Information:\n"
                         f"Chat ID: {result['chat_id']}\n"
                         f"Type: {chat_type}\n"
                         f"Name: {first_name}\n"
                         f"Username: @{username if username != 'N/A' else 'None'}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to get chat info: {result['error']}"
                )]

        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"❌ Error in tool execution: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    logger.info("🚀 Starting Telegram MCP Server...")

    # Start Telethon client
    await telegram_client.start()

    me = await telegram_client.get_me()
    logger.info(f"📱 Logged in as: {me['first_name']} (@{me.get('username', 'No username')})")
    logger.info("✅ Server ready!")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())