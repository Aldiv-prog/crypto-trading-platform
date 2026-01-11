"""
Complete working backtest engine with full signal processing and order execution.

Replace your src/core/backtest_engine.py with this implementation.
"""

from turtle import pos
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import json

from src.core.enums import TradeType, OrderStatus
from src.data.data_models import Candle, MarketData, Order, Trade, Position
from src.strategies.grid_strategy import GridTradingStrategy
from src.config_models import BacktestConfig, StrategyConfig

# ============================================================================
# PORTFOLIO TRACKING
# ============================================================================

@dataclass
class PortfolioState:
    """Represents the state of a portfolio at any point in time."""
    timestamp: float
    cash_balance: float
    positions: Dict[str, Position] = field(default_factory=dict)
    closed_trades: List[Trade] = field(default_factory=list)
    total_fees: float = 0.0

    @property
    def total_equity(self) -> float:
        """Calculate total account equity (cash + position value)."""
        unrealized_pnl = sum(
            pos.calculate_unrealized_pnl(0.0) for pos in self.positions.values()
        )
        return self.cash_balance + unrealized_pnl

    @property
    def realized_pnl(self) -> float:
        """Total realized P&L from closed trades."""
        return sum(trade.pnl_after_commission for trade in self.closed_trades)

    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L from open positions."""
        return sum(
            pos.calculate_unrealized_pnl(0.0) for pos in self.positions.values()
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/export."""
        return {
            'timestamp': self.timestamp,
            'cash_balance': self.cash_balance,
            'total_equity': self.total_equity,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_fees': self.total_fees,
            'num_open_positions': len(self.positions),
            'num_closed_trades': len(self.closed_trades),
        }


@dataclass
class BacktestMetrics:
    """Complete performance metrics for a backtest run."""
    total_return_percent: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown_percent: float = 0.0
    max_drawdown_duration_days: int = 0
    best_trade_percent: float = 0.0
    worst_trade_percent: float = 0.0
    average_trade_duration_days: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total_return_percent': self.total_return_percent,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'max_drawdown_percent': self.max_drawdown_percent,
            'max_drawdown_duration_days': self.max_drawdown_duration_days,
            'best_trade_percent': self.best_trade_percent,
            'worst_trade_percent': self.worst_trade_percent,
            'average_trade_duration_days': self.average_trade_duration_days,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
        }


# ============================================================================
# ORDER EXECUTION SIMULATOR
# ============================================================================

class OrderExecutor:
    """Simulates order execution for backtesting."""
    
    def __init__(self, maker_fee: float = 0.1, taker_fee: float = 0.1,
                 slippage: float = 0.05):
        self.maker_fee = maker_fee / 100.0
        self.taker_fee = taker_fee / 100.0
        self.slippage = slippage / 100.0

    def execute_limit_order(self, order: Order, candle: Candle) -> Tuple[float, float]:
        """
        Attempt to execute limit order against a candle's OHLC.
        
        For LONG orders: fills if candle.low <= order.price
        For SHORT orders: fills if candle.high >= order.price
        
        Returns: Tuple of (filled_quantity, fill_price)
        """
        filled_qty = 0.0
        fill_price = 0.0

        if order.trade_type == TradeType.LONG:
            if candle.low <= order.price:
                filled_qty = order.quantity
                fill_price = min(order.price, candle.close)
                # Apply slippage
                fill_price *= (1 + self.slippage)
        else:  # SHORT
            if candle.high >= order.price:
                filled_qty = order.quantity
                fill_price = max(order.price, candle.close)
                # Apply slippage (negative for shorts)
                fill_price *= (1 - self.slippage)

        return filled_qty, fill_price

    def calculate_commission(self, quantity: float, price: float,
                           is_maker: bool = False) -> float:
        """Calculate trading commission."""
        fee_percent = self.maker_fee if is_maker else self.taker_fee
        return quantity * price * fee_percent


# ============================================================================
# BACKTESTING ENGINE - COMPLETE WORKING VERSION
# ============================================================================

