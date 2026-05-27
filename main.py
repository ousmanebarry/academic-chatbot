from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from config import settings
from models import ChatRequest, ChatResponse, DocumentUploadRequest, HealthResponse, StatsResponse
from services.chat_service import ChatService
from services.document_service import DocumentService
from services.cache_service import CacheService
from services.performance_monitor import monitor, performance_tracking

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Global services
chat_service: ChatService = None
document_service: DocumentService = None
cache_service: CacheService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application services"""
    global chat_service, document_service, cache_service
    
    logger.info("Starting ScholarAI API...")
    
    # Initialize services
    try:
        cache_service = CacheService()
        await cache_service.initialize()
        
        document_service = DocumentService()
        await document_service.initialize()
        
        chat_service = ChatService(document_service, cache_service)
        await chat_service.initialize()
        
        logger.info("All services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        # Cleanup
        if cache_service:
            await cache_service.close()
        logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="ScholarAI",
    description="High-performance academic Q&A assistant with semantic search",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get services
async def get_chat_service() -> ChatService:
    if chat_service is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    return chat_service

async def get_document_service() -> DocumentService:
    if document_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    return document_service

@app.get("/ui")
@app.get("/")
async def serve_ui():
    """Serve the web UI"""
    return FileResponse("index.html")

@app.get("/styles.css")
async def serve_styles():
    return FileResponse("styles.css", media_type="text/css")

@app.get("/script.js")
async def serve_script():
    return FileResponse("script.js", media_type="application/javascript")

@app.get("/favicon.svg")
async def serve_favicon():
    return FileResponse("favicon.svg", media_type="image/svg+xml")

@app.get("/api", response_model=dict)
@app.get("/api/", response_model=dict)
async def root():
    """Root API endpoint"""
    return {
        "message": "ScholarAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        services={
            "chat_service": chat_service is not None,
            "document_service": document_service is not None,
            "cache_service": cache_service is not None
        }
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats(service: ChatService = Depends(get_chat_service)):
    """Get system statistics including performance metrics"""
    try:
        stats = await service.get_statistics()
        perf_metrics = monitor.get_performance_metrics()
        
        # Merge performance metrics
        stats.update({
            "performance_status": perf_metrics["performance_status"],
            "active_requests": perf_metrics["active_requests"]
        })
        
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.post("/chat", response_model=ChatResponse)
@performance_tracking
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Main chat endpoint with performance optimization"""
    try:
        start_time = time.time()
        
        # Process the chat request
        response = await service.process_chat(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        response.response_time_ms = response_time
        
        logger.info(f"Chat request processed in {response_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request")

@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Streaming chat endpoint"""
    try:
        async def generate_response():
            async for chunk in service.process_chat_stream(request):
                yield f"data: {chunk}\n\n"
                
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process streaming request")

@app.post("/documents/upload")
async def upload_documents(
    request: DocumentUploadRequest,
    service: DocumentService = Depends(get_document_service)
):
    """Upload and index documents"""
    try:
        result = await service.upload_documents(request)
        return {"message": "Documents uploaded successfully", "processed": result["processed"]}
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload documents")

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Delete a document from the index"""
    try:
        await service.delete_document(document_id)
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
