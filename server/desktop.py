import sys
import os
import threading
import time
import uvicorn
import webview
from dotenv import load_dotenv
load_dotenv() # This pulls the keys from your local .env file automatically!

# Ensure the parent directory is in the system path so it can resolve your app imports cleanly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.app import app

def run_fastapi():
    """Boots your production FastAPI server locally on a background loopback thread."""
    # We force a fixed port for the desktop client loopback handshake
    uvicorn.run(app, host="127.0.0.1", port=8443, log_level="warning")

if __name__ == "__main__":
    print("🛰️  Initializing Desktop Co-Brain Engine...")
    
    # 1. Fire up the FastAPI server on a background worker thread
    server_thread = threading.Thread(target=run_fastapi, daemon=True)
    server_thread.start()
    
    # 2. Give the server a brief moment to bind the socket port before launching the UI window
    time.sleep(1.0)
    
    print("🧊 Spawning Glassmorphic Cockpit Window Surface...")
    
# 3. Create the dedicated native desktop window wrapper frame
    window = webview.create_window(
        title="Quantum Noise Co-Brain Operator Console",
        url="http://127.0.0.1:8443",
        width=1280,
        height=800,
        resizable=True,
        min_size=(1024, 768)
    )
    
    # 🚀 FIXED LOOP CONFIGURATION: 
    # Disable private isolation mode and explicitly tell pywebview to maintain a persistent cookie jar
    webview.start(private_mode=False, http_server=True)
    
    print("🔌 Desktop Session Terminated cleanly.")
