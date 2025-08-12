"""
Output formatting utilities for better user experience
"""
from datetime import datetime
from typing import Dict, Any
import json

class OutputFormatter:
    """Formats trading bot output for better readability"""
    
    @staticmethod
    def format_price(price: float, symbol: str = "USDT") -> str:
        """Format price with proper currency symbol"""
        if symbol.endswith("USDT"):
            return f"${price:,.2f}"
        return f"{price:,.8f}"
    
    @staticmethod
    def format_quantity(quantity: float) -> str:
        """Format quantity with appropriate decimal places"""
        if quantity >= 1:
            return f"{quantity:,.3f}"
        return f"{quantity:.6f}"
    
    @staticmethod
    def print_header(title: str):
        """Print a formatted header"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    @staticmethod
    def print_order_summary(order_type: str, symbol: str, side: str, 
                          quantity: float, price: float = None):
        """Print a clean order summary"""
        print(f"\n📊 {order_type.upper()} ORDER SUMMARY")
        print("-" * 30)
        print(f"Symbol:    {symbol}")
        print(f"Side:      {side}")
        print(f"Quantity:  {OutputFormatter.format_quantity(quantity)}")
        if price:
            print(f"Price:     {OutputFormatter.format_price(price)}")
        print(f"Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    @staticmethod
    def print_success(order_id: str, message: str = "Order placed successfully"):
        """Print success message"""
        print(f"\n✅ {message}")
        print(f"Order ID: {order_id}")
        print("-" * 30)
    
    @staticmethod
    def print_error(error_msg: str):
        """Print error message"""
        print(f"\n❌ ERROR: {error_msg}")
        print("-" * 30)
    
    @staticmethod
    def print_current_price(symbol: str, price: float):
        """Print current market price"""
        formatted_price = OutputFormatter.format_price(price)
        print(f"\n💰 Current {symbol} Price: {formatted_price}")
