"""
Volatility calculator - real-time volatility measurement using 4 methods.

This module provides production-ready volatility calculations:
- Bollinger Bands (simple, reliable)
- Garman-Klass (optimal for OHLC)
- ATR (professional standard)
- EWMA (fast, responsive)
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class VolatilityMeasures:
    """Container for all 4 volatility measurements."""
    bollinger_bandwidth: float  # % of price
    garman_klass: float  # % volatility
    atr: float  # absolute value
    ewma: float  # % volatility
    composite: float  # weighted average

    def __repr__(self) -> str:
        return (
            f"VolatilityMeasures(bb={self.bollinger_bandwidth:.3f}%, "
            f"gk={self.garman_klass:.3f}%, atr={self.atr:.6f}, "
            f"ewma={self.ewma:.3f}%, composite={self.composite:.3f}%)"
        )


class VolatilityCalculator:
    """Real-time volatility calculation engine."""

    def __init__(self,
                 bb_period: int = 20,
                 bb_std_dev: float = 2.0,
                 atr_period: int = 14,
                 ewma_alpha: float = 0.33):
        """
        Initialize volatility calculator.

        Args:
            bb_period: Bollinger Bands lookback period
            bb_std_dev: Bollinger Bands standard deviations
            atr_period: ATR lookback period
            ewma_alpha: EWMA smoothing factor (0-1, higher = more responsive)
        """
        self.bb_period = bb_period
        self.bb_std_dev = bb_std_dev
        self.atr_period = atr_period
        self.ewma_alpha = ewma_alpha

        # History buffers
        self.closes: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        self.opens: List[float] = []
        self.previous_ewma: Optional[float] = None

    def update(self,
               high: float,
               low: float,
               close: float,
               open_price: float) -> VolatilityMeasures:
        """
        Update volatility with new candle data.

        Args:
            high: Candle high price
            low: Candle low price
            close: Candle close price
            open_price: Candle open price

        Returns:
            VolatilityMeasures with all 4 calculations
        """
        self.closes.append(close)
        self.highs.append(high)
        self.lows.append(low)
        self.opens.append(open_price)

        # Keep only needed history
        max_history = max(self.bb_period, self.atr_period) + 5
        if len(self.closes) > max_history:
            self.closes.pop(0)
            self.highs.pop(0)
            self.lows.pop(0)
            self.opens.pop(0)

        return VolatilityMeasures(
            bollinger_bandwidth=self._calculate_bollinger_bandwidth(),
            garman_klass=self._calculate_garman_klass(),
            atr=self._calculate_atr(),
            ewma=self._calculate_ewma(),
            composite=0.0  # Will be set after all calculations
        )

    def _calculate_bollinger_bandwidth(self) -> float:
        """Calculate Bollinger Bands bandwidth as % of price."""
        if len(self.closes) < self.bb_period:
            return 0.0

        recent = self.closes[-self.bb_period:]
        mean = np.mean(recent)
        std_dev = np.std(recent)
        bandwidth = (self.bb_std_dev * std_dev) / mean * 100

        return bandwidth

    def _calculate_garman_klass(self) -> float:
        """Calculate Garman-Klass volatility (optimal for OHLC)."""
        if len(self.closes) < self.atr_period:
            return 0.0

        recent_h = self.highs[-self.atr_period:]
        recent_l = self.lows[-self.atr_period:]
        recent_c = self.closes[-self.atr_period:]
        recent_o = self.opens[-self.atr_period:]

        gk_sum = 0.0
        for i in range(len(recent_h)):
            hl = np.log(recent_h[i] / recent_l[i])
            co = np.log(recent_c[i] / recent_o[i])
            gk_sum += 0.5 * (hl ** 2) - (2 * np.log(2) - 1) * (co ** 2)

        gk_variance = gk_sum / len(recent_h)
        gk_volatility = np.sqrt(abs(gk_variance)) * 100

        return gk_volatility

    def _calculate_atr(self) -> float:
        """Calculate Average True Range."""
        if len(self.closes) < self.atr_period + 1:
            return 0.0

        tr_values = []
        for i in range(1, len(self.closes)):
            high_low = self.highs[i] - self.lows[i]
            high_close = abs(self.highs[i] - self.closes[i - 1])
            low_close = abs(self.lows[i] - self.closes[i - 1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)

        recent_tr = tr_values[-self.atr_period:]
        atr = np.mean(recent_tr)

        return atr

    def _calculate_ewma(self) -> float:
        """Calculate Exponential Weighted Moving Average volatility."""
        if len(self.closes) < 2:
            return 0.0

        # Calculate simple returns
        returns = []
        for i in range(1, len(self.closes)):
            ret = (self.closes[i] - self.closes[i - 1]) / self.closes[i - 1]
            returns.append(ret)

        # EWMA of squared returns
        if self.previous_ewma is None:
            self.previous_ewma = np.var(returns) if returns else 0.0
        else:
            latest_return = returns[-1] if returns else 0.0
            self.previous_ewma = (self.ewma_alpha * (latest_return ** 2) +
                                  (1 - self.ewma_alpha) * self.previous_ewma)

        ewma_volatility = np.sqrt(abs(self.previous_ewma)) * 100

        return ewma_volatility

    def get_composite_volatility(self, measures: VolatilityMeasures) -> float:
        """
        Calculate composite volatility as weighted average of all 4 measures.

        Weights: Equal (25% each) - can be customized
        """
        if (measures.bollinger_bandwidth == 0 and
            measures.garman_klass == 0 and
            measures.atr == 0 and
            measures.ewma == 0):
            return 0.0

        # Normalize ATR to percentage if needed
        # This is a simplified normalization
        normalized_atr = measures.atr * 100 if measures.atr > 0 else 0

        # Equal weights
        composite = (
            measures.bollinger_bandwidth * 0.25 +
            measures.garman_klass * 0.25 +
            normalized_atr * 0.25 +
            measures.ewma * 0.25
        )

        return composite
