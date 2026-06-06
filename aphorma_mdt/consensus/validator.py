from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valid: bool
    confidence: float
    reason: str
    validators_count: int = 0

class ConsensusValidator:
    def __init__(self, required_validators: int = 2):
        self.required_validators = required_validators
        self.validators: Dict[str, Dict] = {}
    
    def register_validator(self, validator_id: str, weight: float = 1.0):
        self.validators[validator_id] = {"weight": weight, "active": True}
    
    def validate_action(self, agent_id: str, action: str, context: Dict) -> Dict:
        active_validators = [v for v in self.validators.values() if v["active"]]
        
        if len(active_validators) < self.required_validators:
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": "Insufficient validators",
                "validators_count": len(active_validators)
            }
        
        allowed_actions = ["mint", "transfer", "stake", "unstake"]
        if action not in allowed_actions:
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": f"Action {action} not allowed",
                "validators_count": len(active_validators)
            }
        
        confidence = min(1.0, len(active_validators) / self.required_validators)
        
        return {
            "valid": True,
            "confidence": confidence,
            "reason": "Validated by consensus",
            "validators_count": len(active_validators)
        }

validator = ConsensusValidator(required_validators=2)
validator.register_validator("validator-1", weight=1.0)
validator.register_validator("validator-2", weight=1.0)
