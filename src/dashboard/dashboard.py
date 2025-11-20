#!/usr/bin/env python3
"""
Gemma Voice Assistant Dashboard
- Web interface to view conversations
- Real-time log monitoring
- Optional visual feedback
"""

from flask import Flask, render_template, jsonify
import json
import os
import time
from datetime import datetime
import threading

app = Flask(__name__)

class ConversationLogger:
    def __init__(self):
        self.conversations = []
        # Use data directory from project root
        self.log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'conversations.json')
        self.load_conversations()
    
    def load_conversations(self):
        """Load existing conversations from file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.conversations = json.load(f)
            except:
                self.conversations = []
    
    def save_conversations(self):
        """Save conversations to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.conversations, f, indent=2)
    
    def add_conversation(self, user_input, ai_response):
        """Add new conversation entry"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "ai": ai_response,
            "id": len(self.conversations) + 1
        }
        self.conversations.append(entry)
        self.save_conversations()
    
    def get_recent_conversations(self, limit=20):
        """Get recent conversations"""
        return self.conversations[-limit:] if self.conversations else []

# Global logger
conversation_logger = ConversationLogger()

def monitor_gemma_logs():
    """Monitor Gemma logs for conversations"""
    log_file = "gemma.log"
    if not os.path.exists(log_file):
        return
    
    # Read existing log
    with open(log_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    user_input = None
    
    for line in lines:
        if "👤 User:" in line:
            user_input = line.split("👤 User:", 1)[1].strip()
        elif "🗣️  Gemma:" in line and user_input:
            ai_response = line.split("🗣️  Gemma:", 1)[1].strip()
            conversation_logger.add_conversation(user_input, ai_response)
            user_input = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/conversations')
def get_conversations():
    """API endpoint for conversations"""
    return jsonify({
        'conversations': conversation_logger.get_recent_conversations(),
        'total': len(conversation_logger.conversations)
    })

@app.route('/api/status')
def get_status():
    """Check if Gemma is running"""
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'auto_voice_assistant.py'], 
                              capture_output=True, text=True)
        is_running = bool(result.stdout.strip())
        return jsonify({
            'running': is_running,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except:
        return jsonify({'running': False, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Monitor logs in background
    threading.Thread(target=monitor_gemma_logs, daemon=True).start()
    
    print("🌐 Starting Gemma Dashboard...")
    print("📊 Open: http://localhost:5001")
    print("🎤 Say 'Hey Gemma' and watch the dashboard!")
    
    app.run(host='0.0.0.0', port=5001, debug=False)