# 🔌 MCP Server for Telegram

## What is This?

An **MCP (Model Context Protocol) server** that exposes Telegram bot capabilities to any MCP client.

---

## 🎯 Architecture

```
┌─────────────────────────────────────┐
│   MCP Client (Voice Assistant)      │
│   - Sends commands                   │
│   - Receives responses               │
└──────────────┬──────────────────────┘
               │ MCP Protocol (stdio)
               ▼
┌─────────────────────────────────────┐
│   MCP Server (Telegram)              │
│   - Exposes 5 tools                  │
│   - Handles Telegram API calls       │
└──────────────┬──────────────────────┘
               │ Telegram Bot API
               ▼
┌─────────────────────────────────────┐
│   Telegram                           │
│   - Delivers messages                │
└─────────────────────────────────────┘
```

---

## 🛠️ Available Tools

### 1. **send_telegram_message**
Send a text message via Telegram

**Parameters:**
- `message` (required): The message text
- `chat_id` (optional): Target chat ID

**Example:**
```json
{
  "message": "Hello from MCP!",
  "chat_id": "1237082783"
}
```

---

### 2. **send_telegram_photo**
Send a photo via Telegram

**Parameters:**
- `photo_path` (required): Path to photo file
- `caption` (optional): Photo caption
- `chat_id` (optional): Target chat ID

**Example:**
```json
{
  "photo_path": "/path/to/image.jpg",
  "caption": "Check this out!"
}
```

---

### 3. **send_telegram_document**
Send a document/file via Telegram

**Parameters:**
- `document_path` (required): Path to document
- `caption` (optional): Document caption
- `chat_id` (optional): Target chat ID

---

### 4. **get_telegram_bot_info**
Get information about the bot

**No parameters required**

**Returns:**
- Bot name
- Bot username
- Bot ID

---

### 5. **get_telegram_chat_info**
Get information about a chat

**Parameters:**
- `chat_id` (optional): Chat ID to query

---

## 🚀 Running the Server

### Manual Mode (Testing)

```bash
cd "/Users/sanatankhemariya/Desktop/whatsapp automation"
source venv/bin/activate
python src/mcp_servers/telegram_server.py
```

The server runs in stdio mode and communicates via stdin/stdout.

---

### With MCP Inspector (Debug Mode)

```bash
npx @modelcontextprotocol/inspector python src/mcp_servers/telegram_server.py
```

Opens a web interface at http://localhost:5173 to test tools interactively.

---

### As MCP Client (Programmatic)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["src/mcp_servers/telegram_server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Call a tool
        result = await session.call_tool("send_telegram_message", {
            "message": "Hello from MCP client!"
        })
```

---

## 🧪 Testing

Run the test script:

```bash
source venv/bin/activate
python test_mcp_server.py
```

This will:
1. List all available tools
2. Get bot information
3. Send a test message to your Telegram

---

## 🔧 Configuration

The server reads from `config/.env`:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## 💡 Why MCP?

### Without MCP (Direct Integration)
```python
# Tightly coupled - hard to extend
from telegram_client import send_message
send_message("Hello")
```

### With MCP (Standardized)
```python
# Loosely coupled - easy to extend
mcp_client.call_tool("send_telegram_message", {
    "message": "Hello"
})

# Same interface for WhatsApp, Slack, Email, etc!
```

---

## 🎁 Benefits

✅ **Reusable** - Any MCP client can use it
✅ **Standardized** - Follows MCP protocol
✅ **Discoverable** - Tools self-describe
✅ **Extensible** - Easy to add more tools
✅ **AI-Friendly** - LLMs understand MCP natively
✅ **Decoupled** - Server independent of clients

---

## 📁 File Structure

```
src/
├── messaging/
│   └── telegram_client.py        # Low-level Telegram API wrapper
└── mcp_servers/
    └── telegram_server.py         # MCP server (this file)
```

---

## 🔜 Next Steps

1. **Test the server**: `python test_mcp_server.py`
2. **Create MCP client** in voice assistant
3. **Integrate with Gemma** for voice commands
4. **Add more tools** (groups, polls, etc.)
5. **Build WhatsApp MCP server** (same pattern!)

---

## 🐛 Troubleshooting

### Server won't start
- Check if `TELEGRAM_BOT_TOKEN` is set in `.env`
- Ensure virtual environment is activated
- Verify MCP is installed: `pip list | grep mcp`

### Tool calls fail
- Check Telegram bot token is valid
- Verify chat ID is correct
- Check network connectivity

### Import errors
- Make sure you're in the venv: `source venv/bin/activate`
- Install dependencies: `pip install -r config/requirements.txt`

---

**Built with ❤️ using MCP + Telegram Bot API**