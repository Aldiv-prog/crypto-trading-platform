"""
Data models for market data, orders, positions, and trades.

Provides strongly-typed models for all entities in the trading system.

UPDATED: Compatible with backtest_engine_fixed.py
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from src.core.enums import TradeType, OrderStatus, OrderType, SignalType
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict, validator


# ============================================================================
# MARKET DATA MODELS
# ============================================================================

@dataclass
class Candle:
    """
    Represents a single candlestick in OHLCV format.
    
    Attributes:
        timestamp: Unix timestamp (seconds) of candle open
        open: Opening price
        high: Highest price during period
        low: Lowest price during period
        close: Closing price
        volume: Trading volume in base asset
        quote_asset_volume: Trading volume in quote asset (optional)
    """
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_asset_volume: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate candle data."""
        if not (self.low <= self.close <= self.high and
                self.low <= self.open <= self.high):
            raise ValueError(f"Invalid candle data: L={self.low}, O={self.open}, C={self.close}, H={self.high}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'quote_asset_volume': self.quote_asset_volume,
        }


@dataclass
class MarketData:
    """
    Container for market data (candles) for a symbol.
    
    Attributes:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        candles: List of Candle objects, ordered by timestamp (ascending)
        timeframe: Timeframe of candles (e.g., '1h')
    """
    symbol: str
    candles: List[Candle]
    timeframe: str

    def __post_init__(self) -> None:
        """Validate that candles are sorted by timestamp."""
        if self.candles:
            timestamps = [c.timestamp for c in self.candles]
            if timestamps != sorted(timestamps):
                raise ValueError("Candles must be sorted by timestamp (ascending)")

    @property
    def latest_candle(self) -> Optional[Candle]:
        """Get the most recent candle."""
        return self.candles[-1] if self.candles else None

    @property
    def latest_close(self) -> Optional[float]:
        """Get the latest close price."""
        candle = self.latest_candle
        return candle.close if candle else None

    def get_last_n_candles(self, n: int) -> List[Candle]:
        """Get last N candles."""
        return self.candles[-n:] if n > 0 else []

    def calculate_volatility(self, period: int = 20) -> float:
        """
        Calculate rolling volatility (standard deviation of returns).
        
        Args:
            period: Number of candles to use for calculation
        
        Returns:
            Volatility as percentage
        """
        candles = self.get_last_n_candles(period + 1)
        if len(candles) < 2:
            return 0.0

        # Calculate returns
        returns = []
        for i in range(1, len(candles)):
            ret = (candles[i].close - candles[i-1].close) / candles[i-1].close
            returns.append(ret)

        # Calculate standard deviation
        if not returns:
            return 0.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * 100

        return volatility


@dataclass
class MarketTicker(BaseModel):
    """Market ticker information"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float = 0.0


# ============================================================================
# ORDER MODELS
# ============================================================================

@dataclass
class Order:
    """
    Represents a single order placed in the system.
    
    Attributes:
        order_id: Unique identifier for the order
        symbol: Trading pair symbol
        trade_type: LONG or SHORT
        order_type: LIMIT or MARKET
        quantity: Amount to trade
        price: Price for limit orders (None for market)
        status: Current order status
        created_at: Timestamp when order was created
        filled_quantity: Amount actually filled
        filled_price: Average price of filled quantity
        commission: Trading fee paid
    """
    order_id: str
    symbol: str
    trade_type: TradeType
    order_type: OrderType
    quantity: float
    price: Optional[float]
    status: OrderStatus = OrderStatus.PENDING
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.filled_quantity >= self.quantity

    @property
    def fill_percent(self) -> float:
        """Get fill percentage (0-100)."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100

    def fill_order(self, filled_qty: float, fill_price: float, commission: float = 0.0) -> None:
        """
        Update order with fill information.
        
        Args:
            filled_qty: Quantity filled
            fill_price: Price at which filled
            commission: Trading fee
        """
        self.filled_quantity += filled_qty
        self.commission += commission

        # Calculate weighted average fill price
        if self.filled_price is None:
            self.filled_price = fill_price
        else:
            total_filled = self.filled_quantity
            self.filled_price = (
                (self.filled_price * (total_filled - filled_qty) + fill_price * filled_qty)
                / total_filled
            )

        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.CLOSED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'trade_type': self.trade_type.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status.value,
            'created_at': self.created_at,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'commission': self.commission,
        }


