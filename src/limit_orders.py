"""
Limit Orders Implementation
"""
import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.binance_client import BinanceFuturesClient
from src.utils.validator import InputValidator
from src.utils.logger import BotLogger

class LimitOrderBot:
    """Handles limit order operations"""
    
    def __init__(self, testnet: bool = True):
        self.client = BinanceFuturesClient(testnet=testnet)
        self.logger = BotLogger()
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, 
                         price: float, time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Order response from Binance API
        """
        # Validate inputs
        errors = InputValidator.validate_limit_order(symbol, side, quantity, price)
        if errors:
            error_msg = f"Validation errors: {', '.join(errors)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not InputValidator.validate_time_in_force(time_in_force):
            raise ValueError(f"Invalid time in force: {time_in_force}")
        
        try:
            # Get current price for comparison
            current_price = self.client.get_ticker_price(symbol)
            self.logger.info(f"Current {symbol} price: {current_price}, Limit price: {price}")
            
            # Place limit order
            order_response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force
            )
            
            self.logger.info(f"Limit order placed successfully: {order_response}")
            return order_response
            
        except Exception as e:
            self.logger.log_error(e, {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': 'LIMIT'
            })
            raise
    
    def cancel_limit_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel a limit order"""
        try:
            result = self.client.cancel_order(symbol, order_id)
            self.logger.info(f"Limit order {order_id} cancelled successfully")
            return result
        except Exception as e:
            self.logger.log_error(e, {'symbol': symbol, 'order_id': order_id})
            raise

def main():
    """CLI interface for limit orders"""
    if len(sys.argv) not in [5, 6]:
        print("Usage: python src/limit_orders.py <SYMBOL> <SIDE> <QUANTITY> <PRICE> [TIME_IN_FORCE]")
        print("Example: python src/limit_orders.py BTCUSDT BUY 0.01 45000 GTC")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    quantity = float(sys.argv[3])
    price = float(sys.argv[4])
    time_in_force = sys.argv[5] if len(sys.argv) == 6 else 'GTC'
    
    try:
        bot = LimitOrderBot(testnet=True)
        result = bot.place_limit_order(symbol, side, quantity, price, time_in_force)
        print(f"Limit order placed successfully: {result['orderId']}")
        
    except Exception as e:
        print(f"Error placing limit order: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
