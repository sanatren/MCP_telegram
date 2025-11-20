# Gemma Voice Assistant + Telegram MCP Integration - Detailed Project Flow

## 🎯 Project Overview
A voice-activated AI assistant (like Siri) that uses local Ollama LLM for responses and integrates with Telegram messaging via MCP (Model Context Protocol). Users can speak naturally to send messages, get information, and control Telegram through voice commands.

---

## 📐 System Architecture

### High-Level Components
```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERACTION                        │
│          Voice Input → Microphone → Audio Processing         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    VOICE ASSISTANT CORE                      │
│  • Auto Voice Assistant (auto_voice_assistant.py)           │
│  • Activation Detection (Hello, Hi, Computer, Assistant)     │
│  • Conversation Management (60s timeout like Siri)           │
│  • Speech-to-Text (OpenAI gpt-4o-mini-transcribe)          │
│  • Text-to-Speech (Local pyttsx3 or OpenAI TTS)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     INTENT UNDERSTANDING                     │
│  • Intent Parser (intent_parser.py)                         │
│  • GPT-4o-mini for natural language understanding           │
│  • Context-aware (tracks conversation history)              │
│  • Distinguishes: Message sending vs General chat           │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴───────────┐
          │                        │
          ▼                        ▼
┌──────────────────┐    ┌──────────────────────┐
│  TELEGRAM PATH   │    │   GENERAL CHAT PATH  │
│  (if message     │    │   (if casual conv.)  │
│   intent)        │    │                      │
└────────┬─────────┘    └───────┬──────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐    ┌──────────────────────┐
│  MCP CLIENT      │    │  OLLAMA LLM          │
│  (mcp_client.py) │    │  (gemma2:2b)         │
│                  │    │  Local inference     │
└────────┬─────────┘    └───────┬──────────────┘
         │                      │
         ▼                      │
┌──────────────────┐            │
│  MCP SERVER      │            │
│  (telegram_      │            │
│   server.py)     │            │
│  Stdio protocol  │            │
└────────┬─────────┘            │
         │                      │
         ▼                      │
┌──────────────────┐            │
│  TELETHON USER   │            │
│  CLIENT          │            │
│  (telethon_user_ │            │
│   client.py)     │            │
└────────┬─────────┘            │
         │                      │
         ▼                      │
┌──────────────────┐            │
│  TELEGRAM API    │            │
│  (Sends message  │            │
│   from user      │            │
│   account)       │            │
└──────────────────┘            │
                                │
                    ┌───────────┘
                    ▼
           ┌──────────────────┐
           │   RESPONSE       │
           │   Spoken to user │
           └──────────────────┘
```

---

## 🔄 Detailed Flow Diagrams

### 1️⃣ VOICE ACTIVATION FLOW
```
START: Background listening mode
   │
   ├─► Record 2-second audio chunk
   │      │
   │      ├─► Check volume threshold (> 0.008)
   │      │      │
   │      │      ├─ NO → Continue listening
   │      │      │
   │      │      └─ YES → Send to OpenAI Whisper API
   │      │              │
   │      │              ├─► Transcribe audio
   │      │              │
   │      │              └─► Check for activation words
   │      │                     [hello, hi, computer, assistant]
   │      │                     │
   │      │                     ├─ NO → Continue listening
   │      │                     │
   │      │                     └─ YES → START CONVERSATION
   │      │                              │
   │      │                              ├─► Play "Hi! What can I help you with?"
   │      │                              ├─► Set 60s timeout timer
   │      │                              ├─► Clear conversation history
   │      │                              └─► Enter conversation loop
   │      │
   │      └─► Loop back to start
   │
   └─► Repeat continuously
```

### 2️⃣ CONVERSATION FLOW (Active Session)
```
CONVERSATION ACTIVE (60s timeout running)
   │
   ├─► Record 8-second audio chunk
   │      │
   │      ├─► Check volume threshold (> 0.004)
   │      │      │
   │      │      ├─ NO → Show "Silence..." message
   │      │      │      └─► Check timeout (elapsed > 60s?)
   │      │      │            ├─ YES → End conversation, speak goodbye
   │      │      │            └─ NO → Continue waiting
   │      │      │
   │      │      └─ YES → Transcribe with OpenAI
   │      │              │
   │      │              ├─► Get user text
   │      │              │
   │      │              ├─► RESET 60s timer (user spoke!)
   │      │              │
   │      │              ├─► Check for exit commands
   │      │              │      [goodbye, bye, thanks, that's all, stop, exit]
   │      │              │      │
   │      │              │      ├─ YES → End conversation, speak goodbye
   │      │              │      │
   │      │              │      └─ NO → Process user input
   │      │              │              │
   │      │              │              └─► GO TO: INTENT UNDERSTANDING FLOW
   │      │              │
   │      │              └─► After response:
   │      │                     ├─► Log to conversations.json
   │      │                     ├─► Speak response
   │      │                     └─► Loop back (with reset timer)
   │      │
   │      └─► Check timeout before next iteration
   │             │
   │             ├─ Timeout reached → End conversation
   │             │
   │             └─ Time remaining → Continue loop
   │
   └─► Exit: Return to listening mode
```

