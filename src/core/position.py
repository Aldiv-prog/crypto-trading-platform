"""
Position management module.

This module handles position tracking and management for the trading system.
Positions represent open trades with associated metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from .enums import PositionStatus, OrderSide, TradeType


@dataclass
class Position:
    """
    Represents a trading position.
    
    A position is created when a trade is opened and closed when the trade exits.
    Tracks all relevant metrics including entry price, size, fees, and P&L.
    """
    
    position_id: str
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    opened_at: datetime
    status: PositionStatus = PositionStatus.OPEN
    
    # Exit information
    exit_price: Optional[float] = None
    closed_at: Optional[datetime] = None
    
    # Fees and costs
    entry_fee: float = 0.0
    exit_fee: float = 0.0
    
    # Orders associated with this position
    entry_order_ids: List[str] = field(default_factory=list)
    exit_order_ids: List[str] = field(default_factory=list)
    
    # Additional metadata
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    max_price: float = field(default=0.0)
    min_price: float = field(default=float('inf'))
    
    def __post_init__(self):
        """Validate position on creation."""
        if self.quantity <= 0:
            raise ValueError("Position quantity must be positive")
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.side not in [OrderSide.BUY, OrderSide.SELL]:
            raise ValueError("Side must be BUY or SELL")
        
        # Initialize max/min prices
        self.max_price = self.entry_price
        self.min_price = self.entry_price
    
    @property
    def entry_cost(self) -> float:
        """Total cost to enter position (including fees)."""
        return (self.entry_price * self.quantity) + self.entry_fee
    
    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.status == PositionStatus.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.status in [PositionStatus.CLOSED, PositionStatus.LIQUIDATED]
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L at current price.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized profit/loss in quote currency
        """
        if not self.is_open:
            return 0.0
        
        if self.side == OrderSide.BUY:
            pnl = (current_price - self.entry_price) * self.quantity
        else:  # SELL
            pnl = (self.entry_price - current_price) * self.quantity
        
        return pnl - self.entry_fee
    
    def get_unrealized_pnl_percent(self, current_price: float) -> float:
        """
        Calculate unrealized P&L percentage.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized P&L as percentage
        """
        if self.entry_cost == 0:
            return 0.0
        
        pnl = self.get_unrealized_pnl(current_price)
        return (pnl / self.entry_cost) * 100
    
    def get_realized_pnl(self) -> Optional[float]:
        """
        Calculate realized P&L if position is closed.
        
        Returns:
            Realized profit/loss or None if position is still open
        """
        if not self.is_closed or self.exit_price is None:
            return None
        
        if self.side == OrderSide.BUY:
            pnl = (self.exit_price - self.entry_price) * self.quantity
        else:  # SELL
            pnl = (self.entry_price - self.exit_price) * self.quantity
        
        return pnl - self.entry_fee - self.exit_fee
    
    def get_realized_pnl_percent(self) -> Optional[float]:
        """
        Calculate realized P&L percentage.
        
        Returns:
            Realized P&L as percentage or None if position is still open
        """
        if not self.is_closed:
            return None
        
        if self.entry_cost == 0:
            return 0.0
        
        pnl = self.get_realized_pnl()
        if pnl is None:
            return None
        
        return (pnl / self.entry_cost) * 100
    
    def update_price(self, current_price: float) -> None:
        """
        Update position with current price for high/low tracking.
        
        Args:
            current_price: Current market price
        """
        if self.is_open:
            self.max_price = max(self.max_price, current_price)
            self.min_price = min(self.min_price, current_price)
    
    def close_position(
        self,
        exit_price: float,
        closed_at: Optional[datetime] = None,
        exit_fee: float = 0.0
    ) -> None:
        """
        Close the position at specified price.
        
        Args:
            exit_price: Price at which position is closed
            closed_at: Timestamp of close (default: now)
            exit_fee: Fee for closing position
        """
        if not self.is_open:
            raise ValueError(f"Cannot close {self.status} position")
        
        self.exit_price = exit_price
        self.closed_at = closed_at or datetime.now()
        self.exit_fee = exit_fee
        self.status = PositionStatus.CLOSED
    
    def liquidate_position(self, exit_price: float, exit_fee: float = 0.0) -> None:
        """
        Liquidate the position (forced close).
        
        Args:
            exit_price: Price at which position is liquidated
            exit_fee: Fee for liquidation
        """
        if not self.is_open:
            raise ValueError(f"Cannot liquidate {self.status} position")
        
        self.exit_price = exit_price
        self.closed_at = datetime.now()
        self.exit_fee = exit_fee
        self.status = PositionStatus.LIQUIDATED
    
    def to_dict(self) -> dict:
        """Convert position to dictionary for serialization."""
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'status': self.status.value,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'entry_fee': self.entry_fee,
            'exit_fee': self.exit_fee,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'max_price': self.max_price,
            'min_price': self.min_price,
            'entry_order_ids': self.entry_order_ids,
            'exit_order_ids': self.exit_order_ids,
            'unrealized_pnl': self.get_unrealized_pnl(self.exit_price) if self.exit_price else None,
            'realized_pnl': self.get_realized_pnl(),
            'realized_pnl_percent': self.get_realized_pnl_percent(),
        }


@dataclass
class PositionMetrics:
    """Metrics for a collection of positions."""
    
    total_positions: int = 0
    open_positions: int = 0
    closed_positions: int = 0
    total_entry_cost: float = 0.0
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_fees: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    avg_winning_trade: float = 0.0
    avg_losing_trade: float = 0.0
    profit_factor: float = 0.0
    
    @classmethod
    def calculate(cls, positions: List[Position]) -> 'PositionMetrics':
        """
        Calculate metrics from a list of positions.
        
        Args:
            positions: List of Position objects
            
        Returns:
            PositionMetrics object with calculated values
        """
        metrics = cls()
        metrics.total_positions = len(positions)
        
        total_gross_profit = 0.0
        total_gross_loss = 0.0
        
        for position in positions:
            if position.is_open:
                metrics.open_positions += 1
            else:
                metrics.closed_positions += 1
                pnl = position.get_realized_pnl()
                
                if pnl is not None:
                    metrics.total_realized_pnl += pnl
                    
                    if pnl > 0:
                        metrics.win_count += 1
                        total_gross_profit += pnl
                        metrics.avg_winning_trade += pnl
                    elif pnl < 0:
                        metrics.loss_count += 1
                        total_gross_loss += abs(pnl)
                        metrics.avg_losing_trade += pnl
            
            metrics.total_entry_cost += position.entry_cost
            metrics.total_fees += position.entry_fee + position.exit_fee
        
        # Calculate averages
        if metrics.win_count > 0:
            metrics.avg_winning_trade /= metrics.win_count
        if metrics.loss_count > 0:
            metrics.avg_losing_trade /= metrics.loss_count
        
        # Calculate win rate
        total_closed = metrics.win_count + metrics.loss_count
        if total_closed > 0:
            metrics.win_rate = (metrics.win_count / total_closed) * 100
        
        # Calculate profit factor
        if total_gross_loss > 0:
            metrics.profit_factor = total_gross_profit / total_gross_loss
        elif total_gross_profit > 0:
            metrics.profit_factor = float('inf')
        
        return metrics
