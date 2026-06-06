from typing import Dict, List, Optional, Any

class PolicyEngine:
    def __init__(self):
        self.policies = {}
        self.active_policy = "default"
        self._init_defaults()
    
    def _init_defaults(self):
        self.policies["default"] = {
            "name": "Default",
            "rules": {
                "mint": {"max_amount": 10000},
                "transfer": {"max_amount": 1000}
            }
        }
        self.policies["strict"] = {
            "name": "Strict",
            "rules": {
                "mint": {"max_amount": 1000},
                "transfer": {"max_amount": 100}
            }
        }
    
    def check_permission(self, action: str, **kwargs) -> Dict[str, Any]:
        policy = self.policies.get(self.active_policy)
        if not policy:
            return {"allowed": False, "reason": "No policy"}
        rules = policy.get("rules", {})
        action_rules = rules.get(action, {})
        if not action_rules:
            return {"allowed": True, "reason": "OK"}
        for rule, value in action_rules.items():
            if rule in kwargs and kwargs[rule] > value:
                return {"allowed": False, "reason": f"{rule} > {value}"}
        return {"allowed": True, "reason": "OK"}
    
    def list_policies(self) -> List[str]:
        return list(self.policies.keys())
