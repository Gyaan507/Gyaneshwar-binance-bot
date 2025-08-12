"""
Binance Futures API Client
"""
import hashlib
import hmac
import time
import requests
import sys
import os
from typing import Dict, Any, Optional
from urllib.parse import urlencode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.utils.logger import BotLogger

class BinanceFuturesClient:
    """Binance Futures API Client"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.base_url = Config.TESTNET_URL if testnet else Config.BASE_URL
        self.logger = BotLogger()
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate signature for authenticated requests"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=params, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.log_error(e, {'endpoint': endpoint, 'params': params})
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        response = self._make_request('GET', '/fapi/v1/exchangeInfo')
        for symbol_info in response['symbols']:
            if symbol_info['symbol'] == symbol.upper():
                return symbol_info
        raise ValueError(f"Symbol {symbol} not found")
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price"""
        params = {'symbol': symbol.upper()}
        response = self._make_request('GET', '/fapi/v1/ticker/price', params)
        return float(response['price'])
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: float = None, **kwargs) -> Dict[str, Any]:
        """Place an order"""
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(quantity)
        }
        
        if price is not None:
            params['price'] = str(price)
        
        # Add additional parameters
        params.update(kwargs)
        
        # Log order attempt
        self.logger.log_order(order_type, symbol, side, quantity, price, **kwargs)
        
        try:
            response = self._make_request('POST', '/fapi/v1/order', params, signed=True)
            self.logger.info(f"Order placed successfully: {response['orderId']}")
            return response
        except Exception as e:
            self.logger.log_error(e, {'order_params': params})
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        params = {
            'symbol': symbol.upper(),
            'orderId': order_id
        }
        
        try:
            response = self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
            self.logger.info(f"Order cancelled: {order_id}")
            return response
        except Exception as e:
            self.logger.log_error(e, {'symbol': symbol, 'order_id': order_id})
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        params = {
            'symbol': symbol.upper(),
            'orderId': order_id
        }
        return self._make_request('GET', '/fapi/v1/order', params, signed=True)
