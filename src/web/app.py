#!/usr/bin/env python3
import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.config import *
from src.api.binance_client import BinanceClient
from src.strategies.tdi_strategy import TDIStrategy
from src.indicators.tdi import TDI

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
binance_client = None
strategies = {}

def init_client():
    """Initialize Binance client with current configuration"""
    global binance_client
    try:
        # Check if API keys are provided
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            logger.error("Binance API keys are missing in configuration")
            return False
            
        binance_client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)
        
        # Test connection by making a simple API call
        exchange_info = binance_client.get_exchange_info()
        if not exchange_info:
            logger.error("Failed to get exchange info from Binance API")
            return False
            
        logger.info("Successfully initialized Binance client")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Binance client: {e}")
        binance_client = None
        return False

def init_strategies():
    """Initialize trading strategies for all symbols"""
    global strategies
    strategies = {}
    
    try:
        # Set up TDI parameters
        tdi_params = {
            'rsi_length': TDI_RSI_LENGTH,
            'fast_ma': TDI_FAST_MA,
            'slow_ma': TDI_SLOW_MA,
            'volatility_band_length': TDI_VOLATILITY_BAND_LENGTH,
            'std_dev_multiplier': TDI_STD_DEV_MULTIPLIER
        }
        
        # Create strategies for each symbol
        for symbol in TRADING_SYMBOLS:
            strategies[symbol] = TDIStrategy(
                binance_client,
                symbol,
                tdi_params=tdi_params,
                account_risk=ACCOUNT_RISK_PER_TRADE,
                max_leverage=MAX_LEVERAGE,
                use_cross_market_correlation=USE_CROSS_MARKET_CORRELATION,
                use_ml_filter=USE_ML_FILTER
            )
            # Initialize data for the strategy immediately
            strategies[symbol].update_data()
            logger.info(f"Strategy initialized for {symbol}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error setting up strategies: {e}")
        return False

def read_env_file():
    """Read the .env file and return its contents as a dictionary"""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key, value = line.split('=', 1)
                env_vars[key] = value
        return env_vars
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return {}

