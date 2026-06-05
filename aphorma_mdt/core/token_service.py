import time
from typing import Optional
from sqlalchemy.orm import Session
from aphorma_mdt.storage.models import MultidimensionalToken
from aphorma_mdt.cache.redis_cache import RedisCacheLayer
from aphorma_mdt.ton.ton_client import ton_client
import asyncio

class MDTokenService:
    def __init__(self, session: Session, consensus_window_seconds: int = 30, cache: Optional[RedisCacheLayer] = None):
        self.session = session
        self.consensus_window = consensus_window_seconds
        self.cache = cache
    
    def get_or_create_token(self, agent_id: str) -> MultidimensionalToken:
        if self.cache:
            cached = self.cache.get_mdt(agent_id)
            if cached and cached.get("is_consensus_valid"):
                return self._dict_to_token(cached)
        
        token = self.session.query(MultidimensionalToken).filter_by(agent_id=agent_id).first()
        if not token:
            token = self._create_initial_token(agent_id)
            self.session.add(token)
            self.session.commit()
        
        if self.cache:
            self.cache.set_mdt(agent_id, token.to_dict(), ttl=self.consensus_window)
        
        return token
    
    def _create_initial_token(self, agent_id: str) -> MultidimensionalToken:
        now = int(time.time())
        return MultidimensionalToken(
            token_id=f"mdt-{agent_id}",
            agent_id=agent_id,
            balance=0,
            stake=0,
            reputation_score=0,
            trust_level=1,
            skill_levels="{}",
            permissions_mask="{}",
            is_active=True,
            health_factor=1.0,            last_verified_at=now,
            consensus_window_start=now,
            consensus_window_end=now + self.consensus_window,
            version="1.1",
            created_at=now,
            last_updated=now
        )
    
    def _dict_to_token(self, data: dict) -> MultidimensionalToken:
        token = MultidimensionalToken()
        token.token_id = data["token_id"]
        token.agent_id = data["agent_id"]
        token.balance = data["balance"]
        token.stake = data["stake"]
        token.reputation_score = data["reputation_score"]
        token.trust_level = data["trust_level"]
        token.skill_levels = data["skill_levels"]
        token.permissions_mask = data["permissions_mask"]
        token.is_active = data["is_active"]
        token.health_factor = data["health_factor"]
        token.last_verified_at = data["last_verified_at"]
        token.consensus_window_start = data["consensus_window_start"]
        token.consensus_window_end = data["consensus_window_end"]
        token.version = data["version"]
        token.created_at = data["created_at"]
        token.last_updated = data["last_updated"]
        return token
    
    def get_effective_balance(self, agent_id: str) -> int:
        token = self.get_or_create_token(agent_id)
        return token.effective_balance
    
    def is_consensus_valid(self, agent_id: str) -> bool:
        token = self.get_or_create_token(agent_id)
        return token.is_consensus_valid
    
    def mint(self, agent_id: str, amount: int):
        token = self.get_or_create_token(agent_id)
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
        
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(ton_client.anchor_event(agent_id, "mint", {"amount": amount}))
        except Exception as e:
            print(f"Warning: Failed to anchor on-chain: {e}")
        
        if self.cache:
            self.cache.invalidate_mdt(agent_id)    
    def get_token_summary(self, agent_id: str) -> dict:
        token = self.get_or_create_token(agent_id)
        return token.to_dict()
