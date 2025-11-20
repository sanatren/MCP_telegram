#!/usr/bin/env python3
"""
Voice Assistant with Telegram Message Listener
Receives notifications and can reply naturally
"""

import os
import sys
import time
import tempfile
import requests
import pyttsx3
import sounddevice as sd
import numpy as np
import wave
import threading
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.mcp_client import MCPClientSync
from src.core.intent_parser import IntentParser
from src.messaging.telegram_listener import TelegramMessageListener

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)


class VoiceAssistantWithNotifications:
    """Voice assistant that can receive and reply to Telegram messages"""

    def __init__(self):
        # ... (copy all the __init__ code from auto_voice_assistant.py)
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'gemma2:2b')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.use_openai_tts = os.getenv('USE_OPENAI_TTS', 'false').lower() == 'true'

        # Load contacts
        self.contacts = self._load_contacts()

        # NEW: Track last received message for replies
        self.last_received_message = None
        self.pending_notification = None

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 2
        self.command_duration = 8
        self.chunk_size = 1024

        print("🔧 Initializing TTS...")
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 140)
        self.tts_engine.setProperty('volume', 0.9)

        print("✅ OpenAI Whisper API ready!")

        self.is_processing = False
        self.in_conversation = False
        self.conversation_timeout = 60
        self.last_interaction_time = 0
        self.conversation_history = []

        # Initialize MCP client
        print("🔌 Initializing MCP client for Telegram...")
        try:
            self.mcp_client = MCPClientSync()
            self.intent_parser = IntentParser()
            self.telegram_enabled = self.mcp_client.connect_telegram()
            if self.telegram_enabled:
                print("✅ Telegram MCP connected!")
        except Exception as e:
            print(f"⚠️  Could not initialize MCP: {e}")
            self.telegram_enabled = False

        # NEW: Start Telegram listener in background (OPTIONAL - can be disabled)
        self.telegram_listener = None
        self.listener_thread = None
        self.enable_notifications = os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'false').lower() == 'true'

        print("✅ Voice Assistant with Notifications ready!")

        if self.enable_notifications:
            print("⏳ Starting Telegram listener in background...")
            # Start listener after everything else is ready
            try:
                self._start_listener_thread()
            except Exception as e:
                print(f"⚠️  Telegram listener failed to start: {e}")
                print("⚠️  You can still use voice assistant, but won't get notifications")
        else:
            print("📵 Telegram notifications disabled (set ENABLE_TELEGRAM_NOTIFICATIONS=true to enable)")

    def _load_contacts(self):
        """Load contacts from contacts.json"""
        try:
            contacts_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'contacts.json')
            if os.path.exists(contacts_path):
                with open(contacts_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️  Could not load contacts: {e}")
            return {}

    def _start_listener_thread(self):
        """Start Telegram listener in a background thread"""

        def run_listener():
            """Run the async listener"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def start_listening():
                try:
                    self.telegram_listener = TelegramMessageListener(
                        on_message_callback=lambda msg: self.on_message_received(msg)
                    )
                    print("👂 Telegram listener connecting...")
                    await self.telegram_listener.start()
                except Exception as e:
                    print(f"❌ Listener error: {e}")

            try:
                loop.run_until_complete(start_listening())
            except Exception as e:
                print(f"❌ Failed to start listener: {e}")
            finally:
                loop.close()

        self.listener_thread = threading.Thread(target=run_listener, daemon=True)
        self.listener_thread.start()
        time.sleep(1)  # Give it a second to initialize
        print("✅ Telegram listener thread started (running in background)")

    def on_message_received(self, message_data):
        """Callback when new Telegram message received"""
        sender_name = message_data['sender_name']
        message_text = message_data['message']

        # Store for reply context
        self.last_received_message = message_data

        notification = f"New message from {sender_name}: {message_text}"

        # If in conversation, announce immediately
        if self.in_conversation:
            print(f"\n📩 {notification}")
            self.speak(notification)
            self.speak("Say 'reply' to respond.")
        else:
            # Store for later
            self.pending_notification = notification
            print(f"📩 {notification} (stored for next activation)")

    def fuzzy_match_contact(self, spoken_name):
        """Fuzzy match contact names"""
        contact_names = list(self.contacts.keys())
        if not contact_names:
            return {"matched": False, "name": spoken_name, "needs_confirmation": False}

        # Exact match
        spoken_lower = spoken_name.lower()
        if spoken_lower in contact_names:
            print(f"✅ Exact match: '{spoken_name}' → '{spoken_lower}'")
            return {"matched": True, "name": spoken_lower, "needs_confirmation": False, "confidence": 1.0}

        # Fuzzy match
        import difflib
        close_matches = difflib.get_close_matches(spoken_lower, contact_names, n=3, cutoff=0.6)

        if close_matches:
            best_match = close_matches[0]
            confidence = difflib.SequenceMatcher(None, spoken_lower, best_match).ratio()
            print(f"🔍 Fuzzy match: '{spoken_name}' → '{best_match}' ({confidence:.0%})")

            return {
                "matched": True,
                "name": best_match,
                "needs_confirmation": confidence < 0.9,
                "confidence": confidence,
                "alternatives": close_matches[1:] if len(close_matches) > 1 else []
            }

        print(f"❌ No match for '{spoken_name}'")
        return {"matched": False, "name": spoken_name, "needs_confirmation": False}

    def speak(self, text):
        """Text to speech"""
        print(f"🗣️  Gemma: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except:
            print("TTS Error")

    def query_ollama(self, prompt):
        """Query Ollama for general chat"""
        try:
            print("🧠 Thinking...")
            context = ""
            if len(self.conversation_history) > 0:
                context = "Previous conversation:\n"
                for user_msg, ai_msg in self.conversation_history[-3:]:
                    context += f"User: {user_msg}\nGemma: {ai_msg}\n"
                context += "\nCurrent question:\n"

            full_prompt = f"You are Gemma, a helpful voice assistant. Keep responses very short (1-2 sentences). {context}User: {prompt}"

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": full_prompt, "stream": False},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json().get('response', 'I did not understand that.').strip()
                sentences = result.split('.')[:2]
                ai_response = '.'.join(sentences).strip() + '.'
                self.conversation_history.append((prompt, ai_response))
                return ai_response
            else:
                return "I'm having trouble thinking right now."
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Sorry, I'm having connection issues."

    def record_and_transcribe_fast(self, duration, description=""):
        """Record and transcribe audio"""
        print(f"🎤 {description} ({duration}s)")

        try:
            audio_data = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=self.channels, dtype=np.float32)
            sd.wait()

            volume = np.sqrt(np.mean(audio_data**2))
            threshold = 0.008 if description == "Listening..." else 0.004
            if volume < threshold:
                return ""

            audio_data = np.clip(audio_data * 1.5, -1.0, 1.0)

            import io
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes((audio_data.flatten() * 32767).astype(np.int16).tobytes())

            wav_buffer.seek(0)

            transcript = self.openai_client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=("audio.wav", wav_buffer.read(), "audio/wav"),
                language="en",
                response_format="text"
            )

            text = transcript.strip() if transcript else ""
            if text and len(text) > 1:
                print(f"👂 {text}")
                return text
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def detect_activation(self, text):
        """Detect activation words"""
        if not text:
            return False
        text_lower = text.lower().replace(',', '').replace('.', '')
        activations = ["hello", "hi", "computer", "assistant"]
        for phrase in activations:
            if phrase in text_lower:
                print(f"🔥 Activation: '{phrase}' in '{text}'")
                return True
        return False

    def handle_user_input(self, user_text):
        """Handle user input with intent parsing"""
        print("🧠 Understanding intent...")

        intent = self.intent_parser.parse(user_text, self.conversation_history)

        if intent["action"] == "send_message" and intent["success"]:
            print(f"📱 Message intent ({intent.get('confidence', 0):.0%})")

            message = intent.get("message")
            recipient = intent.get("recipient", "recipient")

            if not message:
                return "I couldn't figure out what message to send."

            # NEW: Handle reply to last received message
            if recipient.lower() in ["him", "her", "reply", "them"] and self.last_received_message:
                recipient = self.last_received_message["sender_name"].lower().split()[0]
                print(f"💬 Replying to: {recipient}")

            # Fuzzy match
            match_result = self.fuzzy_match_contact(recipient)

            if not match_result["matched"]:
                return f"I couldn't find '{recipient}' in contacts."

            matched_name = match_result["name"]

            # Confirmation if needed
            if match_result.get("needs_confirmation"):
                self.speak(f"Did you mean {matched_name}? Yes or no.")
                conf = self.record_and_transcribe_fast(5, "Confirmation")
                if conf and "yes" in conf.lower():
                    recipient = matched_name
                else:
                    return "Message cancelled."
            else:
                recipient = matched_name

            # Send message
            try:
                result = self.mcp_client.send_telegram_message(message, recipient)
                if result and "successfully" in result:
                    response = f"Message sent to {recipient}!"
                    self.intent_parser.update_context(user_text, response, recipient)
                    return response
                else:
                    return f"Failed to send. {result}"
            except Exception as e:
                print(f"❌ Error: {e}")
                return "Sorry, I had trouble sending."
        else:
            return self.query_ollama(user_text)

    def start_conversation(self):
        """Start conversation"""
        self.in_conversation = True
        self.last_interaction_time = time.time()
        self.conversation_history = []

        print("\n🔥 Conversation started! (60s timeout)")

        # NEW: Announce pending notifications
        if self.pending_notification:
            self.speak(self.pending_notification)
            self.speak("Say 'reply' to respond.")
            self.pending_notification = None
        else:
            self.speak("Hi! What can I help you with?")

        # Conversation loop
        while self.in_conversation:
            try:
                elapsed = time.time() - self.last_interaction_time
                if elapsed > self.conversation_timeout:
                    print("⏰ Timeout")
                    self.speak("Going back to sleep. Say 'Hello' to wake me.")
                    self.in_conversation = False
                    break

                remaining = int(self.conversation_timeout - elapsed)
                user_text = self.record_and_transcribe_fast(self.command_duration, f"Listening... ({remaining}s left)")

                if user_text and len(user_text.strip()) > 2:
                    self.last_interaction_time = time.time()
                    print(f"👤 User: {user_text}")

                    if any(word in user_text.lower() for word in ["goodbye", "bye", "thanks", "stop", "exit"]):
                        self.speak("Goodbye!")
                        self.in_conversation = False
                        break

                    if self.telegram_enabled:
                        response = self.handle_user_input(user_text)
                    else:
                        response = self.query_ollama(user_text)

                    self.speak(response)
            except KeyboardInterrupt:
                self.in_conversation = False
                break
            except Exception as e:
                print(f"Error: {e}")

    def run(self):
        """Run voice activation mode"""
        print("\n🎙️  Voice Assistant Active!")
        print("Say 'Hello', 'Hi', 'Computer', or 'Assistant' to activate!")
        print("=" * 60)

        while True:
            try:
                if not self.is_processing:
                    text = self.record_and_transcribe_fast(self.chunk_duration, "Listening...")
                    if text and self.detect_activation(text):
                        self.start_conversation()
                        print("\n👂 Back to listening...")
                else:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print("\n👋 Stopped!")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

    def start(self):
        """Start the assistant"""
        # Check Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if response.status_code != 200:
                print("❌ Ollama not running!")
                return
            print("✅ Ollama connected")
        except:
            print("❌ Ollama not running!")
            return

        if not os.getenv('OPENAI_API_KEY'):
            print("❌ OpenAI API key not set!")
            return

        print("✅ OpenAI API key loaded")
        self.run()


def main():
    assistant = VoiceAssistantWithNotifications()
    assistant.start()


if __name__ == "__main__":
    main()