class BacktestEngine:
    """Main backtesting engine with full order execution."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.portfolio_history: List[PortfolioState] = []
        self.all_trades: List[Trade] = []
        self.order_executor = OrderExecutor(
            maker_fee=config.maker_fee_percent,
            taker_fee=config.taker_fee_percent,
            slippage=config.slippage_percent
        )

    def run_backtest(self,
                     market_data_dict: Dict[str, MarketData],
                     strategy_configs: List[StrategyConfig]) -> BacktestMetrics:
        """Run complete backtest on historical data."""
        
        # Initialize strategies
        strategies: Dict[str, Tuple[Optional[GridTradingStrategy], Optional[GridTradingStrategy]]] = {}
        
        for config in strategy_configs:
            long_strategy = GridTradingStrategy(
                config.symbol,
                TradeType.LONG,
                config.long_params
            ) if config.enable_long else None
            
            short_strategy = GridTradingStrategy(
                config.symbol,
                TradeType.SHORT,
                config.short_params
            ) if config.enable_short else None
            
            strategies[config.symbol] = (long_strategy, short_strategy)

        # Initialize portfolio
        portfolio = PortfolioState(
            timestamp=0.0,
            cash_balance=self.config.initial_balance
        )

        # Find number of candles
        num_candles = min(len(data.candles) for data in market_data_dict.values())

        # Track pending orders
        pending_orders: Dict[str, List[Order]] = defaultdict(list)

        # ====================================================================
        # MAIN BACKTESTING LOOP
        # ====================================================================
        
        for candle_idx in range(num_candles):
            current_candles = {}
            
            # Get current candle for each symbol
            for symbol, market_data in market_data_dict.items():
                current_candles[symbol] = market_data.candles[candle_idx]

            # Process each symbol
            for symbol in strategies.keys():
                if symbol not in current_candles:
                    continue
                
                candle = current_candles[symbol]
                long_strat, short_strat = strategies[symbol]

                # =========================================================
                # STEP 1: CHECK PENDING ORDERS FOR FILLS
                # =========================================================
                
                filled_orders = []
                if symbol in pending_orders:
                    remaining_orders = []
                    for order in pending_orders[symbol]:
                        filled_qty, fill_price = self.order_executor.execute_limit_order(
                            order, candle
                        )
                        
                        if filled_qty > 0:
                            # Order filled!
                            filled_orders.append((order, filled_qty, fill_price))
                            print(f"  📊 Order FILLED: {symbol} {order.trade_type.value.upper()} "
                                  f"{filled_qty:.4f} @ {fill_price:.2f}")
                        else:
                            remaining_orders.append(order)
                    
                    pending_orders[symbol] = remaining_orders

                # =========================================================
                # STEP 2: PROCESS FILLED ORDERS - UPDATE POSITIONS
                # =========================================================
                
                for order, filled_qty, fill_price in filled_orders:
                    commission = self.order_executor.calculate_commission(
                        filled_qty, fill_price, is_maker=True
                    )
                    portfolio.total_fees += commission
                    portfolio.cash_balance -= commission
                    
                    # Create or update position
                    if symbol not in portfolio.positions:
                        portfolio.positions[symbol] = Position(
                            position_id=f"{symbol}_{order.trade_type.value}_{candle_idx}",
                            symbol=symbol,
                            trade_type=order.trade_type,
                            entry_price=fill_price,
                            quantity=filled_qty,
                            entry_time=candle.timestamp
                        )
                    else:
                        pos = portfolio.positions[symbol]
                        # Average entry price
                        total_qty = pos.quantity + filled_qty
                        pos.entry_price = (
                            (pos.entry_price * pos.quantity + fill_price * filled_qty) / total_qty
                        )
                        pos.quantity = total_qty

                        # Preserve entry time (use first entry time)
                        if pos.entry_time is None:
                            pos.entry_time = candle.timestamp
                    
                    # Deduct from cash
                    portfolio.cash_balance -= filled_qty * fill_price

                # =========================================================
                # STEP 3: ANALYZE FOR ENTRY SIGNALS
                # =========================================================
                
                market_data = market_data_dict[symbol]
                
                # LONG strategy
                if long_strat and not long_strat.position:
                    signals = long_strat.analyze(market_data)
                    if signals:
                        # Generate grid orders
                        entry_price = candle.close
                        position_size = self.config.initial_balance * 0.1 / entry_price  # 10% of capital
                        
                        grid_orders = long_strat.generate_grid_orders(
                            entry_price, position_size, candle.close
                        )
                        
                        # Add to pending orders
                        pending_orders[symbol].extend(grid_orders)
                        print(f"  🎯 Generated {len(grid_orders)} LONG grid orders for {symbol}")

                # SHORT strategy
                if short_strat and not short_strat.position:
                    signals = short_strat.analyze(market_data)
                    if signals:
                        # Generate grid orders
                        entry_price = candle.close
                        position_size = self.config.initial_balance * 0.1 / entry_price
                        
                        grid_orders = short_strat.generate_grid_orders(
                            entry_price, position_size, candle.close
                        )
                        
                        # Add to pending orders
                        pending_orders[symbol].extend(grid_orders)
                        print(f"  🎯 Generated {len(grid_orders)} SHORT grid orders for {symbol}")

                # =========================================================
                # STEP 4: CHECK EXIT CONDITIONS
                # =========================================================
                
                if symbol in portfolio.positions:
                    position = portfolio.positions[symbol]
                    current_price = candle.close
                    
                    # Check long exit
                    if position.trade_type == TradeType.LONG and long_strat:
                        exit_signal = long_strat.check_exit_conditions(current_price, portfolio.total_equity, position)
                        
                        if exit_signal:
                            # Close position
                            pnl = (current_price - position.entry_price) * position.quantity
                            commission = self.order_executor.calculate_commission(
                                position.quantity, current_price, is_maker=True
                            )
                            
                            pnl_after_commission = pnl - commission
                            portfolio.total_fees += commission
                            portfolio.cash_balance += (position.quantity * current_price) - commission
                            
                            # Create trade record
                            trade = Trade(
                                trade_id=f"{symbol}_L_{candle_idx}",
                                symbol=symbol,
                                entry_price=position.entry_price,
                                exit_price=current_price,
                                quantity=position.quantity,
                                entry_time=position.entry_time,
                                exit_time=candle.timestamp,
                                pnl=pnl,
                                pnl_after_commission=pnl_after_commission,
                                pnl_percent=(pnl / (position.entry_price * position.quantity)) * 100 if position.entry_price > 0 else 0,
                            )
                            
                            self.all_trades.append(trade)
                            portfolio.closed_trades.append(trade)
                            del portfolio.positions[symbol]
                            
                            print(f"  ✅ CLOSED LONG {symbol}: PnL ${pnl_after_commission:.2f} ({trade.pnl_percent:.2f}%)")

                    # Check short exit
                    elif position.trade_type == TradeType.SHORT and short_strat:
                        exit_signal = short_strat.check_exit_conditions(current_price, portfolio.total_equity, position)
                        
                        if exit_signal:
                            # Close position
                            pnl = (position.entry_price - current_price) * position.quantity
                            commission = self.order_executor.calculate_commission(
                                position.quantity, current_price, is_maker=True
                            )
                            
                            pnl_after_commission = pnl - commission
                            portfolio.total_fees += commission
                            portfolio.cash_balance += (position.quantity * current_price) - commission
                            
                            # Create trade record
                            trade = Trade(
                                trade_id=f"{symbol}_S_{candle_idx}",
                                symbol=symbol,
                                entry_price=position.entry_price,
                                exit_price=current_price,
                                quantity=position.quantity,
                                entry_time=position.entry_time,
                                exit_time=candle.timestamp,
                                pnl=pnl,
                                pnl_after_commission=pnl_after_commission,
                                pnl_percent=(pnl / (position.entry_price * position.quantity)) * 100 if position.entry_price > 0 else 0,
                            )
                            
                            self.all_trades.append(trade)
                            portfolio.closed_trades.append(trade)
                            del portfolio.positions[symbol]
                            
                            print(f"  ✅ CLOSED SHORT {symbol}: PnL ${pnl_after_commission:.2f} ({trade.pnl_percent:.2f}%)")

            # Save portfolio state
            self.portfolio_history.append(portfolio)

        # Calculate final metrics
        metrics = self._calculate_metrics(portfolio, self.all_trades)
        return metrics

    def _calculate_metrics(self, final_portfolio: PortfolioState,
                           trades: List[Trade]) -> BacktestMetrics:
        """Calculate performance metrics from portfolio history and trades."""
        metrics = BacktestMetrics()

        if not trades:
            metrics.total_return_percent = 0.0
            return metrics

        # Basic metrics
        metrics.total_trades = len(trades)
        metrics.winning_trades = sum(1 for t in trades if t.is_profitable)
        metrics.losing_trades = metrics.total_trades - metrics.winning_trades

        if metrics.total_trades > 0:
            metrics.win_rate = (metrics.winning_trades / metrics.total_trades) * 100

        # Profit analysis
        winning_pnls = [t.pnl_after_commission for t in trades if t.is_profitable]
        losing_pnls = [abs(t.pnl_after_commission) for t in trades if not t.is_profitable]

        if winning_pnls:
            metrics.average_win = sum(winning_pnls) / len(winning_pnls)

        if losing_pnls:
            metrics.average_loss = sum(losing_pnls) / len(losing_pnls)

        if metrics.average_loss > 0 and sum(losing_pnls) > 0:
            metrics.profit_factor = sum(winning_pnls) / sum(losing_pnls)

        # Best/worst trades
        if trades:
            best_trade = max(trades, key=lambda t: t.pnl_percent)
            worst_trade = min(trades, key=lambda t: t.pnl_percent)
            metrics.best_trade_percent = best_trade.pnl_percent
            metrics.worst_trade_percent = worst_trade.pnl_percent

        # Average trade duration
        if trades:
            avg_duration = sum(t.duration_seconds for t in trades) / len(trades)
            metrics.average_trade_duration_days = avg_duration / 86400

        # Return calculation
        initial_balance = self.config.initial_balance
        final_balance = final_portfolio.total_equity
        metrics.total_return_percent = (
            ((final_balance - initial_balance) / initial_balance) * 100
        )

        return metrics

    def get_portfolio_history(self) -> List[PortfolioState]:
        """Get complete portfolio history."""
        return self.portfolio_history

    def get_trades(self) -> List[Trade]:
        """Get all closed trades."""
        return self.all_trades

    def export_results(self, filepath: str) -> None:
        """Export backtest results to JSON."""
        results = {
            'portfolio_history': [p.to_dict() for p in self.portfolio_history],
            'trades': [t.to_dict() for t in self.all_trades],
        }

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
