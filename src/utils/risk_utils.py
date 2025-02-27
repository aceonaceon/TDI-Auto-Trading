import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_position_size(account_balance, risk_per_trade, entry_price, stop_loss_price, leverage=1):
    """
    Calculate position size based on account risk parameters.
    
    Args:
        account_balance (float): Total account balance
        risk_per_trade (float): Percentage of account to risk per trade (0.01 = 1%)
        entry_price (float): Entry price
        stop_loss_price (float): Stop loss price
        leverage (float): Leverage multiplier
        
    Returns:
        float: Position size in base currency
    """
    # Calculate risk amount in account currency
    risk_amount = account_balance * risk_per_trade
    
    # Calculate price difference percentage
    if entry_price > stop_loss_price:  # Long position
        price_diff_pct = (entry_price - stop_loss_price) / entry_price
    else:  # Short position
        price_diff_pct = (stop_loss_price - entry_price) / entry_price
    
    # Calculate position size
    position_size = (risk_amount / price_diff_pct) / entry_price
    
    # Apply leverage
    position_size = position_size * leverage
    
    return position_size

def calculate_dynamic_leverage(atr, channel_width_pct, account_balance, max_leverage=5, base_risk=0.1):
    """
    Calculate dynamic leverage based on market volatility.
    
    Args:
        atr (float): Average True Range value
        channel_width_pct (float): TDI channel width as percentage
        account_balance (float): Total account balance
        max_leverage (float): Maximum allowed leverage
        base_risk (float): Base risk factor
        
    Returns:
        float: Calculated leverage value
    """
    # Calculate volatility factor (higher volatility = lower leverage)
    volatility_factor = 1 / (channel_width_pct * 10)
    
    # Calculate base leverage
    base_leverage = (base_risk * account_balance) / (atr * channel_width_pct)
    
    # Apply volatility adjustment
    adjusted_leverage = base_leverage * volatility_factor
    
    # Cap at maximum leverage
    final_leverage = min(adjusted_leverage, max_leverage)
    
    # Ensure minimum leverage of 1
    final_leverage = max(final_leverage, 1)
    
    return final_leverage

def calculate_stop_loss_price(entry_price, atr_value, multiplier=2.0, is_long=True):
    """
    Calculate stop loss price based on ATR.
    
    Args:
        entry_price (float): Entry price
        atr_value (float): ATR value
        multiplier (float): Multiplier for ATR
        is_long (bool): True for long positions, False for short positions
        
    Returns:
        float: Stop loss price
    """
    if is_long:
        stop_loss = entry_price - (atr_value * multiplier)
    else:
        stop_loss = entry_price + (atr_value * multiplier)
    
    return stop_loss

def calculate_take_profit_levels(entry_price, stop_loss_price, risk_reward_ratios=[1.5, 2.5, 3.5], is_long=True):
    """
    Calculate multiple take profit levels based on risk-reward ratios.
    
    Args:
        entry_price (float): Entry price
        stop_loss_price (float): Stop loss price
        risk_reward_ratios (list): List of risk-reward ratios for each level
        is_long (bool): True for long positions, False for short positions
        
    Returns:
        list: List of take profit prices
    """
    # Calculate risk (distance from entry to stop loss)
    if is_long:
        risk = entry_price - stop_loss_price
        take_profits = [entry_price + (risk * rr) for rr in risk_reward_ratios]
    else:
        risk = stop_loss_price - entry_price
        take_profits = [entry_price - (risk * rr) for rr in risk_reward_ratios]
    
    return take_profits

def calculate_trailing_stop(current_price, highest_price, atr_value, multiplier=2.0, is_long=True):
    """
    Calculate trailing stop price.
    
    Args:
        current_price (float): Current market price
        highest_price (float): Highest price since entry for long, lowest for short
        atr_value (float): ATR value
        multiplier (float): Multiplier for ATR
        is_long (bool): True for long positions, False for short positions
        
    Returns:
        float: Trailing stop price
    """
    if is_long:
        trailing_stop = highest_price - (atr_value * multiplier)
        # Ensure trailing stop is not below current price
        trailing_stop = min(trailing_stop, current_price)
    else:
        trailing_stop = highest_price + (atr_value * multiplier)
        # Ensure trailing stop is not above current price
        trailing_stop = max(trailing_stop, current_price)
    
    return trailing_stop

def calculate_fractal_stop_loss(df, current_index, n_fractals=3, is_long=True):
    """
    Calculate stop loss based on recent price fractals.
    
    Args:
        df (pd.DataFrame): DataFrame with fractal data
        current_index (int): Current index in the DataFrame
        n_fractals (int): Number of fractals to consider
        is_long (bool): True for long positions, False for short positions
        
    Returns:
        float: Fractal-based stop loss price
    """
    if current_index < n_fractals:
        return None
    
    # Get subset of data up to current index
    subset = df.iloc[:current_index]
    
    if is_long:
        # For long positions, find the lowest recent fractal low
        fractal_lows = subset[subset['fractal_low']]['low'].tail(n_fractals)
        if not fractal_lows.empty:
            return fractal_lows.min()
    else:
        # For short positions, find the highest recent fractal high
        fractal_highs = subset[subset['fractal_high']]['high'].tail(n_fractals)
        if not fractal_highs.empty:
            return fractal_highs.max()
    
    return None

def adjust_position_for_correlation(position_size, correlation_coefficient, max_adjustment=0.5):
    """
    Adjust position size based on correlation with another market.
    
    Args:
        position_size (float): Original position size
        correlation_coefficient (float): Correlation coefficient (-1 to 1)
        max_adjustment (float): Maximum adjustment factor
        
    Returns:
        float: Adjusted position size
    """
    # Only adjust if correlation is significant
    if abs(correlation_coefficient) > 0.6:
        # Calculate adjustment factor (higher correlation = lower position size)
        adjustment = 1 - (abs(correlation_coefficient) * max_adjustment)
        return position_size * adjustment
    
    return position_size

def calculate_max_drawdown(equity_curve):
    """
    Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve (pd.Series): Series of account equity values
        
    Returns:
        float: Maximum drawdown as a percentage
    """
    # Calculate running maximum
    running_max = equity_curve.cummax()
    
    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max
    
    # Get maximum drawdown
    max_drawdown = drawdown.min()
    
    return max_drawdown
