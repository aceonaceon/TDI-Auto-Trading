#!/usr/bin/env python3
"""
Run script for the TDI Auto Trading web interface.
"""
from app import app, init_client, init_strategies, logger

if __name__ == '__main__':
    # Initialize client and strategies
    client_initialized = init_client()
    if client_initialized:
        strategies_initialized = init_strategies()
        if not strategies_initialized:
            logger.warning("Failed to initialize strategies. Some features may not work correctly.")
    else:
        logger.error("Failed to initialize Binance client. Trading features will not work.")
        
    app.run(host='0.0.0.0', port=5001, debug=True)
