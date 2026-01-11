

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

"""
Adaptive parameter engine - scales trading parameters based on real-time volatility.

Automatically adjusts:
- grid_spacing_percent: tighter in low vol, wider in high vol
- order_volume: larger in low vol, smaller in high vol
- take_profit_percent: smaller in low vol, larger in high vol
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np
from src.volatility import VolatilityMeasures   


@dataclass
class ScaledParameters:
    """Container for scaled trading parameters."""
    grid_spacing_percent: float  # Scaled grid spacing
    order_volume: float  # Scaled order volume
    take_profit_percent: float  # Scaled take profit
    max_drawdown_percent: float  # Scaled max drawdown
    volatility_level: str  # 'LOW', 'NORMAL', 'HIGH', 'EXTREME'
    scaling_factor: float  # Applied scaling multiplier
    timestamp: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'grid_spacing_percent': self.grid_spacing_percent,
            'order_volume': self.order_volume,
            'take_profit_percent': self.take_profit_percent,
            'max_drawdown_percent': self.max_drawdown_percent,
            'volatility_level': self.volatility_level,
            'scaling_factor': self.scaling_factor,
            'timestamp': self.timestamp,
        }

@dataclass
class AdaptiveParameterConfig:
    """Configuration for adaptive parameter scaling."""
    # Base parameters (fixed)
    base_grid_spacing_percent: float = 0.5
    base_order_volume: float = 0.02
    base_take_profit_percent: float = 5.0
    base_max_drawdown_percent: float = 8.0

    # Volatility reference points (for scaling)
    low_volatility_threshold: float = 1.0  # % below this = LOW vol
    high_volatility_threshold: float = 5.0  # % above this = HIGH vol

    # Scaling limits (safety bounds)
    min_scaling_factor: float = 0.4  # Don't scale below 40%
    max_scaling_factor: float = 2.5  # Don't scale above 250%

    # Volatility weights (4 measures combined)
    bb_weight: float = 0.25
    gk_weight: float = 0.25
    atr_weight: float = 0.25
    ewma_weight: float = 0.25

    # Scaling modes for each parameter
    # 'direct': higher vol = higher param (e.g., grid_spacing, take_profit)
    # 'inverse': higher vol = lower param (e.g., order_volume)
    scaling_modes: Dict[str, str] = field(default_factory=lambda: {
        'grid_spacing_percent': 'direct',
        'order_volume': 'inverse',
        'take_profit_percent': 'direct',
        'max_drawdown_percent': 'direct',
    })

class AdaptiveParameterEngine:
    """Engine for scaling trading parameters based on volatility."""

    def __init__(self, config: Optional[AdaptiveParameterConfig] = None):
        """
        Initialize adaptive parameter engine.

        Args:
            config: AdaptiveParameterConfig (uses defaults if None)
        """
        self.config = config or AdaptiveParameterConfig()
        self.volatility_history = []
        self.scaling_history = []

    def scale_parameters(self,
                         measures: VolatilityMeasures) -> ScaledParameters:
        """
        Scale parameters based on current volatility.

        Args:
            measures: VolatilityMeasures with all 4 volatility calculations

        Returns:
            ScaledParameters with scaled values
        """
        # Calculate composite volatility
        composite_vol = self._calculate_composite_volatility(measures)

        # Determine volatility level
        vol_level = self._classify_volatility(composite_vol)

        # Calculate scaling factor (0.4 to 2.5)
        scaling_factor = self._calculate_scaling_factor(composite_vol)

        # Apply scaling to each parameter
        scaled = ScaledParameters(
            grid_spacing_percent=self._scale_parameter(
                self.config.base_grid_spacing_percent,
                scaling_factor,
                'grid_spacing_percent'
            ),
            order_volume=self._scale_parameter(
                self.config.base_order_volume,
                scaling_factor,
                'order_volume'
            ),
            take_profit_percent=self._scale_parameter(
                self.config.base_take_profit_percent,
                scaling_factor,
                'take_profit_percent'
            ),
            max_drawdown_percent=self._scale_parameter(
                self.config.base_max_drawdown_percent,
                scaling_factor,
                'max_drawdown_percent'
            ),
            volatility_level=vol_level,
            scaling_factor=scaling_factor,
        )

        # Track history
        self.volatility_history.append(composite_vol)
        self.scaling_history.append(scaled)

        return scaled

    def _calculate_composite_volatility(self, measures: VolatilityMeasures) -> float:
        """Calculate weighted composite volatility from all 4 measures."""
        # Normalize ATR to percentage if needed
        normalized_atr = measures.atr * 100 if measures.atr > 0 else 0

        composite = (
            measures.bollinger_bandwidth * self.config.bb_weight +
            measures.garman_klass * self.config.gk_weight +
            normalized_atr * self.config.atr_weight +
            measures.ewma * self.config.ewma_weight
        )

        return max(0.0, composite)  # Ensure non-negative

    def _classify_volatility(self, volatility: float) -> str:
        """Classify volatility level."""
        if volatility < self.config.low_volatility_threshold:
            return 'LOW'
        elif volatility > self.config.high_volatility_threshold:
            return 'HIGH'
        elif volatility > self.config.high_volatility_threshold * 1.5:
            return 'EXTREME'
        else:
            return 'NORMAL'

    def _calculate_scaling_factor(self, volatility: float) -> float:
        """
        Calculate scaling factor based on volatility.

        Formula: scaling = volatility / reference_volatility
        Clamped to [min_scaling, max_scaling]
        """
        # Use mean of thresholds as reference point
        reference_vol = (self.config.low_volatility_threshold +
                         self.config.high_volatility_threshold) / 2

        if reference_vol == 0:
            reference_vol = 1.0

        # Direct scaling
        scaling = volatility / reference_vol

        # Apply safety limits
        scaling = max(self.config.min_scaling_factor,
                      min(self.config.max_scaling_factor, scaling))

        return scaling

    def _scale_parameter(self,
                         base_value: float,
                         scaling_factor: float,
                         param_name: str) -> float:
        """
        Apply scaling to a parameter.

        Args:
            base_value: Base/fixed parameter value
            scaling_factor: Scaling multiplier
            param_name: Parameter name (for mode lookup)

        Returns:
            Scaled value
        """
        mode = self.config.scaling_modes.get(param_name, 'direct')

        if mode == 'direct':
            # Higher vol = higher param
            scaled = base_value * scaling_factor
        else:  # inverse
            # Higher vol = lower param
            scaled = base_value / scaling_factor

        return max(0.0, scaled)  # Ensure non-negative

    def get_volatility_history(self) -> list:
        """Get complete volatility history."""
        return self.volatility_history.copy()

    def get_scaling_history(self) -> list:
        """Get complete scaling history."""
        return self.scaling_history.copy()

    def print_status(self, scaled: ScaledParameters) -> None:
        """Print current status."""
        print(f"\n{'='*60}")
        print(f"Volatility Level: {scaled.volatility_level}")
        print(f"Scaling Factor: {scaled.scaling_factor:.2f}x")
        print(f"\nScaled Parameters:")
        print(f"  Grid Spacing:     {scaled.grid_spacing_percent:.4f}%")
        print(f"  Order Volume:     {scaled.order_volume:.6f}")
        print(f"  Take Profit:      {scaled.take_profit_percent:.2f}%")
        print(f"  Max Drawdown:     {scaled.max_drawdown_percent:.2f}%")
        print(f"{'='*60}\n")

    def export_history(self, filepath: str) -> None:
        """Export scaling history to JSON file."""
        import json

        history_dict = {
            'volatility_history': self.volatility_history,
            'scaling_history': [s.to_dict() for s in self.scaling_history],
        }

        with open(filepath, 'w') as f:
            json.dump(history_dict, f, indent=2)
