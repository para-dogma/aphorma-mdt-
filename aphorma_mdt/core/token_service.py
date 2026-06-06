import json
import time
from typing import Dict
from sqlalchemy.orm import Session
from aphorma_mdt.storage.models import MultidimensionalToken
from aphorma_mdt.config.settings import settings


class MDTokenService:
    def __init__(self, db: Session):
        self.session = db
        self.consensus_window_seconds = settings.CONSENSUS_WINDOW_SECONDS

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

    def _refresh_token(self, token: MultidimensionalToken):
        now = int(time.time())
        token.last_verified_at = now
        token.consensus_window_start = now
        token.consensus_window_end = now + self.consensus_window_seconds
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
        return int(token.balance * token.health_factor)

    def mint(self, agent_id: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        token = self.get_or_create_token(agent_id)
        token.balance += amount
        token.last_updated = int(time.time())
        self.session.commit()

    def get_token_summary(self, agent_id: str) -> Dict:
        token = self.get_or_create_token(agent_id)
        return token.to_dict()
