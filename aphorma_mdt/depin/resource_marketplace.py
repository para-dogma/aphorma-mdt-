"""Resource Marketplace for DePIN supply/demand coordination"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    SENSOR = "sensor"
    WIFI_SENSING = "wifi_sensing"

class OrderStatus(Enum):
    OPEN = "open"
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class SupplyOrder:
    order_id: str
    node_id: str
    resource_type: ResourceType
    amount: float
    price_per_unit: float
    available_from: int
    available_until: int
    status: OrderStatus = OrderStatus.OPEN
    location: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)

@dataclass
class DemandOrder:
    order_id: str
    requester_id: str
    resource_type: ResourceType
    amount: float
    max_price: float
    required_from: int
    required_until: int
    status: OrderStatus = OrderStatus.OPEN    location: Optional[str] = None
    min_trust_score: float = 0.5

@dataclass
class MatchResult:
    match_id: str
    supply_order: SupplyOrder
    demand_order: DemandOrder
    matched_amount: float
    agreed_price: float
    timestamp: int
    sla_terms: Dict

class ResourceMarketplace:
    def __init__(self):
        self.supply_orders: Dict[str, SupplyOrder] = {}
        self.demand_orders: Dict[str, DemandOrder] = {}
        self.matches: Dict[str, MatchResult] = {}
        self.order_expiry_hours = 24
    
    def create_supply_order(self, node_id: str, resource_type: ResourceType,
                           amount: float, price_per_unit: float,
                           duration_hours: int = 24,
                           location: Optional[str] = None,
                           capabilities: List[str] = None) -> SupplyOrder:
        """Create a supply order from a node"""
        order_id = hashlib.sha256(
            f"{node_id}:{resource_type.value}:{int(datetime.utcnow().timestamp())}".encode()
        ).hexdigest()[:16]
        
        now = int(datetime.utcnow().timestamp())
        order = SupplyOrder(
            order_id=order_id,
            node_id=node_id,
            resource_type=resource_type,
            amount=amount,
            price_per_unit=price_per_unit,
            available_from=now,
            available_until=now + (duration_hours * 3600),
            location=location,
            capabilities=capabilities or []
        )
        
        self.supply_orders[order_id] = order
        return order
    
    def create_demand_order(self, requester_id: str, resource_type: ResourceType,
                           amount: float, max_price: float,
                           duration_hours: int = 24,
                           location: Optional[str] = None,                           min_trust_score: float = 0.5) -> DemandOrder:
        """Create a demand order from a requester"""
        order_id = hashlib.sha256(
            f"{requester_id}:{resource_type.value}:{int(datetime.utcnow().timestamp())}".encode()
        ).hexdigest()[:16]
        
        now = int(datetime.utcnow().timestamp())
        order = DemandOrder(
            order_id=order_id,
            requester_id=requester_id,
            resource_type=resource_type,
            amount=amount,
            max_price=max_price,
            required_from=now,
            required_until=now + (duration_hours * 3600),
            location=location,
            min_trust_score=min_trust_score
        )
        
        self.demand_orders[order_id] = order
        return order
    
    def find_matches(self, demand_order_id: str) -> List[MatchResult]:
        """Find matching supply orders for a demand order"""
        if demand_order_id not in self.demand_orders:
            return []
        
        demand = self.demand_orders[demand_order_id]
        if demand.status != OrderStatus.OPEN:
            return []
        
        matches = []
        
        for supply in self.supply_orders.values():
            if supply.status != OrderStatus.OPEN:
                continue
            
            # Check resource type match
            if supply.resource_type != demand.resource_type:
                continue
            
            # Check price compatibility
            if supply.price_per_unit > demand.max_price:
                continue
            
            # Check time overlap
            if supply.available_until < demand.required_from:
                continue
            if supply.available_from > demand.required_until:
                continue            
            # Check location (if specified)
            if demand.location and supply.location:
                if demand.location != supply.location:
                    continue
            
            # Calculate matched amount
            matched_amount = min(supply.amount, demand.amount)
            
            # Calculate agreed price (midpoint)
            agreed_price = (supply.price_per_unit + demand.max_price) / 2
            
            # Create match
            match_id = hashlib.sha256(
                f"{supply.order_id}:{demand.order_id}".encode()
            ).hexdigest()[:16]
            
            match = MatchResult(
                match_id=match_id,
                supply_order=supply,
                demand_order=demand,
                matched_amount=matched_amount,
                agreed_price=agreed_price,
                timestamp=int(datetime.utcnow().timestamp()),
                sla_terms={
                    'resource_type': supply.resource_type.value,
                    'amount': matched_amount,
                    'price': agreed_price,
                    'duration_hours': min(
                        (supply.available_until - supply.available_from) / 3600,
                        (demand.required_until - demand.required_from) / 3600
                    )
                }
            )
            
            matches.append(match)
            
            # Update order statuses
            supply.status = OrderStatus.MATCHED
            supply.amount -= matched_amount
            if supply.amount <= 0:
                supply.status = OrderStatus.COMPLETED
            
            demand.amount -= matched_amount
            if demand.amount <= 0:
                demand.status = OrderStatus.MATCHED
            
            self.matches[match_id] = match
        
        return matches    
    def complete_match(self, match_id: str, actual_delivery: float) -> bool:
        """Mark a match as completed with actual delivery amount"""
        if match_id not in self.matches:
            return False
        
        match = self.matches[match_id]
        
        # Calculate payment based on actual delivery
        payment = actual_delivery * match.agreed_price
        
        # Update statuses
        match.supply_order.status = OrderStatus.COMPLETED
        match.demand_order.status = OrderStatus.COMPLETED
        
        return True
    
    def cancel_order(self, order_id: str, is_supply: bool = True) -> bool:
        """Cancel an order"""
        if is_supply:
            if order_id in self.supply_orders:
                self.supply_orders[order_id].status = OrderStatus.CANCELLED
                return True
        else:
            if order_id in self.demand_orders:
                self.demand_orders[order_id].status = OrderStatus.CANCELLED
                return True
        return False
    
    def get_market_stats(self, resource_type: Optional[ResourceType] = None) -> Dict:
        """Get marketplace statistics"""
        supply_orders = list(self.supply_orders.values())
        demand_orders = list(self.demand_orders.values())
        
        if resource_type:
            supply_orders = [s for s in supply_orders if s.resource_type == resource_type]
            demand_orders = [d for d in demand_orders if d.resource_type == resource_type]
        
        open_supply = sum(1 for s in supply_orders if s.status == OrderStatus.OPEN)
        open_demand = sum(1 for d in demand_orders if d.status == OrderStatus.OPEN)
        total_matches = len(self.matches)
        
        avg_price = 0
        if self.matches:
            avg_price = sum(m.agreed_price for m in self.matches.values()) / len(self.matches)
        
        return {
            'open_supply_orders': open_supply,
            'open_demand_orders': open_demand,
            'total_matches': total_matches,            'average_price': avg_price,
            'total_supply_amount': sum(s.amount for s in supply_orders),
            'total_demand_amount': sum(d.amount for d in demand_orders)
        }

resource_marketplace = ResourceMarketplace()
