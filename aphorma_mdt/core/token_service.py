import time
import json
from typing import Optional, Dict
from sqlalchemy.orm import Session
from aphorma_mdt.storage.models import MultidimensionalToken

class MDTokenService:
    def __init__(self, session: Session, consensus_window_seconds: int = 30):
        self.session = session
        self.consensus_window_seconds = consensus_window_seconds
    
    def get_or_create_token(self, agent_id: str) -> MultidimensionalToken:
        token = self.session.query(MultidimensionalToken).filter_by(agent_id=agent_id).first()
        
        if not token:
            token = self._create_initial_token(agent_id)
            self.session.add(token)
            self.session.commit()
        else:
            self._refresh_token(token)
            self.session.commit()
        
        return token
    
    def _create_initial_token(self, agent_id: str) -> MultidimensionalToken:
        now = int(time.time())
        return MultidimensionalToken(
            token_id=f"mdt-{agent_id}-{now}",
            agent_id=agent_id,
            balance=0,
            stake=0,
            reputation_score=0,
            trust_level=1,
            skill_levels='{}',
            permissions_mask='{}',
            is_active=True,
            health_factor=1.0,
            last_verified_at=now,
            consensus_window_start=now,
            consensus_window_end=now + self.consensus_window_seconds,
            version='1.1',
            created_at=now,
            last_updated=now
        )
    
    def _refresh_token(self, token: MultidimensionalToken):
        now = int(time.time())
        token.last_verified_at = now
        token.consensus_window_start = now        token.consensus_window_end = now + self.consensus_window_seconds
        token.last_updated = now
        token.health_factor = self._calculate_health_factor(token)
    
    def _calculate_health_factor(self, token: MultidimensionalToken) -> float:
        now = int(time.time())
        if now > token.consensus_window_end:
            return 0.5
        if now - token.last_updated > 3600:
            return 0.7
        return 1.0
    
    def get_effective_balance(self, agent_id: str) -> int:
        token = self.get_or_create_token(agent_id)
        return token.effective_balance
    
    def is_consensus_valid(self, agent_id: str) -> bool:
        token = self.get_or_create_token(agent_id)
        return token.is_consensus_valid
    
    def mint(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
    
    def transfer(self, from_agent: str, to_agent: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        from_token = self.get_or_create_token(from_agent)
        to_token = self.get_or_create_token(to_agent)
        if from_token.effective_balance < amount:
            raise ValueError(f"Insufficient effective balance")
        from_token.balance -= amount
        to_token.balance += amount
        now = int(time.time())
        from_token.last_updated = now
        to_token.last_updated = now
        self.session.commit()
    
    def stake(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        if token.balance < amount:
            raise ValueError(f"Insufficient balance")
        token.balance -= amount
        token.stake += amount        token.last_updated = int(time.time())
        self.session.commit()
    
    def unstake(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        if token.stake < amount:
            raise ValueError(f"Insufficient stake")
        token.stake -= amount
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
    
    def get_token_summary(self, agent_id: str) -> Dict:
        token = self.get_or_create_token(agent_id)
        return token.to_dict()
