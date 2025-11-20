# 🎙️ Gemma Voice Assistant

A real-time voice assistant that works like Siri, powered by local Ollama and OpenAI's latest speech models.

## ✨ Features

- 🎤 **Voice Activation**: Say "Hello", "Hi", "Computer", or "Assistant" to activate
- 🧠 **Local AI**: Uses Ollama Gemma for private, offline responses  
- 🌐 **OpenAI Speech**: Latest gpt-4o-mini-transcribe for accurate STT (50% cheaper)
- ⏰ **Smart Timeout**: 60-second conversation timeout like Siri
- 💬 **Context Memory**: Remembers conversation history within session
- 📊 **Web Dashboard**: Optional visual interface to view conversations
- 🔄 **Background Service**: Runs silently, always listening

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed and running (`ollama serve`)
- OpenAI API key
- Microphone access permissions

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your OpenAI API key
   ```

3. **Run the assistant:**
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
gemma-voice-assistant/
├── main.py                    # Main entry point
├── run_dashboard.py           # Dashboard entry point
├── README.md                  # This file
├── config/                    # Configuration files
│   ├── .env                   # Environment variables
│   ├── requirements.txt       # Python dependencies
│   └── *.plist               # macOS service configs
├── src/                       # Source code
│   ├── core/                  # Core voice assistant
│   │   └── auto_voice_assistant.py
│   └── dashboard/             # Web dashboard
│       ├── dashboard.py
│       └── templates/
├── scripts/                   # Utility scripts
│   ├── start_gemma_background.sh
│   ├── stop_gemma.sh
│   ├── install_service.sh
│   └── uninstall_service.sh
├── data/                      # Data files
│   └── conversations.json    # Conversation history
├── logs/                      # Log files
│   ├── gemma.log
│   └── *.pid
└── docs/                      # Documentation
    └── OPENAI_MODELS_2024.md
```

## 🎯 Usage

### Manual Mode (Terminal)
```bash
python main.py
```
Shows real-time output and voice detection.

### Background Mode (Always-On)
```bash
./scripts/start_gemma_background.sh
```
Runs silently in background, always listening.

### Web Dashboard
```bash
python run_dashboard.py
# Open http://localhost:5001
```
View conversation history and status.

### Auto-Start Service (macOS)
```bash
./scripts/install_service.sh
```
Starts automatically on login.

## 🎤 Voice Commands

**Activation Words:**
- "Hello" 
- "Hi"
- "Computer"
- "Assistant"

**Exit Commands:**
- "Goodbye"
- "Bye" 
- "Thanks"
- "That's all"
- Or wait 60 seconds for auto-timeout

## ⚙️ Configuration

Edit `config/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here

# TTS Options: 'false'=free local, 'true'=paid OpenAI
USE_OPENAI_TTS=false

# Ollama Configuration  
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:2b
```

## 🔧 Scripts

| Script | Purpose |
|--------|---------|
| `main.py` | Run assistant in terminal |
| `run_dashboard.py` | Start web dashboard |
| `scripts/start_gemma_background.sh` | Start background service |
| `scripts/stop_gemma.sh` | Stop background service |
| `scripts/install_service.sh` | Install auto-start service |
| `scripts/uninstall_service.sh` | Remove auto-start service |

## 💰 Costs

- **STT**: $0.003/minute (gpt-4o-mini-transcribe - 50% cheaper)
- **TTS**: Free (local) or $0.015/minute (OpenAI)
- **LLM**: Free (local Ollama)
- **Total**: ~$0.63/month for 1 hour daily usage

## 🔍 Troubleshooting

**Assistant not responding:**
1. Check microphone permissions
2. Increase microphone volume in System Preferences
3. Ensure Ollama is running: `ollama serve`
4. Check logs: `tail -f logs/gemma.log`

**Service won't start:**
1. Run `./scripts/stop_gemma.sh` first
2. Check for conflicting processes: `ps aux | grep main.py`

## 🎯 Examples

**Basic Usage:**
```
👤 "Hello"
🗣️ "Hi! What can I help you with?"
👤 "What's 2+2?"
🗣️ "2+2 equals 4."
👤 "Thanks"
🗣️ "Goodbye! Say 'Hello' when you need me again."
```

**Context Conversation:**
```
👤 "Hello"
🗣️ "Hi! What can I help you with?"
👤 "Tell me about cats"
🗣️ "Cats are independent pets known for hunting and sleeping."
👤 "How long do they live?"
🗣️ "Cats typically live 12-18 years, depending on their health and care."
```

## 📈 Monitoring

- **Logs**: `logs/gemma.log`
- **Dashboard**: http://localhost:5001
- **Process Status**: `ps aux | grep main.py`
- **Conversations**: `data/conversations.json`

---

**Built with ❤️ using OpenAI's latest 2024 models and local Ollama**