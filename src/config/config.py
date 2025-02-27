import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() in ('true', '1', 't')

# Trading Parameters
TRADING_SYMBOLS = os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT').split(',')
BASE_ORDER_QUANTITY = float(os.getenv('BASE_ORDER_QUANTITY', '0.001'))  # For BTC
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '5'))
ACCOUNT_RISK_PER_TRADE = float(os.getenv('ACCOUNT_RISK_PER_TRADE', '0.02'))  # 2% risk per trade

# TDI Parameters
TDI_RSI_LENGTH = int(os.getenv('TDI_RSI_LENGTH', '8'))  # Optimized for crypto from traditional 14
TDI_FAST_MA = int(os.getenv('TDI_FAST_MA', '2'))  # Fast line period
TDI_SLOW_MA = int(os.getenv('TDI_SLOW_MA', '7'))  # Slow line period
TDI_VOLATILITY_BAND_LENGTH = int(os.getenv('TDI_VOLATILITY_BAND_LENGTH', '20'))  # Volatility band period
TDI_STD_DEV_MULTIPLIER = float(os.getenv('TDI_STD_DEV_MULTIPLIER', '2.2'))  # Standard deviation multiplier

# Timeframes for multi-timeframe analysis
MACRO_TIMEFRAME = os.getenv('MACRO_TIMEFRAME', '1w')  # Weekly
STRATEGY_TIMEFRAME = os.getenv('STRATEGY_TIMEFRAME', '1d')  # Daily
EXECUTION_TIMEFRAME = os.getenv('EXECUTION_TIMEFRAME', '4h')  # 4-hour
MICRO_TIMEFRAME = os.getenv('MICRO_TIMEFRAME', '1h')  # 1-hour

# Risk Management
MAX_DRAWDOWN = float(os.getenv('MAX_DRAWDOWN', '0.15'))  # 15% max drawdown
TRAILING_STOP_ACTIVATION = float(os.getenv('TRAILING_STOP_ACTIVATION', '0.03'))  # Activate trailing stop after 3% profit
PARTIAL_TAKE_PROFIT = float(os.getenv('PARTIAL_TAKE_PROFIT', '0.05'))  # Take 50% profit at 5% gain

# Advanced Features
USE_ML_FILTER = os.getenv('USE_ML_FILTER', 'False').lower() in ('true', '1', 't')
USE_SENTIMENT_ANALYSIS = os.getenv('USE_SENTIMENT_ANALYSIS', 'False').lower() in ('true', '1', 't')
USE_CROSS_MARKET_CORRELATION = os.getenv('USE_CROSS_MARKET_CORRELATION', 'True').lower() in ('true', '1', 't')

# Logging and Debugging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
BACKTEST_MODE = os.getenv('BACKTEST_MODE', 'False').lower() in ('true', '1', 't')
