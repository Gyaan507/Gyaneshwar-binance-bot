"""
OCO (One-Cancels-the-Other) Orders Implementation
"""
import sys
import os
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.binance_client import BinanceFuturesClient
from src.utils.validator import InputValidator
from src.utils.logger import BotLogger

class OCOOrderBot:
    """Handles OCO (One-Cancels-the-Other) order operations"""
    
    def __init__(self, testnet: bool = True):
        self.client = BinanceFuturesClient(testnet=testnet)
        self.logger = BotLogger()
    
    def place_oco_order(self, symbol: str, side: str, quantity: float,
                       price: float, stop_price: float, stop_limit_price: float = None) -> List[Dict[str, Any]]:
        """
        Place an OCO order (Take Profit + Stop Loss)
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Take profit price
            stop_price: Stop loss trigger price
            stop_limit_price: Stop limit price (if None, uses stop_price)
            
        Returns:
            List of order responses
        """
        # Validate inputs
        errors = InputValidator.validate_limit_order(symbol, side, quantity, price)
        if not InputValidator.validate_price(stop_price):
            errors.append(f"Invalid stop price: {stop_price}")
        
        if errors:
            error_msg = f"Validation errors: {', '.join(errors)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if stop_limit_price is None:
            stop_limit_price = stop_price
        
        try:
            current_price = self.client.get_ticker_price(symbol)
            self.logger.info(f"Placing OCO order - Current: {current_price}, TP: {price}, SL: {stop_price}")
            
            orders = []
            
            # Determine opposite side for OCO orders
            opposite_side = 'SELL' if side == 'BUY' else 'BUY'
            
            # Place take profit order
            tp_order = self.client.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            orders.append(tp_order)
            self.logger.info(f"Take profit order placed: {tp_order['orderId']}")
            
            # Place stop loss order
            sl_order = self.client.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type='STOP',
                quantity=quantity,
                price=stop_limit_price,
                stopPrice=stop_price,
                timeInForce='GTC'
            )
            orders.append(sl_order)
            self.logger.info(f"Stop loss order placed: {sl_order['orderId']}")
            
            self.logger.info(f"OCO order group created successfully")
            return orders
            
        except Exception as e:
            self.logger.log_error(e, {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'stop_price': stop_price,
                'order_type': 'OCO'
            })
            raise
    
    def cancel_oco_orders(self, symbol: str, order_ids: List[int]) -> List[Dict[str, Any]]:
        """Cancel OCO order group"""
        results = []
        for order_id in order_ids:
            try:
                result = self.client.cancel_order(symbol, order_id)
                results.append(result)
                self.logger.info(f"OCO order {order_id} cancelled")
            except Exception as e:
                self.logger.log_error(e, {'symbol': symbol, 'order_id': order_id})
        return results

def main():
    """CLI interface for OCO orders"""
    if len(sys.argv) not in [6, 7]:
        print("Usage: python src/advanced/oco.py <SYMBOL> <SIDE> <QUANTITY> <TP_PRICE> <SL_PRICE> [SL_LIMIT_PRICE]")
        print("Example: python src/advanced/oco.py BTCUSDT BUY 0.01 46000 44000")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    quantity = float(sys.argv[3])
    tp_price = float(sys.argv[4])
    sl_price = float(sys.argv[5])
    sl_limit_price = float(sys.argv[6]) if len(sys.argv) == 7 else None
    
    try:
        bot = OCOOrderBot(testnet=True)
        orders = bot.place_oco_order(symbol, side, quantity, tp_price, sl_price, sl_limit_price)
        print(f"OCO orders placed successfully:")
        for order in orders:
            print(f"  Order ID: {order['orderId']}")
        
    except Exception as e:
        print(f"Error placing OCO order: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
