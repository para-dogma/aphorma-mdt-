import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mdt.db")
    
    # Consensus
    CONSENSUS_WINDOW_SECONDS: int = int(os.getenv("CONSENSUS_WINDOW_SECONDS", "30"))
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Redis (optional)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

settings = Settings()
