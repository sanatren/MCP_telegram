#!/usr/bin/env python3
"""
Telegram Message Listener
Listens for incoming messages and notifies the voice assistant
"""

import os
import asyncio
from telethon import events
from dotenv import load_dotenv
import logging
from datetime import datetime
from .shared_telegram_client import get_shared_client

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramMessageListener:
    """Listens for incoming Telegram messages and provides callbacks"""

    def __init__(self, on_message_callback=None):
        # Use shared client to avoid database locks
        self.shared_client = get_shared_client()
        self.client = self.shared_client.client

        # Callback for when a message is received
        self.on_message_callback = on_message_callback

        # Track last received message for reply context
        self.last_message = None

        logger.info("✅ Telegram listener initialized")

    async def start(self):
        """Start the listener and authenticate if needed"""
        # Use shared client's start method
        await self.shared_client.start()

        me = await self.client.get_me()
        logger.info(f"✅ Listening as: {me.first_name} (@{me.username})")

        # Register message handler - ONLY personal messages (no channels/groups)
        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handle_new_message(event):
            """Handle incoming messages from users only"""
            try:
                sender = await event.get_sender()
                message_text = event.message.message

                # Get sender name (users only, not channels)
                if hasattr(sender, 'first_name'):
                    sender_name = sender.first_name or ""
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"
                else:
                    # Skip non-user messages (channels, etc.)
                    logger.info(f"⏭️ Skipping non-user message from {sender.title if hasattr(sender, 'title') else 'Unknown'}")
                    return

                # Get username safely
                sender_username = getattr(sender, 'username', None)

                # Store message for context
                self.last_message = {
                    "sender_id": sender.id,
                    "sender_name": sender_name,
                    "sender_username": sender_username,
                    "message": message_text,
                    "timestamp": datetime.now()
                }

                logger.info(f"📩 New message from {sender_name}: {message_text}")

                # Call callback if provided
                if self.on_message_callback:
                    await self.on_message_callback(self.last_message)

            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                import traceback
                traceback.print_exc()

        logger.info("👂 Listening for incoming messages...")

        # Keep running
        await self.client.run_until_disconnected()

    def get_last_sender(self):
        """Get the last person who sent you a message"""
        if self.last_message:
            return {
                "name": self.last_message["sender_name"],
                "username": self.last_message["sender_username"],
                "id": self.last_message["sender_id"]
            }
        return None

    async def stop(self):
        """Stop the listener"""
        await self.client.disconnect()
        logger.info("👋 Listener stopped")


async def main():
    """Test the listener"""

    async def on_message(message):
        """Callback when message is received"""
        print(f"\n🔔 NOTIFICATION:")
        print(f"   From: {message['sender_name']}")
        print(f"   Message: {message['message']}")
        print(f"   Time: {message['timestamp'].strftime('%H:%M:%S')}")

    listener = TelegramMessageListener(on_message_callback=on_message)
    await listener.start()


if __name__ == "__main__":
    asyncio.run(main())
