"""
Logging and debugging utilities.

This module provides logging configuration and debugging helpers.
"""

import logging
from typing import Optional
from datetime import datetime


class Logger:
    """
    Centralized logging system for the trading system.
    
    Provides logging to file and console with different levels.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize logger."""
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('trading_system')
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def setup_file_logging(self, filename: str, level: int = logging.DEBUG) -> None:
        """
        Setup file logging.
        
        Args:
            filename: Log file path
            level: Logging level
        """
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


class DebugTracer:
    """
    Debug tracer for tracking execution flow.
    
    Helps identify issues and understand execution path.
    """
    
    def __init__(self, enabled: bool = False):
        """
        Initialize debug tracer.
        
        Args:
            enabled: Enable tracing
        """
        self.enabled = enabled
        self.traces: list = []
    
    def trace(self, location: str, data: dict) -> None:
        """
        Record trace point.
        
        Args:
            location: Location identifier
            data: Data to trace
        """
        if not self.enabled:
            return
        
        trace_entry = {
            'timestamp': datetime.now().isoformat(),
            'location': location,
            'data': data,
        }
        self.traces.append(trace_entry)
    
    def get_traces(self) -> list:
        """Get all traces."""
        return self.traces.copy()
    
    def clear(self) -> None:
        """Clear all traces."""
        self.traces.clear()
    
    def export(self, filename: str) -> None:
        """Export traces to JSON file."""
        import json
        with open(filename, 'w') as f:
            json.dump(self.traces, f, indent=2)


class PerformanceMonitor:
    """
    Monitor system performance metrics.
    
    Tracks execution time, memory usage, and other performance indicators.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
    
    def start_timer(self, name: str) -> None:
        """Start performance timer."""
        self.metrics[f"{name}_start"] = datetime.now()
    
    def end_timer(self, name: str) -> float:
        """
        End performance timer.
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds
        """
        start_key = f"{name}_start"
        if start_key not in self.metrics:
            return 0.0
        
        elapsed = (datetime.now() - self.metrics[start_key]).total_seconds()
        self.metrics[f"{name}_elapsed"] = elapsed
        return elapsed
    
    def get_elapsed(self, name: str) -> float:
        """Get elapsed time for timer."""
        return self.metrics.get(f"{name}_elapsed", 0.0)
    
    def get_all_metrics(self) -> dict:
        """Get all performance metrics."""
        return self.metrics.copy()
    
    def print_report(self) -> None:
        """Print performance report."""
        print("\nPerformance Report")
        print("-" * 40)
        for key, value in self.metrics.items():
            if 'elapsed' in key:
                print(f"{key:30s}: {value:.4f}s")
