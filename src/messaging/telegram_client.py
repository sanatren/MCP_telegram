#!/usr/bin/env python3
"""
Telegram Bot Client
Handles all Telegram API interactions for sending/receiving messages
"""

import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import logging

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramClient:
    """Telegram Bot client for sending and receiving messages"""

    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.default_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")

        # Create bot with longer timeout
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(connection_pool_size=8, read_timeout=30, write_timeout=30, connect_timeout=30)
        self.bot = Bot(token=self.token, request=request)
        self.application = None
        logger.info("✅ Telegram client initialized")

    async def send_message(self, text: str, chat_id: str = None) -> dict:
        """
        Send a text message to a Telegram chat

        Args:
            text: Message text to send
            chat_id: Telegram chat ID (uses default if not provided)

        Returns:
            dict with message details
        """
        try:
            target_chat_id = chat_id or self.default_chat_id

            if not target_chat_id:
                raise ValueError("No chat_id provided and TELEGRAM_CHAT_ID not set in .env")

            message = await self.bot.send_message(
                chat_id=target_chat_id,
                text=text
            )

            logger.info(f"✅ Message sent to {target_chat_id}: {text[:50]}...")

            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "text": message.text,
                "date": message.date.isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_photo(self, photo_path: str, caption: str = None, chat_id: str = None) -> dict:
        """Send a photo to a Telegram chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id

            if not target_chat_id:
                raise ValueError("No chat_id provided and TELEGRAM_CHAT_ID not set")

            with open(photo_path, 'rb') as photo:
                message = await self.bot.send_photo(
                    chat_id=target_chat_id,
                    photo=photo,
                    caption=caption
                )

            logger.info(f"✅ Photo sent to {target_chat_id}")

            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id
            }

        except Exception as e:
            logger.error(f"❌ Failed to send photo: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_document(self, document_path: str, caption: str = None, chat_id: str = None) -> dict:
        """Send a document to a Telegram chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id

            if not target_chat_id:
                raise ValueError("No chat_id provided and TELEGRAM_CHAT_ID not set")

            with open(document_path, 'rb') as document:
                message = await self.bot.send_document(
                    chat_id=target_chat_id,
                    document=document,
                    caption=caption
                )

            logger.info(f"✅ Document sent to {target_chat_id}")

            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id
            }

        except Exception as e:
            logger.error(f"❌ Failed to send document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_bot_info(self) -> dict:
        """Get information about the bot"""
        try:
            bot_info = await self.bot.get_me()

            return {
                "success": True,
                "bot_id": bot_info.id,
                "bot_name": bot_info.first_name,
                "bot_username": bot_info.username,
                "is_bot": bot_info.is_bot
            }

        except Exception as e:
            logger.error(f"❌ Failed to get bot info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_chat_info(self, chat_id: str = None) -> dict:
        """Get information about a chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id

            if not target_chat_id:
                raise ValueError("No chat_id provided and TELEGRAM_CHAT_ID not set")

            chat = await self.bot.get_chat(chat_id=target_chat_id)

            return {
                "success": True,
                "chat_id": chat.id,
                "type": chat.type,
                "title": chat.title,
                "username": chat.username,
                "first_name": chat.first_name,
                "last_name": chat.last_name
            }

        except Exception as e:
            logger.error(f"❌ Failed to get chat info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def start_bot(self):
        """Start the Telegram bot to listen for incoming messages"""
        if not self.application:
            self.application = Application.builder().token(self.token).build()

            # Add handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        logger.info("🤖 Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Hi! I'm Gemma Voice Assistant Bot!\n\n"
            f"Your chat ID is: {update.effective_chat.id}\n\n"
            "Add this ID to your .env file as TELEGRAM_CHAT_ID to receive messages."
        )

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "🎙️ Gemma Voice Assistant Bot\n\n"
            "Commands:\n"
            "/start - Get your chat ID\n"
            "/help - Show this help message\n\n"
            "I can send you messages when you use voice commands!"
        )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user_message = update.message.text
        logger.info(f"📨 Received message: {user_message}")

        # Echo back for now
        await update.message.reply_text(f"You said: {user_message}")


# Synchronous wrapper functions for easy use
def send_telegram_message(text: str, chat_id: str = None) -> dict:
    """Synchronous wrapper to send a Telegram message"""
    client = TelegramClient()
    return asyncio.run(client.send_message(text, chat_id))


def send_telegram_photo(photo_path: str, caption: str = None, chat_id: str = None) -> dict:
    """Synchronous wrapper to send a Telegram photo"""
    client = TelegramClient()
    return asyncio.run(client.send_photo(photo_path, caption, chat_id))


def send_telegram_document(document_path: str, caption: str = None, chat_id: str = None) -> dict:
    """Synchronous wrapper to send a Telegram document"""
    client = TelegramClient()
    return asyncio.run(client.send_document(document_path, caption, chat_id))


def get_telegram_bot_info() -> dict:
    """Synchronous wrapper to get bot info"""
    client = TelegramClient()
    return asyncio.run(client.get_bot_info())


if __name__ == "__main__":
    # Test the bot
    client = TelegramClient()

    print("Testing Telegram bot...")
    print("\n1. Getting bot info...")
    bot_info = asyncio.run(client.get_bot_info())
    print(f"Bot info: {bot_info}")

    print("\n2. To get your chat ID:")
    print("   - Open Telegram")
    print("   - Search for @GemmaVoiceBot")
    print("   - Send /start")
    print("   - Copy the chat ID and add it to .env file")

    print("\n3. Starting bot (press Ctrl+C to stop)...")
    try:
        client.start_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")