### 3️⃣ INTENT UNDERSTANDING FLOW
```
USER TEXT INPUT
   │
   ├─► Pass to IntentParser.parse(user_text, conversation_history)
   │      │
   │      ├─► Build context from recent conversation
   │      │      │
   │      │      ├─► Include last 3 message exchanges
   │      │      ├─► Track recipients from previous messages
   │      │      └─► Handle pronouns (him, her, them) using context
   │      │
   │      ├─► Send to GPT-4o-mini with system prompt
   │      │      │
   │      │      ├─► System: You are intent parser...
   │      │      ├─► Context: Recent conversation with recipients...
   │      │      └─► User: Analyze this command: "{user_text}"
   │      │
   │      ├─► GPT-4o-mini returns JSON
   │      │      {
   │      │        "action": "send_message" | "general_chat",
   │      │        "recipient": "name",
   │      │        "message": "cleaned message content",
   │      │        "confidence": 0.85,
   │      │        "reasoning": "explanation"
   │      │      }
   │      │
   │      └─► Check confidence > 0.7 → Set success: true
   │
   ├─► BRANCH on action type:
   │      │
   │      ├─► ACTION: "send_message" (confidence > 0.7)
   │      │      │
   │      │      └─► GO TO: TELEGRAM MESSAGE FLOW
   │      │
   │      └─► ACTION: "general_chat" OR low confidence
   │             │
   │             └─► GO TO: OLLAMA CHAT FLOW
   │
   └─► Return response to conversation loop
```

### 4️⃣ TELEGRAM MESSAGE FLOW
```
SEND_MESSAGE INTENT DETECTED
   │
   ├─► Extract recipient and message from intent
   │      │
   │      ├─► recipient = intent["recipient"]
   │      └─► message = intent["message"]
   │
   ├─► FUZZY MATCH RECIPIENT
   │      │
   │      ├─► Load contacts from config/contacts.json
   │      │      {
   │      │        "john": "+1234567890",
   │      │        "sarah": "+9876543210",
   │      │        ...
   │      │      }
   │      │
   │      ├─► Try exact match (case-insensitive)
   │      │      │
   │      │      ├─ FOUND → confidence = 1.0, no confirmation needed
   │      │      │
   │      │      └─ NOT FOUND → Try fuzzy matching
   │      │              │
   │      │              ├─► Use difflib.get_close_matches()
   │      │              │      cutoff = 0.6
   │      │              │
   │      │              ├─► Calculate similarity ratio
   │      │              │
   │      │              ├─► If ratio < 0.9 → needs_confirmation = true
   │      │              │      │
   │      │              │      ├─► Speak: "Did you mean {name}? Say yes or no."
   │      │              │      ├─► Record 5s audio
   │      │              │      ├─► Transcribe
   │      │              │      │
   │      │              │      ├─ "yes" → Use matched name
   │      │              │      │
   │      │              │      └─ "no" → Try alternatives
   │      │              │            │
   │      │              │            ├─ Has alternatives?
   │      │              │            │    └─► Ask about next match
   │      │              │            │
   │      │              │            └─ No alternatives?
   │      │              │                 └─► "Message cancelled"
   │      │              │
   │      │              └─► If ratio >= 0.9 → Auto-accept match
   │      │
   │      └─► No match found → Return error message
   │
   ├─► SEND VIA MCP
   │      │
   │      ├─► Call MCPClientSync.send_telegram_message(message, recipient)
   │      │      │
   │      │      ├─► Check if MCP connected
   │      │      │      └─► If not, connect first
   │      │      │
   │      │      ├─► Build arguments: {"message": text, "recipient": name}
   │      │      │
   │      │      └─► asyncio.run(client.call_tool("telegram", "send_telegram_message", args))
   │      │
   │      ├─► MCP CLIENT LAYER
   │      │      │
   │      │      ├─► Create StdioServerParameters
   │      │      │      command: "python"
   │      │      │      args: ["src/mcp_servers/telegram_server.py"]
   │      │      │
   │      │      ├─► Open stdio connection to MCP server
   │      │      │
   │      │      ├─► Initialize ClientSession
   │      │      │
   │      │      ├─► Call session.call_tool(tool_name, arguments)
   │      │      │
   │      │      └─► Extract text from result.content[0].text
   │      │
   │      ├─► MCP SERVER LAYER
   │      │      │
   │      │      ├─► Receive stdio request
   │      │      │
   │      │      ├─► Parse tool name: "send_telegram_message"
   │      │      │
   │      │      ├─► Extract arguments: recipient, message
   │      │      │
   │      │      ├─► Call TelethonUserClient.send_message(recipient, message)
   │      │      │
   │      │      └─► Return TextContent with result
   │      │
   │      ├─► TELETHON USER CLIENT LAYER
   │      │      │
   │      │      ├─► Load config/contacts.json
   │      │      │
   │      │      ├─► Resolve recipient:
   │      │      │      │
   │      │      │      ├─► Is it a contact name? → Look up phone number
   │      │      │      ├─► Is it @username? → Use as-is
   │      │      │      └─► Is it phone number? → Use as-is
   │      │      │
   │      │      ├─► Connect to Telegram via Telethon
   │      │      │      │
   │      │      │      ├─► Use session file: config/telegram_session.session
   │      │      │      ├─► API ID and API Hash from .env
   │      │      │      └─► Authenticate as USER account (not bot)
   │      │      │
   │      │      ├─► Get entity (user or chat)
   │      │      │      await client.get_entity(recipient)
   │      │      │
   │      │      ├─► Send message
   │      │      │      await client.send_message(entity, message)
   │      │      │
   │      │      └─► Return result:
   │      │             {
   │      │               "success": true,
   │      │               "message_id": 12345,
   │      │               "recipient": "john",
   │      │               "resolved_as": "+1234567890"
   │      │             }
   │      │
   │      └─► TELEGRAM API
   │             │
   │             └─► Message delivered to recipient
   │
   ├─► UPDATE CONTEXT
   │      │
   │      └─► intent_parser.update_context(user_text, response, recipient)
   │             ├─► Store in conversation_context list
   │             └─► Keep only last 5 exchanges
   │
   └─► RETURN RESPONSE
          │
          ├─ SUCCESS → "Message sent to {recipient}!"
          │
          └─ FAILURE → "Failed to send message: {error}"
```

