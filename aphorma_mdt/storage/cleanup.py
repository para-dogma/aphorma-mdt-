from sqlalchemy import text, delete
from sqlalchemy.orm import Session
from aphorma_mdt.storage.database import engine, SessionLocal
from aphorma_mdt.storage.models import MultidimensionalToken
import time

class CleanupService:
    def __init__(self):
        self.session = SessionLocal()
    
    def run_cleanup(self) -> dict:
        """Run cleanup of old/expired data"""
        current_time = int(time.time())
        
        # Clean up tokens that haven't been updated in a long time (optional)
        # For now, just count total tokens
        total_tokens = self.session.query(MultidimensionalToken).count()
        
        # Clean up old consensus events (if implemented)
        # This is a placeholder for future implementation
        
        return {
            "status": "completed",
            "tokens_count": total_tokens,
            "cleanup_time": current_time
        }
    
    def cleanup_old_tokens(self, days: int = 30) -> int:
        """Remove tokens not updated for specified days"""
        cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
        
        deleted = self.session.query(MultidimensionalToken).filter(
            MultidimensionalToken.last_updated < cutoff_time
        ).delete(synchronize_session=False)
        
        self.session.commit()
        return deleted
    
    def close(self):
        """Close session"""
        self.session.close()
