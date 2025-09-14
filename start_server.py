#!/usr/bin/env python3
"""
Convenient server startup script with environment validation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY",
        "PINECONE_API_KEY", 
        "PINECONE_ENVIRONMENT"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        print("Copy .env.example to .env and fill in your API keys.")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Academic Q&A Chatbot")
    print("=" * 35)
    
    # Check if .env file exists
    if not Path(".env").exists() and not Path(".env.example").exists():
        print("⚠️  No .env file found. Creating .env.example...")
        # The .env.example should already be created by our setup
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment variables validated")
    print("🌐 Starting server on http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("💾 Redis should be running on localhost:6379")
    print("")
    print("Press Ctrl+C to stop the server")
    print("-" * 35)
    
    # Import and run the server
    try:
        import uvicorn
        from main import app
        from config import settings
        
        uvicorn.run(
            "main:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=True,
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
