#!/usr/bin/env python3
"""
MCP Client for Voice Assistant
Connects to MCP servers (like Telegram) to execute tasks
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client to interact with various MCP servers"""

    def __init__(self):
        self.servers = {}
        self.sessions = {}
        logger.info("✅ MCP Client initialized")

    async def connect_server(self, server_name: str, command: str, args: list):
        """
        Connect to an MCP server

        Args:
            server_name: Name to identify this server (e.g., "telegram")
            command: Command to start server (e.g., "python")
            args: Arguments for command (e.g., ["src/mcp_servers/telegram_server.py"])
        """
        try:
            logger.info(f"🔌 Connecting to {server_name} MCP server...")

            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=None
            )

            # Store server params
            self.servers[server_name] = server_params

            logger.info(f"✅ Connected to {server_name} server")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to {server_name}: {e}")
            return False

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """
        Call a tool on an MCP server

        Args:
            server_name: Name of the server (e.g., "telegram")
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Result text or None if failed
        """
        try:
            if server_name not in self.servers:
                logger.error(f"❌ Server {server_name} not connected")
                return None

            logger.info(f"📞 Calling {server_name}.{tool_name} with args: {arguments}")

            server_params = self.servers[server_name]

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Call the tool
                    result = await session.call_tool(tool_name, arguments)

                    # Extract text from result
                    if result.content and len(result.content) > 0:
                        response_text = result.content[0].text
                        logger.info(f"✅ Tool result: {response_text[:100]}...")
                        return response_text
                    else:
                        logger.warning("⚠️ Tool returned no content")
                        return None

        except Exception as e:
            logger.error(f"❌ Error calling tool: {e}")
            return None

    async def list_tools(self, server_name: str) -> list:
        """
        List available tools from a server

        Args:
            server_name: Name of the server

        Returns:
            List of tool dictionaries
        """
        try:
            if server_name not in self.servers:
                logger.error(f"❌ Server {server_name} not connected")
                return []

            server_params = self.servers[server_name]

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    tools_result = await session.list_tools()

                    tools = []
                    for tool in tools_result.tools:
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema.get("properties", {})
                        })

                    return tools

        except Exception as e:
            logger.error(f"❌ Error listing tools: {e}")
            return []


# Synchronous wrapper for easy use
class MCPClientSync:
    """Synchronous wrapper for MCP client"""

    def __init__(self):
        self.client = MCPClient()
        self._connected = False

    def connect_telegram(self):
        """Connect to Telegram MCP server"""
        result = asyncio.run(self.client.connect_server(
            "telegram",
            "python",
            ["src/mcp_servers/telegram_server.py"]
        ))
        self._connected = result
        return result

    def send_telegram_message(self, message: str, recipient: str = None, chat_id: str = None) -> Optional[str]:
        """Send a Telegram message"""
        if not self._connected:
            self.connect_telegram()

        args = {"message": message}
        if recipient:
            args["recipient"] = recipient
        if chat_id:
            args["chat_id"] = chat_id

        return asyncio.run(self.client.call_tool(
            "telegram",
            "send_telegram_message",
            args
        ))

    def send_telegram_photo(self, photo_path: str, caption: str = None, chat_id: str = None) -> Optional[str]:
        """Send a Telegram photo"""
        if not self._connected:
            self.connect_telegram()

        args = {"photo_path": photo_path}
        if caption:
            args["caption"] = caption
        if chat_id:
            args["chat_id"] = chat_id

        return asyncio.run(self.client.call_tool(
            "telegram",
            "send_telegram_photo",
            args
        ))

    def get_bot_info(self) -> Optional[str]:
        """Get Telegram bot info"""
        if not self._connected:
            self.connect_telegram()

        return asyncio.run(self.client.call_tool(
            "telegram",
            "get_telegram_bot_info",
            {}
        ))

    def list_telegram_tools(self) -> list:
        """List available Telegram tools"""
        if not self._connected:
            self.connect_telegram()

        return asyncio.run(self.client.list_tools("telegram"))


if __name__ == "__main__":
    # Test the MCP client
    print("🧪 Testing MCP Client")
    print("=" * 50)

    client = MCPClientSync()

    print("\n1️⃣ Connecting to Telegram server...")
    if client.connect_telegram():
        print("✅ Connected!")

        print("\n2️⃣ Listing available tools...")
        tools = client.list_telegram_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool['name']}")

        print("\n3️⃣ Getting bot info...")
        result = client.get_bot_info()
        print(f"✅ {result}")

        print("\n4️⃣ Sending test message...")
        result = client.send_telegram_message("🧪 Test from MCP Client!")
        print(f"✅ {result}")
    else:
        print("❌ Failed to connect")

    print("\n" + "=" * 50)
    print("✅ Tests complete!")