### 5️⃣ OLLAMA CHAT FLOW
```
GENERAL_CHAT OR NON-MESSAGE INTENT
   │
   ├─► Build context from conversation_history
   │      │
   │      ├─► Get last 3 user-AI exchanges
   │      │      [
   │      │        ("what's the weather", "It's sunny today"),
   │      │        ("and tomorrow?", "Tomorrow will be rainy"),
   │      │      ]
   │      │
   │      └─► Format as:
   │             "Previous conversation:
   │              User: what's the weather
   │              Gemma: It's sunny today
   │              User: and tomorrow?
   │              Gemma: Tomorrow will be rainy
   │
   │              Current question:
   │              User: {current_prompt}"
   │
   ├─► Send to Ollama API
   │      │
   │      ├─► Endpoint: http://localhost:11434/api/generate
   │      │
   │      ├─► Request:
   │      │      {
   │      │        "model": "gemma2:2b",
   │      │        "prompt": full_prompt_with_context,
   │      │        "stream": false
   │      │      }
   │      │
   │      ├─► Response:
   │      │      {
   │      │        "response": "AI generated response...",
   │      │        ...
   │      │      }
   │      │
   │      └─► Extract and clean response
   │             │
   │             ├─► Take first 2 sentences (for brevity)
   │             └─► Store in conversation_history
   │
   └─► RETURN RESPONSE
          │
          └─► Response spoken to user via TTS
```

---

## 📦 Component Breakdown

### Core Components

#### 1. AutoVoiceAssistant (`auto_voice_assistant.py`)
**Purpose**: Main orchestrator - handles voice activation, recording, transcription, and coordination

**Key Methods**:
- `__init__()`: Initialize OpenAI, Ollama, TTS, MCP client, contacts
- `run()`: Main loop for voice activation listening
- `detect_activation(text)`: Check for [hello, hi, computer, assistant]
- `start_conversation()`: Enter 60s conversation mode
- `record_and_transcribe_fast(duration)`: Record audio → OpenAI Whisper → text
- `handle_user_input(user_text)`: Route to Telegram or Ollama based on intent
- `fuzzy_match_contact(name)`: Match spoken name to contacts.json with confirmation
- `speak(text)`: Output via local TTS or OpenAI TTS
- `log_conversation()`: Save to data/conversations.json

**State Management**:
- `in_conversation`: Boolean flag
- `last_interaction_time`: Timestamp for timeout
- `conversation_history`: List of (user_text, ai_response) tuples
- `is_processing`: Prevent parallel processing

**Audio Settings**:
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Chunk duration: 2s (activation listening)
- Command duration: 8s (user input)
- Volume thresholds: 0.008 (activation), 0.004 (conversation)

#### 2. IntentParser (`intent_parser.py`)
**Purpose**: AI-powered natural language understanding using GPT-4o-mini

