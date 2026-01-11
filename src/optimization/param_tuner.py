"""
Parameter tuning and adjustment utilities.

This module provides tools for dynamically adjusting parameters during
strategy execution.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import numpy as np


@dataclass
class ParameterAdjustment:
    """Configuration for parameter adjustment."""
    
    parameter_name: str
    adjustment_type: str  # linear, exponential, dynamic
    sensitivity: float  # How much to adjust (0-1)
    min_value: float
    max_value: float
    trigger_metric: str  # Metric that triggers adjustment


class ParameterTuner:
    """
    Dynamically adjust strategy parameters based on performance.
    
    Modifies parameters during execution to adapt to market conditions.
    """
    
    def __init__(self, base_params: Dict[str, float]):
        """
        Initialize parameter tuner.
        
        Args:
            base_params: Initial parameter values
        """
        self.base_params = base_params.copy()
        self.current_params = base_params.copy()
        self.adjustment_history: List[Dict[str, Any]] = []
    
    def adjust_linear(
        self,
        param_name: str,
        current_value: float,
        direction: int,
        adjustment: float
    ) -> float:
        """
        Linear adjustment.
        
        Args:
            param_name: Parameter name
            current_value: Current value
            direction: +1 or -1
            adjustment: Amount to adjust
            
        Returns:
            New parameter value
        """
        new_value = current_value + (direction * adjustment)
        return new_value
    
    def adjust_exponential(
        self,
        param_name: str,
        current_value: float,
        direction: int,
        factor: float
    ) -> float:
        """
        Exponential adjustment.
        
        Args:
            param_name: Parameter name
            current_value: Current value
            direction: +1 or -1
            factor: Multiplication factor
            
        Returns:
            New parameter value
        """
        if direction > 0:
            new_value = current_value * factor
        else:
            new_value = current_value / factor
        
        return new_value
    
    def adjust_adaptive(
        self,
        param_name: str,
        current_value: float,
        performance_metric: float,
        target_metric: float,
        sensitivity: float = 0.1
    ) -> float:
        """
        Adaptive adjustment based on performance.
        
        Args:
            param_name: Parameter name
            current_value: Current value
            performance_metric: Current performance
            target_metric: Target performance
            sensitivity: Adjustment sensitivity
            
        Returns:
            New parameter value
        """
        # Calculate deviation from target
        deviation = (performance_metric - target_metric) / target_metric if target_metric != 0 else 0
        
        # Calculate adjustment
        adjustment = current_value * deviation * sensitivity
        new_value = current_value + adjustment
        
        return new_value
    
    def update_param(
        self,
        param_name: str,
        new_value: float,
        min_value: float,
        max_value: float
    ) -> float:
        """
        Update a parameter with bounds checking.
        
        Args:
            param_name: Parameter name
            new_value: New value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Constrained parameter value
        """
        # Constrain value
        constrained_value = max(min_value, min(new_value, max_value))
        
        # Store in adjustment history
        self.adjustment_history.append({
            'parameter': param_name,
            'old_value': self.current_params.get(param_name),
            'new_value': constrained_value,
        })
        
        # Update current params
        self.current_params[param_name] = constrained_value
        
        return constrained_value
    
    def scale_parameters(
        self,
        scaling_factor: float,
        exclude: List[str] = None
    ) -> Dict[str, float]:
        """
        Scale all parameters by a factor.
        
        Args:
            scaling_factor: Factor to multiply by
            exclude: Parameters to exclude
            
        Returns:
            Updated parameters
        """
        exclude = exclude or []
        
        for param_name, value in self.current_params.items():
            if param_name not in exclude and isinstance(value, (int, float)):
                self.current_params[param_name] = value * scaling_factor
        
        return self.current_params.copy()
    
    def reset_to_base(self) -> None:
        """Reset parameters to base values."""
        self.current_params = self.base_params.copy()
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get current parameter value."""
        return self.current_params.get(name, default)
    
    def get_all_parameters(self) -> Dict[str, float]:
        """Get all current parameters."""
        return self.current_params.copy()
    
    def get_adjustment_count(self) -> int:
        """Get total number of adjustments made."""
        return len(self.adjustment_history)
    
    def get_adjustment_history(self) -> List[Dict[str, Any]]:
        """Get adjustment history."""
        return self.adjustment_history.copy()


class DynamicParameterAdjuster:
    """
    Automatically adjust parameters based on market conditions.
    
    Monitors performance metrics and adjusts parameters dynamically.
    """
    
    def __init__(self, tuner: ParameterTuner):
        """
        Initialize dynamic adjuster.
        
        Args:
            tuner: ParameterTuner instance
        """
        self.tuner = tuner
        self.adjustment_rules: List[ParameterAdjustment] = []
    
    def add_rule(self, rule: ParameterAdjustment) -> None:
        """
        Add adjustment rule.
        
        Args:
            rule: ParameterAdjustment rule
        """
        self.adjustment_rules.append(rule)
    
    def evaluate(self, metrics: Dict[str, Any]) -> None:
        """
        Evaluate metrics and apply adjustments.
        
        Args:
            metrics: Current performance metrics
        """
        for rule in self.adjustment_rules:
            trigger_value = metrics.get(rule.trigger_metric)
            
            if trigger_value is None:
                continue
            
            current_value = self.tuner.get_parameter(rule.parameter_name)
            
            if rule.adjustment_type == "linear":
                direction = 1 if trigger_value > 0 else -1
                new_value = self.tuner.adjust_linear(
                    rule.parameter_name,
                    current_value,
                    direction,
                    rule.sensitivity
                )
            
            elif rule.adjustment_type == "exponential":
                direction = 1 if trigger_value > 0 else -1
                factor = 1 + rule.sensitivity
                new_value = self.tuner.adjust_exponential(
                    rule.parameter_name,
                    current_value,
                    direction,
                    factor
                )
            
            else:  # dynamic
                new_value = self.tuner.adjust_adaptive(
                    rule.parameter_name,
                    current_value,
                    trigger_value,
                    0,  # target
                    rule.sensitivity
                )
            
            # Apply constraints
            self.tuner.update_param(
                rule.parameter_name,
                new_value,
                rule.min_value,
                rule.max_value
            )
