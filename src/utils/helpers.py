"""
Helper functions and utilities for the trading system.

This module provides general utility functions used throughout the system.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import os


class FileHelper:
    """File and directory utilities."""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """
        Ensure directory exists.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created
        """
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                return True
            except Exception as e:
                print(f"Error creating directory {path}: {e}")
                return False
        return True
    
    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str) -> bool:
        """
        Save data to JSON file.
        
        Args:
            data: Data to save
            filepath: File path
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")
            return False
    
    @staticmethod
    def load_json(filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load data from JSON file.
        
        Args:
            filepath: File path
            
        Returns:
            Dictionary or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {filepath}: {e}")
            return None


class DateTimeHelper:
    """Date and time utilities."""
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp as ISO string."""
        return datetime.now().isoformat()
    
    @staticmethod
    def parse_timestamp(ts: str) -> datetime:
        """
        Parse timestamp string.
        
        Args:
            ts: Timestamp string
            
        Returns:
            Datetime object
        """
        return datetime.fromisoformat(ts)
    
    @staticmethod
    def get_date_range(start: datetime, end: datetime) -> Tuple[int, int, int]:
        """
        Get date range statistics.
        
        Args:
            start: Start date
            end: End date
            
        Returns:
            Tuple of (days, weeks, months)
        """
        delta = end - start
        days = delta.days
        weeks = days // 7
        months = days // 30
        
        return days, weeks, months
    
    @staticmethod
    def get_trading_days(start: datetime, end: datetime) -> int:
        """
        Get approximate trading days between dates.
        
        Args:
            start: Start date
            end: End date
            
        Returns:
            Number of trading days (approx)
        """
        total_days = (end - start).days
        # Approximate: 5/7 of days are trading days
        return int(total_days * (5 / 7))


class MathHelper:
    """Mathematical utilities."""
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        Safely divide two numbers.
        
        Args:
            numerator: Numerator
            denominator: Denominator
            default: Default value if denominator is 0
            
        Returns:
            Division result or default
        """
        if denominator == 0:
            return default
        return numerator / denominator
    
    @staticmethod
    def calculate_percentage_change(old: float, new: float) -> float:
        """
        Calculate percentage change.
        
        Args:
            old: Old value
            new: New value
            
        Returns:
            Percentage change
        """
        if old == 0:
            return 0.0
        return ((new - old) / old) * 100
    
    @staticmethod
    def round_to_decimals(value: float, decimals: int = 2) -> float:
        """
        Round to specific decimal places.
        
        Args:
            value: Value to round
            decimals: Number of decimal places
            
        Returns:
            Rounded value
        """
        return round(value, decimals)
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """
        Clamp value between min and max.
        
        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Clamped value
        """
        return max(min_val, min(value, max_val))


class ConfigHelper:
    """Configuration utilities."""
    
    @staticmethod
    def load_env_config() -> Dict[str, str]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dictionary of config values
        """
        config = {}
        env_vars = [
            'EXCHANGE_API_KEY',
            'EXCHANGE_API_SECRET',
            'EXCHANGE_NAME',
            'INITIAL_BALANCE',
            'DATABASE_URL',
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                config[var] = value
        
        return config
    
    @staticmethod
    def load_config_file(filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration from file.
        
        Args:
            filepath: Path to config file
            
        Returns:
            Configuration dictionary or None
        """
        if filepath.endswith('.json'):
            return FileHelper.load_json(filepath)
        elif filepath.endswith('.env'):
            return ConfigHelper._load_env_file(filepath)
        return None
    
    @staticmethod
    def _load_env_file(filepath: str) -> Dict[str, str]:
        """Load .env file format."""
        config = {}
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            print(f"Error loading .env file: {e}")
        
        return config


class ValidationHelper:
    """Data validation utilities."""
    
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """
        Validate trading symbol format.
        
        Args:
            symbol: Symbol string
            
        Returns:
            True if valid
        """
        return bool(symbol) and len(symbol) >= 3
    
    @staticmethod
    def is_valid_price(price: float) -> bool:
        """
        Validate price value.
        
        Args:
            price: Price value
            
        Returns:
            True if valid
        """
        return isinstance(price, (int, float)) and price > 0
    
    @staticmethod
    def is_valid_quantity(quantity: float) -> bool:
        """
        Validate quantity value.
        
        Args:
            quantity: Quantity value
            
        Returns:
            True if valid
        """
        return isinstance(quantity, (int, float)) and quantity > 0
    
    @staticmethod
    def validate_trade_params(
        symbol: str,
        price: float,
        quantity: float,
        side: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate complete trade parameters.
        
        Args:
            symbol: Trading symbol
            price: Trade price
            quantity: Trade quantity
            side: BUY or SELL
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not ValidationHelper.is_valid_symbol(symbol):
            return False, "Invalid symbol"
        
        if not ValidationHelper.is_valid_price(price):
            return False, "Invalid price"
        
        if not ValidationHelper.is_valid_quantity(quantity):
            return False, "Invalid quantity"
        
        if side not in ['BUY', 'SELL']:
            return False, "Invalid side"
        
        return True, None


class FormatHelper:
    """Output formatting utilities."""
    
    @staticmethod
    def format_currency(value: float, currency: str = "USD") -> str:
        """
        Format value as currency.
        
        Args:
            value: Value to format
            currency: Currency code
            
        Returns:
            Formatted string
        """
        if currency == "USD":
            return f"${value:,.2f}"
        return f"{value:,.2f} {currency}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """
        Format value as percentage.
        
        Args:
            value: Value to format
            decimals: Decimal places
            
        Returns:
            Formatted string
        """
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """
        Format number with decimals.
        
        Args:
            value: Value to format
            decimals: Decimal places
            
        Returns:
            Formatted string
        """
        return f"{value:.{decimals}f}"