def write_env_file(env_vars):
    """Write the environment variables to the .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    
    try:
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        return True
    except Exception as e:
        logger.error(f"Error writing .env file: {e}")
        return False

def get_available_symbols():
    """Get available trading symbols from Binance"""
    if not binance_client:
        return []
    
    try:
        exchange_info = binance_client.get_exchange_info()
        if not exchange_info:
            return []
        
        symbols = []
        for symbol_info in exchange_info['symbols']:
            if symbol_info['quoteAsset'] == 'USDT' and symbol_info['status'] == 'TRADING':
                symbols.append(symbol_info['symbol'])
        
        return sorted(symbols)
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return []

def get_performance_data(symbol):
    """Get performance data for a specific symbol"""
    if symbol not in strategies:
        logger.error(f"Strategy not found for {symbol}")
        return {'error': f"Strategy not found for {symbol}. Please add it to your trading symbols."}
    
    # Check if Binance client is initialized
    if binance_client is None:
        logger.error("Binance client is not initialized")
        return {'error': "Binance client is not initialized. Please check your API keys and connection."}
    
    try:
        strategy = strategies[symbol]
        
        # Ensure the strategy has a valid client
        if strategy.client is None:
            logger.error(f"Binance client is not initialized for strategy {symbol}")
            strategy.client = binance_client
        
        # Update data to get latest
        strategy.update_data()
        
        # Check if data is available for this symbol
        if not strategy.data or 'execution' not in strategy.data or strategy.data['execution'] is None or strategy.data['execution'].empty:
            logger.error(f"No data available for {symbol}")
            return {'error': f"No data available for {symbol}. Please try again later."}
        
        # Get performance stats
        stats = strategy.get_performance_stats()
        
        # Get trade history
        trades = strategy.trades
        
        # Get current position
        current_position = {
            'symbol': symbol,
            'position': strategy.current_position,
            'entry_price': strategy.position_entry_price,
            'position_size': strategy.position_size,
            'stop_loss': strategy.stop_loss_price,
            'take_profit_levels': strategy.take_profit_levels
        }
        
        # Get latest price data for chart
        if 'execution' in strategy.data and not strategy.data['execution'].empty and len(strategy.data['execution']) > 0:
            df = strategy.data['execution'].tail(100).copy()
            
            # Check if required columns exist
            required_price_columns = ['open', 'high', 'low', 'close', 'volume']
            required_tdi_columns = ['rsi', 'fast_line', 'slow_line', 'market_baseline', 'upper_band', 'lower_band']
            
            # Check if all required price columns exist
            if all(col in df.columns for col in required_price_columns):
                price_data = df[required_price_columns].reset_index()
                price_data['timestamp'] = price_data['timestamp'].astype(str)
            else:
                missing_cols = [col for col in required_price_columns if col not in df.columns]
                logger.error(f"Missing price columns: {missing_cols}")
                price_data = []
            
            # Check if all required TDI columns exist
            if all(col in df.columns for col in required_tdi_columns):
                tdi_data = df[required_tdi_columns].reset_index()
                tdi_data['timestamp'] = tdi_data['timestamp'].astype(str)
            else:
                missing_cols = [col for col in required_tdi_columns if col not in df.columns]
                logger.error(f"Missing TDI columns: {missing_cols}")
                tdi_data = []
        else:
            logger.error(f"No execution data available for {symbol}")
            price_data = []
            tdi_data = []
        
        return {
            'stats': stats,
            'trades': trades,
            'current_position': current_position,
            'price_data': price_data.to_dict(orient='records') if not isinstance(price_data, list) else [],
            'tdi_data': tdi_data.to_dict(orient='records') if not isinstance(tdi_data, list) else []
        }
    except Exception as e:
        logger.error(f"Error getting performance data for {symbol}: {e}")
        return {'error': f"Error getting performance data for {symbol}: {str(e)}"}

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """API endpoint to get current configuration"""
    env_vars = read_env_file()
    return jsonify(env_vars)

@app.route('/api/config', methods=['POST'])
def update_config():
    """API endpoint to update configuration"""
    env_vars = read_env_file()
    
    # Update with new values
    for key, value in request.form.items():
        env_vars[key] = value
    
    # Write updated config to .env file
    if write_env_file(env_vars):
        # Reload configuration
        from importlib import reload
        import src.config.config
        reload(src.config.config)
        # Import specific variables instead of using wildcard import
        from src.config.config import (
            BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET, TRADING_SYMBOLS,
            ACCOUNT_RISK_PER_TRADE, MAX_LEVERAGE, USE_CROSS_MARKET_CORRELATION,
            USE_ML_FILTER, TDI_RSI_LENGTH, TDI_FAST_MA, TDI_SLOW_MA,
            TDI_VOLATILITY_BAND_LENGTH, TDI_STD_DEV_MULTIPLIER, LOG_LEVEL
        )
        
        # Reinitialize client and strategies
        init_client()
        init_strategies()
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update configuration'})

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """API endpoint to get available trading symbols"""
    symbols = get_available_symbols()
    return jsonify(symbols)

@app.route('/api/trading_symbols', methods=['GET'])
def get_trading_symbols():
    """API endpoint to get currently tracked trading symbols"""
    return jsonify(TRADING_SYMBOLS)

@app.route('/api/trading_symbols', methods=['POST'])
def update_trading_symbols():
    """API endpoint to update tracked trading symbols"""
    symbols = request.json.get('symbols', [])
    
    # Update .env file
    env_vars = read_env_file()
    env_vars['TRADING_SYMBOLS'] = ','.join(symbols)
    
    if write_env_file(env_vars):
        # Reload configuration
        from importlib import reload
        import src.config.config
        reload(src.config.config)
        # Import specific variables instead of using wildcard import
        from src.config.config import (
            BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET, TRADING_SYMBOLS,
            ACCOUNT_RISK_PER_TRADE, MAX_LEVERAGE, USE_CROSS_MARKET_CORRELATION,
            USE_ML_FILTER, TDI_RSI_LENGTH, TDI_FAST_MA, TDI_SLOW_MA,
            TDI_VOLATILITY_BAND_LENGTH, TDI_STD_DEV_MULTIPLIER, LOG_LEVEL
        )
        
        # Reinitialize strategies
        success = init_strategies()
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to initialize strategies for new symbols'})
    else:
        return jsonify({'success': False, 'error': 'Failed to update trading symbols'})

@app.route('/api/performance/<symbol>', methods=['GET'])
def get_symbol_performance(symbol):
    """API endpoint to get performance data for a specific symbol"""
    # Check if Binance client is initialized
    if binance_client is None:
        logger.error("Binance client is not initialized")
        return jsonify({'error': "Binance client is not initialized. Please check your API keys and connection."}), 500
        
    data = get_performance_data(symbol)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': f'Failed to get performance data for {symbol}'}), 404

@app.route('/api/run_strategy/<symbol>', methods=['POST'])
def run_strategy(symbol):
    """API endpoint to run the strategy for a specific symbol once"""
    if symbol not in strategies:
        return jsonify({'error': f'Strategy not found for {symbol}'}), 404
    
    try:
        action = strategies[symbol].run_iteration()
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        logger.error(f"Error running strategy for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Initialize client and strategies
    client_initialized = init_client()
    if client_initialized:
        strategies_initialized = init_strategies()
        if not strategies_initialized:
            logger.warning("Failed to initialize strategies. Some features may not work correctly.")
    else:
        logger.error("Failed to initialize Binance client. Trading features will not work.")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
