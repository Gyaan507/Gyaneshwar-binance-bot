"""
Logging utilities for the trading bot
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict

class BotLogger:
    """Custom logger for the trading bot"""
    
    def __init__(self, log_file: str = 'bot.log', log_level: str = 'INFO'):
        self.log_file = log_file
        self.logger = logging.getLogger('BinanceFuturesBot')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_order(self, order_type: str, symbol: str, side: str, 
                  quantity: float, price: float = None, **kwargs):
        """Log order placement"""
        order_data = {
            'type': order_type,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(f"ORDER_PLACED: {order_data}")
    
    def log_execution(self, order_id: str, symbol: str, executed_qty: float, 
                     executed_price: float):
        """Log order execution"""
        execution_data = {
            'order_id': order_id,
            'symbol': symbol,
            'executed_qty': executed_qty,
            'executed_price': executed_price,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(f"ORDER_EXECUTED: {execution_data}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with context"""
        error_data = {
            'error': str(error),
            'type': type(error).__name__,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        self.logger.error(f"ERROR: {error_data}")
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
