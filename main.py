#!/usr/bin/env python3
import os
import sys
import logging
import time
import schedule
import argparse
from datetime import datetime

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET, TRADING_SYMBOLS,
    ACCOUNT_RISK_PER_TRADE, MAX_LEVERAGE, USE_CROSS_MARKET_CORRELATION,
    USE_ML_FILTER, TDI_RSI_LENGTH, TDI_FAST_MA, TDI_SLOW_MA,
    TDI_VOLATILITY_BAND_LENGTH, TDI_STD_DEV_MULTIPLIER, LOG_LEVEL,
    BACKTEST_MODE
)
from src.api.binance_client import BinanceClient
from src.strategies.tdi_strategy import TDIStrategy

# Set up logging
# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Set up log file with timestamp
log_file = os.path.join(logs_dir, f"trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_strategies():
    """
    Set up trading strategies for all symbols.
    
    Returns:
        dict: Dictionary of strategies with symbols as keys
    """
    strategies = {}
    
    try:
        # Initialize Binance client
        client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)
        
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
                client,
                symbol,
                tdi_params=tdi_params,
                account_risk=ACCOUNT_RISK_PER_TRADE,
                max_leverage=MAX_LEVERAGE,
                use_cross_market_correlation=USE_CROSS_MARKET_CORRELATION,
                use_ml_filter=USE_ML_FILTER
            )
            logger.info(f"Strategy initialized for {symbol}")
        
        return strategies
    
    except Exception as e:
        logger.error(f"Error setting up strategies: {e}")
        return {}

def run_strategies(strategies):
    """
    Run all strategies once.
    
    Args:
        strategies (dict): Dictionary of strategies
    """
    for symbol, strategy in strategies.items():
        try:
            logger.info(f"Running strategy for {symbol}")
            action = strategy.run_iteration()
            logger.info(f"Action taken for {symbol}: {action}")
            
            # Log performance stats
            stats = strategy.get_performance_stats()
            logger.info(f"Performance for {symbol}: {stats}")
            
        except Exception as e:
            logger.error(f"Error running strategy for {symbol}: {e}")

def schedule_runs(strategies, interval_minutes=60):
    """
    Schedule regular strategy runs.
    
    Args:
        strategies (dict): Dictionary of strategies
        interval_minutes (int): Interval between runs in minutes
    """
    logger.info(f"Scheduling strategy runs every {interval_minutes} minutes")
    
    # Schedule the first run
    schedule.every(interval_minutes).minutes.do(run_strategies, strategies)
    
    # Run immediately once
    run_strategies(strategies)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_backtest(strategies, start_date, end_date):
    """
    Run backtest for all strategies.
    
    Args:
        strategies (dict): Dictionary of strategies
        start_date (str): Start date for backtest (YYYY-MM-DD)
        end_date (str): End date for backtest (YYYY-MM-DD)
    """
    logger.info(f"Running backtest from {start_date} to {end_date}")
    
    # TODO: Implement backtest functionality
    logger.warning("Backtest functionality not yet implemented")

def main():
    """Main function to run the trading system."""
    parser = argparse.ArgumentParser(description='TDI Auto Trading System')
    parser.add_argument('--backtest', action='store_true', help='Run in backtest mode')
    parser.add_argument('--start-date', type=str, help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--interval', type=int, default=60, help='Interval between strategy runs in minutes')
    
    args = parser.parse_args()
    
    logger.info("Starting TDI Auto Trading System")
    logger.info(f"Trading symbols: {TRADING_SYMBOLS}")
    logger.info(f"Using testnet: {USE_TESTNET}")
    
    # Set up strategies
    strategies = setup_strategies()
    if not strategies:
        logger.error("Failed to set up strategies. Exiting.")
        return
    
    # Run in backtest mode if specified
    if args.backtest or BACKTEST_MODE:
        start_date = args.start_date or "2023-01-01"
        end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
        run_backtest(strategies, start_date, end_date)
    else:
        # Run in live mode
        schedule_runs(strategies, args.interval)

if __name__ == "__main__":
    main()
