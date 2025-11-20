#!/usr/bin/env python3
"""
AI-powered Intent Parser
Uses OpenAI GPT-4o-mini to understand user intent naturally with conversation context
"""

import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)

logger = logging.getLogger(__name__)


class IntentParser:
    """Uses GPT-4o-mini to parse user intent naturally with conversation history"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_context = []  # Store recent messages for context
        logger.info("✅ AI Intent Parser initialized (GPT-4o-mini)")

    def update_context(self, user_text: str, assistant_response: str = None, recipient: str = None):
        """Update conversation context for better parsing"""
        self.conversation_context.append({
            "user": user_text,
            "assistant": assistant_response,
            "recipient": recipient
        })
        # Keep only last 5 exchanges for context
        if len(self.conversation_context) > 5:
            self.conversation_context = self.conversation_context[-5:]

    def parse(self, user_text: str, conversation_history: list = None) -> dict:
        """
        Use GPT-4o-mini to understand what the user wants to do with conversation context

        Args:
            user_text: Natural language from user
            conversation_history: Recent conversation for context (list of tuples)

        Returns:
            dict with parsed intent
        """
        try:
            # Build context messages for GPT
            context_messages = []

            # System prompt
            system_prompt = """You are an intent parser for a voice assistant. Analyze user commands and extract:
1. Whether they want to send a message
2. Who the recipient is (including pronouns like "him", "her", "them")
3. What message to send

CRITICAL RULES FOR MESSAGE EXTRACTION:
- Extract CLEAN message content - remove command words and filler words
- Remove: "tell him", "remind him", "notify him", "saying", "that", "to" at start
- "send message to John saying that I won't" → message: "I won't"
- "tell him that I'll be late" → message: "I'll be late"
- "tell Sarthal to drink water" → message: "drink water"
- "remind him to eat healthy food" → message: "eat healthy food"
- "notify him I'm running late" → message: "I'm running late"

CONTEXT AND FOLLOW-UP RULES:
- Keywords "also", "and", "too", "plus" indicate FOLLOW-UP to same recipient
- "also notify him to eat healthy" → use LAST recipient, message: "eat healthy"
- "and tell him about the meeting" → use LAST recipient, message: "about the meeting"
- If user says "him", "her", "them" without name, ALWAYS use LAST recipient from context
- If NO explicit recipient AND user says "also/and/too", use LAST recipient
- For follow-up messages, ALWAYS resolve to actual recipient name from context

EXAMPLES:
- "send message to Sarthal saying drink water" → recipient: "sarthal", message: "drink water"
- "also notify him to eat healthy food" → recipient: "{LAST_RECIPIENT}", message: "eat healthy food"
- "and tell him I'll be late" → recipient: "{LAST_RECIPIENT}", message: "I'll be late"
- "tell him about the meeting" → recipient: "{LAST_RECIPIENT}", message: "about the meeting"
- "how are you" → action: "general_chat"

Respond ONLY with valid JSON:
{
  "action": "send_message" or "general_chat",
  "recipient": "name or use context recipient",
  "message": "the actual content to send (cleaned of command words)",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}"""

            context_messages.append({"role": "system", "content": system_prompt})

            # Add conversation history AND self.conversation_context for recipient tracking
            if self.conversation_context and len(self.conversation_context) > 0:
                context_str = "Recent conversation with recipients:\n"
                for ctx in self.conversation_context[-3:]:  # Last 3 exchanges
                    user_msg = ctx.get("user", "")
                    recipient = ctx.get("recipient", "")
                    if recipient:
                        context_str += f"User: {user_msg} [Recipient was: {recipient}]\n"
                    else:
                        context_str += f"User: {user_msg}\n"
                context_messages.append({"role": "user", "content": f"Context:\n{context_str}\n\nIMPORTANT: When user says 'him', 'her', or 'also', use the LAST recipient from context above."})

            # Add current user input
            context_messages.append({
                "role": "user",
                "content": f'Analyze this command: "{user_text}"'
            })

            # Call GPT-4o (full model for best accuracy)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=context_messages,
                temperature=0.1,  # Low temp for consistent parsing
                max_tokens=200,
                response_format={"type": "json_object"}  # Force JSON output
            )

            ai_response = response.choices[0].message.content.strip()
            parsed = json.loads(ai_response)

            # Add success flag based on confidence
            parsed["success"] = parsed.get("confidence", 0) > 0.7

            logger.info(f"✅ Intent: {parsed['action']} | Recipient: {parsed.get('recipient')} | Confidence: {parsed.get('confidence', 0):.2f}")

            return parsed

        except Exception as e:
            logger.error(f"❌ Intent parsing error: {e}")
            return self._fallback_parse(user_text)

    def _fallback_parse(self, user_text: str) -> dict:
        """Simple fallback if AI parsing fails"""
        text_lower = user_text.lower()

        # Simple keyword check as fallback
        message_keywords = ["send", "message", "tell", "notify", "inform", "let know", "text"]

        if any(keyword in text_lower for keyword in message_keywords):
            return {
                "action": "send_message",
                "recipient": "unknown",
                "message": user_text,
                "confidence": 0.5,
                "success": True,
                "reasoning": "Fallback pattern matching"
            }
        else:
            return {
                "action": "general_chat",
                "recipient": None,
                "message": None,
                "confidence": 0.5,
                "success": False,
                "reasoning": "No message keywords detected"
            }


if __name__ == "__main__":
    # Test the intent parser
    parser = IntentParser()

    test_phrases = [
        "send message to John saying hello",
        "notify him I won't be available after dinner",
        "tell Sarah the meeting is at 3pm",
        "let him know I'm running late",
        "inform Mike about the changes",
        "what's the weather today",
        "how are you",
        "can you help me with something",
    ]

    print("🧪 Testing GPT-4o-mini Intent Parser")
    print("=" * 60)

    # Simulate conversation history
    history = [
        ("send message to John saying hello", "Message sent to John!"),
        ("also tell him about the meeting", "Message sent to John!")
    ]

    for phrase in test_phrases:
        print(f"\n📝 Input: '{phrase}'")
        result = parser.parse(phrase, conversation_history=history)
        print(f"✅ Action: {result['action']}")
        print(f"   Recipient: {result.get('recipient', 'N/A')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
