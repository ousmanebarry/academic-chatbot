#!/usr/bin/env python3
"""
Environment setup script for Academic Chatbot
This script helps you configure your environment variables
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with template"""
    env_content = """# Academic Chatbot Configuration
# Fill in your actual API keys below

# Required API Keys (get these from your provider dashboards)
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Pinecone Configuration  
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=academic-chatbot-index

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Vector Database Configuration
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_DIMENSION=1536
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Response Configuration
MAX_TOKENS=500
TEMPERATURE=0.7
TOP_K_RESULTS=5

# Model Configuration (adjust based on your OpenAI access)
CHAT_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
"""

    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Backing up to .env.backup")
        os.rename(".env", ".env.backup")
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env and add your API keys:")
    print("   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys")
    print("   - PINECONE_API_KEY: Get from https://app.pinecone.io/")

def main():
    """Main setup function"""
    print("🚀 Academic Chatbot Environment Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    print("\n🔧 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Install Redis: docker run -d -p 6379:6379 redis:alpine")
    print("3. Install dependencies: pip install -r requirements.txt")  
    print("4. Run the server: python start_server.py")
    print("\n💡 Need help? Check the README.md file")

if __name__ == "__main__":
    main()
