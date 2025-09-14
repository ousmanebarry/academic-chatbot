import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    
    # Pinecone Configuration
    pinecone_environment: str
    pinecone_index_name: str = "academic-chatbot-index"
    
    # Redis Configuration
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    # Vector Database Configuration
    embedding_model: str = "text-embedding-ada-002"
    vector_dimension: int = 1536
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Response Configuration
    max_tokens: int = 500
    temperature: float = 0.7
    top_k_results: int = 5
    
    # Model Configuration
    chat_model: str = "gpt-3.5-turbo"  # Changed default to gpt-3.5-turbo for better availability
    
    # Performance Configuration
    cache_ttl: int = 3600  # 1 hour in seconds
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
