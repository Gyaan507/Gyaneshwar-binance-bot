"""
Input validation utilities for the trading bot
"""
import re
from typing import Union, List, Optional
from decimal import Decimal, InvalidOperation

class InputValidator:
    """Validates trading inputs"""
    
    # Common trading symbols pattern
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}USDT$')
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        if not isinstance(symbol, str):
            return False
        return bool(InputValidator.SYMBOL_PATTERN.match(symbol.upper()))
    
    @staticmethod
    def validate_quantity(quantity: Union[str, float, int]) -> bool:
        """Validate order quantity"""
        try:
            qty = Decimal(str(quantity))
            return qty > 0
        except (InvalidOperation, ValueError):
            return False
    
    @staticmethod
    def validate_price(price: Union[str, float, int]) -> bool:
        """Validate price value"""
        try:
            price_val = Decimal(str(price))
            return price_val > 0
        except (InvalidOperation, ValueError):
            return False
    
    @staticmethod
    def validate_side(side: str) -> bool:
        """Validate order side (BUY/SELL)"""
        return side.upper() in ['BUY', 'SELL']
    
    @staticmethod
    def validate_order_type(order_type: str) -> bool:
        """Validate order type"""
        valid_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET']
        return order_type.upper() in valid_types
    
    @staticmethod
    def validate_time_in_force(tif: str) -> bool:
        """Validate time in force parameter"""
        valid_tif = ['GTC', 'IOC', 'FOK', 'GTX']
        return tif.upper() in valid_tif
    
    @classmethod
    def validate_basic_order(cls, symbol: str, side: str, quantity: Union[str, float]) -> List[str]:
        """Validate basic order parameters and return list of errors"""
        errors = []
        
        if not cls.validate_symbol(symbol):
            errors.append(f"Invalid symbol format: {symbol}")
        
        if not cls.validate_side(side):
            errors.append(f"Invalid side: {side}. Must be BUY or SELL")
        
        if not cls.validate_quantity(quantity):
            errors.append(f"Invalid quantity: {quantity}. Must be positive number")
        
        return errors
    
    @classmethod
    def validate_limit_order(cls, symbol: str, side: str, quantity: Union[str, float], 
                           price: Union[str, float]) -> List[str]:
        """Validate limit order parameters"""
        errors = cls.validate_basic_order(symbol, side, quantity)
        
        if not cls.validate_price(price):
            errors.append(f"Invalid price: {price}. Must be positive number")
        
        return errors
