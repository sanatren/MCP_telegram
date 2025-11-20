# 🤖 Telegram Bot Integration Guide

## ✅ Setup Complete!

Your Telegram bot **@GemmaVoiceBot** is now integrated with Gemma Voice Assistant!

---

## 📋 Quick Start Checklist

- [x] Created bot with @BotFather
- [x] Got bot token: `8364724814:AAE-eSdur6A4VmCxzcBvhXl49XcHXKmvfcg`
- [x] Added token to `.env` file
- [x] Installed `python-telegram-bot` library
- [x] Created Telegram client wrapper
- [ ] **Next: Get your Telegram Chat ID** 👇

---

## 🆔 Get Your Telegram Chat ID (Important!)

### Method 1: Use Your Bot

1. Open Telegram (phone or desktop)
2. Search for: **@GemmaVoiceBot**
3. Click **"Start"** or send `/start`
4. The bot will reply with your **Chat ID**
5. Copy the Chat ID

### Method 2: Use @userinfobot

1. Open Telegram
2. Search for: **@userinfobot**
3. Send `/start`
4. It will show your user ID (this is your chat ID)

### Add Chat ID to .env

Edit `config/.env` and add your chat ID:

```bash
TELEGRAM_CHAT_ID=123456789  # Replace with your actual chat ID
```

---

## 🧪 Test Your Bot

Run the test script:

```bash
python test_telegram.py
```

This will:
- ✅ Verify bot connection
- ✅ Check configuration
- ✅ Send a test message to you

---

## 📁 Project Structure

```
whatsapp automation/
├── config/
│   └── .env                          # Bot token + chat ID here
├── src/
│   ├── core/
│   │   └── auto_voice_assistant.py   # Voice assistant (existing)
│   └── messaging/                     # NEW
│       ├── __init__.py
│       └── telegram_client.py         # Telegram integration
├── test_telegram.py                   # Test script
└── README_TELEGRAM.md                 # This file
```

---

## 💻 Usage Examples

### Send a Simple Message

```python
from src.messaging.telegram_client import send_telegram_message

# Send message
result = send_telegram_message("Hello from Gemma!")

if result['success']:
    print(f"Message sent! ID: {result['message_id']}")
```

### Send a Photo

```python
from src.messaging.telegram_client import send_telegram_photo

result = send_telegram_photo(
    photo_path="/path/to/image.jpg",
    caption="Check out this photo!"
)
```

### Send a Document

```python
from src.messaging.telegram_client import send_telegram_document

result = send_telegram_document(
    document_path="/path/to/file.pdf",
    caption="Here's the document you requested"
)
```

### Async Usage (Advanced)

```python
import asyncio
from src.messaging.telegram_client import TelegramClient

async def main():
    client = TelegramClient()

    # Send message
    await client.send_message("Hello!")

    # Get bot info
    info = await client.get_bot_info()
    print(f"Bot: @{info['bot_username']}")

asyncio.run(main())
```

---

## 🎙️ Integration with Voice Assistant

Once your chat ID is configured, you can integrate with the voice assistant:

```python
# In your voice assistant code:
from src.messaging.telegram_client import send_telegram_message

def handle_voice_command(command):
    if "send message" in command:
        # Extract message content
        message = extract_message(command)

        # Send via Telegram
        result = send_telegram_message(message)

        if result['success']:
            speak("Message sent successfully!")
```

---

## 🔧 Features

✅ **Send text messages**
✅ **Send photos with captions**
✅ **Send documents/files**
✅ **Get bot information**
✅ **Get chat information**
✅ **Listen for incoming messages**
✅ **Handle /start and /help commands**
✅ **Async and sync wrappers**
✅ **Error handling & logging**

---

## 📊 Bot Commands

When you chat with @GemmaVoiceBot:

- `/start` - Get your chat ID and welcome message
- `/help` - Show help information

---

## 🚀 Next Steps

1. **Get your chat ID** (see above)
2. **Run test script**: `python test_telegram.py`
3. **Design MCP server** with Telegram tools
4. **Integrate with voice assistant**
5. **Test end-to-end**: Voice → MCP → Telegram

---

## 🐛 Troubleshooting

### Bot doesn't respond
- Check if token is correct in `.env`
- Make sure you clicked "Start" in the bot chat

### Can't send messages
- Verify `TELEGRAM_CHAT_ID` is set in `.env`
- Make sure the chat ID is correct (number only, no quotes)

### Import errors
- Run: `pip install python-telegram-bot`
- Check Python version (needs 3.9+)

---

## 📚 Resources

- **Telegram Bot API Docs**: https://core.telegram.org/bots/api
- **python-telegram-bot Docs**: https://docs.python-telegram-bot.org
- **Your Bot**: https://t.me/GemmaVoiceBot

---

**Built with ❤️ for Gemma Voice Assistant**