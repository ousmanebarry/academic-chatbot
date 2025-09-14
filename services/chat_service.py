import logging
import time
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from config import settings
from models import ChatRequest, ChatResponse, SourceDocument, ChatMessage
from services.document_service import DocumentService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class ChatService:
    """Main chat service that orchestrates the Q&A process"""
    
    def __init__(self, document_service: DocumentService, cache_service: CacheService):
        self.document_service = document_service
        self.cache_service = cache_service
        self.openai_client: Optional[AsyncOpenAI] = None
        self.conversations: Dict[str, List[ChatMessage]] = {}
        
        # Statistics
        self.total_queries = 0
        self.daily_queries = 0
        self.response_times = []
        self.start_time = time.time()
        
    async def initialize(self):
        """Initialize the chat service"""
        try:
            # Initialize OpenAI client
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Test OpenAI connection
            await self.openai_client.models.list()
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return response"""
        start_time = time.time()
        
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or f"conv_{int(time.time())}"
            
            # Check cache first
            cached_response = await self._get_cached_response(request.message, conversation_id)
            if cached_response:
                try:
                    logger.info(f"Using cached response for query: {request.message[:50]}...")
                    self._update_stats(start_time, cached=True)
                    
                    # Ensure conversation_id is set correctly
                    cached_response['conversation_id'] = conversation_id
                    
                    # Create ChatResponse object safely
                    response = ChatResponse(**cached_response)
                    logger.info(f"Successfully created cached ChatResponse")
                    return response
                    
                except Exception as e:
                    logger.error(f"Error creating ChatResponse from cache: {e}", exc_info=True)
                    logger.info("Falling back to generating new response")
                    # Fall through to generate new response
            
            # Get conversation context
            context = self._get_conversation_context(conversation_id, request.context_window)
            
            # Search for relevant documents
            similar_docs = await self.document_service.search_similar_documents(
                request.message, 
                k=settings.top_k_results
            )
            
            # Generate response using OpenAI
            response_text = await self._generate_response(
                request.message, 
                similar_docs, 
                context
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(similar_docs, response_text)
            
            # Format source documents
            sources = self._format_sources(similar_docs)
            
            # Create response
            response = ChatResponse(
                answer=response_text,
                sources=sources,
                conversation_id=conversation_id,
                confidence=confidence,
                cached=False
            )
            
            # Update conversation history
            self._update_conversation(conversation_id, request.message, response_text)
            
            # Cache the response
            await self._cache_response(request.message, conversation_id, response.dict())
            
            # Update statistics
            self._update_stats(start_time, cached=False)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}", exc_info=True)
            
            # Provide more specific error messages based on the exception type
            error_message = "I apologize, but I encountered an error processing your request. Please try again."
            
            if "openai" in str(e).lower() or "api" in str(e).lower():
                error_message = "I'm having trouble connecting to the AI service. Please check the API configuration and try again."
            elif "pinecone" in str(e).lower() or "vector" in str(e).lower():
                error_message = "I'm having trouble accessing the document database. Please check the Pinecone configuration."
            elif "no relevant documents found" in str(e).lower():
                error_message = "I don't have any relevant documents to answer your question. Please upload some documents first."
            elif "redis" in str(e).lower() or "cache" in str(e).lower():
                error_message = "I'm having trouble with the caching system, but I can still try to help you."
            
            return ChatResponse(
                answer=error_message,
                sources=[],
                conversation_id=request.conversation_id or "error",
                confidence=0.0,
                cached=False
            )
    
    async def process_chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Process chat request with streaming response"""
        try:
            conversation_id = request.conversation_id or f"conv_{int(time.time())}"
            
            # Get context and similar documents
            context = self._get_conversation_context(conversation_id, request.context_window)
            similar_docs = await self.document_service.search_similar_documents(
                request.message, 
                k=settings.top_k_results
            )
            
            # Stream response from OpenAI
            async for chunk in self._generate_response_stream(request.message, similar_docs, context):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield json.dumps({"error": "An error occurred while processing your request."})
    
    async def _get_cached_response(self, query: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        try:
            context = self._get_conversation_context(conversation_id, 2)
            context_str = json.dumps([msg.dict() for msg in context], default=str)
            cached_data = await self.cache_service.get_chat_response(query, context_str)
            
            if cached_data:
                # Ensure sources are properly formatted as SourceDocument objects
                if 'sources' in cached_data and cached_data['sources']:
                    sources = []
                    for source_data in cached_data['sources']:
                        if isinstance(source_data, dict):
                            sources.append(SourceDocument(**source_data))
                        else:
                            sources.append(source_data)
                    cached_data['sources'] = sources
                
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_data
                
        except Exception as e:
            logger.error(f"Error processing cached response: {e}", exc_info=True)
            
        return None
    
    async def _cache_response(self, query: str, conversation_id: str, response: Dict[str, Any]):
        """Cache the response"""
        try:
            context = self._get_conversation_context(conversation_id, 2)
            context_str = json.dumps([msg.dict() for msg in context], default=str)
            
            # Create a serializable version of the response
            cacheable_response = response.copy()
            
            # Convert SourceDocument objects to dictionaries for caching
            if 'sources' in cacheable_response and cacheable_response['sources']:
                sources_data = []
                for source in cacheable_response['sources']:
                    if hasattr(source, 'dict'):  # Pydantic model
                        sources_data.append(source.dict())
                    elif isinstance(source, dict):
                        sources_data.append(source)
                    else:
                        # Convert other types to dict
                        sources_data.append({
                            'id': getattr(source, 'id', 'unknown'),
                            'title': getattr(source, 'title', 'Unknown'),
                            'content': getattr(source, 'content', ''),
                            'score': getattr(source, 'score', 0.0),
                            'metadata': getattr(source, 'metadata', {})
                        })
                cacheable_response['sources'] = sources_data
            
            await self.cache_service.set_chat_response(query, context_str, cacheable_response)
            logger.debug(f"Successfully cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}", exc_info=True)
    
    def _get_conversation_context(self, conversation_id: str, window_size: int) -> List[ChatMessage]:
        """Get conversation context for the given ID"""
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id]
        return messages[-window_size:] if len(messages) > window_size else messages
    
    def _update_conversation(self, conversation_id: str, user_message: str, assistant_response: str):
        """Update conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].extend([
            ChatMessage(role="user", content=user_message),
            ChatMessage(role="assistant", content=assistant_response)
        ])
        
        # Keep only last 20 messages per conversation
        if len(self.conversations[conversation_id]) > 20:
            self.conversations[conversation_id] = self.conversations[conversation_id][-20:]
    
    async def _generate_response(self, query: str, similar_docs: List[Dict], context: List[ChatMessage]) -> str:
        """Generate response using OpenAI"""
        try:
            # Build context from similar documents
            context_text = self._build_context_from_docs(similar_docs)
            
            # Build conversation history
            conversation_history = []
            for msg in context:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Create the system prompt
            system_prompt = self._create_system_prompt(context_text)
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": query})
            
            # Generate response - using configured model with fallback
            try:
                response = await self.openai_client.chat.completions.create(
                    model=settings.chat_model,
                    messages=messages,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature
                )
            except Exception as e:
                if "model" in str(e).lower() or "404" in str(e) or "insufficient_quota" in str(e):
                    fallback_model = "gpt-3.5-turbo" if settings.chat_model != "gpt-3.5-turbo" else "gpt-3.5-turbo-0125"
                    logger.warning(f"{settings.chat_model} not available, falling back to {fallback_model}")
                    response = await self.openai_client.chat.completions.create(
                        model=fallback_model,
                        messages=messages,
                        max_tokens=settings.max_tokens,
                        temperature=settings.temperature
                    )
                else:
                    raise
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response. Please try again."
    
    async def _generate_response_stream(self, query: str, similar_docs: List[Dict], context: List[ChatMessage]) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI"""
        try:
            context_text = self._build_context_from_docs(similar_docs)
            system_prompt = self._create_system_prompt(context_text)
            
            conversation_history = []
            for msg in context:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": query})
            
            # Stream response - using configured model with fallback
            try:
                stream = await self.openai_client.chat.completions.create(
                    model=settings.chat_model,
                    messages=messages,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    stream=True
                )
            except Exception as e:
                if "model" in str(e).lower() or "404" in str(e) or "insufficient_quota" in str(e):
                    fallback_model = "gpt-3.5-turbo" if settings.chat_model != "gpt-3.5-turbo" else "gpt-3.5-turbo-0125"
                    logger.warning(f"{settings.chat_model} not available for streaming, falling back to {fallback_model}")
                    stream = await self.openai_client.chat.completions.create(
                        model=fallback_model,
                        messages=messages,
                        max_tokens=settings.max_tokens,
                        temperature=settings.temperature,
                        stream=True
                    )
                else:
                    raise
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield json.dumps({
                        "type": "content",
                        "data": chunk.choices[0].delta.content
                    })
            
            # Send completion signal
            yield json.dumps({"type": "complete"})
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield json.dumps({"type": "error", "data": str(e)})
    
    def _create_system_prompt(self, context_text: str) -> str:
        """Create system prompt for the assistant"""
        return f"""You are an academic assistant helping students and researchers with course-related questions.
        
Use the following context from academic documents to answer questions accurately and helpfully:

{context_text}

Guidelines:
1. Provide accurate, well-structured answers based on the context provided
2. If you're not sure about something, say so rather than guessing
3. Include relevant examples from the context when helpful
4. Keep responses concise but comprehensive
5. If the context doesn't contain enough information to answer the question, say so clearly
6. Always maintain an academic and professional tone

Answer the user's question based on the context provided."""

    def _build_context_from_docs(self, similar_docs: List[Dict]) -> str:
        """Build context text from similar documents"""
        if not similar_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(similar_docs, 1):
            title = doc.get('metadata', {}).get('title', 'Unknown Document')
            content = doc.get('content', '')
            score = doc.get('score', 0)
            
            context_parts.append(f"Document {i} (Relevance: {score:.3f}):\nTitle: {title}\nContent: {content}\n")
        
        return "\n".join(context_parts)
    
    def _format_sources(self, similar_docs: List[Dict]) -> List[SourceDocument]:
        """Format similar documents as source documents"""
        sources = []
        for doc in similar_docs:
            metadata = doc.get('metadata', {})
            sources.append(SourceDocument(
                id=metadata.get('document_id', 'unknown'),
                title=metadata.get('title', 'Unknown Document'),
                content=doc.get('content', '')[:500] + "..." if len(doc.get('content', '')) > 500 else doc.get('content', ''),
                score=doc.get('score', 0.0),
                metadata=metadata
            ))
        return sources
    
    def _calculate_confidence(self, similar_docs: List[Dict], response_text: str) -> float:
        """Calculate confidence score for the response"""
        if not similar_docs:
            return 0.1
        
        # Simple confidence calculation based on similarity scores
        avg_score = sum(doc.get('score', 0) for doc in similar_docs) / len(similar_docs)
        
        # Adjust based on response length (longer responses might be more detailed)
        length_factor = min(len(response_text) / 500, 1.0)
        
        confidence = (avg_score * 0.7) + (length_factor * 0.3)
        return min(confidence, 1.0)
    
    def _update_stats(self, start_time: float, cached: bool = False):
        """Update service statistics"""
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        self.total_queries += 1
        if not cached:
            self.daily_queries += 1
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_stats = await self.cache_service.get_stats()
        doc_stats = await self.document_service.get_stats()
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "total_queries": self.total_queries,
            "daily_queries": self.daily_queries,
            "average_response_time": avg_response_time,
            "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
            "active_documents": doc_stats.get("total_vectors", 0),
            "system_uptime": time.time() - self.start_time
        }
