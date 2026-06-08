from typing import Dict, List, Optional
from dataclasses import dataclass
import time

@dataclass
class ConsensusEvent:
    agent_id: str
    action: str
    timestamp: int
    data: Dict
    validator_id: Optional[str] = None

class ConsensusWindow:
    def __init__(self, window_seconds: int = 30, min_events: int = 1):
        self.window_seconds = window_seconds
        self.min_events = min_events
        self.events: Dict[str, List[ConsensusEvent]] = {}
    
    def add_event(self, agent_id: str, action: str, data: Dict = None, validator_id: str = None):
        event = ConsensusEvent(
            agent_id=agent_id,
            action=action,
            timestamp=int(time.time()),
            data=data or {},
            validator_id=validator_id
        )
<<<<<<< HEAD
        if agent_id not in self.events:
            self.events[agent_id] = []
=======
        
        if agent_id not in self.events:
            self.events[agent_id] = []
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        self.events[agent_id].append(event)
        self._cleanup_old_events(agent_id)
    
    def _cleanup_old_events(self, agent_id: str):
        if agent_id not in self.events:
            return
<<<<<<< HEAD
        current_time = int(time.time())
        cutoff = current_time - self.window_seconds
        self.events[agent_id] = [e for e in self.events[agent_id] if e.timestamp >= cutoff]
=======
        
        current_time = int(time.time())
        cutoff = current_time - self.window_seconds
        
        self.events[agent_id] = [
            e for e in self.events[agent_id]
            if e.timestamp >= cutoff
        ]
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
    
    def get_events_in_window(self, agent_id: str) -> List[ConsensusEvent]:
        self._cleanup_old_events(agent_id)
        return self.events.get(agent_id, [])
<<<<<<< HEAD
    
    def is_valid(self, agent_id: str) -> bool:
        events = self.get_events_in_window(agent_id)
        event_count = len(events)
        if not events:
            return False
        now = int(time.time())
        last_event_time = max(e.timestamp for e in events)
=======
        def is_valid(self, agent_id: str) -> bool:
        events = self.get_events_in_window(agent_id)
        event_count = len(events)
        
        if not events:
            return False
        
        now = int(time.time())
        last_event_time = max(e.timestamp for e in events)
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        is_valid = event_count >= self.min_events and (now - last_event_time) < self.window_seconds
        return is_valid
    
    def get_consensus_for_agent(self, agent_id: str) -> Dict:
        events = self.get_events_in_window(agent_id)
        current_time = int(time.time())
<<<<<<< HEAD
=======
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        result = {
            "agent_id": agent_id,
            "window_start": current_time - self.window_seconds if events else 0,
            "window_end": current_time + self.window_seconds if events else 0,
            "events_count": len(events),
            "events": [],
            "is_valid": self.is_valid(agent_id)
        }
<<<<<<< HEAD
=======
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        for e in events:
            result["events"].append({
                "action": e.action,
                "timestamp": e.timestamp,
                "validator": e.validator_id
            })
<<<<<<< HEAD
=======
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        return result
    
    def get_stats(self) -> Dict:
        total_agents = len(self.events)
        total_events = sum(len(events) for events in self.events.values())
<<<<<<< HEAD
=======
        
>>>>>>> 66c446d (feat: add WiFi Sensing, Edge Consensus, Blockchain modules)
        return {
            "total_agents": total_agents,
            "total_events": total_events,
            "window_seconds": self.window_seconds,
            "min_events": self.min_events
        }

consensus_window = ConsensusWindow()