**Key Methods**:
- `parse(user_text, conversation_history)`: Main parsing function
- `update_context(user_text, response, recipient)`: Track conversation for pronoun resolution
- `_fallback_parse(user_text)`: Simple keyword matching if GPT fails

**System Prompt Logic**:
```
Analyze user commands and extract:
1. Action type (send_message vs general_chat)
2. Recipient (with pronoun resolution using context)
3. Clean message content (remove filler words)

RULES:
- "saying that X" → message: "X" (not "that X")
- "also tell him" → use LAST recipient from context
- Handle pronouns: him, her, them, also
```

**Context Tracking**:
- Stores last 5 message exchanges
- Each entry: {user, assistant, recipient}
- Used to resolve pronouns like "him" → "john"

**Output Format**:
```json
{
  "action": "send_message" | "general_chat",
  "recipient": "john",
  "message": "cleaned text",
  "confidence": 0.85,
  "reasoning": "explanation",
  "success": true/false
}
```

#### 3. MCPClient (`mcp_client.py`)
**Purpose**: Connect to MCP servers and execute tools programmatically

**Key Classes**:
- `MCPClient`: Async client for MCP protocol
- `MCPClientSync`: Synchronous wrapper for voice assistant

**Key Methods**:
- `connect_server(name, command, args)`: Establish stdio connection to MCP server
- `call_tool(server_name, tool_name, arguments)`: Execute MCP tool
- `list_tools(server_name)`: Discover available tools

**Connection Flow**:
```python
server_params = StdioServerParameters(
    command="python",
    args=["src/mcp_servers/telegram_server.py"]
)
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(tool_name, args)
```

#### 4. TelegramServer (`telegram_server.py`)
**Purpose**: MCP server exposing Telegram capabilities via stdio protocol

**Available Tools**:
1. `send_telegram_message`: Send text from user account
   - Parameters: recipient (name/@username/phone), message
2. `send_telegram_photo`: Send photo
   - Parameters: photo_path, caption, chat_id
3. `send_telegram_document`: Send file
   - Parameters: document_path, caption, chat_id
4. `get_telegram_bot_info`: Get bot details
5. `get_telegram_chat_info`: Get chat details

**MCP Protocol**:
- Transport: stdio (stdin/stdout)
- Format: JSON-RPC
- Decorators: @app.list_tools(), @app.call_tool()

**Execution Flow**:
```
Request → stdio → @call_tool() → TelethonUserClient → Telegram API
Response ← stdio ← TextContent ← Result ← API Response
```

#### 5. TelethonUserClient (`telethon_user_client.py`)
**Purpose**: Actual Telegram API integration using Telethon (user account, not bot)

**Key Features**:
- Authenticates as user account (not bot)
- Supports contact names, @usernames, phone numbers
- Loads contacts from config/contacts.json
- Session persistence in config/telegram_session.session

**Key Methods**:
- `start()`: Initialize and authenticate Telethon client
- `send_message(recipient, message)`: Resolve recipient and send
- `send_photo()`, `send_document()`: Media sending
- `get_me()`: Get current user info
- `_resolve_recipient(identifier)`: Convert name/username/phone to entity

**Recipient Resolution Logic**:
```
Input: "john"
  └─► Load contacts.json → {"john": "+1234567890"}
      └─► Use phone number to get entity
          └─► Send message

Input: "@johndoe"
  └─► Use username directly
      └─► Get entity by username
          └─► Send message

Input: "+1234567890"
  └─► Use phone directly
      └─► Get entity by phone
          └─► Send message
```

---

## 🗂️ Data Structures

### Configuration Files

#### `config/.env`
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:2b

# TTS
USE_OPENAI_TTS=false  # false = local, true = OpenAI

# Telegram Bot (legacy, for bot approach)
TELEGRAM_BOT_TOKEN=8364724814:...
TELEGRAM_CHAT_ID=1237082783

# Telethon (for user account messaging)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
```

#### `config/contacts.json`
```json
{
  "john": "+1234567890",
  "sarah": "+9876543210",
  "mike": "+1122334455",
  "emma": "@emma_username"
}
```

#### `data/conversations.json`
```json
[
  {
    "id": 1,
    "timestamp": "2024-11-03 15:30:22",
    "user": "send message to john saying hello",
    "ai": "Message sent to john!"
  },
  {
    "id": 2,
    "timestamp": "2024-11-03 15:31:05",
    "user": "what's the weather",
    "ai": "I don't have access to weather data currently."
  }
]
```

---

## 🔀 Key Algorithms

### 1. Fuzzy Contact Matching
```python
def fuzzy_match_contact(spoken_name: str) -> dict:
    # Step 1: Exact match (case-insensitive)
    if spoken_name.lower() in contacts:
        return {matched: True, name: spoken_name, confidence: 1.0}

    # Step 2: Fuzzy matching
    import difflib
    matches = difflib.get_close_matches(
        spoken_name.lower(),
        contact_names,
        n=3,  # Top 3 matches
        cutoff=0.6  # 60% similarity minimum
    )

    if matches:
        best_match = matches[0]
        confidence = SequenceMatcher(None, spoken_name, best_match).ratio()

        # Step 3: Confirmation check
        if confidence < 0.9:  # 90% threshold
            needs_confirmation = True
            # Voice assistant will ask: "Did you mean {best_match}?"

        return {
            matched: True,
            name: best_match,
            confidence: confidence,
            needs_confirmation: needs_confirmation,
            alternatives: matches[1:]
        }

    return {matched: False}
