#!/usr/bin/env python3
"""
Simple HTTP server to test DeepSeek capabilities
"""

import http.server
import socketserver
import os
import threading
import time
import webbrowser

PORT = 8080
HTML_FILE = "test_deepseek.html"

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/' + HTML_FILE
        return super().do_GET()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_server():
    """Start HTTP server in background"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    handler = TestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"✅ Server started at http://localhost:{PORT}")
        print(f"📄 Serving: {HTML_FILE}")
        print("🔄 Server running... Press Ctrl+C to stop")
        httpd.serve_forever()

if __name__ == "__main__":
    print("=" * 50)
    print("DeepSeek AI Assistant - HTTP Server Test")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(HTML_FILE):
        print(f"❌ Error: {HTML_FILE} not found!")
        exit(1)
    
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📄 HTML file: {HTML_FILE} ({os.path.getsize(HTML_FILE)} bytes)")
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    print(f"\n🌐 Open browser to: http://localhost:{PORT}")
    print("🧪 Testing DeepSeek capabilities...")
    
    try:
        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        print("✅ DeepSeek test completed successfully!")