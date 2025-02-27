import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import ccxt

logger = logging.getLogger(__name__)

def fetch_ohlcv_data(exchange, symbol, timeframe, limit=500, since=None):
    """
    Fetch OHLCV (Open, High, Low, Close, Volume) data from exchange.
    
    Args:
        exchange: ccxt exchange instance
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
        timeframe (str): Timeframe (e.g., '1h', '4h', '1d')
        limit (int): Number of candles to fetch
        since (int, optional): Timestamp in milliseconds for start time
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    try:
        # Fetch the OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    except Exception as e:
        logger.error(f"Error fetching OHLCV data: {e}")
        return pd.DataFrame()

def fetch_multi_timeframe_data(exchange, symbol, timeframes, limit=500):
    """
    Fetch data for multiple timeframes.
    
    Args:
        exchange: ccxt exchange instance
        symbol (str): Trading pair symbol
        timeframes (list): List of timeframe strings
        limit (int): Number of candles to fetch
        
    Returns:
        dict: Dictionary with timeframes as keys and DataFrames as values
    """
    data = {}
    
    for tf in timeframes:
        logger.info(f"Fetching {symbol} data for {tf} timeframe")
        data[tf] = fetch_ohlcv_data(exchange, symbol, tf, limit)
        
    return data

def calculate_vwap(df, window=20):
    """
    Calculate Volume Weighted Average Price (VWAP).
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        window (int): Window period for VWAP calculation
        
    Returns:
        pd.DataFrame: DataFrame with VWAP added
    """
    df = df.copy()
    
    # Calculate typical price
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    
    # Calculate VWAP
    df['vwap'] = (df['typical_price'] * df['volume']).rolling(window=window).sum() / df['volume'].rolling(window=window).sum()
    
    return df

def detect_fractals(df, n=2):
    """
    Detect price fractals for dynamic support/resistance levels.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        n (int): Number of periods to look before and after
        
    Returns:
        pd.DataFrame: DataFrame with fractal columns added
    """
    df = df.copy()
    
    # Initialize fractal columns
    df['fractal_high'] = False
    df['fractal_low'] = False
    
    # Detect bullish fractals (low points)
    for i in range(n, len(df) - n):
        if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, n+1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, n+1)):
            df['fractal_low'].iloc[i] = True
    
    # Detect bearish fractals (high points)
    for i in range(n, len(df) - n):
        if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, n+1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, n+1)):
            df['fractal_high'].iloc[i] = True
    
    return df

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR) for volatility measurement.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        period (int): Period for ATR calculation
        
    Returns:
        pd.DataFrame: DataFrame with ATR column added
    """
    df = df.copy()
    
    # Calculate True Range
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # Calculate ATR
    df['atr'] = df['tr'].rolling(window=period).mean()
    
    # Clean up
    df.drop(['tr0', 'tr1', 'tr2', 'tr'], axis=1, inplace=True)
    
    return df

def calculate_correlation(df1, df2, window=5):
    """
    Calculate rolling correlation between two price series.
    
    Args:
        df1 (pd.DataFrame): First DataFrame with 'close' column
        df2 (pd.DataFrame): Second DataFrame with 'close' column
        window (int): Window for rolling correlation
        
    Returns:
        pd.Series: Rolling correlation series
    """
    # Ensure both DataFrames have the same index
    common_index = df1.index.intersection(df2.index)
    df1 = df1.loc[common_index]
    df2 = df2.loc[common_index]
    
    # Calculate rolling correlation
    correlation = df1['close'].rolling(window=window).corr(df2['close'])
    
    return correlation
