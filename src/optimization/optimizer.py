"""
Parameter optimization engine for trading strategies.

This module provides tools for optimizing strategy parameters using
historical data.
"""

from typing import Dict, List, Any, Callable, Tuple
from dataclasses import dataclass
import itertools


@dataclass
class OptimizationParam:
    """Parameter configuration for optimization."""
    
    name: str
    min_value: float
    max_value: float
    step: float
    
    def get_values(self) -> List[float]:
        """Get all values for this parameter."""
        values = []
        current = self.min_value
        while current <= self.max_value:
            values.append(current)
            current += self.step
        return values


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    
    parameters: Dict[str, float]
    fitness_score: float
    metrics: Dict[str, Any]
    
    def __lt__(self, other):
        """Compare by fitness score (higher is better)."""
        return self.fitness_score > other.fitness_score


class Optimizer:
    """
    Optimize strategy parameters.
    
    Searches parameter space to find optimal configurations.
    """
    
    def __init__(
        self,
        strategy_runner: Callable,
        fitness_func: Callable,
        params: List[OptimizationParam],
        verbose: bool = True
    ):
        """
        Initialize optimizer.
        
        Args:
            strategy_runner: Function that runs strategy with params
            fitness_func: Function that calculates fitness score
            params: List of parameters to optimize
            verbose: Print optimization progress
        """
        self.strategy_runner = strategy_runner
        self.fitness_func = fitness_func
        self.params = params
        self.verbose = verbose
        self.results: List[OptimizationResult] = []
    
    def grid_search(self, top_n: int = 10) -> List[OptimizationResult]:
        """
        Grid search optimization.
        
        Tests all combinations of parameter values.
        
        Args:
            top_n: Return top N results
            
        Returns:
            List of optimization results
        """
        if self.verbose:
            print("Starting grid search optimization...")
        
        param_values = [p.get_values() for p in self.params]
        total_combinations = 1
        for values in param_values:
            total_combinations *= len(values)
        
        if self.verbose:
            print(f"Total combinations: {total_combinations}")
        
        self.results = []
        combination_count = 0
        
        for values in itertools.product(*param_values):
            combination_count += 1
            
            # Create parameter dict
            params_dict = {self.params[i].name: values[i] for i in range(len(self.params))}
            
            # Run strategy with these parameters
            try:
                metrics = self.strategy_runner(params_dict)
                
                # Calculate fitness score
                fitness_score = self.fitness_func(metrics)
                
                # Store result
                result = OptimizationResult(
                    parameters=params_dict,
                    fitness_score=fitness_score,
                    metrics=metrics
                )
                self.results.append(result)
                
                if self.verbose and combination_count % max(1, total_combinations // 10) == 0:
                    print(f"  Progress: {combination_count}/{total_combinations} ({fitness_score:.4f})")
            
            except Exception as e:
                if self.verbose:
                    print(f"  Error with params {params_dict}: {e}")
                continue
        
        # Sort by fitness score
        self.results.sort()
        
        if self.verbose:
            print(f"Optimization complete. Top result: {self.results[0].fitness_score:.4f}")
        
        return self.results[:top_n]
    
    def random_search(
        self,
        iterations: int = 100,
        top_n: int = 10
    ) -> List[OptimizationResult]:
        """
        Random search optimization.
        
        Tests random parameter combinations.
        
        Args:
            iterations: Number of random combinations to test
            top_n: Return top N results
            
        Returns:
            List of optimization results
        """
        import random
        
        if self.verbose:
            print(f"Starting random search with {iterations} iterations...")
        
        self.results = []
        
        for i in range(iterations):
            # Generate random parameters
            params_dict = {}
            for param in self.params:
                value = random.uniform(param.min_value, param.max_value)
                params_dict[param.name] = value
            
            # Run strategy
            try:
                metrics = self.strategy_runner(params_dict)
                fitness_score = self.fitness_func(metrics)
                
                result = OptimizationResult(
                    parameters=params_dict,
                    fitness_score=fitness_score,
                    metrics=metrics
                )
                self.results.append(result)
                
                if self.verbose and (i + 1) % max(1, iterations // 10) == 0:
                    print(f"  Progress: {i + 1}/{iterations} (best: {self.results[0].fitness_score:.4f})")
            
            except Exception as e:
                if self.verbose:
                    print(f"  Error with params {params_dict}: {e}")
                continue
        
        # Sort by fitness score
        self.results.sort()
        
        if self.verbose:
            print(f"Search complete. Best result: {self.results[0].fitness_score:.4f}")
        
        return self.results[:top_n]
    
    def get_best(self) -> OptimizationResult:
        """Get best result."""
        if not self.results:
            return None
        return self.results[0]
    
    def get_top_n(self, n: int) -> List[OptimizationResult]:
        """Get top N results."""
        return self.results[:n]


class FitnessCalculator:
    """Calculate fitness scores for optimization."""
    
    @staticmethod
    def sharpe_ratio(metrics: Dict[str, Any]) -> float:
        """Use Sharpe ratio as fitness."""
        return metrics.get('sharpe_ratio', 0.0)
    
    @staticmethod
    def profit_factor(metrics: Dict[str, Any]) -> float:
        """Use profit factor as fitness."""
        return metrics.get('profit_factor', 0.0)
    
    @staticmethod
    def return_per_drawdown(metrics: Dict[str, Any]) -> float:
        """Return per unit of drawdown."""
        annual_return = metrics.get('annual_return_percent', 0.0)
        max_dd = metrics.get('max_drawdown_percent', 1.0)
        
        if max_dd == 0:
            return 0.0
        
        return annual_return / max_dd
    
    @staticmethod
    def win_rate_weighted(metrics: Dict[str, Any]) -> float:
        """Weight by win rate and profit factor."""
        win_rate = metrics.get('win_rate', 0.0)
        profit_factor = metrics.get('profit_factor', 1.0)
        
        return (win_rate / 100.0) * profit_factor
    
    @staticmethod
    def custom_score(
        metrics: Dict[str, Any],
        weights: Dict[str, float]
    ) -> float:
        """Calculate custom weighted score."""
        score = 0.0
        for metric_name, weight in weights.items():
            value = metrics.get(metric_name, 0.0)
            score += value * weight
        return score
