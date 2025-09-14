from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    context_window: int = Field(5, description="Number of previous messages to include")
    search_filters: Optional[Dict[str, Any]] = Field(None, description="Additional search filters")

class SourceDocument(BaseModel):
    """Source document reference"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Relevant content excerpt")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceDocument] = Field(default_factory=list, description="Source documents")
    conversation_id: str = Field(..., description="Conversation ID")
    confidence: float = Field(..., description="Response confidence score")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    cached: bool = Field(False, description="Whether response was cached")

class DocumentUploadRequest(BaseModel):
    """Document upload request"""
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to upload")
    collection_name: Optional[str] = Field("default", description="Collection name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    overwrite: bool = Field(False, description="Whether to overwrite existing documents")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: float = Field(..., description="Response timestamp")
    services: Dict[str, bool] = Field(..., description="Individual service status")

class StatsResponse(BaseModel):
    """Statistics response"""
    total_queries: int = Field(..., description="Total number of queries processed")
    daily_queries: int = Field(..., description="Queries processed today")
    average_response_time: float = Field(..., description="Average response time in ms")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    active_documents: int = Field(..., description="Number of indexed documents")
    system_uptime: float = Field(..., description="System uptime in seconds")
    performance_status: Optional[str] = Field("healthy", description="System performance status")
    active_requests: Optional[int] = Field(0, description="Currently active requests")

class DocumentProcessingResult(BaseModel):
    """Document processing result"""
    document_id: str = Field(..., description="Processed document ID")
    chunks_created: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
