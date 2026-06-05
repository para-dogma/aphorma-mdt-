import time
from typing import Dict, List
from aphorma_mdt.consensus.consensus_service import consensus_window

class ConsensusValidator:
    """
    Validates agent actions based on consensus
    
    Features:
    - Multi-agent verification
    - Reputation-weighted consensus
    - Time-based validation
    """
    
    def __init__(self):
        self.verification_threshold = 0.6  # 60% agreement
    
    def validate_action(self, agent_id: str, action: str, data: Dict) -> Dict:
        """
        Validate if action should be allowed
                Returns: {"valid": bool, "confidence": float, "reason": str}
        """
        # Add event to consensus window
        consensus_window.add_event(agent_id, action, data)
        
        # Get consensus state
        consensus_state = consensus_window.get_consensus_for_agent(agent_id)
        
        if not consensus_state["is_consensus_valid"]:
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": f"Insufficient consensus: {consensus_state['event_count']}/{consensus_state['min_required']} events"
            }
        
        # Calculate confidence based on event density
        confidence = min(1.0, consensus_state["event_count"] / (consensus_state["min_required"] * 2))
        
        return {
            "valid": True,
            "confidence": confidence,
            "reason": f"Consensus achieved with {consensus_state['event_count']} events"
        }
    
    def get_validation_stats(self, agent_id: str) -> Dict:
        """Get validation statistics for agent"""
        return consensus_window.get_consensus_for_agent(agent_id)

# Global validator
validator = ConsensusValidator()
