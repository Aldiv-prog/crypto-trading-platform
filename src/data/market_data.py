"""
Market data handling and management.

This module provides utilities for loading, managing, and processing market data
from various sources.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import csv

from .data_models import Candle, MarketData

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    ConfigDict,
    validator,
)

class MarketDataLoader:
    """Load market data from various sources."""
    
    @staticmethod
    def load_from_csv(
        filepath: str,
        symbol: str,
        timeframe: str
    ) -> MarketData:
        """
        Load market data from CSV file.
        
        CSV format expected: timestamp, open, high, low, close, volume
        
        Args:
            filepath: Path to CSV file
            symbol: Trading pair symbol
            timeframe: Candlestick timeframe
            
        Returns:
            MarketData object
        """
        candles = []
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    candle = Candle(
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=float(row['volume']),
                    )
                    candles.append(candle)
                except (KeyError, ValueError) as e:
                    print(f"Error parsing row: {row}, error: {e}")
                    continue
        
        return MarketData(symbol=symbol, timeframe=timeframe, candles=candles)
    
    @staticmethod
    def load_from_json(
        filepath: str,
        symbol: str,
        timeframe: str
    ) -> MarketData:
        """
        Load market data from JSON file.
        
        Args:
            filepath: Path to JSON file
            symbol: Trading pair symbol
            timeframe: Candlestick timeframe
            
        Returns:
            MarketData object
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        candles = []
        for item in data.get('candles', []):
            try:
                candle = Candle(
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=float(item['volume']),
                )
                candles.append(candle)
            except (KeyError, ValueError) as e:
                print(f"Error parsing item: {item}, error: {e}")
                continue
        
        return MarketData(symbol=symbol, timeframe=timeframe, candles=candles)
    
    @staticmethod
    def load_from_list(
        data: List[Dict[str, Any]],
        symbol: str,
        timeframe: str
    ) -> MarketData:
        """
        Load market data from list of dictionaries.
        
        Args:
            data: List of candle dictionaries
            symbol: Trading pair symbol
            timeframe: Candlestick timeframe
            
        Returns:
            MarketData object
        """
        candles = []
        
        for item in data:
            try:
                candle = Candle(
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=float(item['volume']),
                )
                candles.append(candle)
            except (KeyError, ValueError) as e:
                print(f"Error parsing item: {item}, error: {e}")
                continue
        
        return MarketData(symbol=symbol, timeframe=timeframe, candles=candles)


class MarketDataCache:
    """Cache and manage market data in memory."""
    
    def __init__(self):
        """Initialize the cache."""
        self.data: Dict[str, MarketData] = {}
    
    def add(self, symbol: str, market_data: MarketData) -> None:
        """
        Add market data to cache.
        
        Args:
            symbol: Trading pair symbol
            market_data: MarketData object
        """
        self.data[symbol] = market_data
    
    def get(self, symbol: str) -> Optional[MarketData]:
        """
        Get market data from cache.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            MarketData object or None if not found
        """
        return self.data.get(symbol)
    
    def has(self, symbol: str) -> bool:
        """
        Check if symbol is in cache.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if symbol is cached
        """
        return symbol in self.data
    
    def remove(self, symbol: str) -> bool:
        """
        Remove symbol from cache.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if symbol was removed
        """
        if symbol in self.data:
            del self.data[symbol]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.data.clear()
    
    def get_symbols(self) -> List[str]:
        """Get all cached symbols."""
        return list(self.data.keys())
    
    def get_size(self) -> int:
        """Get number of cached symbols."""
        return len(self.data)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save cache to JSON file.
        
        Args:
            filepath: Path to save file
        """
        cache_data = {}
        for symbol, market_data in self.data.items():
            cache_data[symbol] = market_data.to_dict()
        
        with open(filepath, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def load_from_file(self, filepath: str) -> None:
        """
        Load cache from JSON file.
        
        Args:
            filepath: Path to load file
        """
        with open(filepath, 'r') as f:
            cache_data = json.load(f)
        
        for symbol, data in cache_data.items():
            candles = []
            for item in data.get('candles', []):
                candle = Candle(
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=float(item['volume']),
                )
                candles.append(candle)
            
            market_data = MarketData(
                symbol=symbol,
                timeframe=data.get('timeframe', '1h'),
                candles=candles
            )
            self.add(symbol, market_data)