```

### 2. Timeout Management
```python
# On conversation start
in_conversation = True
last_interaction_time = time.time()
timeout = 60  # seconds

# In conversation loop
while in_conversation:
    elapsed = time.time() - last_interaction_time

    if elapsed > timeout:
        speak("I'm going back to sleep now.")
        in_conversation = False
        break

    remaining = timeout - elapsed
    user_text = record_and_transcribe(8, f"Listening... ({remaining}s left)")

    if user_text:
        # Reset timer on valid input
        last_interaction_time = time.time()
        process_input(user_text)
    else:
        # No input - let timer continue (don't reset)
        continue
```

### 3. Volume-Based Voice Detection
```python
def record_and_transcribe(duration, description):
    # Record audio
    audio_data = sd.rec(duration * sample_rate, ...)
    sd.wait()

    # Volume check
    volume = np.sqrt(np.mean(audio_data**2))

    # Different thresholds for different modes
    if description == "Listening...":  # Activation mode
        threshold = 0.008  # Stricter (require louder voice)
    else:  # Conversation mode
        threshold = 0.004  # More sensitive

    if volume < threshold:
        return ""  # Too quiet, ignore

    # Amplify and normalize
    audio_data = np.clip(audio_data * 1.5, -1.0, 1.0)

    # Send to OpenAI Whisper
    transcript = openai_client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=audio_wav,
        language="en"
    )

    return transcript.strip()
