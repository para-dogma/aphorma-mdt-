from aphorma_mdt.consensus.consensus_service import consensus_window

class ConsensusValidator:
    def __init__(self):
        self.verification_threshold = 0.6
    
    def validate_action(self, agent_id: str, action: str, data: Dict) -> Dict:
        consensus_window.add_event(agent_id, action, data)
        consensus_state = consensus_window.get_consensus_for_agent(agent_id)
        if not consensus_state["is_consensus_valid"]:            return {
                "valid": False,
                "confidence": 0.0,
                "reason": f"Insufficient consensus: {consensus_state['event_count']}/{consensus_state['min_required']} events"
            }
        confidence = min(1.0, consensus_state["event_count"] / (consensus_state["min_required"] * 2))
        return {
            "valid": True,
            "confidence": confidence,
            "reason": f"Consensus achieved with {consensus_state['event_count']} events"
        }
    
    def get_validation_stats(self, agent_id: str) -> Dict:
        return consensus_window.get_consensus_for_agent(agent_id)

validator = ConsensusValidator()
