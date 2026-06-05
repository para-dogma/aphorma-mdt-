import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mdt.db")
    CONSENSUS_WINDOW_SECONDS: int = int(os.getenv("CONSENSUS_WINDOW_SECONDS", "30"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

settings = Settings()
