from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict
import time

from aphorma_mdt.storage.database import get_session, init_db, create_tables
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.config.settings import settings

# Initialize FastAPI app
app = FastAPI(
    title="AphormA-MDT",
    description="Consensus-Aware Multidimensional Token for DePIN",
    version="1.1.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print(f"🚀 AphormA-MDT v1.1 started on {settings.API_HOST}:{settings.API_PORT}")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.1.0",
        "timestamp": int(time.time())
    }

# Create agent token
@app.post("/tokens/{agent_id}")
async def create_token(agent_id: str, db: Session = Depends(get_session)):
    """Create or get token for agent"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        token = service.get_or_create_token(agent_id)
        return token.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get token
@app.get("/tokens/{agent_id}")
async def get_token(agent_id: str, db: Session = Depends(get_session)):
    """Get token state for agent"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:        return service.get_token_summary(agent_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get effective balance
@app.get("/tokens/{agent_id}/effective-balance")
async def get_effective_balance(agent_id: str, db: Session = Depends(get_session)):
    """Get health-adjusted balance"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        balance = service.get_effective_balance(agent_id)
        return {"agent_id": agent_id, "effective_balance": balance}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Check consensus validity
@app.get("/tokens/{agent_id}/consensus")
async def check_consensus(agent_id: str, db: Session = Depends(get_session)):
    """Check if token is within consensus window"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        is_valid = service.is_consensus_valid(agent_id)
        token = service.get_or_create_token(agent_id)
        return {
            "agent_id": agent_id,
            "valid": is_valid,
            "consensus_window_start": token.consensus_window_start,
            "consensus_window_end": token.consensus_window_end,
            "current_time": int(time.time()),
            "health_factor": token.health_factor
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Mint tokens
@app.post("/tokens/{agent_id}/mint")
async def mint_tokens(agent_id: str, amount: int, db: Session = Depends(get_session)):
    """Mint new tokens to agent"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        service.mint(agent_id, amount)
        return {"status": "minted", "agent_id": agent_id, "amount": amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Transfer tokens
@app.post("/tokens/{from_agent}/transfer")
async def transfer_tokens(    from_agent: str,
    to: str,
    amount: int,
    db: Session = Depends(get_session)
):
    """Transfer tokens between agents"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        service.transfer(from_agent, to, amount)
        return {
            "status": "transferred",
            "from": from_agent,
            "to": to,
            "amount": amount
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stake tokens
@app.post("/tokens/{agent_id}/stake")
async def stake_tokens(agent_id: str, amount: int, db: Session = Depends(get_session)):
    """Stake tokens for trust building"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        service.stake(agent_id, amount)
        return {"status": "staked", "agent_id": agent_id, "amount": amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unstake tokens
@app.post("/tokens/{agent_id}/unstake")
async def unstake_tokens(agent_id: str, amount: int, db: Session = Depends(get_session)):
    """Unstake tokens"""
    service = MDTokenService(db, settings.CONSENSUS_WINDOW_SECONDS)
    try:
        service.unstake(agent_id, amount)
        return {"status": "unstaked", "agent_id": agent_id, "amount": amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
