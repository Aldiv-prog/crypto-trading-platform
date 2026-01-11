"""
Enum definitions for trading system.

This module contains all enumeration types used throughout the trading system.
"""

from enum import Enum


class TradeType(Enum):
    """Types of trades."""
    
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class OrderType(Enum):
    """Order execution types."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status."""
    
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order side (direction)."""
    
    BUY = "buy"
    SELL = "sell"


class PositionStatus(Enum):
    """Position status."""
    
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    LIQUIDATED = "liquidated"


class SignalType(Enum):
    """Trading signal types."""
    
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"
    EXIT = "exit"
    ENTRY = "entry"


class SignalStrength(Enum):
    """Signal strength indicator."""
    
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    NEUTRAL = "neutral"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class VolatilityLevel(Enum):
    """Volatility classification."""
    
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


class TrendDirection(Enum):
    """Price trend direction."""
    
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    RANGING = "ranging"


class ExecutionMode(Enum):
    """Strategy execution mode."""
    
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class TimeFrame(Enum):
    """Candlestick timeframes."""
    
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class AdaptationState(Enum):
    """State of adaptive system."""
    
    INITIALIZING = "initializing"
    NORMAL = "normal"
    ADAPTING = "adapting"
    ALERT = "alert"
    SAFE_MODE = "safe_mode"


class RiskLevel(Enum):
    """Risk classification."""
    
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GridStatus(Enum):
    """Grid trading status."""
    
    IDLE = "idle"
    ACTIVE = "active"
    SCALING_IN = "scaling_in"
    SCALING_OUT = "scaling_out"
    PAUSED = "paused"
    CLOSED = "closed"


class IndicatorSignal(Enum):
    """Indicator-specific signals."""
    
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"
    DIVERGENCE = "divergence"
    CONVERGENCE = "convergence"
    CROSSOVER = "crossover"
    BREAKDOWN = "breakdown"
    BREAKOUT = "breakout"


class ErrorType(Enum):
    """Error classification."""
    
    INVALID_PARAMETER = "invalid_parameter"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    ORDER_REJECTED = "order_rejected"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class LogLevel(Enum):
    """Log severity levels."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExitReason(Enum):
    """Position exit reasons."""
    
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    SIGNAL = "signal"
    MANUAL = "manual"
    TIMEOUT = "timeout"
    LIQUIDATION = "liquidation"
    SYSTEM_ERROR = "system_error"


class StrategyState(Enum):
    """State of a trading strategy"""
    IDLE = "IDLE"          # Waiting for entry signal
    ACTIVE = "ACTIVE"      # Position is open