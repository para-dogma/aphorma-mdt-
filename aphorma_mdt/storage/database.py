from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    create_tables()
    print(f"✅ Database initialized: {settings.DATABASE_URL}")
