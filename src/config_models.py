

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

"""""
Provides strongly-typed, validated configuration for:
- Binance API credentials
- Strategy parameters
- Backtest settings
- Optimization settings
- Risk management
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from src.core.enums import TimeFrame, ExecutionMode

# ============================================================================
# BINANCE CONFIGURATION
# ============================================================================

class BinanceConfig(BaseModel):
    """Configuration for Binance API connection."""
    
    api_key: str = Field(..., description="Binance API key")
    api_secret: str = Field(..., description="Binance API secret")
    testnet: bool = Field(default=False, description="Use Binance testnet instead of live")
    request_timeout: int = Field(default=5, ge=1, le=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Max API retry attempts")
    
    class Config:
        validate_assignment = True
    
    def validate_credentials(self) -> bool:
        """
        Validate that API key and secret are provided and non-empty.
        
        Returns:
            bool: True if credentials are valid.
            
        Raises:
            ValueError: If credentials are invalid.
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API key and secret must be provided")
        if len(self.api_key) < 10:
            raise ValueError("Invalid API key format")
        if len(self.api_secret) < 10:
            raise ValueError("Invalid API secret format")
        return True

# ============================================================================
# STRATEGY PARAMETERS
# ============================================================================

class GridTradingParams(BaseModel):
    """
    Parameters for grid trading strategy (average-down/average-up).
    
    This configuration defines how the strategy will behave:
    - Initial position sizing
    - Grid spacing and levels
    - Take profit targets
    - Stop loss protection
    """
    
    # Position and sizing
    initial_position_size: float = Field(
        ..., 
        gt=0, 
        description="Initial position size (in base asset quantity)"
    )
    grid_spacing_percent: float = Field(
        ..., 
        gt=0, 
        le=10,
        description="Percentage spacing between grid orders (0-10%)"
    )
    grid_levels: int = Field(
        ..., 
        ge=1, 
        le=20,
        description="Number of grid levels for averaging"
    )
    
    # Take profit
    take_profit_percent: float = Field(
        ...,
        gt=0,
        le=100,
        description="Take profit percentage (0-100%)"
    )
    
    # Risk management
    max_drawdown_percent: float = Field(
        ...,
        gt=0,
        le=100,
        description="Maximum drawdown allowed as % of total equity"
    )
    max_position_size_percent: float = Field(
        default=20.0,
        gt=0,
        le=100,
        description="Maximum position size as % of total equity"
    )
    
    # Order execution
    order_type: str = Field(
        default="limit",
        description="Order type: 'limit' or 'market'"
    )
    limit_order_timeout_seconds: int = Field(
        default=300,
        ge=10,
        description="How long to keep limit orders open before cancelling"
    )
    
    class Config:
        validate_assignment = True
    
    @field_validator('grid_spacing_percent')
    def validate_grid_spacing(cls, v: float) -> float:
        """Ensure grid spacing is reasonable."""
        if v < 0.1:
            raise ValueError("Grid spacing must be at least 0.1%")
        return v
    
    @field_validator('grid_levels')
    def validate_grid_levels(cls, v: int) -> int:
        """Ensure grid levels is reasonable."""
        if v > 50:
            raise ValueError("Grid levels should not exceed 50 to avoid over-trading")
        return v

class StrategyConfig(BaseModel):
    """
    Complete strategy configuration for a single trading pair.
    
    Includes both long and short strategy parameters.
    """
    
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDT')"
    )
    timeframe: TimeFrame = Field(
        default=TimeFrame.ONE_HOUR,
        description="Candle timeframe for analysis"
    )
    
    # Strategy parameters
    long_params: GridTradingParams = Field(
        ...,
        description="Parameters for long (average-down) strategy"
    )
    short_params: GridTradingParams = Field(
        ...,
        description="Parameters for short (average-up) strategy"
    )
    
    # Enable/disable strategies
    enable_long: bool = Field(default=True, description="Enable long strategy")
    enable_short: bool = Field(default=True, description="Enable short strategy")
    
    # Entry conditions
    min_volatility_threshold: float = Field(
        default=0.5,
        gt=0,
        description="Minimum volatility (%) before strategy starts"
    )
    
    class Config:
        validate_assignment = True
    
    @model_validator(mode='after')
    def validate_strategy_config(self):
        if not self.enable_long and not self.enable_short:
            raise ValueError("Either enable_long or enable_short must be True")
        return self


# ============================================================================
# BACKTEST CONFIGURATION
# ============================================================================

class BacktestConfig(BaseModel):
    """Configuration for backtesting runs."""
    
    start_date: str = Field(
        ...,
        description="Backtest start date (YYYY-MM-DD)"
    )
    end_date: str = Field(
        ...,
        description="Backtest end date (YYYY-MM-DD)"
    )
    initial_balance: float = Field(
        ...,
        gt=0,
        description="Starting account balance in USDT"
    )
    
    # Commission and slippage
    maker_fee_percent: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Maker fee percentage (Binance default: 0.1%)"
    )
    taker_fee_percent: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Taker fee percentage (Binance default: 0.1%)"
    )
    slippage_percent: float = Field(
        default=0.05,
        ge=0,
        le=5,
        description="Slippage assumption for limit orders (%)"
    )
    
    # Performance
    use_multiprocessing: bool = Field(
        default=False,
        description="Use multiprocessing for faster backtests"
    )
    num_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Number of worker processes"
    )
    
    class Config:
        validate_assignment = True

