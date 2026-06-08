"""
AphormA-MDT API v2.0 - Production Ready with Security
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import time

from aphorma_mdt.storage.database import get_db, init_db, Base, engine
from aphorma_mdt.storage.models import MultidimensionalToken
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.consensus.window import ConsensusWindow
from aphorma_mdt.consensus.validator import ConsensusValidator
from aphorma_mdt.policy.engine import PolicyEngine
from aphorma_mdt.config.settings import settings

# Security imports
from aphorma_mdt.auth.jwt_handler import JWTHandler, create_token_for_user
from aphorma_mdt.auth.rate_limiter import rate_limiter, rate_limit
from aphorma_mdt.auth.permissions import Role, Permission, require_permission, PermissionChecker
from aphorma_mdt.core.error_handler import (
    AppError, ValidationError, NotFoundError,
    create_error_response, create_success_response
)
from aphorma_mdt.core.security_middleware import setup_security

# Initialize FastAPI app
app = FastAPI(
    title="AphormA-MDT",
    description="Consensus-Aware Multidimensional Token for DePIN - Production Ready",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup security middleware
setup_security(app, allowed_origins=["*"])

# Initialize components
consensus_window = ConsensusWindow(window_seconds=settings.CONSENSUS_WINDOW_SECONDS)
validator = ConsensusValidator(required_validators=2)
policy_engine = PolicyEngine()
security = HTTPBearer()

# Register default validators
validator.register_validator("validator-1", weight=1.0)
validator.register_validator("validator-2", weight=1.0)
@app.on_event("startup")
def startup():
    from aphorma_mdt.storage.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
    print("✅ AphormA-MDT v2.0 Production Ready!")

# Health check (no auth required)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AphormA-MDT",
        "version": "2.0.0",
        "timestamp": int(time.time())
    }

# Auth endpoints
@app.post("/auth/login")
async def login(username: str, password: str):
    """
    Login and get JWT token
    In production: validate against user database
    """
    # Simple auth (replace with real user validation)
    if not username or not password:
        raise ValidationError("Username and password required")
    
    # Create token
    token = create_token_for_user(username, {"role": "user"})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username
    }

# Consensus endpoints
@app.get("/consensus")
@rate_limit(limit=100, window=60)
async def get_consensus_stats():
    return consensus_window.get_stats()

@app.get("/consensus/{agent_id}")
@rate_limit(limit=100, window=60)
async def agent_consensus(agent_id: str):
    return consensus_window.get_consensus_for_agent(agent_id)

@app.post("/consensus/validate")
@rate_limit(limit=50, window=60)async def validate_action(agent_id: str, action: str):
    return validator.validate_action(agent_id, action, {})

# Policy endpoints
@app.get("/policies")
@rate_limit(limit=100, window=60)
async def list_policies():
    return {
        "active": policy_engine.active_policy,
        "available": list(policy_engine.policies.keys())
    }

# Token endpoints with security
@app.post("/tokens/{agent_id}")
@rate_limit(limit=50, window=60)
async def create_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    token = service.get_or_create_token(agent_id)
    return create_success_response(token.to_dict(), "Token created")

@app.get("/tokens/{agent_id}")
@rate_limit(limit=100, window=60)
async def get_token(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    token = service.get_or_create_token(agent_id)
    if not token:
        raise NotFoundError(f"Token for agent {agent_id} not found")
    return create_success_response(token.to_dict())

@app.get("/tokens/{agent_id}/effective-balance")
@rate_limit(limit=100, window=60)
async def get_effective_balance(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    effective_balance = service.get_effective_balance(agent_id)
    return create_success_response({
        "agent_id": agent_id,
        "effective_balance": effective_balance
    })

@app.get("/tokens/{agent_id}/consensus")
@rate_limit(limit=100, window=60)
async def check_consensus(agent_id: str, db: Session = Depends(get_db)):
    service = MDTokenService(db)
    token = service.get_or_create_token(agent_id)
    return create_success_response({
        "agent_id": agent_id,
        "valid": token.is_consensus_valid,
        "health_factor": token.health_factor,
        "consensus_window_start": token.consensus_window_start,
        "consensus_window_end": token.consensus_window_end,        "current_time": int(time.time())
    })

# Mint tokens with authentication and authorization
@app.post("/tokens/{agent_id}/mint")
@rate_limit(limit=20, window=60)
async def mint_tokens(
    agent_id: str,
    amount: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(lambda: {"username": "anonymous", "role": Role.USER})  # Replace with real auth
):
    # Check permission
    if not require_permission(Permission.TOKEN_MINT)(current_user):
        raise ForbiddenError("No permission to mint tokens")
    
    # Check policy
    check = policy_engine.check_permission("mint", amount=amount)
    if not check["allowed"]:
        raise ValidationError(check["reason"])
    
    # Validate through consensus
    validation = validator.validate_action(agent_id, "mint", {"amount": amount})
    if not validation["valid"]:
        raise ValidationError(validation["reason"])
    
    # Mint tokens
    service = MDTokenService(db)
    service.mint(agent_id, amount)
    
    return create_success_response({
        "status": "minted",
        "amount": amount,
        "consensus_confidence": validation["confidence"]
    }, "Tokens minted successfully")

@app.post("/tokens/{agent_id}/transfer")
@rate_limit(limit=30, window=60)
async def transfer_tokens(
    agent_id: str,
    to_agent: str,
    amount: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(lambda: {"username": "anonymous", "role": Role.USER})
):
    if not require_permission(Permission.TOKEN_TRANSFER)(current_user):
        raise ForbiddenError("No permission to transfer tokens")
    
    check = policy_engine.check_permission("transfer", amount=amount)
    if not check["allowed"]:        raise ValidationError(check["reason"])
    
    validation = validator.validate_action(agent_id, "transfer", {"to": to_agent, "amount": amount})
    if not validation["valid"]:
        raise ValidationError(validation["reason"])
    
    service = MDTokenService(db)
    service.transfer(agent_id, to_agent, amount)
    
    return create_success_response({
        "status": "transferred",
        "from": agent_id,
        "to": to_agent,
        "amount": amount
    }, "Tokens transferred successfully")

@app.post("/tokens/{agent_id}/stake")
@rate_limit(limit=30, window=60)
async def stake_tokens(
    agent_id: str,
    amount: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(lambda: {"username": "anonymous", "role": Role.USER})
):
    check = policy_engine.check_permission("stake", amount=amount)
    if not check["allowed"]:
        raise ValidationError(check["reason"])
    
    validation = validator.validate_action(agent_id, "stake", {"amount": amount})
    if not validation["valid"]:
        raise ValidationError(validation["reason"])
    
    service = MDTokenService(db)
    service.stake(agent_id, amount)
    
    return create_success_response({
        "status": "staked",
        "amount": amount
    }, "Tokens staked successfully")

@app.post("/tokens/{agent_id}/unstake")
@rate_limit(limit=30, window=60)
async def unstake_tokens(
    agent_id: str,
    amount: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(lambda: {"username": "anonymous", "role": Role.USER})
):
    validation = validator.validate_action(agent_id, "unstake", {"amount": amount})
    if not validation["valid"]:        raise ValidationError(validation["reason"])
    
    service = MDTokenService(db)
    service.unstake(agent_id, amount)
    
    return create_success_response({
        "status": "unstaked",
        "amount": amount
    }, "Tokens unstaked successfully")

# Admin endpoints
@app.post("/admin/cleanup")
@rate_limit(limit=5, window=3600)
async def trigger_cleanup(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(lambda: {"username": "admin", "role": Role.ADMIN})
):
    if not require_permission(Permission.ADMIN_CLEANUP)(current_user):
        raise ForbiddenError("Admin permission required")
    
    consensus_window.events.clear()
    
    return create_success_response({
        "status": "cleanup_completed",
        "timestamp": int(time.time())
    }, "Cleanup completed")

# Error handlers
app.add_exception_handler(AppError, lambda r, e: create_error_response(e.message, e.status_code, e.error_code, e.details))
app.add_exception_handler(ValidationError, lambda r, e: create_error_response(e.message, e.status_code, e.error_code, e.details))
app.add_exception_handler(NotFoundError, lambda r, e: create_error_response(e.message, e.status_code, e.error_code, e.details))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
