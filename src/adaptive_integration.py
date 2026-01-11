

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

"""
Adaptive strategy integration mixin - adds adaptive volatility scaling to any strategy.

Provides:
- Real-time volatility calculation (4 measures)
- Automatic parameter scaling
- Monitoring and history tracking
- Easy integration into existing strategies
"""

from src.volatility import VolatilityCalculator
from typing import Optional, Dict
from dataclasses import dataclass
from src.volatility import VolatilityCalculator, VolatilityMeasures
from src.adaptive_parameters import AdaptiveParameterEngine, AdaptiveParameterConfig, ScaledParameters

class AdaptiveStrategyMixin:
    """
    Mixin to add adaptive volatility scaling to any strategy.

    Usage:
        class YourStrategy(AdaptiveStrategyMixin):
            def __init__(self):
                self.initialize_adaptive()
                # ... your init code ...
    """

    def initialize_adaptive(self,
                           config: Optional[AdaptiveParameterConfig] = None) -> None:
        """
        Initialize adaptive engine.

        Args:
            config: Optional custom AdaptiveParameterConfig
        """
        self.vol_calculator = VolatilityCalculator()
        self.param_engine = AdaptiveParameterEngine(config)
        self.current_measures: Optional[VolatilityMeasures] = None
        self.current_scaled: Optional[ScaledParameters] = None

    def update_adaptive_parameters(self,
                                   high: float,
                                   low: float,
                                   close: float,
                                   open_price: float) -> ScaledParameters:
        """
        Update volatility and scale parameters.

        Call this once per candle with OHLC data.

        Args:
            high: Candle high price
            low: Candle low price
            close: Candle close price
            open_price: Candle open price

        Returns:
            ScaledParameters with current scaled values
        """
        # Calculate volatility
        self.current_measures = self.vol_calculator.update(
            high=high,
            low=low,
            close=close,
            open_price=open_price
        )

        # Scale parameters based on volatility
        self.current_scaled = self.param_engine.scale_parameters(
            self.current_measures
        )

        return self.current_scaled

    def get_current_grid_spacing(self) -> float:
        """Get current adaptive grid spacing percentage."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.grid_spacing_percent

    def get_current_order_volume(self) -> float:
        """Get current adaptive order volume."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.order_volume

    def get_current_take_profit(self) -> float:
        """Get current adaptive take profit percentage."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.take_profit_percent

    def get_current_max_drawdown(self) -> float:
        """Get current adaptive max drawdown percentage."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.max_drawdown_percent

    def get_volatility_level(self) -> str:
        """Get current volatility level (LOW/NORMAL/HIGH/EXTREME)."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.volatility_level

    def get_scaling_factor(self) -> float:
        """Get current scaling factor applied."""
        if self.current_scaled is None:
            return None
        return self.current_scaled.scaling_factor

    def get_volatility_measures(self) -> Optional[VolatilityMeasures]:
        """Get current volatility measures (all 4 calculations)."""
        return self.current_measures

    def print_adaptive_status(self) -> None:
        """Print current adaptive status."""
        if self.current_scaled is None:
            print("No adaptive data yet")
            return

        self.param_engine.print_status(self.current_scaled)

    def export_adaptive_history(self, filepath: str) -> None:
        """Export adaptive scaling history to JSON."""
        self.param_engine.export_history(filepath)

    def get_adaptive_config(self) -> AdaptiveParameterConfig:
        """Get current adaptive configuration."""
        return self.param_engine.config

    def set_adaptive_config(self, config: AdaptiveParameterConfig) -> None:
        """Update adaptive configuration."""
        self.param_engine.config = config

@dataclass
class AdaptiveStrategyHelper:
    """Helper functions for adaptive strategies."""

    @staticmethod
    def apply_scaled_parameters_to_grid(
            base_grid_spacing: float,
            base_order_volume: float,
            scaled: ScaledParameters) -> Dict:
        """
        Apply scaled parameters to grid trading.

        Args:
            base_grid_spacing: Original grid spacing % from config
            base_order_volume: Original order volume from config
            scaled: ScaledParameters from adaptive engine

        Returns:
            Dictionary with scaled parameters ready to use
        """
        return {
            'grid_spacing_percent': scaled.grid_spacing_percent,
            'order_volume': scaled.order_volume,
            'take_profit_percent': scaled.take_profit_percent,
            'max_drawdown_percent': scaled.max_drawdown_percent,
            'scaling_applied': scaled.scaling_factor,
            'volatility_level': scaled.volatility_level,
        }

    @staticmethod
    def format_volatility_report(measures: VolatilityMeasures) -> str:
        """Format volatility measures as readable report."""
        return (
            f"Volatility Report:\n"
            f"  Bollinger Bands: {measures.bollinger_bandwidth:.3f}%\n"
            f"  Garman-Klass:    {measures.garman_klass:.3f}%\n"
            f"  ATR:             {measures.atr:.6f}\n"
            f"  EWMA:            {measures.ewma:.3f}%\n"
            f"  Composite:       {measures.composite:.3f}%"
        )

    @staticmethod
    def format_scaling_report(scaled: ScaledParameters) -> str:
        """Format scaling results as readable report."""
        return (
            f"Scaling Report:\n"
            f"  Volatility Level: {scaled.volatility_level}\n"
            f"  Scaling Factor:   {scaled.scaling_factor:.2f}x\n"
            f"  Grid Spacing:     {scaled.grid_spacing_percent:.4f}%\n"
            f"  Order Volume:     {scaled.order_volume:.6f}\n"
            f"  Take Profit:      {scaled.take_profit_percent:.2f}%\n"
            f"  Max Drawdown:     {scaled.max_drawdown_percent:.2f}%"
        )
