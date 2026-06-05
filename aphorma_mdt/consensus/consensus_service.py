import time
from typing import Dict
from collections import deque

class ConsensusEvent:
    def __init__(self, timestamp: int, agent_id: str, event_type: str, data: Dict):
        self.timestamp = timestamp
        self.agent_id = agent_id
        self.event_type = event_type
        self.data = data

class ConsensusWindow:
    def __init__(self, window_seconds: int = 30, min_events: int = 3):
        self.window_seconds = window_seconds
        self.min_events = min_events
        self.events = deque()
        self.agent_events = {}
    
    def add_event(self, agent_id: str, event_type: str, data: Dict) -> bool:
        now = int(time.time())
        event = ConsensusEvent(timestamp=now, agent_id=agent_id, event_type=event_type, data=data)
        self.events.append(event)
        if agent_id not in self.agent_events:
            self.agent_events[agent_id] = deque()
        self.agent_events[agent_id].append(event)
        self._cleanup_old_events()
        return True
    
    def _cleanup_old_events(self):
        now = int(time.time())
        cutoff = now - self.window_seconds
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()
        for agent_id in list(self.agent_events.keys()):
            while self.agent_events[agent_id] and self.agent_events[agent_id][0].timestamp < cutoff:
                self.agent_events[agent_id].popleft()
            if not self.agent_events[agent_id]:
                del self.agent_events[agent_id]
    
    def get_consensus_for_agent(self, agent_id: str) -> Dict:
        now = int(time.time())
        events = self.agent_events.get(agent_id, deque())
        event_count = len(events)
        last_event_time = events[-1].timestamp if events else 0
        is_valid = event_count >= self.min_events and (now - last_event_time) < self.window_seconds        return {
            "agent_id": agent_id,
            "is_consensus_valid": is_valid,
            "event_count": event_count,
            "min_required": self.min_events,
            "window_seconds": self.window_seconds,
            "last_event_timestamp": last_event_time,
            "current_time": now
        }
    
    def adjust_window_size(self, total_agents: int):
        if total_agents < 10:
            self.window_seconds = 30
            self.min_events = 3
        elif total_agents < 100:
            self.window_seconds = 60
            self.min_events = 5
        else:
            self.window_seconds = 120
            self.min_events = 10
    
    def get_stats(self) -> Dict:
        return {
            "total_events": len(self.events),
            "active_agents": len(self.agent_events),
            "window_seconds": self.window_seconds,
            "min_events_required": self.min_events
        }

consensus_window = ConsensusWindow()