```

---

## 🌊 Complete User Journey Examples

### Example 1: Send Single Message
```
┌─ User says: "Hello"
│
├─ Voice Assistant:
│    ├─► Detects activation word "hello"
│    ├─► Enters conversation mode (60s timer starts)
│    └─► Speaks: "Hi! What can I help you with?"
│
├─ User says: "Send message to John saying hello how are you"
│
├─ Voice Assistant:
│    ├─► Records 8s audio
│    ├─► Transcribes: "Send message to John saying hello how are you"
│    ├─► Intent Parser (GPT-4o-mini):
│    │     • action: "send_message"
│    │     • recipient: "john"
│    │     • message: "hello how are you"
│    │     • confidence: 0.95
│    │
│    ├─► Fuzzy match "john" in contacts.json
│    │     • Exact match found: "john" → "+1234567890"
│    │     • No confirmation needed (confidence: 1.0)
│    │
│    ├─► Call MCP Client
│    │     ├─► Connect to telegram MCP server
│    │     ├─► Call tool: send_telegram_message
│    │     │     args: {recipient: "john", message: "hello how are you"}
│    │     │
│    │     ├─► MCP Server receives request
│    │     │     ├─► Parse recipient: "john"
│    │     │     ├─► Load contacts.json
│    │     │     ├─► Resolve "john" → "+1234567890"
│    │     │     │
│    │     │     ├─► Telethon sends message
│    │     │     │     ├─► Get entity: +1234567890
│    │     │     │     └─► Send: "hello how are you"
│    │     │     │
│    │     │     └─► Return: "✅ Message sent successfully to john"
│    │     │
│    │     └─► MCP Client returns result to voice assistant
│    │
│    ├─► Update conversation context
│    │     • Store: user="send message...", recipient="john"
│    │
│    ├─► Log to conversations.json
│    │
│    └─► Speak: "Message sent to john!"
│
└─ Conversation continues (timer reset)...
```

### Example 2: Follow-up Message with Pronoun
```
┌─ User says: "Hello"
│
├─ Assistant: "Hi! What can I help you with?"
│
├─ User: "Send message to Sarah saying I'll be late"
│
├─ Assistant:
│    ├─► Intent: send_message, recipient: "sarah", message: "I'll be late"
│    ├─► Fuzzy match: "sarah" → exact match
│    ├─► Send via MCP → Telegram
│    ├─► Update context: user="send message...", recipient="sarah"
│    └─► Speak: "Message sent to Sarah!"
│
├─ User: "Also tell her about the meeting"
│
├─ Assistant:
│    ├─► Intent Parser (with context):
│    │     • Context shows: last recipient = "sarah"
│    │     • GPT-4o-mini detects "her" = "sarah" (pronoun resolution)
│    │     • action: "send_message"
│    │     • recipient: "sarah"  ← Resolved from context!
│    │     • message: "about the meeting"
│    │
│    ├─► No need for fuzzy match (already resolved)
│    ├─► Send via MCP → Telegram
│    ├─► Update context: recipient="sarah"
│    └─► Speak: "Message sent to Sarah!"
│
└─ Conversation continues...
```

### Example 3: Fuzzy Match with Confirmation
```
┌─ User: "Send message to Jon saying hello"
│         (Note: Spelled "Jon" but contact is "John")
│
├─ Assistant:
│    ├─► Intent: send_message, recipient: "jon", message: "hello"
│    │
│    ├─► Fuzzy match:
│    │     • No exact match for "jon"
│    │     • difflib.get_close_matches("jon", ["john", "sarah", ...])
│    │     • Best match: "john" (similarity: 0.88)
│    │     • confidence < 0.9 → needs_confirmation = True
│    │
│    ├─► Speak: "Did you mean john? Say yes or no."
│    │
│    ├─► Record 5s audio → "Yes"
│    │
│    ├─► Confirmation received: "yes" detected
│    │     • Use matched name: "john"
│    │
│    ├─► Send via MCP → Telegram to "john"
│    │
│    └─► Speak: "Message sent to john!"
│
└─ Done
```

### Example 4: General Chat (No Message Intent)
```
┌─ User: "Hello"
│
├─ Assistant: "Hi! What can I help you with?"
│
├─ User: "What's the weather today?"
│
├─ Assistant:
│    ├─► Intent Parser:
│    │     • action: "general_chat"
│    │     • confidence: 0.92
│    │     • No message keywords detected
│    │
│    ├─► Route to Ollama LLM (not Telegram)
│    │     ├─► Build context from conversation_history
│    │     │     Previous conversation: (none)
│    │     │     Current question: "What's the weather today?"
│    │     │
│    │     ├─► Send to Ollama gemma2:2b
│    │     │     POST http://localhost:11434/api/generate
│    │     │
│    │     └─► Response: "I don't have access to weather data, but you can check a weather app."
│    │
│    ├─► Store in conversation_history:
│    │     ("What's the weather today?", "I don't have access...")
│    │
│    └─► Speak: "I don't have access to weather data, but you can check a weather app."
│
├─ User: "Thanks"
│
├─ Assistant:
│    ├─► Detects exit keyword: "thanks"
│    └─► Speak: "Goodbye! Say 'Hello' when you need me again."
│
└─ Return to listening mode
```

### Example 5: Timeout Scenario
```
┌─ User: "Hello"
│
├─ Assistant: "Hi! What can I help you with?"
│    • Timer starts: 60s
│
├─ User: "What's 2+2?"
│    • Timer: 10s elapsed
│
├─ Assistant: "2+2 equals 4."
│    • Timer reset to 0s (user spoke)
│
├─ [Silence for 30 seconds...]
│    • Timer: 30s elapsed
│    • Assistant: [Shows "🔇 Silence... (30s until timeout)"]
│
├─ [Silence for another 20 seconds...]
│    • Timer: 50s elapsed
│    • Assistant: [Shows "⏰ Timing out in 10s..."]
│
├─ [Silence for final 10 seconds...]
│    • Timer: 60s elapsed
│
├─ Assistant:
│    ├─► Timeout triggered!
│    ├─► Set in_conversation = False
│    └─► Speak: "I'm going back to sleep now. Say 'Hello' to wake me up!"
│
└─ Return to listening mode
```

---

## 🧩 Technology Stack

### Core Technologies
- **Python 3.8+**: Main language
- **OpenAI API**:
  - STT: gpt-4o-mini-transcribe ($0.003/min)
  - Intent Understanding: gpt-4o-mini
  - TTS (optional): tts-1 ($0.015/min)
- **Ollama**: Local LLM inference (gemma2:2b)
- **Telethon**: Telegram MTProto API (user account)
- **MCP (Model Context Protocol)**: Standardized tool protocol

### Libraries
- **Audio**:
  - `sounddevice`: Real-time audio recording
  - `numpy`: Audio data processing
  - `wave`: WAV file creation
  - `pyttsx3`: Local TTS engine
- **Telegram**:
  - `telethon`: User account API
  - `python-telegram-bot`: Bot API (legacy)
- **MCP**:
  - `mcp`: MCP SDK
  - `mcp.server`, `mcp.client`: Server/client implementations
- **Utilities**:
  - `dotenv`: Environment variables
  - `requests`: HTTP requests (Ollama)
  - `difflib`: Fuzzy string matching
  - `asyncio`: Async/await support
  - `logging`: Application logging

---

## 📊 Cost Analysis

### Monthly Costs (1 hour daily usage)
```
Assumptions:
- 30 conversations/day × 30 days = 900 conversations/month
- Avg conversation: 3 exchanges = 6 audio chunks
- Avg audio length: 5 seconds/chunk

