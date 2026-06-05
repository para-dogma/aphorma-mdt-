from sqlalchemy import Column, String, Integer, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MultidimensionalToken(Base):
    __tablename__ = 'multidimensional_tokens'
    
    token_id = Column(String, primary_key=True)
    agent_id = Column(String, unique=True, nullable=False, index=True)
    balance = Column(Integer, default=0)
    stake = Column(Integer, default=0)
    reputation_score = Column(Integer, default=0)
    trust_level = Column(Integer, default=1)
    skill_levels = Column(Text, default='{}')
    permissions_mask = Column(Text, default='{}')
    is_active = Column(Boolean, default=True)
    health_factor = Column(Float, default=1.0)
    last_verified_at = Column(Integer, default=0)
    consensus_window_start = Column(Integer, default=0)
    consensus_window_end = Column(Integer, default=0)
    version = Column(String, default='1.1')
    created_at = Column(Integer, nullable=False)
    last_updated = Column(Integer, nullable=False)
    
    @property
    def effective_balance(self) -> int:
        return int(self.balance * self.health_factor)
    
    @property
    def is_consensus_valid(self) -> bool:
        import time
        current_time = int(time.time())
        return self.consensus_window_start <= current_time <= self.consensus_window_end
    
    def to_dict(self) -> dict:
        import json
        return {
            "token_id": self.token_id,
            "agent_id": self.agent_id,
            "balance": self.balance,
            "effective_balance": self.effective_balance,
            "stake": self.stake,
            "reputation_score": self.reputation_score,
            "trust_level": self.trust_level,
            "skill_levels": json.loads(self.skill_levels),
            "permissions_mask": json.loads(self.permissions_mask),
            "is_active": self.is_active,
            "health_factor": self.health_factor,
            "last_verified_at": self.last_verified_at,
            "consensus_window_start": self.consensus_window_start,
            "consensus_window_end": self.consensus_window_end,
            "is_consensus_valid": self.is_consensus_valid,
            "version": self.version,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
