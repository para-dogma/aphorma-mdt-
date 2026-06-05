from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.models import Base
import logging

logger = logging.getLogger(__name__)

# Connection pooling settings
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
    """Enable WAL mode for SQLite (better concurrency)"""
    if "sqlite" in settings.DATABASE_URL:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=10000"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.commit()
        logger.info("✅ WAL mode enabled")

def create_indexes():
    """Create performance indexes"""
    with engine.connect() as conn:
        # Index for agent lookups
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_agent_id ON multidimensional_tokens(agent_id)"
        ))
        # Index for active tokens
        conn.execute(text(            "CREATE INDEX IF NOT EXISTS idx_is_active ON multidimensional_tokens(is_active)"
        ))
        # Index for consensus window
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_consensus_end ON multidimensional_tokens(consensus_window_end)"
        ))
        conn.commit()
    logger.info("✅ Indexes created")

def cleanup_old_tokens(days: int = 30):
    """Remove tokens inactive for N days"""
    import time
    cutoff = int(time.time()) - (days * 86400)
    
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                DELETE FROM multidimensional_tokens 
                WHERE last_updated < :cutoff AND is_active = 0
            """),
            {"cutoff": cutoff}
        )
        conn.commit()
        deleted = result.rowcount
    
    logger.info(f"✅ Cleaned up {deleted} old tokens")
    return deleted

def create_tables():
    """Create all tables with production settings"""
    Base.metadata.create_all(bind=engine)
    enable_wal_mode()
    create_indexes()
    logger.info("✅ Database initialized with production settings")

def get_db_stats() -> dict:
    """Get database statistics"""
    with engine.connect() as conn:
        total_tokens = conn.execute(
            text("SELECT COUNT(*) FROM multidimensional_tokens")
        ).scalar()
        
        active_tokens = conn.execute(
            text("SELECT COUNT(*) FROM multidimensional_tokens WHERE is_active = 1")
        ).scalar()
        
        avg_health = conn.execute(
            text("SELECT AVG(health_factor) FROM multidimensional_tokens")
        ).scalar() or 0.0
        return {
        "total_tokens": total_tokens,
        "active_tokens": active_tokens,
        "avg_health_factor": round(avg_health, 3)
    }
