from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.models import Base
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def enable_wal_mode():
    if "sqlite" in settings.DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.commit()
        logger.info("WAL mode enabled")

def create_indexes():
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agent_id ON multidimensional_tokens(agent_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_is_active ON multidimensional_tokens(is_active)"))
        conn.commit()
    logger.info("Indexes created")

def create_tables():
    Base.metadata.create_all(bind=engine)
    enable_wal_mode()
    create_indexes()
    logger.info("Database initialized")

def get_db_stats() -> dict:
    from sqlalchemy import text
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM multidimensional_tokens")).scalar()
        active = conn.execute(text("SELECT COUNT(*) FROM multidimensional_tokens WHERE is_active = 1")).scalar()
    return {"total_tokens": total, "active_tokens": active}
