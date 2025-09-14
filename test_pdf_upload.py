#!/usr/bin/env python3
"""
Test script for PDF upload functionality
This script tests the new PDF upload capabilities of the Academic Chatbot
"""

import requests
import base64
import json
from pathlib import Path

def test_pdf_upload():
    """Test PDF upload functionality"""
    print("🧪 Testing PDF Upload Functionality")
    print("=" * 40)
    
    # Create a simple test document structure
    test_pdf_document = {
        "id": "test_pdf_001",
        "title": "Test PDF Document",
        "content": "VGhpcyBpcyBhIHRlc3QgUERGIGNvbnRlbnQgZW5jb2RlZCBpbiBiYXNlNjQ=",  # "This is a test PDF content encoded in base64"
        "metadata": {
            "filename": "test_document.pdf",
            "file_size": 1024,
            "file_type": "application/pdf",
            "is_pdf": True,
            "upload_time": "2024-01-01T12:00:00Z"
        }
    }
    
    upload_data = {
        "documents": [test_pdf_document],
        "collection_name": "test_pdf_collection"
    }
    
    try:
        print("📤 Sending PDF test document to server...")
        response = requests.post(
            "http://localhost:8000/documents/upload",
            json=upload_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ PDF upload test successful!")
            print(f"   Processed: {result.get('processed', 0)} document(s)")
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ PDF upload test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF upload test error: {e}")
        return False

def test_health_check():
    """Test basic health check"""
    print("\n🔍 Testing server health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy: {data['status']}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_chat_with_pdf():
    """Test chat functionality after PDF upload"""
    print("\n💭 Testing chat with PDF content...")
    
    chat_data = {
        "message": "What information is available in the uploaded PDF document?",
        "conversation_id": "pdf_test_conv"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat with PDF test successful!")
            print(f"   Answer: {data.get('answer', 'No answer')[:150]}...")
            print(f"   Confidence: {data.get('confidence', 0):.2f}")
            print(f"   Sources: {len(data.get('sources', []))}")
            return True
        else:
            print(f"❌ Chat test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 PDF Upload Test Suite")
    print("Make sure the Academic Chatbot server is running on http://localhost:8000")
    print()
    
    # Test sequence
    tests = [
        ("Health Check", test_health_check),
        ("PDF Upload", test_pdf_upload),
        ("Chat with PDF", test_chat_with_pdf)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All PDF tests passed! PDF upload functionality is working.")
        print("\n💡 Next steps:")
        print("1. Try uploading a real PDF file through the web interface")
        print("2. Test with different PDF types and sizes")
        print("3. Verify text extraction quality with various PDF formats")
    else:
        print("❌ Some tests failed. Check the server logs and requirements.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the server is running: python start_server.py")
        print("2. Install PDF dependencies: pip install PyPDF2 pdfplumber")
        print("3. Check server logs for detailed error messages")

if __name__ == "__main__":
    main()
