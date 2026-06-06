import time
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ConsensusEvent:
    agent_id: str
    action: str
    timestamp: int
    data: Dict
    validator_id: Optional[str] = None

class ConsensusWindow:
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.events: Dict[str, List[ConsensusEvent]] = {}
    
    def add_event(self, agent_id: str, action: str, data: Dict = None, validator_id: str = None):
        event = ConsensusEvent(
            agent_id=agent_id,
            action=action,
            timestamp=int(time.time()),
            data=data or {},
            validator_id=validator_id
        )
        
        if agent_id not in self.events:
            self.events[agent_id] = []
        
        self.events[agent_id].append(event)
        self._cleanup_old_events(agent_id)
    
    def _cleanup_old_events(self, agent_id: str):
        if agent_id not in self.events:
            return
        
        current_time = int(time.time())
        cutoff = current_time - self.window_seconds
        
        self.events[agent_id] = [            e for e in self.events[agent_id]
            if e.timestamp >= cutoff
        ]
    
    def get_events_in_window(self, agent_id: str) -> List[ConsensusEvent]:
        self._cleanup_old_events(agent_id)
        return self.events.get(agent_id, [])
    
    def get_consensus_for_agent(self, agent_id: str) -> Dict:
        events = self.get_events_in_window(agent_id)
        current_time = int(time.time())
        
        return {
            "agent_id": agent_id,
            "window_start": current_time - self.window_seconds if events else 0,
            "window_end": current_time + self.window_seconds if events else 0,
            "events_count": len(events),
            "events": [
                {
                    "action": e.action,
                    "timestamp": e.timestamp,
                    "validator": e.validator_id
                }
                for e in events
            ],
            "is_valid": len(events) > 0
        }
    
    def get_stats(self) -> Dict:
        total_agents = len(self.events)
        total_events = sum(len(events) for events in self.events.values())
        
        return {
            "total_agents": total_agents,
            "total_events": total_events,
            "window_seconds": self.window_seconds
        }
