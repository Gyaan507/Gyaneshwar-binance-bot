"""
Configuration settings for Binance Futures Trading Bot
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the trading bot"""
    
    # Binance API Configuration
    API_KEY: Optional[str] = os.getenv('BINANCE_API_KEY')
    API_SECRET: Optional[str] = os.getenv('BINANCE_API_SECRET')  # Fixed variable name to match .env
    
    USE_TESTNET: bool = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # API Endpoints
    BASE_URL = 'https://fapi.binance.com'
    TESTNET_URL = 'https://testnet.binancefuture.com'
    
    # Trading Configuration
    DEFAULT_LEVERAGE = 1
    MAX_POSITION_SIZE = 1000
    MIN_ORDER_SIZE = 0.001
    
    # Logging Configuration
    LOG_FILE = 'bot.log'
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Risk Management
    MAX_DAILY_LOSS = 100  # USD
    MAX_OPEN_POSITIONS = 5
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.API_KEY or not cls.API_SECRET:
            return False
        return True
    
    @classmethod
    def get_base_url(cls) -> str:
        """Get the appropriate base URL based on testnet setting"""
        return cls.TESTNET_URL if cls.USE_TESTNET else cls.BASE_URL
