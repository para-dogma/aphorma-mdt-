import time
import threading
from sqlalchemy import text
from aphorma_mdt.config.settings import settings
from aphorma_mdt.storage.database import engine

class CleanupService:
    def __init__(self, cleanup_interval_hours: int = 24):
        self.interval = cleanup_interval_hours * 3600
        self.running = False
        self.thread = None
    
    def cleanup_old_tokens(self, days: int = 30) -> int:
        """Remove inactive tokens older than N days"""
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
            return result.rowcount
    
    def cleanup_expired_consensus(self) -> int:
        """Mark tokens with expired consensus as inactive"""
        now = int(time.time())
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    UPDATE multidimensional_tokens 
                    SET is_active = 0 
                    WHERE consensus_window_end < :now AND is_active = 1
                """),
                {"now": now}            )
            conn.commit()
            return result.rowcount
    
    def run_cleanup(self):
        """Run all cleanup tasks"""
        print("🧹 Running cleanup...")
        old_deleted = self.cleanup_old_tokens(days=30)
        expired_marked = self.cleanup_expired_consensus()
        print(f"✅ Cleanup done: {old_deleted} deleted, {expired_marked} marked inactive")
    
    def start_background_cleanup(self):
        """Start background cleanup thread"""
        self.running = True
        
        def cleanup_loop():
            while self.running:
                try:
                    self.run_cleanup()
                except Exception as e:
                    print(f"❌ Cleanup error: {e}")
                time.sleep(self.interval)
        
        self.thread = threading.Thread(target=cleanup_loop, daemon=True)
        self.thread.start()
        print(f"🔄 Background cleanup started (every {self.interval}s)")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
