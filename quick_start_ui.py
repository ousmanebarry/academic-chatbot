#!/usr/bin/env python3
"""
Quick Start Guide for ScholarAI Web UI
This script helps you get the web interface running quickly
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def check_requirements():
    """Check if basic requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if required files exist
    required_files = ['index.html', 'serve_ui.py', 'main.py', 'start_server.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  .env file not found. Running setup...")
        try:
            os.system('python setup_env.py')
            print("📝 Please edit .env with your API keys before continuing")
            print("💡 You can also run: python fix_chatbot_issues.py for guided setup")
        except Exception as e:
            print(f"❌ Setup failed: {e}")
        return False
    
    print("✅ All required files found")
    return True

def check_api_server():
    """Check if the API server is running"""
    print("🔍 Checking API server...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print("⚠️  API server responding but not healthy")
            return False
    except requests.exceptions.RequestException:
        print("❌ API server is not running")
        return False

def start_api_server():
    """Start the API server"""
    print("🚀 Starting API server...")
    print("This will take a few moments to initialize...")
    
    try:
        # Start the server in the background
        process = subprocess.Popen(
            [sys.executable, 'start_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API server started successfully")
                    return process
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ API server failed to start within 30 seconds")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def start_web_ui():
    """Start the web UI server"""
    print("\n🌐 Starting Web UI...")
    
    try:
        # Start the web UI server
        os.system('python serve_ui.py')
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")

def main():
    """Main quick start function"""
    print("🚀 ScholarAI - Web UI Quick Start")
    print("=" * 45)
    
    # Check requirements
    if not check_requirements():
        print("\n💡 Please fix the issues above and try again")
        return
    
    print()
    
    # Check if API server is already running
    if not check_api_server():
        print("\n🚀 API server needs to be started")
        print("Option 1: Start it automatically (recommended)")
        print("Option 2: Start it manually in another terminal")
        
        choice = input("\nChoose option (1/2): ").strip()
        
        if choice == "1":
            api_process = start_api_server()
            if not api_process:
                print("❌ Failed to start API server")
                return
            
            print("\n✅ API server is now running")
            print("📚 API documentation: http://localhost:8000/docs")
            
        elif choice == "2":
            print("\n📝 Manual start instructions:")
            print("1. Open another terminal/command prompt")
            print("2. Navigate to this directory")
            print("3. Run: python start_server.py")
            print("4. Wait for it to start, then come back here")
            
            input("\nPress Enter when API server is running...")
            
            if not check_api_server():
                print("❌ API server still not detected")
                return
        else:
            print("❌ Invalid choice")
            return
    
    # Start web UI
    print("\n🌐 Ready to start Web UI!")
    print("📱 This will open your browser to http://localhost:3000")
    
    input("Press Enter to continue...")
    start_web_ui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Quick start cancelled")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
