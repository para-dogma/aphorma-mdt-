import json
import time
from typing import Dict
from sqlalchemy.orm import Sessionfrom aphorma_mdt.storage.models import MultidimensionalToken
from aphorma_mdt.config.settings import settings
from aphorma_mdt.cache.redis_cache import RedisCacheLayer


class MDTokenService:
    def __init__(self, db: Session, cache: RedisCacheLayer = None):
        self.session = db
        self.cache = cache
        self.consensus_window_seconds = settings.CONSENSUS_WINDOW_SECONDS

    def get_or_create_token(self, agent_id: str) -> MultidimensionalToken:
        # Try cache first
        if self.cache:
            cached = self.cache.get_mdt(agent_id)
            if cached:
                # Return from cache - need to fetch from DB for ORM object
                pass
        
        token = self.session.query(MultidimensionalToken).filter_by(agent_id=agent_id).first()
        if not token:
            token = self._create_initial_token(agent_id)
            self.session.add(token)
            self.session.commit()
        else:
            self._refresh_token(token)
            self.session.commit()
        
        # Update cache
        if self.cache:
            self.cache.set_mdt(agent_id, token.to_dict())
        
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
            last_updated=now,
            health_factor=1.0,
            last_verified_at=now,
            consensus_window_start=now,            consensus_window_end=now + self.consensus_window_seconds,
            version="1.1"
        )

    def _refresh_token(self, token: MultidimensionalToken):
        now = int(time.time())
        token.last_verified_at = now
        token.consensus_window_start = now
        token.consensus_window_end = now + self.consensus_window_seconds
        token.health_factor = self._calculate_health_factor(token)
        token.last_updated = now

    def _calculate_health_factor(self, token: MultidimensionalToken) -> float:
        now = int(time.time())
        age = now - token.last_updated

        if not token.is_active:
            return 0.0

        if age > 3600:
            return 0.5
        elif age > 1800:
            return 0.7

        return 1.0

    def get_effective_balance(self, agent_id: str) -> int:
        token = self.get_or_create_token(agent_id)
        return int(token.balance * token.health_factor)

    def mint(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_mdt(agent_id)

    def transfer(self, from_agent: str, to_agent: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")

        from_token = self.get_or_create_token(from_agent)
        to_token = self.get_or_create_token(to_agent)

        if from_token.balance < amount:            raise ValueError("Insufficient balance")

        from_token.balance -= amount
        to_token.balance += amount

        now = int(time.time())
        from_token.last_updated = now
        to_token.last_updated = now

        self.session.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_mdt(from_agent)
            self.cache.invalidate_mdt(to_agent)

    def stake(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        if token.balance < amount:
            raise ValueError("Insufficient balance")

        token.balance -= amount
        token.stake += amount
        token.last_updated = int(time.time())
        self.session.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_mdt(agent_id)

    def unstake(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        if token.stake < amount:
            raise ValueError("Insufficient stake")

        token.stake -= amount
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_mdt(agent_id)

    def get_token_summary(self, agent_id: str) -> Dict:
        token = self.get_or_create_token(agent_id)        return token.to_dict()
