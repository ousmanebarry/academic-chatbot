#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify issues with the Academic Chatbot
"""

import sys
import os
import requests
import json
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    print("-" * 30)
    
    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("openai", "OpenAI"),
        ("pinecone", "Pinecone"),
        ("langchain", "LangChain"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langchain_pinecone", "LangChain Pinecone"),
        ("redis", "Redis"),
        ("PyPDF2", "PyPDF2"),
        ("pdfplumber", "PDFPlumber"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings")
    ]
    
    missing = []
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔍 Checking Environment Variables...")
    print("-" * 35)
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        from dotenv import load_dotenv
        load_dotenv()
    else:
        print("⚠️  .env file not found")
    
    required_env_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "PINECONE_API_KEY": "Pinecone API Key",
        "PINECONE_ENVIRONMENT": "Pinecone Environment"
    }
    
    missing_vars = []
    for var, description in required_env_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {description}: {masked_value}")
        else:
            print(f"❌ {description}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def check_server_health():
    """Check if server is running and healthy"""
    print("\n🔍 Checking Server Health...")
    print("-" * 28)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Status: {data['status']}")
            
            services = data.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {service}: {status}")
            
            return all(services.values())
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        print("💡 Start with: python start_server.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def test_api_endpoints():
    """Test individual API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    print("-" * 27)
    
    # Test root endpoint
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test stats endpoint
    try:
        response = requests.get("http://localhost:8000/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats endpoint working")
            print(f"   Total queries: {stats.get('total_queries', 0)}")
            print(f"   Active documents: {stats.get('active_documents', 0)}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")

def test_simple_chat():
    """Test basic chat functionality"""
    print("\n🔍 Testing Chat Functionality...")
    print("-" * 30)
    
    simple_message = {
        "message": "Hello, can you help me with testing?",
        "conversation_id": "diagnostic_test"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json=simple_message,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            
            if "I apologize, but I encountered an error" in answer:
                print("❌ Chat returning error response")
                print(f"   Answer: {answer}")
                return False
            else:
                print("✅ Chat working")
                print(f"   Answer: {answer[:100]}...")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                return True
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False

def test_document_upload():
    """Test document upload functionality"""
    print("\n🔍 Testing Document Upload...")
    print("-" * 29)
    
    test_doc = {
        "id": "diagnostic_test_001",
        "title": "Diagnostic Test Document",
        "content": "This is a test document for diagnostic purposes. It contains some sample text to verify the upload functionality is working correctly.",
        "metadata": {
            "filename": "diagnostic_test.txt",
            "file_type": "text/plain",
            "is_pdf": False
        }
    }
    
    upload_data = {
        "documents": [test_doc],
        "collection_name": "diagnostic_test"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/documents/upload",
            json=upload_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            processed = result.get('processed', 0)
            total = result.get('total', 0)
            
            print(f"✅ Upload endpoint working")
            print(f"   Processed: {processed}/{total} documents")
            
            if processed == 0:
                print("❌ No documents were processed")
                print("   Check server logs for detailed error messages")
                return False
            
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False

def check_server_logs():
    """Provide instructions for checking server logs"""
    print("\n🔍 Server Logs Guidance...")
    print("-" * 25)
    print("💡 To get detailed error information:")
    print("1. Look at the terminal where you started the server")
    print("2. Check for ERROR or WARNING messages")
    print("3. Common issues to look for:")
    print("   - OpenAI API key authentication errors")
    print("   - Pinecone connection failures")
    print("   - Redis connection issues")
    print("   - Missing environment variables")

def main():
    """Main diagnostic function"""
    print("🚀 Academic Chatbot Diagnostic Tool")
    print("=" * 40)
    
    all_checks = [
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Server Health", check_server_health),
        ("API Endpoints", test_api_endpoints),
        ("Chat Function", test_simple_chat),
        ("Document Upload", test_document_upload)
    ]
    
    passed = 0
    failed_checks = []
    
    for check_name, check_func in all_checks:
        print(f"\n{'='*len(check_name)}")
        if check_func():
            passed += 1
        else:
            failed_checks.append(check_name)
    
    print("\n" + "="*40)
    print(f"📊 Diagnostic Results: {passed}/{len(all_checks)} checks passed")
    
    if failed_checks:
        print(f"\n❌ Failed checks: {', '.join(failed_checks)}")
        check_server_logs()
        
        print("\n🔧 Recommended actions:")
        if "Dependencies" in failed_checks:
            print("1. Install missing packages: pip install -r requirements.txt")
        if "Environment" in failed_checks:
            print("2. Set up environment: python setup_env.py")
            print("3. Edit .env file with your actual API keys")
        if "Server Health" in failed_checks:
            print("4. Start the server: python start_server.py")
        
        print("\n💡 After fixing issues, run this diagnostic again")
    else:
        print("\n🎉 All checks passed! The system should be working correctly.")

if __name__ == "__main__":
    main()

