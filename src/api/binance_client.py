import logging
import time
from datetime import datetime
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *

logger = logging.getLogger(__name__)

class BinanceClient:
    """
    Wrapper for Binance API client with additional functionality for the TDI trading system.
    """
    
    def __init__(self, api_key, api_secret, testnet=True):
        """
        Initialize Binance client.
        
        Args:
            api_key (str): Binance API key
            api_secret (str): Binance API secret
            testnet (bool): Whether to use testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize client
        self.client = Client(api_key, api_secret, testnet=testnet)
        
        # Test connection
        try:
            self.client.ping()
            logger.info("Successfully connected to Binance API")
            
            # Get account info
            self.update_account_info()
            
        except BinanceAPIException as e:
            logger.error(f"Failed to connect to Binance API: {e}")
            raise
    
    def update_account_info(self):
        """Update account information."""
        self.account_info = self.client.get_account()
        self.balances = {asset['asset']: float(asset['free']) for asset in self.account_info['balances'] if float(asset['free']) > 0}
        logger.info(f"Account balances updated: {self.balances}")
    
    def get_symbol_info(self, symbol):
        """
        Get detailed information about a trading symbol.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            dict: Symbol information
        """
        try:
            return self.client.get_symbol_info(symbol)
        except BinanceAPIException as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def get_exchange_info(self):
        """
        Get exchange information.
        
        Returns:
            dict: Exchange information
        """
        try:
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"Failed to get exchange info: {e}")
            return None
    
    def get_historical_klines(self, symbol, interval, start_str, end_str=None, limit=500):
        """
        Get historical klines (candlestick data).
        
        Args:
            symbol (str): Trading symbol
            interval (str): Kline interval (e.g., '1h', '4h', '1d')
            start_str (str): Start time string
            end_str (str, optional): End time string
            limit (int): Number of klines to fetch
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        try:
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert string values to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Failed to get historical klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """
        Get current price for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Current price
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
    
    def get_order_book(self, symbol, limit=10):
        """
        Get order book for a symbol.
        
        Args:
            symbol (str): Trading symbol
            limit (int): Number of orders to fetch
            
        Returns:
            dict: Order book
        """
        try:
            return self.client.get_order_book(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return None
    
    def place_market_order(self, symbol, side, quantity):
        """
        Place a market order.
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            
        Returns:
            dict: Order response
        """
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logger.info(f"Market order placed: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol, side, quantity, price):
        """
        Place a limit order.
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            price (float): Order price
            
        Returns:
            dict: Order response
        """
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=str(price)
            )
            logger.info(f"Limit order placed: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Failed to place limit order for {symbol}: {e}")
            return None
    
    def place_stop_loss_order(self, symbol, side, quantity, stop_price, limit_price=None):
        """
        Place a stop loss order.
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            stop_price (float): Stop price
            limit_price (float, optional): Limit price (for stop-limit orders)
            
        Returns:
            dict: Order response
        """
        try:
            if limit_price:
                # Stop-limit order
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=ORDER_TYPE_STOP_LOSS_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    stopPrice=str(stop_price),
                    price=str(limit_price)
                )
            else:
                # Stop-market order
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=ORDER_TYPE_STOP_LOSS,
                    quantity=quantity,
                    stopPrice=str(stop_price)
                )
            
            logger.info(f"Stop loss order placed: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Failed to place stop loss order for {symbol}: {e}")
            return None
    
    def place_take_profit_order(self, symbol, side, quantity, stop_price, limit_price=None):
        """
        Place a take profit order.
        
        Args:
            symbol (str): Trading symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            stop_price (float): Stop price
            limit_price (float, optional): Limit price (for take-profit-limit orders)
            
        Returns:
            dict: Order response
        """
        try:
            if limit_price:
                # Take-profit-limit order
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=ORDER_TYPE_TAKE_PROFIT_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    stopPrice=str(stop_price),
                    price=str(limit_price)
                )
            else:
                # Take-profit-market order
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=ORDER_TYPE_TAKE_PROFIT,
                    quantity=quantity,
                    stopPrice=str(stop_price)
                )
            
            logger.info(f"Take profit order placed: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Failed to place take profit order for {symbol}: {e}")
            return None
    
    def cancel_order(self, symbol, order_id):
        """
        Cancel an order.
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID
            
        Returns:
            dict: Cancel response
        """
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order cancelled: {result}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel order {order_id} for {symbol}: {e}")
            return None
    
    def cancel_all_orders(self, symbol):
        """
        Cancel all orders for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            list: List of cancel responses
        """
        try:
            result = self.client.cancel_all_orders(symbol=symbol)
            logger.info(f"All orders cancelled for {symbol}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel all orders for {symbol}: {e}")
            return None
    
    def get_open_orders(self, symbol=None):
        """
        Get open orders.
        
        Args:
            symbol (str, optional): Trading symbol
            
        Returns:
            list: List of open orders
        """
        try:
            if symbol:
                return self.client.get_open_orders(symbol=symbol)
            else:
                return self.client.get_open_orders()
        except BinanceAPIException as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def get_order_status(self, symbol, order_id):
        """
        Get order status.
        
        Args:
            symbol (str): Trading symbol
            order_id (int): Order ID
            
        Returns:
            dict: Order status
        """
        try:
            return self.client.get_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return None
    
    def get_account_balance(self, asset):
        """
        Get account balance for a specific asset.
        
        Args:
            asset (str): Asset symbol (e.g., 'BTC', 'USDT')
            
        Returns:
            float: Asset balance
        """
        try:
            self.update_account_info()
            return self.balances.get(asset, 0)
        except BinanceAPIException as e:
            logger.error(f"Failed to get account balance for {asset}: {e}")
            return 0
    
    def set_leverage(self, symbol, leverage):
        """
        Set leverage for a symbol (futures only).
        
        Args:
            symbol (str): Trading symbol
            leverage (int): Leverage value
            
        Returns:
            dict: Response
        """
        try:
            response = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
            return response
        except BinanceAPIException as e:
            logger.error(f"Failed to set leverage for {symbol}: {e}")
            return None
    
    def get_funding_rate(self, symbol):
        """
        Get current funding rate for a futures symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Current funding rate
        """
        try:
            funding_info = self.client.futures_funding_rate(symbol=symbol, limit=1)[0]
            return float(funding_info['fundingRate'])
        except (BinanceAPIException, IndexError) as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            return None