STT (OpenAI gpt-4o-mini-transcribe):
  • 900 conv × 6 chunks × 5 seconds = 27,000 seconds = 450 minutes
  • $0.003/min × 450 = $1.35/month

Intent Understanding (GPT-4o-mini):
  • 900 conv × 3 intents = 2,700 API calls
  • ~100 tokens/call = 270K tokens
  • $0.15/1M input tokens = $0.04/month

TTS (Local - pyttsx3):
  • FREE

LLM (Ollama gemma2:2b):
  • FREE (local)

TOTAL: ~$1.39/month
```

If using OpenAI TTS: +$6.75/month ($0.015/min × 450 min)

---

## 🔒 Security Considerations

### Authentication
- **Telegram Session**: Stored in `config/telegram_session.session`
  - Contains auth token for user account
  - Protected by file permissions (600)
  - Should NOT be committed to git
- **API Keys**: Stored in `config/.env`
  - OpenAI API key
  - Telegram API ID/Hash
  - Protected by .gitignore

### Privacy
- **Conversation Logs**: Stored in `data/conversations.json`
  - Contains user text and AI responses
  - No audio recordings saved
  - Can be disabled if needed
- **Voice Data**:
  - Processed in-memory
  - Sent to OpenAI Whisper API (encrypted)
  - Not stored on disk

### Network
- **Ollama**: Local (localhost:11434) - no external calls
- **OpenAI**: HTTPS encrypted
- **Telegram**: MTProto encrypted (via Telethon)
- **MCP**: Stdio transport (local only, no network)

---

## 🚀 Deployment Options

### 1. Manual Mode (Development)
```bash
python main.py
# Terminal stays open, shows logs
# Press Ctrl+C to stop
```

### 2. Background Mode (Production)
```bash
./scripts/start_gemma_background.sh
# Runs as daemon, logs to logs/gemma.log
# Use ./scripts/stop_gemma.sh to stop
```

### 3. Auto-Start Service (macOS)
```bash
./scripts/install_service.sh
# Installs LaunchAgent
# Starts on login automatically
# Logs to ~/Library/Logs/gemma_voice_assistant.log
```

---

## 🐛 Error Handling

### Voice Assistant Level
```python
try:
    user_text = record_and_transcribe(...)
except Exception as e:
    print(f"Recording error: {e}")
    # Continue listening, don't crash

try:
    response = handle_user_input(user_text)
except Exception as e:
    print(f"Processing error: {e}")
    speak("Sorry, I had trouble with that.")
```

### Intent Parser Level
```python
try:
    parsed = gpt_mini_api_call(...)
except Exception as e:
    # Fallback to keyword matching
    return _fallback_parse(user_text)
```

### MCP Client Level
```python
try:
    result = await session.call_tool(...)
except Exception as e:
    logger.error(f"MCP call failed: {e}")
    return "Failed to send message."
```

### Telethon Level
```python
try:
    entity = await client.get_entity(recipient)
except Exception as e:
    return {
        "success": False,
        "error": f"Could not find recipient: {e}"
    }
