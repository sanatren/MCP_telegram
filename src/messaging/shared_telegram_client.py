#!/usr/bin/env python3
"""
Shared Telegram Client - Singleton pattern to avoid database locks
"""
import os
import json
import logging
from telethon import TelegramClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)


class SharedTelegramClient:
    """Singleton Telethon client to prevent database lock issues"""

    _instance = None
    _client = None
    _contact_map = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._client is None:
            self.api_id = int(os.getenv('TELEGRAM_API_ID'))
            self.api_hash = os.getenv('TELEGRAM_API_HASH')
            self.phone = os.getenv('TELEGRAM_PHONE_NUMBER')

            session_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'telegram_session')
            self._client = TelegramClient(session_file, self.api_id, self.api_hash)
            self._contact_map = self._load_contact_map()
            logger.info("✅ Shared Telethon client initialized")

    def _load_contact_map(self) -> dict:
        """Load contacts from JSON"""
        contacts_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'contacts.json')
        try:
            with open(contacts_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load contacts: {e}")
            return {}

    @property
    def client(self):
        """Get the Telethon client instance"""
        return self._client

    @property
    def contact_map(self):
        """Get the contact map"""
        return self._contact_map

    async def start(self):
        """Start the client (idempotent - safe to call multiple times)"""
        try:
            if not self._client.is_connected():
                logger.info("🔌 Connecting client...")
                await self._client.connect()
                logger.info("✅ Client connected")

            if not await self._client.is_user_authorized():
                logger.info("🔐 Starting authentication...")
                await self._client.start(phone=self.phone)
                logger.info("✅ Telethon client authenticated")
            else:
                logger.info("✅ Telethon client already authenticated")
        except Exception as e:
            logger.error(f"❌ Error in start(): {e}")
            # If already connected in another place, that's OK
            if "already" in str(e).lower() or "lock" in str(e).lower():
                logger.warning("⚠️ Client may already be connected elsewhere, continuing...")
            else:
                raise

    async def send_message(self, recipient: str, message: str) -> dict:
        """Send message using shared client"""
        try:
            # Ensure connected
            await self.start()

            recipient_lower = recipient.lower()

            # Try to find the recipient
            target = None
            if recipient_lower in self._contact_map:
                target = self._contact_map[recipient_lower]
                logger.info(f"📞 Sending to {recipient} ({target})")
            else:
                # Try as username
                target = recipient
                logger.info(f"📞 Sending to username: {recipient}")

            # Send message
            sent_message = await self._client.send_message(target, message)

            return {
                "success": True,
                "message": f"Message sent to {recipient}",
                "recipient": recipient,
                "message_id": sent_message.id
            }

        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient
            }

    async def disconnect(self):
        """Disconnect the client"""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("🔌 Telethon client disconnected")


# Singleton instance getter
def get_shared_client() -> SharedTelegramClient:
    """Get the shared Telegram client instance"""
    return SharedTelegramClient()
