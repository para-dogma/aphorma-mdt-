import time
from sqlalchemy.orm import Session
from aphorma_mdt.storage.models import MultidimensionalToken

class MDTokenService:
    def __init__(self, session: Session, consensus_window_seconds: int = 30):
        self.session = session
        self.consensus_window = consensus_window_seconds
    
    def get_or_create_token(self, agent_id: str) -> MultidimensionalToken:
        token = self.session.query(MultidimensionalToken).filter_by(agent_id=agent_id).first()
        if not token:
            now = int(time.time())
            token = MultidimensionalToken(
                token_id=f"mdt-{agent_id}",
                agent_id=agent_id,
                balance=0,
                stake=0,
                reputation_score=0,
                trust_level=1,
                skill_levels="{}",
                permissions_mask="{}",
                is_active=True,
                health_factor=1.0,
                last_verified_at=now,
                consensus_window_start=now,
                consensus_window_end=now + self.consensus_window,
                version="1.1",
                created_at=now,
                last_updated=now
            )
            self.session.add(token)
            self.session.commit()
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
    
    def get_token_summary(self, agent_id: str) -> dict:
        token = self.get_or_create_token(agent_id)
        return token.to_dict()
