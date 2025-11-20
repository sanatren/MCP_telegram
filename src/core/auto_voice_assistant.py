#!/usr/bin/env python3
"""
Auto Voice Assistant - Starts directly in voice activation mode
Now with MCP integration for Telegram messaging!
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
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime
import threading
import asyncio

# Add src to path for MCP imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.mcp_client import MCPClientSync
from src.core.intent_parser import IntentParser

# Load config from project root
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(config_path)

class AutoVoiceAssistant:
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'gemma2:2b')

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # TTS options: 'local' (pyttsx3) or 'openai' (cloud TTS)
        self.use_openai_tts = os.getenv('USE_OPENAI_TTS', 'false').lower() == 'true'

        # Load contacts for fuzzy matching
        self.contacts = self._load_contacts()

        # Track last received message for reply context
        self.last_received_message = None
        self.pending_notification = None
        self.notification_just_announced = False  # Flag to prevent double responses
        self.in_reply_mode = False  # Auto-reply mode after notification
        self.notification_time = 0  # When notification was announced

        # Persistent context tracking
        self.last_messaged_recipient = None  # Remember who we last sent a message to
        self.message_context_history = []  # Track recent messaging activity

        # Event loop for Telegram operations
        self.telegram_loop = None

        # Audio settings optimized for real-time processing
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 2  # Shorter for faster detection
        self.command_duration = 8  # Recording time for user questions (increased to 8s)
        self.chunk_size = 1024  # Smaller chunks for real-time

        print("🔧 TTS will initialize on first use...")
        self.tts_engine = None  # Lazy init to avoid hanging

        print("✅ OpenAI Whisper API ready!")

        self.is_processing = False
        self.in_conversation = False
        self.conversation_timeout = 60  # 1 minute timeout like Siri
        self.last_interaction_time = 0
        self.conversation_history = []

        # Initialize Telegram client - use shared client directly to avoid database locks
        print("🔌 Initializing Telegram client...")
        self.telegram_enabled = False
        self.intent_parser = IntentParser()  # AI-powered intent understanding
        self.shared_telegram_client = None

        try:
            from src.messaging.shared_telegram_client import get_shared_client
            self.shared_telegram_client = get_shared_client()
            self.telegram_enabled = True
            print("✅ Telegram messaging enabled (shared client)!")
        except Exception as e:
            print(f"⚠️  Telegram setup failed: {e}")
            print("⚠️  Continuing without Telegram messaging")

        print("✅ Voice Assistant ready!")

        # Start Telegram listener in background (optional)
        self.telegram_listener = None
        if os.getenv('ENABLE_TELEGRAM_LISTENER', 'false').lower() == 'true':
            print("📩 Starting incoming message listener...")
            self._start_telegram_listener()
        else:
            print("📵 Message listener disabled (set ENABLE_TELEGRAM_LISTENER=true to enable)")

    def _start_telegram_listener(self):
        """Start Telegram message listener in background thread"""
        def run_listener():
            """Run async listener in background"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self.telegram_loop = loop  # Store loop for message sending

                async def start_listening():
                    """Keep listener running with auto-reconnect"""
                    retry_count = 0
                    max_retries = 999  # Essentially infinite

                    while retry_count < max_retries:
                        try:
                            from src.messaging.telegram_listener import TelegramMessageListener
                            if retry_count == 0:
                                print("📡 Initializing listener...")
                            else:
                                print(f"🔄 Reconnecting listener (attempt {retry_count + 1})...")

                            async def on_message(msg):
                                """Callback when message received - with error handling"""
                                try:
                                    print(f"📨 Callback triggered for message from {msg.get('sender_name', 'Unknown')}")
                                    self.last_received_message = msg
                                    sender = msg['sender_name']
                                    text = msg['message']
                                    notification = f"New message from {sender}: {text}"

                                    # If in conversation, interrupt with notification
                                    if self.in_conversation:
                                        print(f"\n📩 {notification}")
                                        self.notification_just_announced = True  # Skip next general chat
                                        self.in_reply_mode = True  # Enter auto-reply mode
                                        self.notification_time = time.time()

                                        # Use threading to avoid blocking the listener
                                        def announce():
                                            try:
                                                self.speak(notification)
                                                time.sleep(0.5)  # Let speaker finish
                                                self.speak("Say 'reply' to respond.")
                                                time.sleep(0.8)  # Wait for audio to clear before next listen
                                            except Exception as e:
                                                print(f"⚠️ TTS error in notification: {e}")

                                        # Run in separate thread to not block listener
                                        threading.Thread(target=announce, daemon=True).start()
                                    else:
                                        # Not in conversation - auto-start one to allow reply
                                        print(f"\n📩 {notification}")

                                        # Announce in separate thread to not block
                                        def announce_and_activate():
                                            try:
                                                self.speak(notification)
                                                time.sleep(0.5)  # Let speaker finish
                                                self.speak("Say 'reply' to respond.")
                                                time.sleep(1.0)  # Wait for audio to clear before listening

                                                # Auto-start conversation for easy reply
                                                if not self.in_conversation:
                                                    print("🔥 Auto-activating for reply...")
                                                    self.in_reply_mode = True
                                                    self.notification_time = time.time()
                                                    self.start_conversation(skip_greeting=True)
                                            except Exception as e:
                                                print(f"⚠️ Error in announce_and_activate: {e}")

                                        threading.Thread(target=announce_and_activate, daemon=True).start()

                                    print("✅ Message callback completed successfully")
                                except Exception as e:
                                    print(f"❌ Error in message callback: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    # Don't re-raise - keep listener alive!

                            self.telegram_listener = TelegramMessageListener(on_message_callback=on_message)
                            print("👂 Listener connecting to Telegram...")
                            await self.telegram_listener.start()

                            # If we get here, listener disconnected
                            print("⚠️ Listener disconnected, will reconnect in 5s...")
                            await asyncio.sleep(5)
                            retry_count += 1

                        except Exception as e:
                            print(f"\n❌ Listener error: {e}")
                            import traceback
                            traceback.print_exc()
                            print("🔄 Retrying in 10 seconds...")
                            await asyncio.sleep(10)
                            retry_count += 1

                loop.run_until_complete(start_listening())
            except Exception as e:
                print(f"\n❌ Failed to start listener thread: {e}")
                import traceback
                traceback.print_exc()
            finally:
                try:
                    loop.close()
                except:
                    pass

        listener_thread = threading.Thread(target=run_listener, daemon=True, name="TelegramListener")
        listener_thread.start()

        # Wait for event loop to be ready
        for i in range(50):  # Wait up to 5 seconds
            if self.telegram_loop:
                print("✅ Message listener thread started")
                break
            time.sleep(0.1)

        if not self.telegram_loop:
            print("⚠️ Warning: Telegram loop not ready yet")

        # Start monitoring thread
        def monitor_listener():
            """Monitor listener thread and report status"""
            while True:
                time.sleep(30)  # Check every 30 seconds
                if listener_thread.is_alive():
                    print("💚 Listener thread is alive")
                else:
                    print("❌ WARNING: Listener thread died!")

        monitor_thread = threading.Thread(target=monitor_listener, daemon=True, name="ListenerMonitor")
        monitor_thread.start()

    def _load_contacts(self) -> dict:
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

    def fuzzy_match_contact(self, spoken_name: str) -> dict:
        """Use LLM to find best matching contact name with confirmation"""
        try:
            # Get list of contact names
            contact_names = list(self.contacts.keys())

            if not contact_names:
                return {"matched": False, "name": spoken_name, "needs_confirmation": False}

            # First try exact match (case-insensitive)
            spoken_lower = spoken_name.lower()
            if spoken_lower in contact_names:
                print(f"✅ Exact match found: '{spoken_name}' → '{spoken_lower}'")
                return {
                    "matched": True,
                    "name": spoken_lower,
                    "needs_confirmation": False,
                    "confidence": 1.0
                }

            # Try fuzzy matching with Levenshtein-like similarity
            import difflib
            close_matches = difflib.get_close_matches(spoken_lower, contact_names, n=3, cutoff=0.6)

            if close_matches:
                best_match = close_matches[0]
                confidence = difflib.SequenceMatcher(None, spoken_lower, best_match).ratio()

                print(f"🔍 Fuzzy match: '{spoken_name}' → '{best_match}' (confidence: {confidence:.2f})")

                return {
                    "matched": True,
                    "name": best_match,
                    "needs_confirmation": confidence < 0.9,
                    "confidence": confidence,
                    "alternatives": close_matches[1:] if len(close_matches) > 1 else []
                }

            # No match found
            print(f"❌ No match found for '{spoken_name}'")
            return {"matched": False, "name": spoken_name, "needs_confirmation": False}


        except Exception as e:
            print(f"❌ Fuzzy match error: {e}")
            return {"matched": False, "name": spoken_name, "needs_confirmation": False}

    def log_conversation(self, user_input, ai_response):
        """Log conversation to JSON file for dashboard"""
        
        # Use data directory from project root
        log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'conversations.json')
        
        # Load existing conversations
        conversations = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    conversations = json.load(f)
            except:
                conversations = []
        
        # Add new conversation
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "ai": ai_response,
            "id": len(conversations) + 1
        }
        conversations.append(entry)
        
        # Save to file
        with open(log_file, 'w') as f:
            json.dump(conversations, f, indent=2)
    
    def speak(self, text):
        """Convert text to speech using local or OpenAI TTS"""
        print(f"🗣️  Gemma: {text}")

        # Lazy init TTS engine
        if self.tts_engine is None and not self.use_openai_tts:
            try:
                print("🔧 Initializing TTS engine...")
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 140)
                self.tts_engine.setProperty('volume', 0.9)
                print("✅ TTS ready")
            except Exception as e:
                print(f"⚠️ TTS init failed: {e}")
                self.tts_engine = False  # Mark as failed

        if self.use_openai_tts:
            try:
                # Use OpenAI TTS with latest model
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=text,
                    speed=1.1
                )
                
                # Play audio directly
                import pygame
                pygame.mixer.init()
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    response.stream_to_file(tmp_file.name)
                    pygame.mixer.music.load(tmp_file.name)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    os.unlink(tmp_file.name)
                    
            except Exception as e:
                print(f"OpenAI TTS error: {e}, falling back to local TTS")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        else:
            # Use local TTS
            if self.tts_engine and self.tts_engine is not False:
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except:
                    print("TTS Error - but continuing...")
            else:
                print("⚠️ TTS not available - text only")
    
    def query_ollama(self, prompt):
        """Query local Ollama model with conversation context"""
        try:
            print("🧠 Thinking...")
            
            # Build context from recent conversation
            context = ""
            if len(self.conversation_history) > 0:
                context = "Previous conversation:\n"
                for i, (user_msg, ai_msg) in enumerate(self.conversation_history[-3:]):  # Last 3 exchanges
                    context += f"User: {user_msg}\nGemma: {ai_msg}\n"
                context += "\nCurrent question:\n"
            
            full_prompt = f"You are Gemma, a helpful voice assistant. Keep responses very short (1-2 sentences). {context}User: {prompt}"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', 'I did not understand that.').strip()
                sentences = result.split('.')[:2]
                ai_response = '.'.join(sentences).strip() + '.'
                
                # Add to conversation history
                self.conversation_history.append((prompt, ai_response))
                
                return ai_response
            else:
                return "I'm having trouble thinking right now."
                
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Sorry, I'm having connection issues."
    
    def record_and_transcribe_fast(self, duration, description=""):
        """Fast record and transcribe using OpenAI Whisper API with optimizations"""
        print(f"🎤 {description} ({duration}s)")
        
        try:
            # Record with minimal processing
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32
            )
            sd.wait()

            # Check for invalid audio data
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                return ""

            # Quick volume check with MORE SENSITIVE threshold
            audio_squared = audio_data**2
            # Handle potential overflow
            audio_squared = np.nan_to_num(audio_squared, nan=0.0, posinf=0.0, neginf=0.0)
            volume = np.sqrt(np.mean(audio_squared))

            # Lowered thresholds for better sensitivity
            threshold = 0.002 if description == "Listening..." else 0.001
            if volume < threshold or np.isnan(volume) or np.isinf(volume):
                return ""

            # Amplify MORE for better sensitivity (3x instead of 1.5x)
            audio_data = np.clip(audio_data * 3.0, -1.0, 1.0)
            # Clean up any remaining NaN/inf values
            audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)
            
            # Create audio file in memory buffer
            import io
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes((audio_data.flatten() * 32767).astype(np.int16).tobytes())
            
            wav_buffer.seek(0)
            
            try:
                # Use Whisper-1 (best accuracy)
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", wav_buffer.read(), "audio/wav"),
                    language="en",
                    response_format="text"
                )
                
                text = transcript.strip() if transcript else ""
                
                if text and len(text) > 1:
                    print(f"👂 {text}")
                    return text
                else:
                    return ""
                        
            except Exception as e:
                print(f"API error: {e}")
                return ""
                    
        except Exception as e:
            print(f"Recording error: {e}")
            return ""
    
    def detect_activation(self, text):
        """Check if text contains activation words"""
        if not text:
            return False

        text_lower = text.lower().replace(',', '').replace('.', '')

        activations = [
            "hello", "hi", "computer", "assistant"
        ]

        for phrase in activations:
            if phrase in text_lower:
                print(f"🔥 Activation detected: '{phrase}' in '{text}'")
                return True

        return False

    def normalize_message_to_first_person(self, message: str) -> str:
        """Convert 3rd person commands to 1st person messages for natural conversation"""
        import re

        # Remove command prefixes (tell him, remind him, notify him, etc.)
        message = re.sub(r'^\s*(tell|remind|notify|inform|let|ask)\s+(him|her|them)\s+(that\s+)?', '', message, flags=re.IGNORECASE)
        message = re.sub(r'^\s*(tell|remind|notify|inform|let|ask)\s+', '', message, flags=re.IGNORECASE)

        # Remove "that" at the beginning
        message = re.sub(r'^\s*that\s+', '', message, flags=re.IGNORECASE)

        # Remove "to" at the beginning (e.g., "to drink water" -> "drink water")
        message = re.sub(r'^\s*to\s+', '', message, flags=re.IGNORECASE)

        # Clean up extra spaces
        message = ' '.join(message.split())

        return message.strip()

    def send_telegram_message_sync(self, message: str, recipient: str) -> str:
        """Synchronous wrapper for async send_message"""
        if not self.telegram_loop:
            return None

        async def _send():
            result = await self.shared_telegram_client.send_message(recipient, message)
            if result.get("success"):
                return f"Message sent to {recipient} successfully"
            else:
                return None

        # Use the listener's event loop to avoid loop conflicts
        future = asyncio.run_coroutine_threadsafe(_send(), self.telegram_loop)
        try:
            return future.result(timeout=10)  # 10 second timeout
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None

    def handle_user_input(self, user_text):
        """
        Intelligently handle user input using AI intent parsing with conversation history
        Determines if it's a Telegram command or regular chat
        """
        user_lower = user_text.lower()

        # Check if we're in auto-reply mode (within 60 seconds of notification)
        time_since_notification = time.time() - self.notification_time
        if self.in_reply_mode and time_since_notification < 60 and self.last_received_message:
            # Check if user wants to exit reply mode
            if any(phrase in user_lower for phrase in ["never mind", "no thanks", "skip", "ignore", "cancel"]):
                self.in_reply_mode = False
                return "Okay, cancelled."

            # Check if this is NOT a new send command or general question
            if not any(word in user_lower for word in ["send message to", "tell someone", "notify someone", "what", "how", "why", "when", "who"]):
                # Treat this as a reply to the last message
                sender = self.last_received_message["sender_name"].split()[0].lower()

                # Normalize to 1st person
                message = self.normalize_message_to_first_person(user_text)

                print(f"💬 Auto-reply to {sender}: {message}")

                try:
                    result = self.send_telegram_message_sync(message, sender)
                    if result and "successfully" in result:
                        # Track this messaging activity
                        self.last_messaged_recipient = sender
                        self.message_context_history.append({
                            "recipient": sender,
                            "message": message,
                            "type": "auto_reply"
                        })
                        # Exit reply mode after successful send
                        self.in_reply_mode = False
                        return f"Reply sent to {sender}!"
                    else:
                        self.in_reply_mode = False
                        return f"Failed to send reply. Error: {result}"
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
                    self.in_reply_mode = False
                    return "Sorry, I had trouble sending that reply."

        # Check for explicit "reply" command
        is_reply = any(word in user_lower for word in ["reply", "respond", "answer"])

        if is_reply and self.last_received_message:
            # This is a reply to the last message
            sender = self.last_received_message["sender_name"].split()[0].lower()

            # Extract the message content (remove "reply" keywords only)
            import re
            # Remove reply keywords but keep the actual message
            message = user_text
            # Remove leading "reply/respond/answer" keywords
            message = re.sub(r'^\s*(reply|respond|answer)\s*,?\s*', '', message, flags=re.IGNORECASE)

            # Normalize to 1st person
            message = self.normalize_message_to_first_person(message)

            if len(message) > 2:
                print(f"💬 Quick reply to {sender}: {message}")

                try:
                    result = self.send_telegram_message_sync(message, sender)
                    if result and "successfully" in result:
                        # Track this messaging activity
                        self.last_messaged_recipient = sender
                        self.message_context_history.append({
                            "recipient": sender,
                            "message": message,
                            "type": "reply"
                        })
                        return f"Reply sent to {sender}!"
                    else:
                        return f"Failed to send reply. Error: {result}"
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
                    return "Sorry, I had trouble sending that reply."

        # Check if this is a follow-up message (no explicit recipient mentioned)
        # Keywords that suggest follow-up: "also", "and", "plus", "additionally"
        follow_up_keywords = ["also", "and also", "plus", "additionally", "too"]
        is_follow_up = any(keyword in user_lower for keyword in follow_up_keywords)

        if is_follow_up and self.last_messaged_recipient and not any(word in user_lower for word in ["send message to", "tell", "notify"]):
            # This is a follow-up to the last person we messaged
            recipient = self.last_messaged_recipient

            # Extract message (remove follow-up keywords)
            import re
            message = user_text
            message = re.sub(r'^\s*(also|and also|plus|additionally|too)\s*,?\s*', '', message, flags=re.IGNORECASE)

            # Normalize to 1st person
            message = self.normalize_message_to_first_person(message)

            print(f"📤 Follow-up message to {recipient}: {message}")

            try:
                result = self.send_telegram_message_sync(message, recipient)
                if result and "successfully" in result:
                    # Track this messaging activity
                    self.message_context_history.append({
                        "recipient": recipient,
                        "message": message,
                        "type": "follow_up"
                    })
                    return f"Message sent to {recipient}!"
                else:
                    return f"Failed to send message. Error: {result}"
            except Exception as e:
                print(f"❌ Telegram error: {e}")
                return "Sorry, I had trouble sending that message."

        print("🧠 Understanding intent with context...")

        # Update intent parser with last messaged recipient context
        if self.last_messaged_recipient:
            self.intent_parser.update_context(
                f"Last messaged recipient was {self.last_messaged_recipient}",
                "",
                self.last_messaged_recipient
            )

        # Pass conversation history to intent parser for context
        intent = self.intent_parser.parse(user_text, self.conversation_history)

        if intent["action"] == "send_message" and intent["success"]:
            # User wants to send a message
            print(f"📱 Detected message intent (confidence: {intent.get('confidence', 0):.2f})")
            print(f"   Reasoning: {intent.get('reasoning', 'N/A')}")

            message = intent.get("message")
            recipient = intent.get("recipient", "recipient")

            if not message:
                return "I understood you want to send a message, but I couldn't figure out what to say."

            # Normalize message to 1st person
            message = self.normalize_message_to_first_person(message)
            print(f"📝 Normalized message: {message}")

            # Check if this is a reply to last received message
            if recipient.lower() in ["him", "her", "them", "unknown"] and self.last_received_message:
                recipient = self.last_received_message["sender_name"].lower().split()[0]
                print(f"💬 Replying to last sender: {recipient}")
            # Check if recipient is vague but we have last messaged context
            elif recipient.lower() in ["him", "her", "them", "unknown"] and self.last_messaged_recipient:
                recipient = self.last_messaged_recipient
                print(f"💬 Continuing conversation with: {recipient}")

            # Fuzzy match the recipient name
            match_result = self.fuzzy_match_contact(recipient)

            if not match_result["matched"]:
                return f"I couldn't find '{recipient}' in your contacts. Can you spell it or try another name?"

            matched_name = match_result["name"]

            # If needs confirmation, ask user
            if match_result.get("needs_confirmation"):
                self.speak(f"Did you mean {matched_name}? Say yes or no.")
                confirmation = self.record_and_transcribe_fast(5, "Waiting for confirmation")

                if confirmation and "yes" in confirmation.lower():
                    recipient = matched_name
                elif confirmation and "no" in confirmation.lower():
                    # Check alternatives
                    alts = match_result.get("alternatives", [])
                    if alts:
                        self.speak(f"How about {alts[0]}? Say yes or no.")
                        conf2 = self.record_and_transcribe_fast(5, "Waiting for confirmation")
                        if conf2 and "yes" in conf2.lower():
                            recipient = alts[0]
                        else:
                            return "Okay, message cancelled. Try again with the correct name."
                    else:
                        return "Okay, message cancelled. Try again with the correct name."
                else:
                    return "I didn't hear a clear yes or no. Message cancelled."
            else:
                recipient = matched_name

            try:
                result = self.send_telegram_message_sync(message, recipient)

                if result and "successfully" in result:
                    response = f"Message sent to {recipient}!"

                    # Track this messaging activity for persistent context
                    self.last_messaged_recipient = recipient
                    self.message_context_history.append({
                        "recipient": recipient,
                        "message": message,
                        "type": "sent"
                    })
                    # Keep only last 10 messages for context
                    if len(self.message_context_history) > 10:
                        self.message_context_history = self.message_context_history[-10:]

                    # Update intent parser context with this interaction
                    self.intent_parser.update_context(user_text, response, recipient)
                    return response
                else:
                    return f"Failed to send the message. Error: {result}"
            except Exception as e:
                print(f"❌ Telegram error: {e}")
                return "Sorry, I had trouble sending that message."

        else:
            # Regular conversation - use Ollama
            return self.query_ollama(user_text)
    
    def start_conversation(self, skip_greeting=False):
        """Start a new conversation session (like Siri)"""
        self.in_conversation = True
        self.last_interaction_time = time.time()
        # Don't clear conversation history - maintain context across activations
        # self.conversation_history = []  # Keep context!

        print("\n🔥 Conversation started! (60s timeout)")

        # Show context info
        if self.last_messaged_recipient:
            print(f"💬 Context: Last messaged {self.last_messaged_recipient}")

        # Announce pending notifications first
        if self.pending_notification:
            self.speak(self.pending_notification)
            self.speak("Say 'reply' to respond, or ask me anything else.")
            self.pending_notification = None
            # Enter reply mode for pending notifications too
            self.in_reply_mode = True
            self.notification_time = time.time()
        elif not skip_greeting:
            # Only greet if not skipping (e.g., auto-activated by notification)
            self.speak("Hi! What can I help you with?")
        
        # Enter conversation loop
        while self.in_conversation:
            try:
                # Check timeout BEFORE trying to record
                elapsed_time = time.time() - self.last_interaction_time
                if elapsed_time > self.conversation_timeout:
                    print("⏰ Conversation timeout - returning to listening mode")
                    self.speak("I'm going back to sleep now. Say 'Hello' to wake me up!")
                    self.in_conversation = False
                    break
                
                # Show remaining time
                remaining_time = int(self.conversation_timeout - elapsed_time)

                # Show reply mode indicator
                mode_indicator = ""
                if self.in_reply_mode and self.last_received_message:
                    mode_indicator = f" [REPLY MODE: {self.last_received_message['sender_name']}]"

                # Listen for user input
                user_text = self.record_and_transcribe_fast(
                    self.command_duration,
                    f"Listening... ({remaining_time}s left){mode_indicator}"
                )
                
                if user_text and len(user_text.strip()) > 2:
                    # Reset timeout on valid input
                    self.last_interaction_time = time.time()
                    print(f"👤 User: {user_text}")

                    # Check if notification was just announced - skip this input to avoid double response
                    if self.notification_just_announced:
                        print("🔕 Skipping response (notification just announced)")
                        self.notification_just_announced = False
                        continue

                    # Check for goodbye/exit commands
                    text_lower = user_text.lower()
                    if any(word in text_lower for word in ["goodbye", "bye", "thanks", "that's all", "stop", "exit"]):
                        self.speak("Goodbye! Say 'Hello' when you need me again.")
                        self.in_conversation = False
                        break

                    # Use AI to intelligently handle input (Telegram or chat)
                    if self.telegram_enabled:
                        response = self.handle_user_input(user_text)
                    else:
                        response = self.query_ollama(user_text)

                    self.speak(response)
                    self.log_conversation(user_text, response)
                    
                else:
                    # No clear input - DON'T reset timer, let it timeout naturally
                    remaining_time = int(self.conversation_timeout - (time.time() - self.last_interaction_time))
                    if remaining_time > 5:
                        print(f"🔇 Silence... ({remaining_time}s until timeout)")
                    elif remaining_time > 0:
                        print(f"⏰ Timing out in {remaining_time}s...")
                    
            except KeyboardInterrupt:
                self.in_conversation = False
                break
            except Exception as e:
                print(f"Conversation error: {e}")
                # Don't reset timeout on errors - let conversation timeout naturally
    
    def run(self):
        """Run voice activation mode"""
        print("\n🎙️  Voice Activation Mode Active!")
        print("Say 'Hello', 'Hi', 'Computer', or 'Assistant' to activate!")
        print("Press Ctrl+C to stop")
        print("=" * 40)
        
        while True:
            try:
                if not self.is_processing:
                    # Listen for activation with fast processing
                    text = self.record_and_transcribe_fast(
                        self.chunk_duration, 
                        "Listening..."
                    )
                    
                    if text and self.detect_activation(text):
                        self.start_conversation()
                        print("\n👂 Back to listening for activation word...")
                else:
                    time.sleep(0.5)
                    
            except KeyboardInterrupt:
                print("\n👋 Voice assistant stopped!")
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
                print("❌ Ollama not running! Start it with: ollama serve")
                return
            print("✅ Ollama connected")
        except:
            print("❌ Cannot connect to Ollama. Start it with: ollama serve")
            return
        
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
            print("❌ OpenAI API key not set! Please add it to .env file")
            return
        
        print("✅ OpenAI API key loaded")
        
        # Start voice activation
        self.run()

def main():
    assistant = AutoVoiceAssistant()
    assistant.start()

if __name__ == "__main__":
    main()