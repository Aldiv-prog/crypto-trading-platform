"""
Base strategy class for all trading strategies.

This module provides the abstract base class that all strategies
should inherit from.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.data.data_models import Candle, MarketData

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

@dataclass
class StrategyInfo:
    """State information for a strategy."""
    
    symbol: str
    trade_type: str  # LONG, SHORT, BOTH
    is_initialized: bool = False
    last_update: Optional[datetime] = None
    position_count: int = 0
    total_trades: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    All trading strategies should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, symbol: str, trade_type: str, **kwargs):
        """
        Initialize the strategy.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            trade_type: LONG, SHORT, or BOTH
            **kwargs: Additional strategy-specific parameters
        """
        self.symbol = symbol
        self.trade_type = trade_type
        self.state = StrategyInfo(symbol=symbol, trade_type=trade_type)
        self.parameters = kwargs
        self.positions: List[Any] = []
        self.orders: List[Any] = []
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the strategy.
        
        Called once at the start of the backtest or trading session.
        Use this to set up any indicators, caches, or state.
        """
        pass
    
    @abstractmethod
    def on_candle(self, candle: Candle) -> None:
        """
        Called when a new candle is received.
        
        This is where the main trading logic happens.
        
        Args:
            candle: The new candlestick data
        """
        pass
    
    @abstractmethod
    def generate_signals(self, market_data: MarketData) -> Dict[str, Any]:
        """
        Generate trading signals based on market data.
        
        Args:
            market_data: Historical market data
            
        Returns:
            Dictionary with signal information
        """
        pass
    
    @abstractmethod
    def on_position_open(self, position_id: str, entry_price: float) -> None:
        """
        Called when a position is opened.
        
        Args:
            position_id: ID of the opened position
            entry_price: Entry price of the position
        """
        pass
    
    @abstractmethod
    def on_position_close(self, position_id: str, exit_price: float, pnl: float) -> None:
        """
        Called when a position is closed.
        
        Args:
            position_id: ID of the closed position
            exit_price: Exit price of the position
            pnl: Profit/loss from the position
        """
        pass
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get a strategy parameter.
        
        Args:
            key: Parameter key
            default: Default value if key not found
            
        Returns:
            Parameter value or default
        """
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """
        Set a strategy parameter.
        
        Args:
            key: Parameter key
            value: Parameter value
        """
        self.parameters[key] = value
    
    def get_state(self) -> StrategyInfo:
        """Get current strategy state."""
        return self.state
    
    def update_state(self, **kwargs) -> None:
        """
        Update strategy state.
        
        Args:
            **kwargs: State fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def is_ready(self) -> bool:
        """Check if strategy is initialized and ready."""
        return self.state.is_initialized
    
    def reset(self) -> None:
        """Reset the strategy state."""
        self.state = StrategyInfo(
            symbol=self.symbol,
            trade_type=self.trade_type
        )
        self.positions.clear()
        self.orders.clear()
    
    def to_dict(self) -> dict:
        """Convert strategy to dictionary."""
        return {
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'is_initialized': self.state.is_initialized,
            'position_count': self.state.position_count,
            'total_trades': self.state.total_trades,
            'parameters': self.parameters,
        }
