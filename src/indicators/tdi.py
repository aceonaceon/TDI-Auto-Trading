import numpy as np
import pandas as pd
import pandas_ta as ta

class TDI:
    """
    Traders Dynamic Index (TDI) implementation optimized for cryptocurrency markets.
    
    The TDI is a composite indicator that combines RSI, moving averages, and volatility bands
    to identify trend direction, momentum, and potential reversal points.
    """
    
    def __init__(self, 
                 rsi_length=8, 
                 fast_ma=2, 
                 slow_ma=7, 
                 volatility_band_length=20, 
                 std_dev_multiplier=2.2):
        """
        Initialize TDI indicator with optimized parameters for crypto markets.
        
        Args:
            rsi_length (int): Period for RSI calculation (default: 8)
            fast_ma (int): Period for fast moving average (default: 2)
            slow_ma (int): Period for slow moving average (default: 7)
            volatility_band_length (int): Period for volatility bands (default: 20)
            std_dev_multiplier (float): Multiplier for standard deviation (default: 2.2)
        """
        self.rsi_length = rsi_length
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.volatility_band_length = volatility_band_length
        self.std_dev_multiplier = std_dev_multiplier
    
    def calculate(self, df):
        """
        Calculate TDI indicator components.
        
        Args:
            df (pd.DataFrame): DataFrame with price data (must contain 'close' column)
            
        Returns:
            pd.DataFrame: DataFrame with TDI indicator components added
        """
        # Make a copy to avoid modifying the original dataframe
        df = df.copy()
        
        # Calculate RSI
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_length)
        
        # Calculate fast and slow moving averages of RSI
        df['fast_line'] = ta.sma(df['rsi'], length=self.fast_ma)
        df['slow_line'] = ta.sma(df['rsi'], length=self.slow_ma)
        
        # Calculate market baseline (mid-line)
        df['market_baseline'] = ta.sma(df['rsi'], length=self.volatility_band_length)
        
        # Calculate volatility bands
        df['rsi_std'] = df['rsi'].rolling(window=self.volatility_band_length).std()
        df['upper_band'] = df['market_baseline'] + (df['rsi_std'] * self.std_dev_multiplier)
        df['lower_band'] = df['market_baseline'] - (df['rsi_std'] * self.std_dev_multiplier)
        
        # Calculate additional metrics
        df['channel_width'] = df['upper_band'] - df['lower_band']
        df['channel_width_pct'] = df['channel_width'] / df['market_baseline']
        
        # Calculate RSI slope for trend strength
        df['rsi_slope'] = df['rsi'].diff(3) / 3
        df['mbl_slope'] = df['market_baseline'].diff(5) / 5
        
        return df
    
    def get_signals(self, df):
        """
        Generate trading signals based on TDI indicator.
        
        Args:
            df (pd.DataFrame): DataFrame with TDI components
            
        Returns:
            pd.DataFrame: DataFrame with signal columns added
        """
        df = df.copy()
        
        # Fast line crosses above slow line (potential buy)
        df['fast_cross_above_slow'] = (df['fast_line'] > df['slow_line']) & (df['fast_line'].shift(1) <= df['slow_line'].shift(1))
        
        # Fast line crosses below slow line (potential sell)
        df['fast_cross_below_slow'] = (df['fast_line'] < df['slow_line']) & (df['fast_line'].shift(1) >= df['slow_line'].shift(1))
        
        # RSI crosses above market baseline (bullish)
        df['rsi_cross_above_mbl'] = (df['rsi'] > df['market_baseline']) & (df['rsi'].shift(1) <= df['market_baseline'].shift(1))
        
        # RSI crosses below market baseline (bearish)
        df['rsi_cross_below_mbl'] = (df['rsi'] < df['market_baseline']) & (df['rsi'].shift(1) >= df['market_baseline'].shift(1))
        
        # RSI crosses above upper band (overbought)
        df['rsi_cross_above_upper'] = (df['rsi'] > df['upper_band']) & (df['rsi'].shift(1) <= df['upper_band'].shift(1))
        
        # RSI crosses below lower band (oversold)
        df['rsi_cross_below_lower'] = (df['rsi'] < df['lower_band']) & (df['rsi'].shift(1) >= df['lower_band'].shift(1))
        
        # Channel width expansion (volatility increasing)
        df['channel_expanding'] = df['channel_width'] > df['channel_width'].rolling(window=5).mean() * 1.15
        
        # Trend strength based on market baseline slope
        df['strong_uptrend'] = (df['mbl_slope'] > 0.2) & (df['rsi'] > 50)
        df['strong_downtrend'] = (df['mbl_slope'] < -0.2) & (df['rsi'] < 50)
        
        # RSI divergence detection (simplified)
        df['price_higher_high'] = (df['close'] > df['close'].shift(1)) & (df['close'].shift(1) > df['close'].shift(2))
        df['rsi_lower_high'] = (df['rsi'] < df['rsi'].shift(1)) & (df['rsi'].shift(1) > df['rsi'].shift(2))
        df['bearish_divergence'] = df['price_higher_high'] & df['rsi_lower_high']
        
        df['price_lower_low'] = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2))
        df['rsi_higher_low'] = (df['rsi'] > df['rsi'].shift(1)) & (df['rsi'].shift(1) < df['rsi'].shift(2))
        df['bullish_divergence'] = df['price_lower_low'] & df['rsi_higher_low']
        
        # Generate composite signals
        df['buy_signal'] = (
            df['fast_cross_above_slow'] & 
            (df['rsi'] > 45) & 
            (df['rsi'] < df['upper_band']) &
            (df['mbl_slope'] > 0)
        )
        
        df['sell_signal'] = (
            df['fast_cross_below_slow'] & 
            (df['rsi'] < 55) & 
            (df['rsi'] > df['lower_band']) &
            (df['mbl_slope'] < 0)
        )
        
        # Strong signals with additional confirmation
        df['strong_buy_signal'] = (
            df['buy_signal'] & 
            df['channel_expanding'] & 
            (df['rsi'] > df['market_baseline']) &
            ~df['bearish_divergence']
        )
        
        df['strong_sell_signal'] = (
            df['sell_signal'] & 
            df['channel_expanding'] & 
            (df['rsi'] < df['market_baseline']) &
            ~df['bullish_divergence']
        )
        
        return df
