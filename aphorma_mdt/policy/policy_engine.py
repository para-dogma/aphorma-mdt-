import yaml
import os
from typing import Dict, Any, Optional

class PolicyEngine:
    def __init__(self, policy_dir="./policies"):
        self.policy_dir = policy_dir
        self.policies = {}
        self.active_policy = None
        os.makedirs(policy_dir, exist_ok=True)
        self._create_default_policies()
        self.load_policies()
    
    def _create_default_policies(self):
        default = {
            "name": "default",
            "version": "1.0",
            "rules": {
                "mint": {"enabled": True, "max_amount": 10000},
                "transfer": {"enabled": True, "max_amount": 1000},
                "stake": {"enabled": True, "min_amount": 100}
            }
        }
        strict = {
            "name": "strict",
            "version": "1.0",
            "rules": {
                "mint": {"enabled": True, "max_amount": 1000},
                "transfer": {"enabled": True, "max_amount": 100},
                "stake": {"enabled": True, "min_amount": 500}
            }
        }
        self._save_policy("default.yaml", default)
        self._save_policy("strict.yaml", strict)
    
    def _save_policy(self, filename, policy):
        filepath = os.path.join(self.policy_dir, filename)
        with open(filepath, "w") as f:
            yaml.dump(policy, f)
    
    def load_policies(self):
        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".yaml"):
                filepath = os.path.join(self.policy_dir, filename)
                with open(filepath, "r") as f:
                    data = yaml.safe_load(f)
                    self.policies[data["name"]] = data
        if "default" in self.policies:
            self.active_policy = "default"
    
    def check_permission(self, action, **kwargs):
        if not self.active_policy:
            return {"allowed": False, "reason": "No policy"}
        policy = self.policies[self.active_policy]
        rules = policy.get("rules", {})
        
        if action == "mint":
            rule = rules.get("mint", {})
            if not rule.get("enabled", False):
                return {"allowed": False, "reason": "Mint disabled"}
            max_amt = rule.get("max_amount", 0)
            amount = kwargs.get("amount", 0)
            if amount > max_amt:
                return {"allowed": False, "reason": f"Exceeds max {max_amt}"}
            return {"allowed": True, "reason": "OK"}
        
        return {"allowed": True, "reason": "OK"}
    
    def activate_policy(self, name):
        if name in self.policies:
            self.active_policy = name
            return True
        return False
    
    def get_active_policy_info(self):
        if not self.active_policy:
            return None
        return self.policies[self.active_policy]
