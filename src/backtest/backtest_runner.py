

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

"""
Backtest runner for executing strategies on historical data.

This module coordinates the execution of trading strategies against
historical market data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..core.backtest_engine import BacktestEngine
from ..config_models import BacktestConfig, StrategyMetrics
from ..data.market_data import MarketDataLoader
from src.volatility import VolatilityCalculator, VolatilityMeasures
from src.adaptive_parameters import AdaptiveParameterEngine, AdaptiveParameterConfig, ScaledParameters
from abc import ABC, abstractmethod
from src.data.data_models import Signal
from src.core.order_executor import Order
from src.config_models import GridTradingParams







class BacktestRunner:
    """
    Orchestrates backtest execution and result processing.
    
    Runs trading strategies against historical data and generates
    performance reports.
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize the backtest runner.
        
        Args:
            config: BacktestConfig object
        """
        self.config = config
        self.engine = BacktestEngine(config)
        self.results: Optional[StrategyMetrics] = None
        self.trade_history: List[Dict[str, Any]] = []
    
    def load_market_data(
        self,
        filepath: str,
        symbol: str,
        format: str = "csv"
    ) -> None:
        """
        Load market data for backtesting.
        
        Args:
            filepath: Path to market data file
            symbol: Trading pair symbol
            format: Data format (csv, json)
        """
        if format == "csv":
            market_data = MarketDataLoader.load_from_csv(
                filepath, symbol, self.config.candle_timeframe
            )
        elif format == "json":
            market_data = MarketDataLoader.load_from_json(
                filepath, symbol, self.config.candle_timeframe
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.engine.set_market_data(market_data)
    
    def run(self, strategies: List[Any]) -> StrategyMetrics:
        """
        Run backtest with provided strategies.
        
        Args:
            strategies: List of strategy objects
            
        Returns:
            StrategyMetrics with backtest results
        """
        print(f"Starting backtest from {self.config.start_date} to {self.config.end_date}")
        
        # Run the backtest engine
        self.results = self.engine.run_backtest(strategies)
        
        # Extract trade history
        self.trade_history = self.engine.get_trade_history()
        
        print(f"Backtest complete. Total trades: {self.results.total_trades}")
        print(f"Win rate: {self.results.win_rate:.2f}%")
        print(f"Profit factor: {self.results.profit_factor:.2f}")
        
        return self.results
    
    def export_results(self, filepath: str) -> None:
        """
        Export backtest results to file.
        
        Args:
            filepath: Path to export file
        """
        if not self.results:
            raise ValueError("No backtest results to export")
        
        export_data = {
            'config': {
                'start_date': self.config.start_date,
                'end_date': self.config.end_date,
                'initial_balance': self.config.initial_balance,
            },
            'metrics': self.results.to_dict(),
            'trades': self.trade_history,
            'timestamp': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Results exported to {filepath}")
    
    def export_trades(self, filepath: str) -> None:
        """
        Export trade history to file.
        
        Args:
            filepath: Path to export file
        """
        with open(filepath, 'w') as f:
            json.dump(self.trade_history, f, indent=2)
        
        print(f"Trade history exported to {filepath}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get backtest summary.
        
        Returns:
            Dictionary with key metrics
        """
        if not self.results:
            return {}
        
        return {
            'total_trades': self.results.total_trades,
            'winning_trades': self.results.winning_trades,
            'losing_trades': self.results.losing_trades,
            'win_rate': self.results.win_rate,
            'profit_factor': self.results.profit_factor,
            'max_drawdown': self.results.max_drawdown_percent,
            'sharpe_ratio': self.results.sharpe_ratio,
            'return_percent': self.results.return_percent,
        }
