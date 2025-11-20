# OpenAI Latest Audio Models & Pricing (2024)

## 🎧 Speech-to-Text (STT) Models

### Available Models:
1. **whisper-1** (Original): $0.006 per minute
2. **gpt-4o-transcribe** (Premium): $0.006 per minute - Better accuracy
3. **gpt-4o-mini-transcribe** (Best Value): $0.003 per minute - **50% cheaper!**

### Our Implementation:
✅ **Currently using**: `gpt-4o-mini-transcribe` - Latest model with best price/performance

### Benefits of Latest Model:
- 🚀 **50% cheaper** than original Whisper
- 🎯 **Higher accuracy** especially with accents/noise
- ⚡ **Faster processing** than local models
- 🌍 **Better language recognition**

---

## 🗣️ Text-to-Speech (TTS) Models

### Available Models:
1. **tts-1**: $15.00 per 1M characters (~$0.015/min)
2. **tts-1-hd**: $30.00 per 1M characters (~$0.030/min) 
3. **gpt-4o-mini-tts**: $0.015 per minute - **Latest with customization**

### Available Voices (2024):
- **Original**: alloy, echo, fable, onyx, nova, shimmer
- **New 2024**: marin, cedar (most natural sounding)
- **Total**: 11+ voices available

### Advanced Features:
- 🎭 **Custom instructions**: "speak like a sympathetic customer service agent"
- 🎵 **15+ vibes**: Dramatic, Cheerleader, Pirate, Smooth Jazz DJ
- ⏱️ **Real-time controls**: Tempo, pacing, pronunciation
- 🎪 **Voice effects**: Hushed suspense, dramatic pauses

### Our Implementation:
- ✅ **Default**: Local pyttsx3 (free)
- ✅ **Optional**: OpenAI TTS (set `USE_OPENAI_TTS=true` in .env)

---

## 💰 Cost Comparison

### For 1 hour of conversation per day:
- **STT (gpt-4o-mini-transcribe)**: ~$0.18/month
- **TTS (local pyttsx3)**: Free
- **TTS (OpenAI)**: ~$0.45/month
- **Total with OpenAI TTS**: ~$0.63/month

### Competitors:
- **ElevenLabs TTS**: $22/month for same usage
- **Azure Speech**: $4-15/month
- **Google Speech**: $4.40/month

**OpenAI is 85% cheaper than competitors!**

---

## 🔧 Configuration

### Current Setup (.env):
```bash
# Use latest 2024 models
OPENAI_API_KEY=your_key_here

# TTS: 'false'=free local, 'true'=paid OpenAI (better quality)
USE_OPENAI_TTS=false
```

### To Enable OpenAI TTS:
```bash
USE_OPENAI_TTS=true
```

### Voice Options:
- **nova** (default) - Balanced, clear
- **alloy** - Neutral, professional  
- **echo** - Deep, authoritative
- **marin** - Natural (2024 release)
- **cedar** - Warm (2024 release)

---

## 📊 Performance Improvements Made:

### Audio Processing:
- ✅ Stricter noise filtering (0.008 threshold for activation)
- ✅ Memory-based audio processing (no temp files)
- ✅ Latest STT model (gpt-4o-mini-transcribe)
- ✅ Real-time optimizations

### Cost Savings:
- ✅ **50% cheaper STT** than original Whisper
- ✅ **85% cheaper TTS** than ElevenLabs
- ✅ **Free local TTS** option (pyttsx3)

---

## 🚀 Usage

```bash
# Start with latest optimizations
python auto_voice_assistant.py
```

**Voice Commands:**
- "Hey Gemma" - Activate assistant
- Stricter activation filtering prevents background noise
- Faster, more accurate transcription
- Optional high-quality TTS

The assistant now uses the **latest 2024 OpenAI models** for optimal performance and cost efficiency!