from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.models import Base

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
