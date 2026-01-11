"""
Backtest metrics calculation and analysis.

This module calculates and analyzes performance metrics from backtest results.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from datetime import datetime


@dataclass
class TradeMetrics:
    """Metrics for a single trade."""
    
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    profit_loss: float
    profit_loss_percent: float
    duration: int  # Duration in candles
    max_profit: float
    max_loss: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'profit_loss': self.profit_loss,
            'profit_loss_percent': self.profit_loss_percent,
            'duration': self.duration,
            'max_profit': self.max_profit,
            'max_loss': self.max_loss,
        }


class MetricsCalculator:
    """Calculate various performance metrics."""
    
    @staticmethod
    def calculate_returns(equity_curve: List[float]) -> List[float]:
        """
        Calculate daily returns.
        
        Args:
            equity_curve: List of account equity values
            
        Returns:
            List of returns (as percentages)
        """
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i - 1] == 0:
                returns.append(0.0)
            else:
                ret = ((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]) * 100
                returns.append(ret)
        
        return returns
    
    @staticmethod
    def calculate_drawdown(equity_curve: List[float]) -> tuple:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: List of account equity values
            
        Returns:
            Tuple of (max_drawdown, max_drawdown_percent, drawdown_duration)
        """
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - running_max) / running_max * 100
        
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        
        # Find start of max drawdown
        start_idx = np.argmax(running_max[:max_dd_idx])
        duration = max_dd_idx - start_idx
        
        return max(abs(drawdown)), abs(max_dd), duration
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading periods per year
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / periods_per_year)
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(periods_per_year)
        return sharpe
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float],
        target_return: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino ratio (downside risk).
        
        Args:
            returns: List of returns
            target_return: Target return (daily)
            periods_per_year: Trading periods per year
            
        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - target_return
        
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = np.std(downside_returns)
        
        if downside_std == 0:
            return 0.0
        
        sortino = (np.mean(excess_returns) / downside_std) * np.sqrt(periods_per_year)
        return sortino
    
    @staticmethod
    def calculate_calmar_ratio(
        annual_return: float,
        max_drawdown_percent: float
    ) -> float:
        """
        Calculate Calmar ratio.
        
        Args:
            annual_return: Annual return (%)
            max_drawdown_percent: Maximum drawdown (%)
            
        Returns:
            Calmar ratio
        """
        if max_drawdown_percent == 0:
            return 0.0
        
        return annual_return / max_drawdown_percent
    
    @staticmethod
    def calculate_win_rate(trades: List[TradeMetrics]) -> float:
        """
        Calculate win rate.
        
        Args:
            trades: List of trades
            
        Returns:
            Win rate (0-100)
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for t in trades if t.profit_loss > 0)
        return (winning_trades / len(trades)) * 100
    
    @staticmethod
    def calculate_profit_factor(trades: List[TradeMetrics]) -> float:
        """
        Calculate profit factor.
        
        Args:
            trades: List of trades
            
        Returns:
            Profit factor (gross profit / gross loss)
        """
        gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        gross_loss = sum(abs(t.profit_loss) for t in trades if t.profit_loss < 0)
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    @staticmethod
    def calculate_recovery_factor(
        net_profit: float,
        max_drawdown: float
    ) -> float:
        """
        Calculate recovery factor.
        
        Args:
            net_profit: Total net profit
            max_drawdown: Maximum drawdown amount
            
        Returns:
            Recovery factor
        """
        if max_drawdown == 0:
            return 0.0
        
        return net_profit / max_drawdown
    
    @staticmethod
    def calculate_metrics_summary(
        trades: List[TradeMetrics],
        equity_curve: List[float],
        initial_balance: float,
        periods_per_year: int = 252
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics summary.
        
        Args:
            trades: List of trades
            equity_curve: List of equity values
            initial_balance: Starting balance
            periods_per_year: Trading periods per year
            
        Returns:
            Dictionary with all metrics
        """
        if not equity_curve:
            return {}
        
        # Basic trade metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.profit_loss > 0)
        losing_trades = total_trades - winning_trades
        
        gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        gross_loss = sum(abs(t.profit_loss) for t in trades if t.profit_loss < 0)
        net_profit = gross_profit - gross_loss
        
        # Return metrics
        final_equity = equity_curve[-1]
        total_return_percent = ((final_equity - initial_balance) / initial_balance) * 100
        annual_return = total_return_percent  # Simplified
        
        # Risk metrics
        max_dd, max_dd_pct, dd_duration = MetricsCalculator.calculate_drawdown(equity_curve)
        returns = MetricsCalculator.calculate_returns(equity_curve)
        
        # Ratio metrics
        sharpe = MetricsCalculator.calculate_sharpe_ratio(returns, periods_per_year=periods_per_year)
        sortino = MetricsCalculator.calculate_sortino_ratio(returns, periods_per_year=periods_per_year)
        calmar = MetricsCalculator.calculate_calmar_ratio(annual_return, max_dd_pct)
        
        # Trade metrics
        win_rate = MetricsCalculator.calculate_win_rate(trades)
        profit_factor = MetricsCalculator.calculate_profit_factor(trades)
        recovery_factor = MetricsCalculator.calculate_recovery_factor(net_profit, max_dd)
        
        avg_winning = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_losing = gross_loss / losing_trades if losing_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_winning_trade': avg_winning,
            'avg_losing_trade': avg_losing,
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'net_profit': net_profit,
            'total_return_percent': total_return_percent,
            'annual_return_percent': annual_return,
            'max_drawdown': max_dd,
            'max_drawdown_percent': max_dd_pct,
            'max_drawdown_duration': dd_duration,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'recovery_factor': recovery_factor,
        }
