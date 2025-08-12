"""
TWAP (Time-Weighted Average Price) Strategy Implementation
"""
import sys
import time
import threading
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..binance_client import BinanceFuturesClient
from ..utils.validator import InputValidator
from ..utils.logger import BotLogger

class TWAPBot:
    """Implements TWAP (Time-Weighted Average Price) strategy"""
    
    def __init__(self, testnet: bool = True):
        self.client = BinanceFuturesClient(testnet=testnet)
        self.logger = BotLogger()
        self.active_twap_orders = {}
        self.stop_flags = {}
    
    def execute_twap_order(self, symbol: str, side: str, total_quantity: float,
                          duration_minutes: int, num_chunks: int = None) -> List[Dict[str, Any]]:
        """
        Execute TWAP order by splitting large order into smaller chunks over time
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            total_quantity: Total quantity to trade
            duration_minutes: Duration to spread the order over
            num_chunks: Number of chunks to split into (default: duration_minutes)
            
        Returns:
            List of executed orders
        """
        # Validate inputs
        errors = InputValidator.validate_basic_order(symbol, side, total_quantity)
        if duration_minutes <= 0:
            errors.append("Duration must be positive")
        
        if errors:
            error_msg = f"Validation errors: {', '.join(errors)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if num_chunks is None:
            num_chunks = min(duration_minutes, 20)  # Max 20 chunks
        
        chunk_size = total_quantity / num_chunks
        interval_seconds = (duration_minutes * 60) / num_chunks
        
        self.logger.info(f"Starting TWAP order: {total_quantity} {symbol} over {duration_minutes} minutes")
        self.logger.info(f"Chunk size: {chunk_size}, Interval: {interval_seconds}s, Chunks: {num_chunks}")
        
        twap_id = f"{symbol}_{side}_{int(time.time())}"
        self.stop_flags[twap_id] = False
        
        # Start TWAP execution in separate thread
        thread = threading.Thread(
            target=self._execute_twap_chunks,
            args=(twap_id, symbol, side, chunk_size, num_chunks, interval_seconds)
        )
        thread.start()
        
        return {'twap_id': twap_id, 'status': 'started'}
    
    def _execute_twap_chunks(self, twap_id: str, symbol: str, side: str,
                           chunk_size: float, num_chunks: int, interval_seconds: float):
        """Execute TWAP chunks in separate thread"""
        executed_orders = []
        
        try:
            for i in range(num_chunks):
                if self.stop_flags.get(twap_id, False):
                    self.logger.info(f"TWAP {twap_id} stopped by user")
                    break
                
                try:
                    # Place market order for chunk
                    order = self.client.place_order(
                        symbol=symbol,
                        side=side,
                        order_type='MARKET',
                        quantity=chunk_size
                    )
                    
                    executed_orders.append(order)
                    self.logger.info(f"TWAP chunk {i+1}/{num_chunks} executed: {order['orderId']}")
                    
                    # Wait for next interval (except for last chunk)
                    if i < num_chunks - 1:
                        time.sleep(interval_seconds)
                        
                except Exception as e:
                    self.logger.log_error(e, {
                        'twap_id': twap_id,
                        'chunk': i+1,
                        'symbol': symbol,
                        'side': side,
                        'chunk_size': chunk_size
                    })
                    continue
            
            self.active_twap_orders[twap_id] = executed_orders
            self.logger.info(f"TWAP {twap_id} completed. Executed {len(executed_orders)} orders")
            
        except Exception as e:
            self.logger.log_error(e, {'twap_id': twap_id})
        finally:
            # Cleanup
            if twap_id in self.stop_flags:
                del self.stop_flags[twap_id]
    
    def stop_twap_order(self, twap_id: str):
        """Stop an active TWAP order"""
        if twap_id in self.stop_flags:
            self.stop_flags[twap_id] = True
            self.logger.info(f"Stop signal sent for TWAP {twap_id}")
        else:
            self.logger.warning(f"TWAP {twap_id} not found or already completed")
    
    def get_twap_status(self, twap_id: str) -> Dict[str, Any]:
        """Get status of TWAP order"""
        if twap_id in self.active_twap_orders:
            return {
                'twap_id': twap_id,
                'status': 'completed',
                'orders': self.active_twap_orders[twap_id]
            }
        elif twap_id in self.stop_flags:
            return {
                'twap_id': twap_id,
                'status': 'running'
            }
        else:
            return {
                'twap_id': twap_id,
                'status': 'not_found'
            }

def main():
    """CLI interface for TWAP orders"""
    if len(sys.argv) not in [5, 6]:
        print("Usage: python src/advanced/twap.py <SYMBOL> <SIDE> <QUANTITY> <DURATION_MINUTES> [NUM_CHUNKS]")
        print("Example: python src/advanced/twap.py BTCUSDT BUY 0.1 30 10")
        sys.exit(1)
    
    symbol = sys.argv[1]
    side = sys.argv[2]
    quantity = float(sys.argv[3])
    duration = int(sys.argv[4])
    num_chunks = int(sys.argv[5]) if len(sys.argv) == 6 else None
    
    try:
        bot = TWAPBot(testnet=True)
        result = bot.execute_twap_order(symbol, side, quantity, duration, num_chunks)
        print(f"TWAP order started: {result['twap_id']}")
        print("Order will execute over the specified duration...")
        
    except Exception as e:
        print(f"Error starting TWAP order: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