# ============================================================================
# POSITION AND TRADE MODELS
# ============================================================================

@dataclass
class Position:
    """
    Represents an open trading position.
    
    Tracks all orders, entry price, and P&L calculations.
    
    Attributes:
        position_id: Unique identifier
        symbol: Trading pair
        trade_type: LONG or SHORT
        entry_price: Entry price (weighted average)
        quantity: Total quantity held
        entry_time: When position was opened
        entry_orders: List of orders that opened this position
    """
    position_id: str
    symbol: str
    trade_type: TradeType
    entry_price: float
    quantity: float
    entry_time: Optional[float] = None
    entry_orders: List[Order] = field(default_factory=list)

    def add_entry_order(self, order: Order) -> None:
        """
        Add a filled order to the position.
        
        Args:
            order: Filled order to add
        """
        if order.filled_quantity == 0:
            return

        # Update average entry price
        old_total = self.quantity * self.entry_price
        new_total = order.filled_quantity * order.filled_price
        self.quantity += order.filled_quantity
        self.entry_price = (old_total + new_total) / self.quantity if self.quantity > 0 else 0
        self.entry_orders.append(order)

        if self.entry_time is None:
            self.entry_time = order.created_at

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L.
        
        Args:
            current_price: Current market price
        
        Returns:
            Unrealized P&L in quote asset (USDT, etc.)
        """
        if self.quantity == 0:
            return 0.0

        if self.trade_type == TradeType.LONG:
            return (current_price - self.entry_price) * self.quantity
        else:  # SHORT
            return (self.entry_price - current_price) * self.quantity

    def calculate_unrealized_pnl_percent(self, current_price: float) -> float:
        """
        Calculate unrealized P&L as percentage.
        
        Args:
            current_price: Current market price
        
        Returns:
            Unrealized P&L percentage
        """
        if self.entry_price == 0:
            return 0.0

        if self.trade_type == TradeType.LONG:
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SHORT
            return ((self.entry_price - current_price) / self.entry_price) * 100

    @property
    def is_open(self) -> bool:
        """Check if position has quantity."""
        return self.quantity > 0


@dataclass
class Trade:
    """
    Represents a closed trade (complete entry and exit).
    
    Attributes:
        trade_id: Unique identifier
        symbol: Trading pair
        entry_price: Price at entry (average if multiple orders)
        exit_price: Price at exit
        quantity: Total quantity traded
        entry_time: When position was opened
        exit_time: When position was closed
        pnl: Realized P&L in quote asset
        pnl_after_commission: P&L after deducting fees
        pnl_percent: Realized P&L as percentage
    """
    trade_id: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: float
    exit_time: float
    pnl: float = 0.0
    pnl_after_commission: float = 0.0
    pnl_percent: float = 0.0

    @property
    def duration_seconds(self) -> float:
        """Duration of trade in seconds."""
        return self.exit_time - self.entry_time

    @property
    def is_profitable(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl_after_commission > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'pnl': self.pnl,
            'pnl_after_commission': self.pnl_after_commission,
            'pnl_percent': self.pnl_percent,
            'duration_seconds': self.duration_seconds,
        }


# ============================================================================
# SIGNAL MODEL
# ============================================================================

@dataclass
class Signal:
    """
    Represents a trading signal generated by a strategy.
    
    Attributes:
        signal_type: Type of signal (BUY, SELL, CLOSE_LONG, CLOSE_SHORT, STOP_LOSS)
        symbol: Trading pair
        strength: Signal strength (0-1), higher = more confident
        generated_at: Timestamp when signal was generated
        rationale: Brief explanation of why signal was generated
    """
    signal_type: SignalType
    symbol: str
    strength: float = 1.0
    generated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    rationale: str = ""

    def __post_init__(self) -> None:
        """Validate signal strength."""
        if not 0 <= self.strength <= 1:
            raise ValueError(f"Signal strength must be between 0 and 1, got {self.strength}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'signal_type': self.signal_type.value,
            'symbol': self.symbol,
            'strength': self.strength,
            'generated_at': self.generated_at,
            'rationale': self.rationale,
        }
