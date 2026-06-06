from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import time
import json
import logging

from aphorma_mdt.storage.database import get_db, init_db, Base, engine
from aphorma_mdt.storage.models import MultidimensionalToken
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.consensus.window import ConsensusWindow
from aphorma_mdt.consensus.validator import ConsensusValidator
from aphorma_mdt.policy.engine import PolicyEngine
from aphorma_mdt.cache.redis_cache import RedisCacheLayer
from aphorma_mdt.config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AphormA-MDT",
    description="Consensus-Aware Multidimensional Token for DePIN",
    version="1.1.0"
)

# Initialize components
cache = RedisCacheLayer(settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://localhost:6379/0")
consensus_window = ConsensusWindow(window_seconds=settings.CONSENSUS_WINDOW_SECONDS)
validator = ConsensusValidator(required_validators=2)
policy_engine = PolicyEngine()

validator.register_validator("validator-1", weight=1.0)
validator.register_validator("validator-2", weight=1.0)

@app.on_event("startup")
def startup():
    from aphorma_mdt.storage.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")

@app.get("/health")def health_check():
    return {
        "status": "healthy",
        "service": "AphormA-MDT",
        "version": "1.1.0",
        "timestamp": int(time.time()),
        "cache_enabled": cache.enabled
    }

@app.get("/cache/stats")
def cache_statistics():
    return cache.get_stats()

@app.get("/consensus")
def get_consensus_stats():
    return consensus_window.get_stats()

@app.get("/consensus/{agent_id}")
def agent_consensus(agent_id: str):
    return consensus_window.get_consensus_for_agent(agent_id)

@app.post("/consensus/validate")
def validate_action(agent_id: str, action: str):
    return validator.validate_action(agent_id, action, {})

@app.get("/policies")
def list_policies():
    return {
        "active": policy_engine.active_policy,
        "available": list(policy_engine.policies.keys())
    }

@app.post("/tokens/{agent_id}")
def create_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db, cache)
    token = service.get_or_create_token(agent_id)
    return token.to_dict()

@app.get("/tokens/{agent_id}")
def get_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db, cache)
    return service.get_token_summary(agent_id)

@app.get("/tokens/{agent_id}/effective-balance")
def get_effective_balance(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db, cache)
    effective_balance = service.get_effective_balance(agent_id)
    return {
        "agent_id": agent_id,
        "effective_balance": effective_balance    }

@app.get("/tokens/{agent_id}/consensus")
def check_consensus(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db, cache)
    token = service.get_or_create_token(agent_id)
    
    return {
        "agent_id": agent_id,
        "valid": token.is_consensus_valid,
        "health_factor": token.health_factor,
        "consensus_window_start": token.consensus_window_start,
        "consensus_window_end": token.consensus_window_end,
        "current_time": int(time.time())
    }

@app.post("/tokens/{agent_id}/mint")
def mint_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    check = policy_engine.check_permission("mint", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    validation = validator.validate_action(agent_id, "mint", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db, cache)
    service.mint(agent_id, amount)
    
    return {
        "status": "minted",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/tokens/{agent_id}/transfer")
def transfer_tokens(agent_id: str, to_agent: str, amount: int, db: Session = Depends(get_db)):
    check = policy_engine.check_permission("transfer", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    validation = validator.validate_action(agent_id, "transfer", {"to": to_agent, "amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db, cache)
    service.transfer(agent_id, to_agent, amount)
    
    return {
        "status": "transferred",        "from": agent_id,
        "to": to_agent,
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/tokens/{agent_id}/stake")
def stake_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    check = policy_engine.check_permission("stake", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    validation = validator.validate_action(agent_id, "stake", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db, cache)
    service.stake(agent_id, amount)
    
    return {
        "status": "staked",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/tokens/{agent_id}/unstake")
def unstake_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    validation = validator.validate_action(agent_id, "unstake", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db, cache)
    service.unstake(agent_id, amount)
    
    return {
        "status": "unstaked",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/admin/cleanup")
def trigger_cleanup(db: Session = Depends(get_db)):
    consensus_window.events.clear()
    cache.clear_stats()
    
    return {
        "status": "cleanup_completed",
        "timestamp": int(time.time())
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level="info")
