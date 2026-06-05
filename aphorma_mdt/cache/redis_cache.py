import json
import time
from typing import Optional, Dict, Any

class RedisCacheLayer:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self.client = None
        self.circuit_open = True
        self.last_error_time = 0
        self.error_count = 0
        self.max_errors = 5
        self.cooldown_seconds = 60
    
    def get_mdt(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            key = f"mdt:{agent_id}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def set_mdt(self, agent_id: str, token_data: Dict[str, Any], ttl: int = 60):
        if not self.client:
            return
        try:
            key = f"mdt:{agent_id}"
            self.client.setex(key, ttl, json.dumps(token_data))
        except Exception:
            pass
    
    def invalidate_mdt(self, agent_id: str):
        if not self.client:
            return
        try:
            key = f"mdt:{agent_id}"
            self.client.delete(key)
        except Exception:
            pass
