"""
Live trade executor for executing trading strategies in real-time.

This module manages live order execution and position management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .exchange_connector import ExchangeConnector
from ..core.position import Position, PositionMetrics


class ExecutionMode(Enum):
    """Execution mode for trades."""
    
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class TradeExecutor:
    """
    Executes trades through exchange connector.
    
    Manages order placement, cancellation, and position tracking
    for live trading.
    """
    
    def __init__(
        self,
        exchange: ExchangeConnector,
        mode: ExecutionMode = ExecutionMode.PAPER
    ):
        """
        Initialize trade executor.
        
        Args:
            exchange: Exchange connector instance
            mode: Execution mode (live, paper, backtest)
        """
        self.exchange = exchange
        self.mode = mode
        self.active_positions: Dict[str, Position] = {}
        self.completed_trades: List[Dict[str, Any]] = []
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
    
    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        **kwargs
    ) -> Optional[str]:
        """
        Open a new position.
        
        Args:
            symbol: Trading pair
            side: LONG or SHORT
            quantity: Position quantity
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            **kwargs: Additional parameters
            
        Returns:
            Position ID or None if failed
        """
        # Place entry order
        order_result = self._place_entry_order(symbol, side, quantity, entry_price)
        
        if not order_result:
            print(f"Failed to open position {symbol}")
            return None
        
        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        position.order_id = order_result.get('order_id')
        self.active_positions[position.id] = position
        
        print(f"Opened {side} position {position.id}: {symbol} @ {entry_price}")
        
        return position.id
    
    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "manual"
    ) -> bool:
        """
        Close an open position.
        
        Args:
            position_id: Position ID
            exit_price: Exit price
            reason: Reason for closing
            
        Returns:
            True if closed successfully
        """
        position = self.active_positions.get(position_id)
        if not position:
            return False
        
        # Cancel any pending orders
        if position.order_id:
            self._cancel_order(position.symbol, position.order_id)
        
        # Calculate metrics
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        
        # Record completed trade
        self.completed_trades.append({
            'position_id': position_id,
            'symbol': position.symbol,
            'side': position.side,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'pnl': position.get_pnl(),
            'pnl_percent': position.get_pnl_percent(),
            'entry_time': position.entry_time,
            'exit_time': position.exit_time,
            'reason': reason,
        })
        
        # Remove from active positions
        del self.active_positions[position_id]
        
        print(f"Closed position {position_id}: PnL = {position.get_pnl():.2f}")
        
        return True
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str = "LIMIT"
    ) -> Optional[str]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
            order_type: Order type
            
        Returns:
            Order ID or None
        """
        if self.mode == ExecutionMode.BACKTEST:
            order_id = f"mock_{len(self.pending_orders)}"
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'type': order_type,
                'timestamp': datetime.now(),
            }
            return order_id
        
        order = self.exchange.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        if order:
            order_id = order.get('order_id')
            self.pending_orders[order_id] = order
            return order_id
        
        return None
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            
        Returns:
            True if cancelled successfully
        """
        return self._cancel_order(symbol, order_id)
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """
        Get position by ID.
        
        Args:
            position_id: Position ID
            
        Returns:
            Position object or None
        """
        return self.active_positions.get(position_id)
    
    def get_active_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        Get all active positions.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of active positions
        """
        positions = list(self.active_positions.values())
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        return positions
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        
        Returns:
            Dictionary with balances
        """
        if self.mode == ExecutionMode.BACKTEST:
            return {}
        
        return self.exchange.get_account_balance()
    
    def update_position(
        self,
        position_id: str,
        current_price: float
    ) -> None:
        """
        Update position with current market price.
        
        Args:
            position_id: Position ID
            current_price: Current market price
        """
        position = self.active_positions.get(position_id)
        if position:
            position.update_price(current_price)
    
    def _place_entry_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Optional[Dict[str, Any]]:
        """Place entry order."""
        if self.mode == ExecutionMode.BACKTEST:
            return {
                'order_id': f'mock_{len(self.pending_orders)}',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
            }
        
        return self.exchange.place_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price
        )
    
    def _cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order."""
        if self.mode == ExecutionMode.BACKTEST:
            return order_id in self.pending_orders
        
        return self.exchange.cancel_order(symbol, order_id)
