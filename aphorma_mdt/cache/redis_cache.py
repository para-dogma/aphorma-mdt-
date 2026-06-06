import json
import redis
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedisCacheLayer:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            self.enabled = True
            logger.info("✅ Redis connected")
        except redis.ConnectionError:
            self.client = None
            self.enabled = False
            logger.warning("⚠️  Redis not available, cache disabled")
        
        self.hits = 0
        self.misses = 0
    
    def get_mdt(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            key = f"mdt:{agent_id}"
            data = self.client.get(key)
            if data:
                self.hits += 1
                return json.loads(data)
            self.misses += 1            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set_mdt(self, agent_id: str, token_data: Dict[str, Any], ttl: int = 60):
        if not self.enabled:
            return
        
        try:
            key = f"mdt:{agent_id}"
            self.client.setex(key, ttl, json.dumps(token_data))
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def invalidate_mdt(self, agent_id: str):
        if not self.enabled:
            return
        
        try:
            key = f"mdt:{agent_id}"
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_ratio = self.hits / total if total > 0 else 0.0
        
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": round(hit_ratio, 2),
            "total_requests": total
        }
    
    def clear_stats(self):
        self.hits = 0
        self.misses = 0
