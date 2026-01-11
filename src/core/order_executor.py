"""
Order execution module.

This module handles order creation, submission, and execution tracking.
It serves as the interface between the strategy and the exchange.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid

from .enums import OrderType, OrderStatus, OrderSide


@dataclass
class Order:
    """
    Represents a single order.
    
    Orders are created by strategies and submitted to exchanges.
    This class tracks all order metadata and status.
    """
    
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    
    # Status tracking
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Execution info
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    
    # Stop/Limit parameters
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good-til-Cancelled
    
    # Exchange reference
    exchange_order_id: Optional[str] = None
    
    # Additional info
    position_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    child_orders: List[str] = field(default_factory=list)
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate order on creation."""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.price < 0:
            raise ValueError("Order price must be non-negative")
        if self.side not in [OrderSide.BUY, OrderSide.SELL]:
            raise ValueError("Side must be BUY or SELL")
    
    @classmethod
    def create(
        cls,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        position_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> 'Order':
        """
        Factory method to create a new order.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            order_type: MARKET, LIMIT, STOP, STOP_LIMIT
            quantity: Order size
            price: Limit price (required for LIMIT orders)
            stop_price: Stop trigger price (for STOP orders)
            time_in_force: GTC, IOC, FOK, GTD
            position_id: Associated position ID
            tags: Custom metadata
            
        Returns:
            New Order instance
        """
        order_id = str(uuid.uuid4())
        
        return cls(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            position_id=position_id,
            tags=tags or {},
        )
    
    @property
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.OPEN,
            OrderStatus.PARTIALLY_FILLED
        ]
    
    @property
    def is_closed(self) -> bool:
        """Check if order is closed."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]
    
    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.status == OrderStatus.PARTIALLY_FILLED
    
    @property
    def remaining_quantity(self) -> float:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage (0-100)."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100
    
    def update_fill(
        self,
        filled_qty: float,
        fill_price: float,
        commission: float = 0.0
    ) -> None:
        """
        Update order with fill information.
        
        Args:
            filled_qty: Quantity filled in this update
            fill_price: Price at which filled
            commission: Commission for this fill
        """
        if filled_qty < 0:
            raise ValueError("Filled quantity cannot be negative")
        
        total_filled = self.filled_quantity + filled_qty
        
        if total_filled > self.quantity:
            raise ValueError(
                f"Total filled ({total_filled}) exceeds order quantity ({self.quantity})"
            )
        
        # Update average fill price
        if self.filled_quantity > 0:
            # Weighted average
            self.average_fill_price = (
                (self.average_fill_price * self.filled_quantity + fill_price * filled_qty) /
                total_filled
            )
        else:
            self.average_fill_price = fill_price
        
        self.filled_quantity = total_filled
        self.commission += commission
        self.updated_at = datetime.now()
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def cancel(self) -> None:
        """Cancel the order."""
        if self.is_closed:
            raise ValueError(f"Cannot cancel {self.status} order")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def reject(self, reason: str = "") -> None:
        """
        Reject the order.
        
        Args:
            reason: Rejection reason
        """
        if self.is_closed:
            raise ValueError(f"Cannot reject {self.status} order")
        
        self.status = OrderStatus.REJECTED
        if reason:
            self.tags['rejection_reason'] = reason
        self.updated_at = datetime.now()
    
    def expire(self) -> None:
        """Mark order as expired."""
        if self.is_closed:
            raise ValueError(f"Cannot expire {self.status} order")
        
        self.status = OrderStatus.EXPIRED
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert order to dictionary for serialization."""
        return {
            'order_id': self.order_id,
            'exchange_order_id': self.exchange_order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'status': self.status.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'filled_quantity': self.filled_quantity,
            'average_fill_price': self.average_fill_price,
            'commission': self.commission,
            'time_in_force': self.time_in_force,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'position_id': self.position_id,
            'parent_order_id': self.parent_order_id,
            'child_orders': self.child_orders,
            'tags': self.tags,
        }


class OrderExecutor:
    """
    Handles order execution and tracking.
    
    The OrderExecutor manages all orders in the system, tracks their
    status, and provides utilities for order management.
    """
    
    def __init__(self):
        """Initialize the order executor."""
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        stop_price: Optional[float] = None,
        position_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Order:
        """
        Create a new order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            order_type: Order type
            quantity: Order quantity
            price: Limit price
            stop_price: Stop trigger price
            position_id: Associated position
            tags: Custom metadata
            
        Returns:
            Created Order
        """
        order = Order.create(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            position_id=position_id,
            tags=tags,
        )
        
        self.orders[order.order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get all open orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        orders = [o for o in self.orders.values() if o.is_open]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_position_orders(self, position_id: str) -> List[Order]:
        """
        Get all orders for a position.
        
        Args:
            position_id: Position ID
            
        Returns:
            List of orders for the position
        """
        return [o for o in self.orders.values() if o.position_id == position_id]
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order to cancel
            
        Returns:
            True if cancellation was successful
        """
        order = self.get_order(order_id)
        if not order:
            return False
        
        try:
            order.cancel()
            return True
        except ValueError:
            return False
    
    def close_order(self, order_id: str) -> None:
        """
        Archive a closed order to history.
        
        Args:
            order_id: Order to archive
        """
        order = self.orders.pop(order_id, None)
        if order:
            self.order_history.append(order)
    
    def get_order_stats(self, symbol: Optional[str] = None) -> dict:
        """
        Get order statistics.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            Dictionary with order statistics
        """
        orders = list(self.orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        all_orders = orders + self.order_history
        if symbol:
            all_orders = [o for o in all_orders if o.symbol == symbol]
        
        return {
            'total_orders': len(all_orders),
            'open_orders': len([o for o in orders if o.is_open]),
            'filled_orders': len([o for o in all_orders if o.is_filled]),
            'cancelled_orders': len([o for o in all_orders if o.status == OrderStatus.CANCELLED]),
            'rejected_orders': len([o for o in all_orders if o.status == OrderStatus.REJECTED]),
            'total_commission': sum(o.commission for o in all_orders),
            'avg_commission': (
                sum(o.commission for o in all_orders) / len(all_orders)
                if all_orders else 0.0
            ),
        }
