from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./aphorma_mdt.db"
    REDIS_URL: Optional[str] = None
    CONSENSUS_WINDOW_SECONDS: int = 30
    DEFAULT_HEALTH_FACTOR: float = 1.0
    TON_NETWORK: str = "testnet"
    TON_ENDPOINT: str = "https://testnet.toncenter.com/api/v2"
    TON_API_KEY: Optional[str] = None
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
