"""
Market Orders Implementation
"""
import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.utils.validator import InputValidator
from src.utils.logger import BotLogger
from src.utils.formatter import OutputFormatter

class MarketOrderBot:
    """Handles market order operations"""
    
    def __init__(self, testnet: bool = True):
        self.client = BinanceFuturesClient(testnet=testnet)
        self.logger = BotLogger()
        self.formatter = OutputFormatter()
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            
        Returns:
            Order response from Binance API
        """
        # Validate inputs
        errors = InputValidator.validate_basic_order(symbol, side, quantity)
        if errors:
            error_msg = f"Validation errors: {', '.join(errors)}"
            self.logger.error(error_msg)
            self.formatter.print_error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Get current price for logging
            current_price = self.client.get_ticker_price(symbol)
            self.logger.info(f"Current {symbol} price: {current_price}")
            
            self.formatter.print_current_price(symbol, current_price)
            
            self.formatter.print_order_summary("MARKET", symbol, side, quantity)
            
            # Place market order
            order_response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            self.logger.info(f"Market order placed successfully: {order_response}")
            
            self.formatter.print_success(str(order_response['orderId']))
            
            return order_response
            
        except Exception as e:
            self.logger.log_error(e, {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'order_type': 'MARKET'
            })
            self.formatter.print_error(str(e))
            raise

def main():
    """CLI interface for market orders"""
    if len(sys.argv) != 4:
        print("Usage: python src/market_orders.py <SYMBOL> <SIDE> <QUANTITY>")
        print("Example: python src/market_orders.py BTCUSDT BUY 0.01")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    quantity = float(sys.argv[3])
    
    OutputFormatter.print_header("BINANCE FUTURES TRADING BOT - MARKET ORDERS")
    
    try:
        bot = MarketOrderBot(testnet=True)
        result = bot.place_market_order(symbol, side, quantity)
        
    except Exception as e:
        print(f"\nError placing market order: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