# ============================================================================
# OPTIMIZATION CONFIGURATION
# ============================================================================

class OptimizationConfig(BaseModel):
    """Configuration for parameter optimization."""
    
    method: str = Field(
        default="bayesian",
        description="Optimization method: 'bayesian', 'grid', 'random'"
    )
    num_trials: int = Field(
        default=100,
        ge=10,
        le=10000,
        description="Number of optimization trials"
    )
    num_jobs: int = Field(
        default=-1,
        description="Number of parallel jobs (-1 = all CPUs)"
    )
    
    # Parameter search space
    param_space: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameter ranges to search"
    )
    
    # Objective function
    optimization_metric: str = Field(
        default="sharpe_ratio",
        description="Metric to optimize: 'sharpe_ratio', 'total_return', 'win_rate'"
    )
    minimize: bool = Field(
        default=False,
        description="Minimize metric (if True) or maximize (if False)"
    )
    
    class Config:
        validate_assignment = True

# ============================================================================
# LIVE TRADING CONFIGURATION
# ============================================================================

class LiveTradingConfig(BaseModel):
    """Configuration for live trading bot."""
    
    # Connection
    binance_config: BinanceConfig = Field(..., description="Binance API configuration")
    
    # Portfolio
    total_equity: float = Field(
        ...,
        gt=0,
        description="Total account equity to allocate to strategy"
    )
    max_leverage: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Maximum leverage allowed"
    )
    
    # Execution
    order_check_interval: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Interval to check order status (seconds)"
    )
    websocket_reconnect_timeout: int = Field(
        default=10,
        ge=5,
        le=60,
        description="WebSocket reconnection timeout (seconds)"
    )
    
    # Risk limits
    max_concurrent_positions: int = Field(
        default=5,
        ge=1,
        description="Maximum number of concurrent positions"
    )
    daily_loss_limit_percent: float = Field(
        default=5.0,
        gt=0,
        le=50,
        description="Daily loss limit as % of equity"
    )
    
    # State management
    state_save_interval: int = Field(
        default=60,
        ge=10,
        description="Interval to save bot state (seconds)"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        validate_assignment = True

# ============================================================================
# MAIN PLATFORM CONFIGURATION
# ============================================================================

class PlatformConfig(BaseModel):
    """
    Master configuration for the entire trading platform.
    
    Combines all sub-configurations and provides validation.
    """
    
    mode: ExecutionMode = Field(
        default=ExecutionMode.BACKTEST,
        description="Execution mode: backtest, live, or paper_trading"
    )
    
    # Sub-configurations
    binance: BinanceConfig = Field(..., description="Binance connection config")
    strategies: List[StrategyConfig] = Field(..., description="List of strategy configs")
    
    # Mode-specific configs
    backtest: Optional[BacktestConfig] = Field(None, description="Backtest configuration")
    optimization: Optional[OptimizationConfig] = Field(None, description="Optimization config")
    live_trading: Optional[LiveTradingConfig] = Field(None, description="Live trading config")
    
    # Global settings
    timezone: str = Field(default="UTC", description="Timezone for logging and reporting")
    log_level: str = Field(default="INFO", description="Global logging level")
    
    class Config:
        validate_assignment = True
    
    @model_validator(mode='after')
    def validate_mode_configs(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required configs exist for selected mode."""
        mode = getattr(self, 'mode')
        
        if mode == ExecutionMode.BACKTEST and not getattr(self, 'backtest'):
            raise ValueError("BacktestConfig required when mode is BACKTEST")
        
        if mode == ExecutionMode.LIVE and not getattr(self, 'live_trading'):
            raise ValueError("LiveTradingConfig required when mode is LIVE")
        
        return values
    
    def to_file(self, filepath: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path to save config file.
        """
        import json
        with open(filepath, 'w') as f:
            json.dump(self.dict(), f, indent=2)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'PlatformConfig':
        """
        Load configuration from JSON file.
        
        Args:
            filepath: Path to config file.
            
        Returns:
            PlatformConfig: Loaded configuration.
        """
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class TradeConfig(BaseModel):
    """Configuration for individual trades"""
    symbol: str
    trade_type: str  # 'LONG' or 'SHORT'
    entry_price: float
    quantity: float
    stop_loss_percent: float = Field(default=2.0)
    take_profit_percent: float = Field(default=5.0)
    timeframe: TimeFrame = TimeFrame.ONE_HOUR
    
    class Config:
        validate_assignment = True


class StrategyMetrics(BaseModel):
    """Metrics for a strategy"""
    total_return_percent: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    # Add other fields as needed
    
    class Config:
        validate_assignment = True
