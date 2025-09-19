"""
Caching mechanism for BearTech Token Analysis Bot
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..config import CACHE_TTL, MAX_CACHE_SIZE

logger = logging.getLogger(__name__)


class TokenAnalysisCache:
    """In-memory cache for token analysis results"""
    
    def __init__(self, ttl: int = CACHE_TTL, max_size: int = MAX_CACHE_SIZE):
        self.ttl = ttl  # Time to live in seconds
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key
        """
        async with self._lock:
            if key not in self.cache:
                return None
            
            # Check if data is expired
            if self._is_expired(key):
                await self._remove(key)
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            
            # Return cached data
            return self.cache[key].copy()
    
    async def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Set cached data with key
        """
        async with self._lock:
            # Check cache size limit
            if len(self.cache) >= self.max_size:
                await self._evict_oldest()
            
            # Store data with timestamp
            self.cache[key] = {
                "data": data.copy(),
                "timestamp": time.time(),
                "created_at": datetime.utcnow().isoformat()
            }
            self.access_times[key] = time.time()
    
    async def get_or_set(self, key: str, fetch_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Get from cache or fetch and cache the result
        """
        # Try to get from cache first
        cached_data = await self.get(key)
        if cached_data is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_data
        
        # Fetch data if not in cache
        logger.debug(f"Cache miss for key: {key}, fetching data...")
        try:
            data = await fetch_func(*args, **kwargs)
            if data:
                await self.set(key, data)
            return data or {}
        except Exception as e:
            logger.error(f"Error fetching data for cache key {key}: {str(e)}")
            return {}
    
    async def invalidate(self, key: str) -> None:
        """
        Invalidate cached data by key
        """
        async with self._lock:
            await self._remove(key)
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern
        """
        async with self._lock:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                await self._remove(key)
    
    async def clear(self) -> None:
        """
        Clear all cached data
        """
        async with self._lock:
            self.cache.clear()
            self.access_times.clear()
    
    async def cleanup_expired(self) -> None:
        """
        Remove all expired entries
        """
        async with self._lock:
            expired_keys = [key for key in self.cache.keys() if self._is_expired(key)]
            for key in expired_keys:
                await self._remove(key)
    
    def _is_expired(self, key: str) -> bool:
        """Check if cached data is expired"""
        if key not in self.cache:
            return True
        
        cache_entry = self.cache[key]
        timestamp = cache_entry["timestamp"]
        return time.time() - timestamp > self.ttl
    
    async def _remove(self, key: str) -> None:
        """Remove entry from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
    
    async def _evict_oldest(self) -> None:
        """Evict the least recently used entry"""
        if not self.access_times:
            return
        
        # Find the oldest accessed entry
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        await self._remove(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hit_rate": self._calculate_hit_rate(),
            "oldest_entry": self._get_oldest_entry(),
            "newest_entry": self._get_newest_entry()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        # This is a simplified calculation
        # In a real implementation, you'd track hits and misses
        return 0.0
    
    def _get_oldest_entry(self) -> Optional[str]:
        """Get the oldest entry timestamp"""
        if not self.cache:
            return None
        
        oldest_timestamp = min(entry["timestamp"] for entry in self.cache.values())
        return datetime.fromtimestamp(oldest_timestamp).isoformat()
    
    def _get_newest_entry(self) -> Optional[str]:
        """Get the newest entry timestamp"""
        if not self.cache:
            return None
        
        newest_timestamp = max(entry["timestamp"] for entry in self.cache.values())
        return datetime.fromtimestamp(newest_timestamp).isoformat()


class CacheManager:
    """Manages multiple caches for different data types"""
    
    def __init__(self):
        self.caches = {
            "token_analysis": TokenAnalysisCache(ttl=300),  # 5 minutes
            "market_data": TokenAnalysisCache(ttl=60),      # 1 minute
            "security_data": TokenAnalysisCache(ttl=600),   # 10 minutes
            "contract_data": TokenAnalysisCache(ttl=1800),  # 30 minutes
            "deployer_data": TokenAnalysisCache(ttl=3600),  # 1 hour
        }
        self._cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                for cache in self.caches.values():
                    await cache.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    def get_cache(self, cache_type: str) -> Optional[TokenAnalysisCache]:
        """Get cache by type"""
        return self.caches.get(cache_type)
    
    async def get_token_analysis(self, address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Get cached token analysis"""
        cache = self.get_cache("token_analysis")
        if cache:
            key = f"{chain}:{address}"
            return await cache.get(key)
        return None
    
    async def set_token_analysis(self, address: str, chain: str, data: Dict[str, Any]) -> None:
        """Set cached token analysis"""
        cache = self.get_cache("token_analysis")
        if cache:
            key = f"{chain}:{address}"
            await cache.set(key, data)
    
    async def get_market_data(self, address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Get cached market data"""
        cache = self.get_cache("market_data")
        if cache:
            key = f"{chain}:{address}"
            return await cache.get(key)
        return None
    
    async def set_market_data(self, address: str, chain: str, data: Dict[str, Any]) -> None:
        """Set cached market data"""
        cache = self.get_cache("market_data")
        if cache:
            key = f"{chain}:{address}"
            await cache.set(key, data)
    
    async def get_security_data(self, address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Get cached security data"""
        cache = self.get_cache("security_data")
        if cache:
            key = f"{chain}:{address}"
            return await cache.get(key)
        return None
    
    async def set_security_data(self, address: str, chain: str, data: Dict[str, Any]) -> None:
        """Set cached security data"""
        cache = self.get_cache("security_data")
        if cache:
            key = f"{chain}:{address}"
            await cache.set(key, data)
    
    async def invalidate_token(self, address: str, chain: str) -> None:
        """Invalidate all cached data for a token"""
        key_pattern = f"{chain}:{address}"
        for cache in self.caches.values():
            await cache.invalidate_pattern(key_pattern)
    
    async def clear_all(self) -> None:
        """Clear all caches"""
        for cache in self.caches.values():
            await cache.clear()
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            cache_type: cache.get_stats()
            for cache_type, cache in self.caches.items()
        }


# Global cache manager instance
cache_manager = CacheManager()



