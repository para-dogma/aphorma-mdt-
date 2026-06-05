from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from aphorma_mdt.storage.database import get_db, create_tables
from aphorma_mdt.core.token_service import MDTokenService
from aphorma_mdt.config.settings import settings

app = FastAPI(title="AphormA-MDT", version="1.1.0")

@app.on_event("startup")
def startup():
    create_tables()
    print("🚀 AphormA-MDT v1.1 started")

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.1.0"}

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
    service = MDTokenService(db)
    service.mint(agent_id, amount)
    return {"status": "minted", "amount": amount}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
