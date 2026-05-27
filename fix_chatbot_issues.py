#!/usr/bin/env python3
"""
Step-by-step fix for ScholarAI issues
This script helps identify and fix common problems
"""

import os
import sys
import subprocess
from pathlib import Path

def check_and_fix_environment():
    """Check and fix environment setup"""
    print("🔧 Step 1: Environment Setup")
    print("-" * 30)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file missing")
        print("💡 Creating .env file...")
        try:
            subprocess.run([sys.executable, "setup_env.py"], check=True)
            print("✅ .env file created")
            print("📝 Please edit .env with your actual API keys:")
            print("   - OPENAI_API_KEY (from https://platform.openai.com/api-keys)")
            print("   - PINECONE_API_KEY (from https://app.pinecone.io/)")
            return False
        except Exception as e:
            print(f"❌ Failed to create .env: {e}")
            return False
    else:
        print("✅ .env file exists")
    
    # Load and check environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        
        if not openai_key or openai_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not set or using placeholder")
            print("💡 Edit .env file and set your real OpenAI API key")
            return False
        
        if not pinecone_key or pinecone_key == "your_pinecone_api_key_here":
            print("❌ Pinecone API key not set or using placeholder")
            print("💡 Edit .env file and set your real Pinecone API key")
            return False
        
        print("✅ API keys are configured")
        return True
        
    except ImportError:
        print("❌ python-dotenv not installed")
        return False

def check_and_install_dependencies():
    """Check and install missing dependencies"""
    print("\n🔧 Step 2: Dependencies")
    print("-" * 25)
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt missing")
        return False
    
    print("📦 Installing/updating dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running manually: pip install -r requirements.txt")
        return False

def start_redis():
    """Instructions for starting Redis"""
    print("\n🔧 Step 3: Redis Setup")
    print("-" * 22)
    
    print("📝 Redis is required for caching. Options:")
    print("1. Docker (recommended): docker run -d -p 6379:6379 redis:alpine")
    print("2. Local installation: Install Redis and start the service")
    print("3. Skip Redis: The app will work but without caching")
    
    return True

def test_core_functionality():
    """Test if the core functionality works"""
    print("\n🔧 Step 4: Test Core Services")
    print("-" * 32)
    
    print("🧪 Testing core imports...")
    try:
        # Test OpenAI
        from openai import AsyncOpenAI
        print("✅ OpenAI import successful")
        
        # Test Pinecone
        from pinecone import Pinecone
        print("✅ Pinecone import successful")
        
        # Test LangChain components
        from langchain_openai import OpenAIEmbeddings
        from langchain_pinecone import PineconeVectorStore
        print("✅ LangChain imports successful")
        
        # Test PDF libraries
        import PyPDF2
        import pdfplumber
        print("✅ PDF libraries available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Some dependencies are missing or incompatible")
        return False

def create_simple_test():
    """Create a simple server test"""
    print("\n🔧 Step 5: Server Test")
    print("-" * 23)
    
    test_script = """
import asyncio
from services.cache_service import CacheService
from services.document_service import DocumentService
from services.chat_service import ChatService

async def test_services():
    try:
        print("Testing cache service...")
        cache = CacheService()
        await cache.initialize()
        print("✅ Cache service OK")
        
        print("Testing document service...")
        docs = DocumentService()
        await docs.initialize()
        print("✅ Document service OK")
        
        print("Testing chat service...")
        chat = ChatService(docs, cache)
        await chat.initialize()
        print("✅ Chat service OK")
        
        await cache.close()
        print("🎉 All services working!")
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_services())
"""
    
    with open("test_services.py", "w") as f:
        f.write(test_script)
    
    print("💡 Created test_services.py")
    print("💡 Run: python test_services.py")
    return True

def main():
    """Main fix function"""
    print("🚀 ScholarAI Issue Fixer")
    print("=" * 35)
    print("This script will help identify and fix common issues.\n")
    
    steps = [
        ("Environment Setup", check_and_fix_environment),
        ("Dependencies", check_and_install_dependencies),
        ("Redis Setup", start_redis),
        ("Core Functionality", test_core_functionality),
        ("Create Test", create_simple_test)
    ]
    
    all_passed = True
    
    for step_name, step_func in steps:
        if not step_func():
            all_passed = False
            if step_name in ["Environment Setup", "Dependencies"]:
                print(f"\n❌ {step_name} failed - this is required before continuing")
                break
    
    print("\n" + "="*35)
    
    if all_passed:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Make sure Redis is running (see Step 3)")
        print("2. Start the server: python start_server.py")
        print("3. Test with: python diagnose_issues.py")
        print("4. Open web UI: python serve_ui.py")
    else:
        print("❌ Some issues need to be fixed first")
        print("💡 Follow the instructions above and run this script again")

if __name__ == "__main__":
    main()

