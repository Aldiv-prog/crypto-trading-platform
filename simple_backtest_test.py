"""
FULLY FIXED BACKTEST - Both Bugs Fixed!

BUG #1: position.entry_orders was never populated
  FIX: Populate entry_orders when filling orders

BUG #2: entry_signal_generated flag never reset after reset()
  FIX: Reset the flag when strategy.reset() is called
"""

import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest_engine import BacktestEngine
from src.config_models import BacktestConfig, StrategyConfig, GridTradingParams
from src.core.enums import TradeType
from src.data.data_models import Candle, MarketData, Order, Trade, Position


def generate_realistic_market_data(symbol: str, num_candles: int = 5000) -> MarketData:
    """Generate realistic market data."""
    candles = []
    current_price = 100.0
    current_timestamp = int(datetime.now().timestamp())
    phase_length = num_candles // 4
    
    for i in range(num_candles):
        phase = (i // phase_length) % 4
        
        if phase == 0:  # UPTREND
            trend = random.uniform(0.15, 0.35)
            noise = random.uniform(-0.3, 0.3)
            change = trend + noise
        elif phase == 1:  # RANGING
            change = random.uniform(-0.4, 0.4)
        elif phase == 2:  # DOWNTREND
            trend = random.uniform(-0.35, -0.15)
            noise = random.uniform(-0.3, 0.3)
            change = trend + noise
        else:  # RANGING
            change = random.uniform(-0.4, 0.4)
        
        current_price = max(current_price + change, 50.0)
        current_price = min(current_price, 200.0)
        
        open_price = current_price
        close_price = current_price + random.uniform(-0.25, 0.25)
        high_price = max(open_price, close_price) + random.uniform(0, 0.5)
        low_price = min(open_price, close_price) - random.uniform(0, 0.5)
        volume = random.uniform(500, 10000)
        
        candle = Candle(
            timestamp=float(current_timestamp + i * 3600),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
        )
        candles.append(candle)
        current_price = close_price
    
    return MarketData(symbol=symbol, candles=candles, timeframe="1h")


def run_fully_fixed_backtest():
    """Run backtest with BOTH bugs fixed."""
    
    print("=" * 100)
    print("FULLY FIXED BACKTEST - BOTH ENTRY_ORDERS AND entry_signal_generated BUGS FIXED!")
    print("=" * 100)
    
    # Generate market data
    print("\n[OK] Step 1: Generating 5000 candles...")
    market_data = generate_realistic_market_data("BTCUSDC", num_candles=30000)
    print(f"   - Candles: {len(market_data.candles)}")
    print(f"   - Price range: ${market_data.candles[0].close:.2f} -> ${market_data.candles[-1].close:.2f}")
    
    # Strategy configuration
    print("\n[OK] Step 2: Creating strategy configuration...")
    long_params = GridTradingParams(
        grid_levels=4,
        grid_spacing_percent=0.15,
        take_profit_percent=1,
        max_drawdown_percent=1,
        max_position_size_percent=10.0,
        initial_position_size=100.0,
    )
    
    strategy_config = StrategyConfig(
        symbol="BTCUSDC",
        enable_long=True,
        enable_short=True,
        long_params=long_params,
        short_params=long_params,
    )
    
    # Backtest configuration
    print("\n[OK] Step 3: Creating backtest configuration...")
    backtest_config = BacktestConfig(
        initial_balance=10000.0,
        start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        maker_fee_percent=0.1,
        taker_fee_percent=0.1,
        slippage_percent=0.05,
    )
    
    # Initialize engine
    print("\n[OK] Step 4: Initializing backtest engine...")
    engine = BacktestEngine(backtest_config)
    
    # Run backtest
    print("\n[OK] Step 5: Running backtest...")
    print("\n" + "=" * 100)
    print("BACKTEST PROGRESS")
    print("=" * 100 + "\n")
    
    market_data_dict = {"BTCUSDC": market_data}
    
    def fully_fixed_run_backtest(market_data_dict, strategy_configs):
        """Backtest with BOTH fixes applied."""
        from src.core.enums import TradeType
        from src.data.data_models import Candle, MarketData, Order, Trade, Position
        from src.strategies.grid_strategy import GridTradingStrategy
        
        # Initialize strategies
        strategies = {}
        for config in strategy_configs:
            long_strategy = GridTradingStrategy(
                config.symbol, TradeType.LONG, config.long_params
            ) if config.enable_long else None
            strategies[config.symbol] = (long_strategy, None)
        
        # Initialize portfolio
        from src.core.backtest_engine import PortfolioState
        portfolio = PortfolioState(
            timestamp=0.0,
            cash_balance=engine.config.initial_balance
        )
        
        num_candles = len(market_data_dict["BTCUSDC"].candles)
        pending_orders = defaultdict(list)
        
        entry_count = 0
        exit_count = 0
        
        # Main backtest loop
        for candle_idx in range(num_candles):
            symbol = "BTCUSDC"
            candle = market_data_dict[symbol].candles[candle_idx]
            long_strat, _ = strategies[symbol]
            market_data_obj = market_data_dict[symbol]
            current_price = candle.close
            
            # ============================================================
            # STEP 1: PROCESS PENDING ORDERS
            # ============================================================
            filled_orders = []
            if symbol in pending_orders and pending_orders[symbol]:
                remaining_orders = []
                for order in pending_orders[symbol]:
                    should_fill = False
                    fill_price = candle.close
                    
                    if order.trade_type == TradeType.LONG:
                        if candle.low <= order.price:
                            should_fill = True
                            fill_price = min(order.price, candle.close)
                    else:
                        if candle.high >= order.price:
                            should_fill = True
                            fill_price = max(order.price, candle.close)
                    
                    if should_fill:
                        filled_orders.append((order, order.quantity, fill_price))
                    else:
                        remaining_orders.append(order)
                
                pending_orders[symbol] = remaining_orders
            
            # ============================================================
            # STEP 2: UPDATE POSITION WITH FILLED ORDERS
            # ============================================================
            for order, filled_qty, fill_price in filled_orders:
                commission = engine.order_executor.calculate_commission(
                    filled_qty, fill_price, is_maker=True
                )
                portfolio.total_fees += commission
                portfolio.cash_balance -= commission
                
                if symbol not in portfolio.positions:
                    portfolio.positions[symbol] = Position(
                        position_id=f"{symbol}_L_{candle_idx}",
                        symbol=symbol,
                        trade_type=order.trade_type,
                        entry_price=fill_price,
                        quantity=filled_qty,
                        entry_time=candle.timestamp,
                        entry_orders=[order]  # FIX #1: Track filled orders!
                    )
                else:
                    pos = portfolio.positions[symbol]
                    total_qty = pos.quantity + filled_qty
                    pos.entry_price = (
                        (pos.entry_price * pos.quantity + fill_price * filled_qty) / total_qty
                    )
                    pos.quantity = total_qty
                    pos.entry_orders.append(order)  # FIX #1: Add filled order!
                
                portfolio.cash_balance -= filled_qty * fill_price
            
            # ============================================================
            # STEP 3: ANALYZE FOR ENTRY SIGNALS
            # ============================================================
            if long_strat and not long_strat.position and symbol not in portfolio.positions:
                signals = long_strat.analyze(market_data_obj)
                if signals:
                    entry_price = candle.close
                    position_size = engine.config.initial_balance * 0.1 / entry_price
                    grid_orders = long_strat.generate_grid_orders(
                        entry_price, position_size, candle.close
                    )
                    pending_orders[symbol].extend(grid_orders)
                    entry_count += 1
            
            # ============================================================
            # STEP 4: CHECK EXIT CONDITIONS
            # ============================================================
            if symbol in portfolio.positions:
                position = portfolio.positions[symbol]
                
                # FIX #1: Check len(entry_orders) > 0
                if len(position.entry_orders) > 0:
                    if position.trade_type == TradeType.LONG and long_strat:
                        exit_signal = long_strat.check_exit_conditions(
                            current_price, portfolio.total_equity, position
                        )
                        
                        if exit_signal:
                            exit_count += 1
                            
                            pnl = (current_price - position.entry_price) * position.quantity
                            commission = engine.order_executor.calculate_commission(
                                position.quantity, current_price, is_maker=True
                            )
                            pnl_after_commission = pnl - commission
                            portfolio.total_fees += commission
                            portfolio.cash_balance += (position.quantity * current_price) - commission
                            
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
                                pnl_percent=(pnl / (position.entry_price * position.quantity) * 100) if position.entry_price > 0 else 0,
                            )
                            engine.all_trades.append(trade)
                            portfolio.closed_trades.append(trade)
                            del portfolio.positions[symbol]
                            
                            # FIX #2: Reset strategy AND RESET entry_signal_generated flag
                            long_strat.reset()
                            long_strat.entry_signal_generated = False  # CRITICAL FIX #2!
            
            engine.portfolio_history.append(portfolio)
            
            # Progress indicator
            if (candle_idx + 1) % 500 == 0:
                print(f"   Processed {candle_idx + 1} candles - Entries: {entry_count}, Exits: {exit_count}")
        
        print(f"\n   Final: Entries: {entry_count}, Exits: {exit_count}")
        return engine._calculate_metrics(portfolio, engine.all_trades)
    
    metrics = fully_fixed_run_backtest(market_data_dict, [strategy_config])
    
    # Print results
    print("\n" + "=" * 100)
    print("BACKTEST RESULTS")
    print("=" * 100)
    
    print("\nPerformance Metrics:")
    print(f"  Total Return:              {metrics.total_return_percent:>10.2f}%")
    print(f"  Total Trades:              {metrics.total_trades:>10}")
    print(f"  Winning Trades:            {metrics.winning_trades:>10}")
    print(f"  Losing Trades:             {metrics.losing_trades:>10}")
    if metrics.total_trades > 0:
        win_rate = (metrics.winning_trades / metrics.total_trades) * 100
        print(f"  Win Rate:                  {win_rate:>10.2f}%")
        print(f"  Average Win:               ${metrics.average_win:>9.2f}")
        print(f"  Average Loss:              ${metrics.average_loss:>9.2f}")
        print(f"  Profit Factor:             {metrics.profit_factor:>10.2f}")
    
    print("\nRisk Metrics:")
    print(f"  Max Drawdown:              {metrics.max_drawdown_percent:>10.2f}%")
    print(f"  Sharpe Ratio:              {metrics.sharpe_ratio:>10.2f}")
    print(f"  Sortino Ratio:             {metrics.sortino_ratio:>10.2f}")
    
    print("\nStrategy Statistics:")
    if metrics.total_trades >= 100:
        print(f"  [SUCCESS] STATISTICALLY SIGNIFICANT ({metrics.total_trades} trades)")
    elif metrics.total_trades >= 50:
        print(f"  [MODERATE] {metrics.total_trades} trades")
    else:
        print(f"  [INSUFFICIENT] {metrics.total_trades} trades")
    
    print("\n" + "=" * 100)
    print("BACKTEST COMPLETED!")
    print("=" * 100)


if __name__ == "__main__":
    run_fully_fixed_backtest()
