import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from aphorma_mdt.config.settings import settings

@dataclass
class PolicyConfig:
    """Policy configuration"""
    name: str
    version: str
    rules: Dict[str, Any]

class PolicyEngine:
    """
    Policy Engine v1.0
    
    Allows configuration of MDT behavior via YAML files
    without code changes.
    """
    
    def __init__(self, policy_dir: str = "./policies"):
        self.policy_dir = policy_dir
        self.policies: Dict[str, PolicyConfig] = {}
        self.active_policy: Optional[str] = None
        
        # Create policies directory
        os.makedirs(policy_dir, exist_ok=True)
        
        # Load default policies
        self._create_default_policies()
        self.load_policies()
    
    def _create_default_policies(self):
        """Create default policy files"""
        
        # Default policy (permissive)
        default_policy = {
            "name": "default",
            "version": "1.0",
            "rules": {
                "mint": {
                    "enabled": True,
                    "max_amount": 10000,
                    "require_approval": False
                },
                "transfer": {
                    "enabled": True,                    "max_amount": 1000,
                    "require_consensus": True
                },
                "stake": {
                    "enabled": True,
                    "min_amount": 100,
                    "lock_period_seconds": 86400
                },
                "health": {
                    "min_health_factor": 0.5,
                    "grace_period_seconds": 300
                },
                "consensus": {
                    "window_seconds": 30,
                    "require_valid": True
                }
            }
        }
        
        # Strict policy (conservative)
        strict_policy = {
            "name": "strict",
            "version": "1.0",
            "rules": {
                "mint": {
                    "enabled": True,
                    "max_amount": 1000,
                    "require_approval": True
                },
                "transfer": {
                    "enabled": True,
                    "max_amount": 100,
                    "require_consensus": True
                },
                "stake": {
                    "enabled": True,
                    "min_amount": 500,
                    "lock_period_seconds": 604800
                },
                "health": {
                    "min_health_factor": 0.8,
                    "grace_period_seconds": 60
                },
                "consensus": {
                    "window_seconds": 10,
                    "require_valid": True
                }
            }
        }
                # Permissive policy (open)
        permissive_policy = {
            "name": "permissive",
            "version": "1.0",
            "rules": {
                "mint": {
                    "enabled": True,
                    "max_amount": 100000,
                    "require_approval": False
                },
                "transfer": {
                    "enabled": True,
                    "max_amount": 10000,
                    "require_consensus": False
                },
                "stake": {
                    "enabled": True,
                    "min_amount": 10,
                    "lock_period_seconds": 3600
                },
                "health": {
                    "min_health_factor": 0.1,
                    "grace_period_seconds": 600
                },
                "consensus": {
                    "window_seconds": 60,
                    "require_valid": False
                }
            }
        }
        
        # Save policies
        self._save_policy("default.yaml", default_policy)
        self._save_policy("strict.yaml", strict_policy)
        self._save_policy("permissive.yaml", permissive_policy)
    
    def _save_policy(self, filename: str, policy: Dict):
        """Save policy to file"""
        filepath = os.path.join(self.policy_dir, filename)
        with open(filepath, 'w') as f:
            yaml.dump(policy, f, default_flow_style=False)
    
    def load_policies(self):
        """Load all policies from directory"""
        for filename in os.listdir(self.policy_dir):
            if filename.endswith('.yaml'):
                filepath = os.path.join(self.policy_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        policy_data = yaml.safe_load(f)                        policy = PolicyConfig(
                            name=policy_data['name'],
                            version=policy_data['version'],
                            rules=policy_data['rules']
                        )
                        self.policies[policy.name] = policy
                        print(f"✅ Loaded policy: {policy.name} v{policy.version}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
        
        # Set default as active
        if 'default' in self.policies:
            self.active_policy = 'default'
    
    def get_rule(self, rule_path: str) -> Any:
        """
        Get rule value from active policy
        
        Example: get_rule("mint.max_amount")
        """
        if not self.active_policy or self.active_policy not in self.policies:
            return None
        
        policy = self.policies[self.active_policy]
        keys = rule_path.split('.')
        value = policy.rules
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def check_permission(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Check if action is allowed by policy
        
        Returns: {"allowed": bool, "reason": str}
        """
        if not self.active_policy:
            return {"allowed": False, "reason": "No active policy"}
        
        # Check mint
        if action == "mint":
            if not self.get_rule("mint.enabled"):
                return {"allowed": False, "reason": "Minting disabled"}
            
            max_amount = self.get_rule("mint.max_amount")            amount = kwargs.get("amount", 0)
            
            if amount > max_amount:
                return {"allowed": False, "reason": f"Amount {amount} exceeds max {max_amount}"}
            
            return {"allowed": True, "reason": "OK"}
        
        # Check transfer
        elif action == "transfer":
            if not self.get_rule("transfer.enabled"):
                return {"allowed": False, "reason": "Transfers disabled"}
            
            max_amount = self.get_rule("transfer.max_amount")
            amount = kwargs.get("amount", 0)
            
            if amount > max_amount:
                return {"allowed": False, "reason": f"Amount {amount} exceeds max {max_amount}"}
            
            return {"allowed": True, "reason": "OK"}
        
        # Check stake
        elif action == "stake":
            if not self.get_rule("stake.enabled"):
                return {"allowed": False, "reason": "Staking disabled"}
            
            min_amount = self.get_rule("stake.min_amount")
            amount = kwargs.get("amount", 0)
            
            if amount < min_amount:
                return {"allowed": False, "reason": f"Amount {amount} below min {min_amount}"}
            
            return {"allowed": True, "reason": "OK"}
        
        return {"allowed": False, "reason": f"Unknown action: {action}"}
    
    def activate_policy(self, policy_name: str) -> bool:
        """Activate a policy"""
        if policy_name in self.policies:
            self.active_policy = policy_name
            print(f"✅ Activated policy: {policy_name}")
            return True
        else:
            print(f"❌ Policy not found: {policy_name}")
            return False
    
    def get_active_policy_info(self) -> Optional[Dict]:
        """Get info about active policy"""
        if not self.active_policy:
            return None
                policy = self.policies[self.active_policy]
        return {
            "name": policy.name,
            "version": policy.version,
            "rules": policy.rules
        }
