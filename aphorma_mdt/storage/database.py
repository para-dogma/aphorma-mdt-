from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db_stats():
    """Get database statistics"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM multidimensional_tokens"))
        token_count = result.scalar()
    
    return {
        "total_tokens": token_count,
        "database_url": settings.DATABASE_URL
    }


def init_db():
    """Initialize database"""
    create_tables()
    print(f"✅ Database initialized: {settings.DATABASE_URL}")
