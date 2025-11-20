#!/usr/bin/env python3
"""
Telethon User Client
Sends messages from YOUR Telegram account (not a bot)
"""

import os
import asyncio
from dotenv import load_dotenv
import logging
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


class TelethonUserClient:
    """Telegram User client for sending messages from YOUR account"""

    def __init__(self):
        # Use shared client to avoid database locks
        self.shared_client = get_shared_client()
        self.client = self.shared_client.client
        self.contact_map = self.shared_client.contact_map

        logger.info("✅ Telethon user client initialized")

    async def start(self):
        """Start the client and authenticate if needed"""
        await self.shared_client.start()
        logger.info("✅ Authenticated and ready!")

    async def send_message(self, recipient: str, message: str) -> dict:
        """
        Send a message from YOUR account to a recipient

        Args:
            recipient: Name, username, or phone number (e.g., "john", "@johndoe", "+1234567890")
            message: Message text to send

        Returns:
            dict with message details
        """
        try:
            # Start client if not started
            if not self.client.is_connected():
                await self.start()

            # Resolve recipient (check contact map first)
            recipient_lower = recipient.lower()

            if recipient_lower in self.contact_map:
                # Use mapped username or ID
                target = self.contact_map[recipient_lower]
                logger.info(f"📇 Mapped '{recipient}' → '{target}'")
            else:
                # Use as-is (username, phone, or ID)
                target = recipient

            # Send message
            sent_message = await self.client.send_message(target, message)

            logger.info(f"✅ Message sent to {recipient}: {message[:50]}...")

            return {
                "success": True,
                "message_id": sent_message.id,
                "recipient": recipient,
                "text": message,
                "date": sent_message.date.isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_me(self) -> dict:
        """Get information about your account"""
        try:
            if not self.client.is_connected():
                await self.start()

            me = await self.client.get_me()

            return {
                "success": True,
                "user_id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone
            }

        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def disconnect(self):
        """Disconnect the client"""
        await self.client.disconnect()
        logger.info("👋 Disconnected")


# Synchronous wrapper functions
def send_telegram_message_as_user(recipient: str, message: str) -> dict:
    """Synchronous wrapper to send a Telegram message as user"""
    client = TelethonUserClient()
    return asyncio.run(client.send_message(recipient, message))


async def main():
    """Test the Telethon user client"""
    client = TelethonUserClient()

    try:
        await client.start()

        # Get account info
        me = await client.get_me()
        print(f"\n✅ Logged in as: {me['first_name']} (@{me['username']})")
        print(f"📱 Phone: {me['phone']}")

        # Test sending message
        recipient = input("\nEnter recipient (name, @username, or phone): ")
        message = input("Enter message: ")

        result = await client.send_message(recipient, message)

        if result['success']:
            print(f"\n✅ Message sent successfully!")
        else:
            print(f"\n❌ Failed: {result['error']}")

        await client.disconnect()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())