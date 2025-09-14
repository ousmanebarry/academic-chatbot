#!/usr/bin/env python3
"""
Production startup script for Railway deployment
"""

import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Get port from Railway environment variable
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
