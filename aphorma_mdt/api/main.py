from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from aphorma_mdt.storage.database import get_db, create_tables, get_db_stats
from aphorma_mdt.storage.cleanup import CleanupService
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.policy.policy_engine import PolicyEngine
from aphorma_mdt.config.settings import settings
import time

app = FastAPI(title="AphormA-MDT", version="1.1.0")

cleanup_service = CleanupService(cleanup_interval_hours=24)
policy_engine = PolicyEngine(policy_dir="./policies")

@app.on_event("startup")
def startup():
    create_tables()
    cleanup_service.start_background_cleanup()
    print("🚀 AphormA-MDT v1.1 started with Policy Engine")

@app.on_event("shutdown")
def shutdown():
    cleanup_service.stop()
    print("👋 Shutdown complete")

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.1.0", "timestamp": int(time.time())}

@app.get("/stats")
def stats():
    return get_db_stats()

@app.get("/policies")
def list_policies():
    """List all available policies"""
    return {
        "active": policy_engine.active_policy,
        "available": list(policy_engine.policies.keys())
    }

@app.get("/policies/active")
def active_policy():
    """Get active policy details"""
    info = policy_engine.get_active_policy_info()
    if not info:
        raise HTTPException(status_code=404, detail="No active policy")
    return info
@app.post("/policies/{policy_name}/activate")
def activate_policy(policy_name: str):
    """Activate a policy"""
    if policy_engine.activate_policy(policy_name):
        return {"status": "activated", "policy": policy_name}
    raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")

@app.post("/policies/check")
def check_policy(action: str, amount: int = 0):
    """Check if action is allowed by current policy"""
    result = policy_engine.check_permission(action, amount=amount)
    return result

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
    return {
        "agent_id": agent_id,
        "valid": token.is_consensus_valid,
        "health_factor": token.health_factor,
        "consensus_window_end": token.consensus_window_end
    }

@app.post("/tokens/{agent_id}/mint")
def mint_tokens(agent_id: str, amount: int, db: Session = Depends(get_db)):
    # Check policy
    check = policy_engine.check_permission("mint", amount=amount)
    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])
    
    service = MDTokenService(db)
    service.mint(agent_id, amount)
    return {"status": "minted", "amount": amount}
@app.post("/admin/cleanup")
def trigger_cleanup():
    cleanup_service.run_cleanup()
    return {"status": "cleanup completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
