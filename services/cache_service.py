import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for performance optimization"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = settings.cache_ttl
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            if settings.redis_url:
                # Use Redis URL (for Render, Heroku, etc.)
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            else:
                # Use individual connection parameters
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}. Running without cache.")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate a cache key from data"""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get_chat_response(self, query: str, context: str = "") -> Optional[Dict[str, Any]]:
        """Get cached chat response"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_key("chat", f"{query}:{context}")
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return json.loads(cached_data)
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            
        return None
    
    async def set_chat_response(self, query: str, context: str, response: Dict[str, Any]) -> None:
        """Cache chat response"""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._generate_key("chat", f"{query}:{context}")
            cached_response = response.copy()
            cached_response['cached'] = True
            
            await self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(cached_response, default=str)
            )
            
            logger.debug(f"Cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def get_document_embeddings(self, document_id: str) -> Optional[List[float]]:
        """Get cached document embeddings"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_key("embeddings", document_id)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
                
        except Exception as e:
            logger.error(f"Error retrieving embeddings from cache: {e}")
            
        return None
    
    async def set_document_embeddings(self, document_id: str, embeddings: List[float]) -> None:
        """Cache document embeddings"""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._generate_key("embeddings", document_id)
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl * 24,  # Cache embeddings longer
                json.dumps(embeddings)
            )
            
        except Exception as e:
            logger.error(f"Error caching embeddings: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"connected": False, "hit_rate": 0.0}
            
        try:
            info = await self.redis_client.info()
            
            # Calculate cache hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            
            return {
                "connected": True,
                "hit_rate": hit_rate,
                "total_keys": info.get('db0', {}).get('keys', 0),
                "memory_usage": info.get('used_memory_human', '0B')
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "hit_rate": 0.0}
    
    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern"""
        if not self.redis_client:
            return 0
            
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
