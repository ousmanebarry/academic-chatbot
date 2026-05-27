#!/usr/bin/env python3
"""
Simple HTTP server to serve the web UI for ScholarAI
This avoids CORS issues that might occur when opening index.html directly
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def main():
    """Start the web UI server"""
    port = 3000
    
    # Check if index.html exists
    if not Path("index.html").exists():
        print("❌ index.html not found in current directory")
        print("Make sure you're running this from the project root")
        sys.exit(1)
    
    # Check if the main server is likely running
    print("🔍 Make sure your ScholarAI API is running on http://localhost:8000")
    print("   You can start it with: python start_server.py")
    print()
    
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"🌐 Web UI Server starting on http://localhost:{port}")
            print(f"📱 Opening web browser...")
            print()
            print("Press Ctrl+C to stop the server")
            print("-" * 40)
            
            # Try to open browser
            try:
                webbrowser.open(f"http://localhost:{port}")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print(f"Please manually open: http://localhost:{port}")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Web UI server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print("Try closing other applications or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
