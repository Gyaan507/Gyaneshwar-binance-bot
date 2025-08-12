"""
Grid Trading Strategy Implementation
"""
import sys
import time
from typing import Dict, Any, List, Optional
from decimal import Decimal

from ..binance_client import BinanceFuturesClient
from ..utils.validator import InputValidator
from ..utils.logger import BotLogger

class GridTradingBot:
    """Implements Grid Trading strategy"""
    
    def __init__(self, testnet: bool = True):
        self.client = BinanceFuturesClient(testnet=testnet)
        self.logger = BotLogger()
        self.active_grids = {}
    
    def create_grid_strategy(self, symbol: str, lower_price: float, upper_price: float,
                           grid_levels: int, total_investment: float) -> Dict[str, Any]:
        """
        Create a grid trading strategy
        
        Args:
            symbol: Trading pair
            lower_price: Lower bound of grid
            upper_price: Upper bound of grid
            grid_levels: Number of grid levels
            total_investment: Total amount to invest
            
        Returns:
            Grid strategy details
        """
        # Validate inputs
        if not InputValidator.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        if not InputValidator.validate_price(lower_price) or not InputValidator.validate_price(upper_price):
            raise ValueError("Invalid price values")
        
        if lower_price >= upper_price:
            raise ValueError("Lower price must be less than upper price")
        
        if grid_levels < 2:
            raise ValueError("Grid levels must be at least 2")
        
        if total_investment <= 0:
            raise ValueError("Total investment must be positive")
        
        # Calculate grid parameters
        price_step = (upper_price - lower_price) / (grid_levels - 1)
        quantity_per_level = total_investment / (grid_levels * ((lower_price + upper_price) / 2))
        
        grid_prices = []
        for i in range(grid_levels):
            price = lower_price + (i * price_step)
            grid_prices.append(round(price, 8))
        
        grid_id = f"{symbol}_grid_{int(time.time())}"
        
        grid_config = {
            'grid_id': grid_id,
            'symbol': symbol,
            'lower_price': lower_price,
            'upper_price': upper_price,
            'grid_levels': grid_levels,
            'price_step': price_step,
            'quantity_per_level': quantity_per_level,
            'grid_prices': grid_prices,
            'total_investment': total_investment,
            'buy_orders': [],
            'sell_orders': [],
            'status': 'created'
        }
        
        self.logger.info(f"Grid strategy created: {grid_config}")
        return grid_config
    
    def deploy_grid_orders(self, grid_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy initial grid orders"""
        try:
            current_price = self.client.get_ticker_price(grid_config['symbol'])
            self.logger.info(f"Current price: {current_price}")
            
            buy_orders = []
            sell_orders = []
            
            # Place buy orders below current price
            for price in grid_config['grid_prices']:
                if price < current_price:
                    try:
                        order = self.client.place_order(
                            symbol=grid_config['symbol'],
                            side='BUY',
                            order_type='LIMIT',
                            quantity=grid_config['quantity_per_level'],
                            price=price,
                            timeInForce='GTC'
                        )
                        buy_orders.append(order)
                        self.logger.info(f"Grid buy order placed at {price}: {order['orderId']}")
                    except Exception as e:
                        self.logger.log_error(e, {'grid_price': price, 'side': 'BUY'})
            
            # Place sell orders above current price
            for price in grid_config['grid_prices']:
                if price > current_price:
                    try:
                        order = self.client.place_order(
                            symbol=grid_config['symbol'],
                            side='SELL',
                            order_type='LIMIT',
                            quantity=grid_config['quantity_per_level'],
                            price=price,
                            timeInForce='GTC'
                        )
                        sell_orders.append(order)
                        self.logger.info(f"Grid sell order placed at {price}: {order['orderId']}")
                    except Exception as e:
                        self.logger.log_error(e, {'grid_price': price, 'side': 'SELL'})
            
            grid_config['buy_orders'] = buy_orders
            grid_config['sell_orders'] = sell_orders
            grid_config['status'] = 'deployed'
            
            self.active_grids[grid_config['grid_id']] = grid_config
            
            self.logger.info(f"Grid deployed: {len(buy_orders)} buy orders, {len(sell_orders)} sell orders")
            return grid_config
            
        except Exception as e:
            self.logger.log_error(e, {'grid_id': grid_config['grid_id']})
            raise
    
    def monitor_and_rebalance_grid(self, grid_id: str) -> Dict[str, Any]:
        """Monitor grid and rebalance when orders are filled"""
        if grid_id not in self.active_grids:
            raise ValueError(f"Grid {grid_id} not found")
        
        grid_config = self.active_grids[grid_id]
        
        try:
            # Check order statuses
            filled_orders = []
            
            # Check buy orders
            for order in grid_config['buy_orders']:
                status = self.client.get_order_status(grid_config['symbol'], order['orderId'])
                if status['status'] == 'FILLED':
                    filled_orders.append(('BUY', order, status))
            
            # Check sell orders
            for order in grid_config['sell_orders']:
                status = self.client.get_order_status(grid_config['symbol'], order['orderId'])
                if status['status'] == 'FILLED':
                    filled_orders.append(('SELL', order, status))
            
            # Rebalance filled orders
            for side, original_order, status in filled_orders:
                try:
                    # Place opposite order at the next grid level
                    opposite_side = 'SELL' if side == 'BUY' else 'BUY'
                    executed_price = float(status['avgPrice'])
                    
                    if side == 'BUY':
                        # Place sell order one level up
                        new_price = executed_price + grid_config['price_step']
                    else:
                        # Place buy order one level down
                        new_price = executed_price - grid_config['price_step']
                    
                    # Check if new price is within grid bounds
                    if grid_config['lower_price'] <= new_price <= grid_config['upper_price']:
                        new_order = self.client.place_order(
                            symbol=grid_config['symbol'],
                            side=opposite_side,
                            order_type='LIMIT',
                            quantity=grid_config['quantity_per_level'],
                            price=new_price,
                            timeInForce='GTC'
                        )
                        
                        self.logger.info(f"Grid rebalanced: {opposite_side} order at {new_price}")
                        
                        # Update grid config
                        if opposite_side == 'BUY':
                            grid_config['buy_orders'].append(new_order)
                        else:
                            grid_config['sell_orders'].append(new_order)
                
                except Exception as e:
                    self.logger.log_error(e, {'rebalance_order': original_order['orderId']})
            
            return {
                'grid_id': grid_id,
                'filled_orders': len(filled_orders),
                'status': 'monitored'
            }
            
        except Exception as e:
            self.logger.log_error(e, {'grid_id': grid_id})
            raise
    
    def stop_grid_strategy(self, grid_id: str) -> Dict[str, Any]:
        """Stop grid strategy and cancel all orders"""
        if grid_id not in self.active_grids:
            raise ValueError(f"Grid {grid_id} not found")
        
        grid_config = self.active_grids[grid_id]
        cancelled_orders = []
        
        # Cancel all buy orders
        for order in grid_config['buy_orders']:
            try:
                result = self.client.cancel_order(grid_config['symbol'], order['orderId'])
                cancelled_orders.append(result)
            except Exception as e:
                self.logger.log_error(e, {'order_id': order['orderId']})
        
        # Cancel all sell orders
        for order in grid_config['sell_orders']:
            try:
                result = self.client.cancel_order(grid_config['symbol'], order['orderId'])
                cancelled_orders.append(result)
            except Exception as e:
                self.logger.log_error(e, {'order_id': order['orderId']})
        
        grid_config['status'] = 'stopped'
        self.logger.info(f"Grid strategy {grid_id} stopped. Cancelled {len(cancelled_orders)} orders")
        
        return {
            'grid_id': grid_id,
            'cancelled_orders': len(cancelled_orders),
            'status': 'stopped'
        }

def main():
    """CLI interface for grid trading"""
    if len(sys.argv) != 6:
        print("Usage: python src/advanced/grid.py <SYMBOL> <LOWER_PRICE> <UPPER_PRICE> <GRID_LEVELS> <INVESTMENT>")
        print("Example: python src/advanced/grid.py BTCUSDT 44000 46000 10 1000")
        sys.exit(1)
    
    symbol = sys.argv[1]
    lower_price = float(sys.argv[2])
    upper_price = float(sys.argv[3])
    grid_levels = int(sys.argv[4])
    investment = float(sys.argv[5])
    
    try:
        bot = GridTradingBot(testnet=True)
        
        # Create grid strategy
        grid_config = bot.create_grid_strategy(symbol, lower_price, upper_price, grid_levels, investment)
        print(f"Grid strategy created: {grid_config['grid_id']}")
        
        # Deploy grid orders
        deployed_grid = bot.deploy_grid_orders(grid_config)
        print(f"Grid deployed with {len(deployed_grid['buy_orders'])} buy and {len(deployed_grid['sell_orders'])} sell orders")
        
    except Exception as e:
        print(f"Error creating grid strategy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
