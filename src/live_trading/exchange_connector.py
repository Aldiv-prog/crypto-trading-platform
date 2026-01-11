"""
Exchange connector for live market data and order execution.

This module provides interfaces to cryptocurrency exchanges and brokers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExchangeConfig:
    """Configuration for exchange connection."""
    
    api_key: str
    api_secret: str
    exchange_name: str
    sandbox: bool = False
    rate_limit: int = 1000  # milliseconds


class ExchangeConnector(ABC):
    """
    Abstract base class for exchange connectors.
    
    Implements unified interface for different exchanges.
    """
    
    def __init__(self, config: ExchangeConfig):
        """
        Initialize exchange connector.
        
        Args:
            config: Exchange configuration
        """
        self.config = config
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to exchange.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from exchange.
        
        Returns:
            True if disconnection successful
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balances.
        
        Returns:
            Dictionary with asset balances
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order information
        """
        pass
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place order on exchange.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            order_type: MARKET or LIMIT
            quantity: Order quantity
            price: Order price (for LIMIT orders)
            **kwargs: Additional order parameters
            
        Returns:
            Order response
        """
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades for symbol.
        
        Args:
            symbol: Trading pair
            limit: Number of trades to fetch
            
        Returns:
            List of trades
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker information.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker information
        """
        pass
    
    @abstractmethod
    def get_candlesticks(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Get candlestick data.
        
        Args:
            symbol: Trading pair
            interval: Candle interval
            limit: Number of candles
            
        Returns:
            List of candlestick data
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if connected to exchange."""
        return self.connected
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ExchangeConnector({self.config.exchange_name})"


class MockExchangeConnector(ExchangeConnector):
    """
    Mock exchange connector for testing and paper trading.
    """
    
    def __init__(self, config: ExchangeConfig):
        """Initialize mock connector."""
        super().__init__(config)
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.balances: Dict[str, float] = {
            'USDT': 10000.0,
            'BTC': 0.0,
            'ETH': 0.0,
        }
        self.order_counter = 0
    
    def connect(self) -> bool:
        """Connect mock exchange."""
        self.connected = True
        print(f"Connected to mock {self.config.exchange_name}")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect mock exchange."""
        self.connected = False
        return True
    
    def get_account_balance(self) -> Dict[str, float]:
        """Get mock balances."""
        return self.balances.copy()
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get mock open orders."""
        orders = list(self.orders.values())
        if symbol:
            orders = [o for o in orders if o['symbol'] == symbol]
        return orders
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get mock order status."""
        return self.orders.get(order_id, {})
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Place mock order."""
        self.order_counter += 1
        order_id = str(self.order_counter)
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'price': price or 0.0,
            'timestamp': datetime.now().isoformat(),
            'status': 'open',
        }
        
        self.orders[order_id] = order
        return order
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel mock order."""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'cancelled'
            return True
        return False
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get mock recent trades."""
        return []
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get mock ticker."""
        return {
            'symbol': symbol,
            'bid': 100.0,
            'ask': 100.1,
            'last': 100.05,
        }
    
    def get_candlesticks(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get mock candlesticks."""
        return []
