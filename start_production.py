#!/usr/bin/env python3
"""
Production startup script for Railway deployment
"""

import os
import uvicorn

if __name__ == "__main__":
    # Get port from Railway environment variable
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting ScholarAI (Production)")
    print("=" * 45)
    print(f"🌐 Server will run on http://0.0.0.0:{port}")
    print(f"📱 Web UI available at: /")
    print(f"📚 API docs available at: /docs")
    print("=" * 45)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
