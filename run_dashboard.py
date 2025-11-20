#!/usr/bin/env python3
"""
Gemma Dashboard - Entry Point
Run the web dashboard from project root
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dashboard.dashboard import app

if __name__ == "__main__":
    print("🌐 Starting Gemma Dashboard...")
    print("📊 Open: http://localhost:5001")
    print("🎤 Say activation word and watch the dashboard!")
    
    app.run(host='0.0.0.0', port=5001, debug=False)