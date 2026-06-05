import time
import json
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from aphorma_mdt.storage.models import MultidimensionalToken, Base

class MDTokenService:
    """
    MDT v1.1 Service - Consensus-Aware Token Management
    
    MVS Features:
    - effective_balance calculation
    - consensus_window validation
    - health_factor management
    """
    
    def __init__(self, session: Session, consensus_window_seconds: int = 30):
        self.session = session
        self.consensus_window_seconds = consensus_window_seconds
    
    def get_or_create_token(self, agent_id: str) -> MultidimensionalToken:
        """Get existing token or create new one with MVS fields"""
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
        """Create new token with MVS fields initialized"""
        now = int(time.time())
        
        return MultidimensionalToken(
            token_id=f"mdt-{agent_id}-{now}",
            agent_id=agent_id,
            balance=0,
            stake=0,
            reputation_score=0,
            trust_level=1,
            skill_levels='{}',
            permissions_mask='{}',            is_active=True,
            health_factor=1.0,
            last_verified_at=now,
            consensus_window_start=now,
            consensus_window_end=now + self.consensus_window_seconds,
            version='1.1',
            created_at=now,
            last_updated=now
        )
    
    def _refresh_token(self, token: MultidimensionalToken):
        """Refresh token state and update consensus window"""
        now = int(time.time())
        token.last_verified_at = now
        token.consensus_window_start = now
        token.consensus_window_end = now + self.consensus_window_seconds
        token.last_updated = now
        
        # Update health factor based on freshness
        token.health_factor = self._calculate_health_factor(token)
    
    def _calculate_health_factor(self, token: MultidimensionalToken) -> float:
        """
        Calculate health factor based on:
        - Token freshness (within consensus window)
        - Time since last update
        """
        now = int(time.time())
        
        # If outside consensus window, reduce health
        if now > token.consensus_window_end:
            return 0.5
        
        # If very old (>1 hour), reduce health
        if now - token.last_updated > 3600:
            return 0.7
        
        # Fresh token
        return 1.0
    
    def get_effective_balance(self, agent_id: str) -> int:
        """Get balance adjusted by health factor"""
        token = self.get_or_create_token(agent_id)
        return token.effective_balance
    
    def is_consensus_valid(self, agent_id: str) -> bool:
        """Check if token is within consensus window"""
        token = self.get_or_create_token(agent_id)
        return token.is_consensus_valid
        def mint(self, agent_id: str, amount: int):
        """Mint new tokens to agent"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        token = self.get_or_create_token(agent_id)
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
    
    def transfer(self, from_agent: str, to_agent: str, amount: int):
        """Transfer tokens between agents (checks effective balance)"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        from_token = self.get_or_create_token(from_agent)
        to_token = self.get_or_create_token(to_agent)
        
        # Check effective balance (health-adjusted)
        if from_token.effective_balance < amount:
            raise ValueError(f"Insufficient effective balance: {from_token.effective_balance} < {amount}")
        
        from_token.balance -= amount
        to_token.balance += amount
        
        now = int(time.time())
        from_token.last_updated = now
        to_token.last_updated = now
        
        self.session.commit()
    
    def stake(self, agent_id: str, amount: int):
        """Stake tokens (lock for trust building)"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        token = self.get_or_create_token(agent_id)
        if token.balance < amount:
            raise ValueError(f"Insufficient balance: {token.balance} < {amount}")
        
        token.balance -= amount
        token.stake += amount
        token.last_updated = int(time.time())
        self.session.commit()
    
    def unstake(self, agent_id: str, amount: int):
        """Unstake tokens (release from trust building)"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
                token = self.get_or_create_token(agent_id)
        if token.stake < amount:
            raise ValueError(f"Insufficient stake: {token.stake} < {amount}")
        
        token.stake -= amount
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()
    
    def get_token_summary(self, agent_id: str) -> Dict:
        """Get full token state as dictionary"""
        token = self.get_or_create_token(agent_id)
        return token.to_dict()