```

---

## 📝 Logging Strategy

### Log Files
- `logs/gemma.log`: Main application log
- `gemma_service.log`: Background service log
- `data/conversations.json`: User conversation history

### Log Levels
```python
logger.info("✅ Normal operation")
logger.warning("⚠️ Non-critical issue")
logger.error("❌ Error occurred")
```

### Example Log Entry
```
2024-11-03 15:30:22 - INFO - 🎙️ Voice Activation Mode Active!
2024-11-03 15:30:24 - INFO - 👂 hello
2024-11-03 15:30:24 - INFO - 🔥 Activation detected: 'hello'
2024-11-03 15:30:25 - INFO - 🗣️ Gemma: Hi! What can I help you with?
2024-11-03 15:30:30 - INFO - 👂 send message to john saying hello
2024-11-03 15:30:30 - INFO - 🧠 Understanding intent with context...
2024-11-03 15:30:31 - INFO - ✅ Intent: send_message | Recipient: john | Confidence: 0.95
2024-11-03 15:30:31 - INFO - 📱 Detected message intent
2024-11-03 15:30:31 - INFO - 📞 Calling telegram.send_telegram_message
2024-11-03 15:30:32 - INFO - ✅ Message sent successfully to john
2024-11-03 15:30:32 - INFO - 🗣️ Gemma: Message sent to john!
```

---

## 🎯 Future Enhancements (Potential)

### 1. Multi-Platform Support
- Add WhatsApp MCP server
- Add Slack MCP server
- Add Email MCP server
- Unified contact management

### 2. Advanced Features
- Voice command customization
- Multiple activation words
- Different voices per contact
- Scheduled messages
- Message templates
- Group chat support

### 3. Intelligence Improvements
- Better pronoun resolution
- Context across sessions (persistent memory)
- Learning user preferences
- Personalized responses

### 4. Platform Expansion
- Linux support
- Windows support
- Mobile app (iOS/Android)
- Web interface

---

## 🔄 State Machine Diagram

```
┌─────────────────────────────────────────────────┐
│               SYSTEM STATES                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────┐                                 │
│  │   IDLE     │  ← Initial state                │
│  │  (Waiting) │                                 │
│  └─────┬──────┘                                 │
│        │                                         │
│        │ Initialization complete                 │
│        │                                         │
│        ▼                                         │
│  ┌────────────────┐                             │
│  │   LISTENING    │  ← Background listening      │
│  │  (Activation   │     for activation word     │
│  │   Detection)   │                             │
│  └────────┬───────┘                             │
│           │                                      │
│           │ Activation word detected            │
│           │ [hello, hi, computer, assistant]    │
│           │                                      │
│           ▼                                      │
│  ┌──────────────────┐                           │
│  │   CONVERSATION   │  ← Active session         │
│  │    (Active)      │     60s timeout           │
│  │                  │                            │
│  │  ┌──────────┐   │                            │
│  │  │ Listening│◄──┤  ← Recording user          │
│  │  └────┬─────┘   │                            │
│  │       │          │                            │
│  │       ├─ Transcribing                        │
│  │       │          │                            │
│  │       ▼          │                            │
│  │  ┌──────────┐   │                            │
│  │  │Processing│   │  ← Intent parsing          │
│  │  └────┬─────┘   │     + execution            │
│  │       │          │                            │
│  │       ├─ Responding                           │
│  │       │          │                            │
│  │       ▼          │                            │
│  │  ┌──────────┐   │                            │
│  │  │ Speaking │   │  ← TTS output              │
│  │  └────┬─────┘   │                            │
│  │       │          │                            │
│  │       └──────────┤  ← Loop back               │
│  │                  │                            │
│  └──────┬───────────┘                           │
│         │                                        │
│         │ Exit command OR timeout               │
│         │                                        │
│         ▼                                        │
│  ┌────────────────┐                             │
│  │   LISTENING    │  ← Back to activation       │
│  │  (Activation   │     detection               │
│  │   Detection)   │                             │
│  └────────────────┘                             │
│                                                  │
│  ERROR STATE (any level):                       │
│  ┌────────────────┐                             │
│  │   RECOVERING   │  ← Handles exceptions       │
│  └────────┬───────┘     Logs error              │
│           │             Returns to LISTENING    │
│           └──────► LISTENING                     │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 📚 API Reference Summary

### OpenAI APIs Used

#### 1. Whisper (STT)
```python
transcript = openai_client.audio.transcriptions.create(
    model="gpt-4o-mini-transcribe",  # Latest, 50% cheaper
    file=("audio.wav", audio_buffer),
    language="en",
    response_format="text"
)
```

#### 2. GPT-4o-mini (Intent Understanding)
```python
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ],
    temperature=0.1,
    response_format={"type": "json_object"}
)
```

#### 3. TTS (Optional)
```python
response = openai_client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=text,
    speed=1.1
)
```

### Ollama API

#### Generate Response
```bash
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "gemma2:2b",
  "prompt": "You are Gemma...",
  "stream": false
}
```

### Telethon API

#### Send Message
```python
await client.send_message(
    entity=recipient_entity,
    message=text
)
```

#### Get Entity
```python
entity = await client.get_entity(
    identifier  # Can be: phone, username, or contact
)
```

---

## 🎬 Conclusion

This system combines multiple cutting-edge technologies to create a Siri-like voice assistant with Telegram integration. The modular architecture using MCP makes it extensible to other platforms, while the AI-powered intent understanding provides a natural conversational experience.

### Key Strengths:
✅ **Natural Language**: GPT-4o-mini understands intent naturally
✅ **Context-Aware**: Tracks conversation history for pronouns
✅ **Fuzzy Matching**: Handles misspelled names with confirmation
✅ **Cost-Effective**: Uses local Ollama LLM for chat (~$1.39/month)
✅ **Modular**: MCP architecture allows easy platform expansion
✅ **User-Friendly**: Works like Siri with voice activation
✅ **Real Account**: Sends from user's Telegram (not bot)

### Use Cases:
- Hands-free Telegram messaging while driving/cooking
- Voice-controlled contact management
- Accessible communication for users with disabilities
- Quick message sending without typing
- Multi-tasking productivity tool

---

**Project Status**: ✅ Production Ready
**Last Updated**: November 2024
**Version**: 1.0