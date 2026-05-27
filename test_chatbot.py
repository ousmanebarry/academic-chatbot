"""
Test script for ScholarAI
This script demonstrates how to use the ScholarAI API
"""

import asyncio
import httpx
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Introduction to Machine Learning",
        "content": """
        Machine learning is a subset of artificial intelligence (AI) that focuses on algorithms 
        that can learn and make decisions from data. The main types of machine learning include:
        
        1. Supervised Learning: Uses labeled training data to learn a mapping function
        2. Unsupervised Learning: Finds patterns in data without labeled examples
        3. Reinforcement Learning: Learns through interaction with an environment
        
        Common algorithms include linear regression, decision trees, neural networks, and support vector machines.
        Applications range from image recognition to natural language processing.
        """
    },
    {
        "id": "doc2", 
        "title": "Deep Learning Fundamentals",
        "content": """
        Deep learning is a subset of machine learning based on artificial neural networks.
        Key concepts include:
        
        - Neural Networks: Composed of layers of interconnected nodes (neurons)
        - Backpropagation: Algorithm for training neural networks
        - Activation Functions: Functions that determine neuron output (ReLU, Sigmoid, Tanh)
        - Convolutional Neural Networks (CNNs): Specialized for image processing
        - Recurrent Neural Networks (RNNs): Designed for sequential data
        
        Deep learning has achieved breakthrough results in computer vision, natural language processing,
        and game playing (like AlphaGo).
        """
    },
    {
        "id": "doc3",
        "title": "Natural Language Processing",
        "content": """
        Natural Language Processing (NLP) combines computational linguistics with machine learning
        to help computers understand and generate human language.
        
        Key NLP tasks include:
        - Tokenization: Breaking text into individual words or tokens
        - Part-of-speech tagging: Identifying grammatical categories
        - Named entity recognition: Identifying people, places, organizations
        - Sentiment analysis: Determining emotional tone
        - Machine translation: Converting between languages
        - Question answering: Providing answers to questions about text
        
        Modern NLP relies heavily on transformer architectures like BERT and GPT.
        """
    }
]

TEST_QUESTIONS = [
    "What is machine learning?",
    "What are the main types of machine learning?",
    "How do neural networks work?",
    "What is the difference between CNNs and RNNs?",
    "What are common NLP tasks?",
    "How does backpropagation work?",
]

class ChatbotTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def test_health(self):
        """Test health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            print(f"Health Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Services: {data.get('services', {})}")
                return True
            return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def upload_test_documents(self):
        """Upload test documents"""
        print("📚 Uploading test documents...")
        try:
            upload_data = {
                "documents": TEST_DOCUMENTS,
                "collection_name": "test_collection"
            }
            
            response = await self.client.post(
                f"{self.base_url}/documents/upload",
                json=upload_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Uploaded {data.get('processed', 0)} documents")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Document upload error: {e}")
            return False
    
    async def test_chat_question(self, question: str, conversation_id: str = None):
        """Test a single chat question"""
        print(f"💭 Asking: {question}")
        
        start_time = time.time()
        try:
            chat_data = {
                "message": question,
                "conversation_id": conversation_id,
                "context_window": 3
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json=chat_data
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response ({response_time:.1f}ms):")
                print(f"   Answer: {data.get('answer', 'No answer')[:200]}...")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Cached: {data.get('cached', False)}")
                return data
            else:
                print(f"❌ Chat failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return None
    
    async def test_streaming_chat(self, question: str):
        """Test streaming chat"""
        print(f"🌊 Streaming: {question}")
        
        try:
            chat_data = {
                "message": question,
                "context_window": 3
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/stream",
                json=chat_data
            ) as response:
                if response.status_code == 200:
                    print("✅ Streaming response:")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk_data = json.loads(line[6:])
                            if chunk_data.get("type") == "content":
                                print(chunk_data.get("data", ""), end="")
                            elif chunk_data.get("type") == "complete":
                                print("\n✅ Stream complete")
                                break
                else:
                    print(f"❌ Streaming failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Streaming error: {e}")
    
    async def test_performance(self):
        """Test performance with multiple concurrent requests"""
        print("⚡ Testing performance with concurrent requests...")
        
        questions = TEST_QUESTIONS * 3  # Test with more questions
        tasks = []
        
        start_time = time.time()
        
        for i, question in enumerate(questions):
            task = self.test_chat_question(f"{question} (test {i})", f"perf_test_{i % 3}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        successful_results = [r for r in results if isinstance(r, dict)]
        
        print(f"\n📊 Performance Results:")
        print(f"   Total requests: {len(questions)}")
        print(f"   Successful: {len(successful_results)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average per request: {total_time/len(questions)*1000:.1f}ms")
        
        if successful_results:
            response_times = [r.get('response_time_ms', 0) for r in successful_results if r.get('response_time_ms')]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                print(f"   Average response time: {avg_response_time:.1f}ms")
    
    async def test_stats(self):
        """Test statistics endpoint"""
        print("📈 Getting system statistics...")
        try:
            response = await self.client.get(f"{self.base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print("✅ System Statistics:")
                for key, value in stats.items():
                    if isinstance(value, float):
                        print(f"   {key}: {value:.2f}")
                    else:
                        print(f"   {key}: {value}")
            else:
                print(f"❌ Stats failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Stats error: {e}")
    
    async def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting ScholarAI Test Suite\n")
        
        # Test health
        if not await self.test_health():
            print("❌ Health check failed. Make sure the server is running.")
            return
        
        print()
        
        # Upload documents
        if not await self.upload_test_documents():
            print("❌ Document upload failed.")
            return
        
        print()
        
        # Wait a bit for documents to be indexed
        print("⏳ Waiting for documents to be indexed...")
        await asyncio.sleep(5)
        
        # Test individual questions
        conversation_id = f"test_conv_{int(time.time())}"
        for question in TEST_QUESTIONS[:3]:  # Test first 3 questions
            await self.test_chat_question(question, conversation_id)
            print()
        
        # Test streaming
        await self.test_streaming_chat("What are the main applications of machine learning?")
        print()
        
        # Test performance
        await self.test_performance()
        print()
        
        # Test stats
        await self.test_stats()
        
        print("\n🎉 Test suite completed!")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main test function"""
    tester = ChatbotTester()
    try:
        await tester.run_full_test()
    finally:
        await tester.close()

if __name__ == "__main__":
    print("ScholarAI Tester")
    print("======================")
    print("Make sure the chatbot server is running on http://localhost:8000")
    print("You can start it with: python main.py")
    print()
    
    asyncio.run(main())
