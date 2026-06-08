"""Sentinel Edge Consensus Module"""
from typing import Dict, List
from dataclasses import dataclass
import time
import numpy as np

@dataclass
class EdgeConsensusResult:
    agent_id: str
    valid: bool
    confidence: float
    validators_count: int
    edge_nodes: List[str]
    timestamp: int

class SentinelNode:
    def __init__(self):        self.node_id = "sentinel-001"
        self.edge_nodes = []
        self.consensus_threshold = 0.67
        self.min_validators = 2
        self.total_validations = 0
    
    def register_edge_node(self, node_id: str, location: str, capabilities: List[str]):
        self.edge_nodes.append({
            "id": node_id,
            "location": location,
            "capabilities": capabilities,
            "last_heartbeat": int(time.time()),
            "reputation": 1.0
        })
    
    def validate_presence(self, agent_id: str, wifi_data: Dict) -> EdgeConsensusResult:
        local_score = wifi_data.get("confidence", 0.5)
        edge_validations = [
            {"node_id": n["id"], "score": local_score * n["reputation"]}
            for n in self.edge_nodes
            if int(time.time()) - n["last_heartbeat"] < 60
        ]
        all_scores = [local_score] + [v["score"] for v in edge_validations]
        consensus_score = np.mean(all_scores)
        valid = consensus_score >= self.consensus_threshold and len(all_scores) >= self.min_validators
        self.total_validations += 1
        return EdgeConsensusResult(
            agent_id=agent_id,
            valid=valid,
            confidence=consensus_score,
            validators_count=len(all_scores),
            edge_nodes=[self.node_id] + [v["node_id"] for v in edge_validations],
            timestamp=int(time.time())
        )
    
    def compute_edge_health_factor(self, agent_id: str, wifi_data: Dict) -> float:
        consensus = self.validate_presence(agent_id, wifi_data)
        if not consensus.valid:
            return 0.0
        validator_bonus = min(0.2, consensus.validators_count * 0.05)
        return max(0.0, min(1.0, consensus.confidence + validator_bonus))
    
    def get_edge_stats(self) -> Dict:
        active_nodes = [n for n in self.edge_nodes if int(time.time()) - n["last_heartbeat"] < 60]
        return {
            "node_id": self.node_id,
            "total_nodes": len(self.edge_nodes),
            "active_nodes": len(active_nodes),
            "consensus_threshold": self.consensus_threshold,
            "total_validations": self.total_validations        }

sentinel_node = SentinelNode()
