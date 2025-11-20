#!/usr/bin/env python3
"""
Gemma Voice Assistant - Main Entry Point
Run the voice assistant directly from project root
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.auto_voice_assistant import AutoVoiceAssistant

def main():
    """Main entry point for Gemma Voice Assistant"""
    print("🎙️  Gemma Voice Assistant")
    print("=" * 30)
    
    assistant = AutoVoiceAssistant()
    assistant.start()

if __name__ == "__main__":
    main()