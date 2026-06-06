from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from aphorma_mdt.storage.database import get_db, create_tables, get_db_stats
from aphorma_mdt.storage.cleanup import CleanupService
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.policy.policy_engine import PolicyEngine
from aphorma_mdt.consensus.validator import validator
from aphorma_mdt.consensus.consensus_service import consensus_window
from aphorma_mdt.config.settings import settings
import time

app = FastAPI(title="AphormA-MDT", version="1.1.0")

cleanup_service = CleanupService(cleanup_interval_hours=24)
policy_engine = PolicyEngine(policy_dir="./policies")

@app.on_event("startup")
def startup():
    create_tables()
    cleanup_service.start_background_cleanup()

@app.on_event("shutdown")
def shutdown():
    cleanup_service.stop()

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.1.0", "timestamp": int(time.time())}

@app.get("/stats")
def stats():
    return get_db_stats()

@app.get("/consensus/stats")
def consensus_stats():
    return consensus_window.get_stats()

@app.get("/consensus/{agent_id}")
def agent_consensus(agent_id: str):
    return consensus_window.get_consensus_for_agent(agent_id)

@app.post("/consensus/validate")
def validate_action(agent_id: str, action: str):
    return validator.validate_action(agent_id, action, {})

@app.get("/policies")
def list_policies():
    return {"active": policy_engine.active_policy, "available": list(policy_engine.policies.keys())}
@app.post("/tokens/{agent_id}")
def create_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    return service.get_or_create_token(agent_id).to_dict()

@app.get("/tokens/{agent_id}")
def get_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    return service.get_token_summary(agent_id)

@app.get("/tokens/{agent_id}/effective-balance")
def get_effective_balance(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    return {"agent_id": agent_id, "effective_balance": service.get_effective_balance(agent_id)}

@app.get("/tokens/{agent_id}/consensus")
def check_consensus(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    token = service.get_or_create_token(agent_id)
    return {"agent_id": agent_id, "valid": token.is_consensus_valid, "health_factor": token.health_factor}

@app.post("/tokens/{agent_id}/mint")
def mint_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    check = policy_engine.check_permission("mint", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    validation = validator.validate_action(agent_id, "mint", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    service = MDTokenService(db)
    service.mint(agent_id, amount)
    return {"status": "minted", "amount": amount, "consensus_confidence": validation["confidence"]}

@app.post("/admin/cleanup")
def trigger_cleanup():
    cleanup_service.run_cleanup()
    return {"status": "cleanup completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

@app.post("/tokens/{agent_id}/transfer")
def transfer_tokens(agent_id: str, to_agent: str, amount: int, db: Session = Depends(get_db)):
    """Transfer tokens between agents"""
    check = policy_engine.check_permission("transfer", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    validation = validator.validate_action(agent_id, "transfer", {"to": to_agent, "amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db)
    service.transfer(agent_id, to_agent, amount)
    
    return {
        "status": "transferred",
        "from": agent_id,
        "to": to_agent,
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/tokens/{agent_id}/stake")
def stake_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    """Stake tokens"""
    check = policy_engine.check_permission("stake", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    validation = validator.validate_action(agent_id, "stake", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db)
    service.stake(agent_id, amount)
    
    return {
        "status": "staked",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }

@app.post("/tokens/{agent_id}/unstake")
def unstake_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    """Unstake tokens"""
    validation = validator.validate_action(agent_id, "unstake", {"amount": amount})
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    service = MDTokenService(db)
    service.unstake(agent_id, amount)
    
    return {
        "status": "unstaked",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }
