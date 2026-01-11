"""
Grid trading strategy implementation with adaptive volatility scaling.

This module provides:
- Abstract base class for all strategies
- Concrete implementation of grid trading (average-down/average-up)
- INTEGRATED ADAPTIVE VOLATILITY SCALING
- Position management and signal generation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

# Enums
from src.core.enums import (
    TradeType,
    OrderType,
    SignalType,
    StrategyState,
    ExitReason,
)

# Data models
from src.data.data_models import Candle, MarketData, Signal, Order, Position, Trade

# Config models
from src.config_models import GridTradingParams

# Adaptive system
from src.adaptive_integration import AdaptiveStrategyMixin


# ============================================================================
# BASE STRATEGY CLASS
# ============================================================================

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Defines the interface that all strategy implementations must follow.
    Strategies are responsible for:
    - Analyzing market data
    - Generating trading signals
    - Managing positions and risk
    """

    def __init__(self, symbol: str, trade_type: TradeType):
        """
        Initialize strategy.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            trade_type: LONG or SHORT
        """
        self.symbol = symbol
        self.trade_type = trade_type
        self.state = StrategyState.IDLE
        self.position: Optional[Position] = None
        self.entry_orders: List[Order] = []
        self.exit_orders: List[Order] = []

    @abstractmethod
    def analyze(self, market_data: MarketData) -> List[Signal]:
        """
        Analyze market data and generate signals.
        
        Args:
            market_data: Current market data (candles)
            
        Returns:
            List of Signal objects (empty if no signals)
        """
        pass

    @abstractmethod
    def calculate_position_size(self, account_balance: float, params: Dict) -> float:
        """
        Calculate initial position size based on account balance and parameters.
        
        Args:
            account_balance: Current account balance
            params: Strategy parameters
            
        Returns:
            Position size in base asset quantity
        """
        pass

    @abstractmethod
    def generate_grid_orders(self,
                            entry_price: float,
                            position_size: float,
                            params: Dict) -> List[Order]:
        """
        Generate grid orders for averaging in/out.
        
        Args:
            entry_price: Initial entry price
            position_size: Size of initial position
            params: Strategy parameters
            
        Returns:
            List of Order objects
        """
        pass

    @abstractmethod
    def check_exit_conditions(self, current_price: float, params: Dict) -> Optional[Signal]:
        """
        Check if position should be exited (TP or SL hit).
        
        Args:
            current_price: Current market price
            params: Strategy parameters
            
        Returns:
            Exit signal if triggered, None otherwise
        """
        pass

    @abstractmethod
    def update_state(self, market_data: MarketData, filled_orders: List[Order]) -> None:
        """
        Update internal state based on market data and order fills.
        
        Args:
            market_data: Current market data
            filled_orders: List of recently filled orders
        """
        pass

    def reset(self) -> None:
        """Reset strategy to idle state."""
        self.state = StrategyState.IDLE
        self.position = None
        self.entry_signal_generated = False
        self.entry_orders = []
        self.exit_orders = []


# ============================================================================
# GRID TRADING STRATEGY WITH ADAPTIVE PARAMETERS
# ============================================================================

class GridTradingStrategy(Strategy, AdaptiveStrategyMixin):
    """
    Grid trading strategy - average down (long) or average up (short).
    
    NOW WITH ADAPTIVE VOLATILITY SCALING!
    
    For LONG positions:
    - Opens with buy orders at progressively lower prices (averaging down)
    - Closes when price increases by TP% above average entry price
    - Uses ADAPTIVE TP% that scales with volatility
    
    For SHORT positions:
    - Opens with sell orders at progressively higher prices (averaging up)
    - Closes when price decreases by TP% below average entry price
    - Uses ADAPTIVE TP% that scales with volatility
    
    Both positions have stop-loss protection at DD% drawdown (also adaptive).
    Grid spacing automatically widens/tightens based on volatility.
    """

    def __init__(self, symbol: str, trade_type: TradeType, params: GridTradingParams):
        """
        Initialize grid trading strategy WITH ADAPTIVE SUPPORT.
        
        Args:
            symbol: Trading pair symbol
            trade_type: LONG or SHORT
            params: GridTradingParams configuration
        """
        # Initialize base strategy
        super().__init__(symbol, trade_type)
        
        # NEW: Initialize adaptive engine
        self.initialize_adaptive()
        
        # Strategy parameters
        self.params = params
        self.grid_prices: List[float] = []
        self.entry_signal_generated = False
        self.current_max_price = 0.0  # Track highest price for SL calculation
        self.current_min_price = float('inf')  # Track lowest price for SL calculation

    def analyze(self, market_data: MarketData) -> List[Signal]:
        """
        Analyze market data for entry signals.
        
        Args:
            market_data: Current market data
            
        Returns:
            List of entry signals
        """
        signals: List[Signal] = []
        
        if self.state == StrategyState.IDLE and not self.entry_signal_generated:
            # Simple entry logic: check if volatility meets minimum threshold
            volatility = market_data.calculate_volatility(period=20)
            min_vol_threshold = (
                self.params.min_volatility_threshold
                if hasattr(self.params, 'min_volatility_threshold')
                else 0.1
            )
            
            if volatility >= min_vol_threshold:
                # Generate entry signal
                signal_type = (
                    SignalType.BUY if self.trade_type == TradeType.LONG
                    else SignalType.SELL
                )
                
                signal = Signal(
                    signal_type=signal_type,
                    symbol=self.symbol,
                    strength=min(volatility / 10.0, 1.0),  # Normalize to 0-1
                    rationale=(
                        f"Volatility {volatility:.2f}% meets threshold "
                        f"for {self.trade_type.value} strategy"
                    )
                )
                signals.append(signal)
                self.entry_signal_generated = True
        
        return signals

    def calculate_position_size(self, account_balance: float,
                               max_position_percent: float = 20.0) -> float:
        """
        Calculate initial position size.
        
        Args:
            account_balance: Current account balance in quote asset
            max_position_percent: Maximum position as % of balance
            
        Returns:
            Position size in base asset quantity
        """
        max_position_value = (
            account_balance * (self.params.max_position_size_percent / 100.0)
        )
        
        # For now, assume entry price is around current price
        # This will be refined when actual entry price is known
        return max_position_value / self.params.initial_position_size

    def generate_grid_orders(self,
                            entry_price: float,
                            position_size: float,
                            current_price: float) -> List[Order]:
        """
        Generate grid orders for averaging in/out.
        
        FOR LONG: Creates buy orders at progressively lower prices
        FOR SHORT: Creates sell orders at progressively higher prices
        USES ADAPTIVE GRID SPACING!
        
        Args:
            entry_price: Entry price for first order
            position_size: Total position size
            current_price: Current market price
            
        Returns:
            List of Order objects
        """
        orders: List[Order] = []
        
        # NEW: Use adaptive grid spacing if available
        if self.current_scaled is not None:
            grid_spacing_percent = self.current_scaled.grid_spacing_percent
        else:
            grid_spacing_percent = self.params.grid_spacing_percent
        
        size_per_order = position_size / self.params.grid_levels
        grid_spacing = grid_spacing_percent / 100.0
        
        if self.trade_type == TradeType.LONG:
            # Create buy orders at progressively lower prices
            for level in range(self.params.grid_levels):
                price = entry_price * (1 - grid_spacing * level)
                order = Order(
                    order_id=f"{self.symbol}_{self.trade_type.value}_grid_{level}",
                    symbol=self.symbol,
                    trade_type=TradeType.LONG,
                    order_type=OrderType.LIMIT,
                    quantity=size_per_order,
                    price=price,
                )
                orders.append(order)
                self.grid_prices.append(price)
        else:  # SHORT
            # Create sell orders at progressively higher prices
            for level in range(self.params.grid_levels):
                price = entry_price * (1 + grid_spacing * level)
                order = Order(
                    order_id=f"{self.symbol}_{self.trade_type.value}_grid_{level}",
                    symbol=self.symbol,
                    trade_type=TradeType.SHORT,
                    order_type=OrderType.LIMIT,
                    quantity=size_per_order,
                    price=price,
                )
                orders.append(order)
                self.grid_prices.append(price)
        
        return orders

    def check_exit_conditions(self, current_price: float,
                             account_equity: float,
                             position: Optional[Position] = None) -> Optional[Signal]:
        """
        Check if position should be exited due to TP or SL.
        
        USES ADAPTIVE TAKE PROFIT AND MAX DRAWDOWN!
        
        Exit conditions:
        1. Take Profit: Price moves TP% in favorable direction from average entry
        2. Stop Loss: Drawdown exceeds DD% of account equity
        
        Args:
            current_price: Current market price
            account_equity: Current account equity
            position: Position object (optional, uses self.position if not provided)
            
        Returns:
            Exit signal if triggered, None otherwise
        """
        pos = position or self.position
        
        if pos is None or not pos.is_open:
            return None
        
        # Track price extremes for drawdown calculation
        self.current_max_price = max(self.current_max_price, current_price)
        self.current_min_price = min(self.current_min_price, current_price)
        
        # NEW: Use adaptive take profit if available
        if self.current_scaled is not None:
            tp_percent = self.current_scaled.take_profit_percent
            dd_percent = self.current_scaled.max_drawdown_percent
        else:
            tp_percent = self.params.take_profit_percent
            dd_percent = self.params.max_drawdown_percent
        
        # Check Take Profit
        pnl_percent = pos.calculate_unrealized_pnl_percent(current_price)
        
        if pnl_percent >= tp_percent:
            # FIXED: Use SignalType.EXIT instead of CLOSE_LONG/CLOSE_SHORT
            return Signal(
                signal_type=SignalType.EXIT,
                symbol=self.symbol,
                strength=1.0,
                rationale=(
                    f"Take profit triggered: {pnl_percent:.2f}% >= {tp_percent}% "
                    f"(adaptive: {self.current_scaled is not None})"
                )
            )
        
        # Check Stop Loss (drawdown-based)
        # Only check if position has entry orders (has been established)
        if pos.entry_orders:
            # Calculate current drawdown from entry point
            if self.trade_type == TradeType.LONG:
                drawdown = (
                    (self.current_max_price - current_price) / self.current_max_price
                ) * 100 if self.current_max_price > 0 else 0
            else:  # SHORT
                drawdown = (
                    (current_price - self.current_min_price) / self.current_min_price
                ) * 100 if self.current_min_price > 0 else 0
            
            max_loss_allowed = account_equity * (dd_percent / 100.0)
            current_loss = abs(pos.calculate_unrealized_pnl(current_price))
            
            if current_loss >= max_loss_allowed:
                # FIXED: Use SignalType.EXIT instead of STOPLOSS
                return Signal(
                    signal_type=SignalType.EXIT,
                    symbol=self.symbol,
                    strength=1.0,
                    rationale=(
                        f"Stop loss triggered: Loss {current_loss:.2f} >= "
                        f"Limit {max_loss_allowed:.2f} "
                        f"(adaptive: {self.current_scaled is not None})"
                    )
                )
        
        return None

    def update_state(self, market_data: MarketData,
                    filled_orders: List[Order]) -> None:
        """
        Update strategy state with new market data and filled orders.
        
        Args:
            market_data: Current market data
            filled_orders: Recently filled orders
        """
        current_price = market_data.latest_close or 0.0
        
        # Update position with filled orders
        if filled_orders:
            if self.position is None:
                # Create new position on first fill
                self.position = Position(
                    position_id=(
                        f"{self.symbol}_{self.trade_type.value}_"
                        f"{market_data.latest_candle.timestamp}"
                    ),
                    symbol=self.symbol,
                    trade_type=self.trade_type,
                )
            
            for order in filled_orders:
                self.position.add_entry_order(order)
                self.entry_orders.append(order)
        
        # Update price extremes
        if self.position and self.position.is_open:
            self.current_max_price = max(self.current_max_price, current_price)
            self.current_min_price = min(self.current_min_price, current_price)
        
        # Update state
        if self.state == StrategyState.IDLE:
            self.state = StrategyState.ACTIVE

    def get_position_info(self) -> Dict:
        """
        Get current position information including adaptive status.
        
        Returns:
            Dictionary with position details
        """
        if self.position is None:
            return {'status': 'no_position'}
        
        info = {
            'position_id': self.position.position_id,
            'quantity': self.position.total_quantity,
            'average_entry_price': self.position.average_entry_price,
            'entry_orders': len(self.position.entry_orders),
            # NEW: Include adaptive info
            'adaptive_enabled': self.current_scaled is not None,
        }
        
        if self.current_scaled is not None:
            info['adaptive_info'] = {
                'volatility_level': self.current_scaled.volatility_level,
                'scaling_factor': self.current_scaled.scaling_factor,
                'current_grid_spacing': self.current_scaled.grid_spacing_percent,
                'current_take_profit': self.current_scaled.take_profit_percent,
                'current_max_drawdown': self.current_scaled.max_drawdown_percent,
            }
        
        return info
