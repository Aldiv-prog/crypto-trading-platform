"""
Comprehensive Module Import Tester
Tests all imports across the entire project to ensure everything is working correctly.
"""

import sys
import traceback
from typing import Dict, List, Tuple


class ImportTester:
    """Test all project imports systematically"""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def test_import(self, module_path: str, items: List[str] = None) -> bool:
        """
        Test importing a module and optionally specific items from it.
        
        Args:
            module_path: Full module path (e.g., 'src.core.enums')
            items: List of items to import from module
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import the module
            module = __import__(module_path, fromlist=[''])
            
            # If specific items requested, try to import them
            if items:
                for item in items:
                    if not hasattr(module, item):
                        self.warnings.append(f"  ⚠️  {module_path}.{item} not found")
                        return False
            
            self.passed.append(f"✅ {module_path}")
            if items:
                self.passed[-1] += f" ({', '.join(items)})"
            return True
            
        except Exception as e:
            self.failed.append(f"❌ {module_path}: {str(e)}")
            return False
    
    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 80)
        print("IMPORT TEST RESULTS")
        print("=" * 80)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)})")
            print("-" * 80)
            for item in self.passed:
                print(item)
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)})")
            print("-" * 80)
            for item in self.failed:
                print(item)
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)})")
            print("-" * 80)
            for item in self.warnings:
                print(item)
        
        # Summary
        total = len(self.passed) + len(self.failed)
        pass_rate = (len(self.passed) / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print(f"SUMMARY: {len(self.passed)}/{total} passed ({pass_rate:.1f}%)")
        print("=" * 80)
        
        return len(self.failed) == 0


def run_tests():
    """Run comprehensive import tests"""
    
    tester = ImportTester()
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE MODULE IMPORT TEST")
    print("=" * 80)
    print("\nTesting all imports across the project...\n")
    
    # ========================================================================
    # CORE MODULES
    # ========================================================================
    print("📦 CORE MODULES")
    print("-" * 80)
    
    tester.test_import('src.core.enums', [
        'TradeType', 'OrderType', 'OrderStatus', 'OrderSide', 'PositionStatus',
        'SignalType', 'SignalStrength', 'VolatilityLevel', 'TrendDirection',
        'ExecutionMode', 'TimeFrame', 'AdaptationState', 'RiskLevel',
        'GridStatus', 'IndicatorSignal', 'ErrorType', 'LogLevel', 'ExitReason'
    ])
    
    tester.test_import('src.core.position', ['Position', 'PositionMetrics'])
    tester.test_import('src.core.order_executor', ['Order', 'OrderExecutor'])
    tester.test_import('src.core.backtest_engine', ['BacktestEngine'])
    
    # ========================================================================
    # DATA LAYER
    # ========================================================================
    print("\n📊 DATA LAYER")
    print("-" * 80)
    
    tester.test_import('src.data.data_models', ['Candle', 'MarketData', 'MarketTicker'])
    tester.test_import('src.data.market_data', ['MarketDataLoader', 'MarketDataCache'])
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    print("\n⚙️  CONFIGURATION")
    print("-" * 80)
    
    tester.test_import('src.config_models', [
        'TradeConfig', 'BacktestConfig', 'ExchangeConfig', 'SystemConfig',
        'StrategyConfig', 'BinanceConfig', 'GridTradingParams', 'StrategyMetrics'
    ])
    
    # ========================================================================
    # STRATEGIES
    # ========================================================================
    print("\n🎯 STRATEGIES")
    print("-" * 80)
    
    tester.test_import('src.strategies.base_strategy', ['Strategy', 'StrategyState'])
    tester.test_import('src.strategies.strategy_utils', [
        'TechnicalIndicators', 'RiskManagement', 'SignalAnalysis'
    ])
    tester.test_import('src.strategies.grid_strategy', ['GridTradingStrategy'])
    
    # ========================================================================
    # BACKTEST LAYER
    # ========================================================================
    print("\n📈 BACKTEST LAYER")
    print("-" * 80)
    
    tester.test_import('src.backtest.backtest_runner', ['BacktestRunner'])
    tester.test_import('src.backtest.metrics', ['MetricsCalculator', 'TradeMetrics'])
    
    # ========================================================================
    # LIVE TRADING
    # ========================================================================
    print("\n💱 LIVE TRADING")
    print("-" * 80)
    
    tester.test_import('src.live_trading.exchange_connector', [
        'ExchangeConnector', 'MockExchangeConnector'
    ])
    tester.test_import('src.live_trading.trade_executor', [
        'TradeExecutor', 'ExecutionMode'
    ])
    
    # ========================================================================
    # OPTIMIZATION
    # ========================================================================
    print("\n🔬 OPTIMIZATION")
    print("-" * 80)
    
    tester.test_import('src.optimization.optimizer', [
        'Optimizer', 'OptimizationParam', 'FitnessCalculator'
    ])
    tester.test_import('src.optimization.param_tuner', [
        'ParameterTuner', 'ParameterAdjustment', 'DynamicParameterAdjuster'
    ])
    
    # ========================================================================
    # VISUALIZATION & REPORTING
    # ========================================================================
    print("\n📊 VISUALIZATION & REPORTING")
    print("-" * 80)
    
    tester.test_import('src.visualization.plotter', ['Plotter'])
    tester.test_import('src.visualization.report_generator', ['ReportGenerator'])
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    print("\n🔧 UTILITIES")
    print("-" * 80)
    
    tester.test_import('src.utils.logger', [
        'Logger', 'DebugTracer', 'PerformanceMonitor'
    ])
    tester.test_import('src.utils.helpers', [
        'FileHelper', 'DateTimeHelper', 'MathHelper',
        'ConfigHelper', 'ValidationHelper', 'FormatHelper'
    ])
    
    # ========================================================================
    # ADAPTIVE SYSTEM
    # ========================================================================
    print("\n🧠 ADAPTIVE SYSTEM")
    print("-" * 80)
    
    tester.test_import('src.volatility', ['VolatilityCalculator'])
    tester.test_import('src.adaptive_parameters', ['AdaptiveParameterEngine'])
    tester.test_import('src.adaptive_integration', ['AdaptiveStrategyMixin'])
    
    # ========================================================================
    # CROSS-MODULE INTEGRATION TEST
    # ========================================================================
    print("\n🔗 CROSS-MODULE INTEGRATION")
    print("-" * 80)
    
    try:
        from src.core.enums import TradeType, TimeFrame, SignalType
        from src.data.data_models import Candle, MarketData
        from src.config_models import StrategyConfig, GridTradingParams
        from src.strategies.base_strategy import Strategy, StrategyState
        from src.strategies.grid_strategy import GridTradingStrategy
        from src.backtest.metrics import MetricsCalculator
        from src.core.position import Position
        from src.utils.logger import Logger
        
        tester.passed.append("✅ Full integration test (all major modules)")
        
    except Exception as e:
        tester.failed.append(f"❌ Integration test: {str(e)}")
    
    # ========================================================================
    # PYDANTIC VALIDATION TEST
    # ========================================================================
    print("\n✔️  PYDANTIC VALIDATION")
    print("-" * 80)
    
    try:
        from src.config_models import BinanceConfig, GridTradingParams, StrategyConfig
        from src.core.enums import TimeFrame
        
        # Test BinanceConfig
        binance = BinanceConfig(
            api_key="test_key",
            api_secret="test_secret"
        )
        tester.passed.append("✅ BinanceConfig validation")
        
        # Test GridTradingParams
        params = GridTradingParams(
            initial_position_size=1.0,
            grid_spacing_percent=0.5,
            grid_levels=10,
            take_profit_percent=5.0,
            max_drawdown_percent=2.0
)

        tester.passed.append("✅ GridTradingParams validation")
        
        # Test StrategyConfig with all required fields
        strategy = StrategyConfig(
            symbol="BTCUSDT",
            trade_type="LONG",
            timeframe=TimeFrame.ONE_HOUR,
            long_params=params,
            short_params=params
        )
        tester.passed.append("✅ StrategyConfig validation")
        
    except Exception as e:
        tester.failed.append(f"❌ Pydantic validation: {str(e)}")
        traceback.print_exc()
    
    # ========================================================================
    # PRINT RESULTS
    # ========================================================================
    success = tester.print_results()
    
    # Return exit code
    return 0 if success else 1


def main():
    """Main entry point"""
    try:
        exit_code = run_tests()
        
        print("\n" + "=" * 80)
        if exit_code == 0:
            print("🎉 ALL TESTS PASSED! Your project is correctly configured!")
        else:
            print("⚠️  SOME TESTS FAILED. Please check the errors above.")
        print("=" * 80 + "\n")
        
        return exit_code
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
