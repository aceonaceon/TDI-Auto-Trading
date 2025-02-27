import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.indicators.tdi import TDI
from src.utils.data_utils import calculate_vwap, detect_fractals, calculate_atr, calculate_correlation
from src.utils.risk_utils import (
    calculate_position_size, calculate_dynamic_leverage, calculate_stop_loss_price,
    calculate_take_profit_levels, calculate_trailing_stop, calculate_fractal_stop_loss,
    adjust_position_for_correlation
)

logger = logging.getLogger(__name__)

class TDIStrategy:
    """
    Trading strategy based on the Traders Dynamic Index (TDI) indicator.
    
    This strategy implements the multi-timeframe approach described in the research,
    with additional filters for extreme volatility and cross-market correlation.
    """
    
    def __init__(self, 
                 binance_client,
                 symbol,
                 tdi_params=None,
                 account_risk=0.02,
                 max_leverage=5,
                 use_cross_market_correlation=True,
                 use_ml_filter=False):
        """
        Initialize TDI strategy.
        
        Args:
            binance_client: BinanceClient instance
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            tdi_params (dict, optional): TDI indicator parameters
            account_risk (float): Risk per trade as percentage of account (0.02 = 2%)
            max_leverage (int): Maximum leverage to use
            use_cross_market_correlation (bool): Whether to use cross-market correlation
            use_ml_filter (bool): Whether to use ML signal filtering
        """
        self.client = binance_client
        self.symbol = symbol
        self.account_risk = account_risk
        self.max_leverage = max_leverage
        self.use_cross_market_correlation = use_cross_market_correlation
        self.use_ml_filter = use_ml_filter
        
        # Initialize TDI indicator with default or custom parameters
        if tdi_params is None:
            tdi_params = {
                'rsi_length': 8,
                'fast_ma': 2,
                'slow_ma': 7,
                'volatility_band_length': 20,
                'std_dev_multiplier': 2.2
            }
        
        self.tdi = TDI(**tdi_params)
        
        # Import timeframes from config
        from src.config.config import (
            MACRO_TIMEFRAME, STRATEGY_TIMEFRAME, EXECUTION_TIMEFRAME, MICRO_TIMEFRAME
        )
        
        # Timeframes for multi-timeframe analysis
        self.timeframes = {
            'macro': MACRO_TIMEFRAME,      # Macro trend
            'strategy': STRATEGY_TIMEFRAME, # Strategy confirmation
            'execution': EXECUTION_TIMEFRAME, # Execution timing
            'micro': MICRO_TIMEFRAME       # Entry/exit fine-tuning
        }
        
        # Data storage for each timeframe
        self.data = {}
        
        # Current position tracking
        self.current_position = None
        self.position_entry_price = None
        self.position_size = None
        self.stop_loss_price = None
        self.take_profit_levels = []
        self.highest_price_since_entry = None
        self.lowest_price_since_entry = None
        
        # Performance tracking
        self.trades = []
        self.equity_curve = []
        
        # Initialize correlation data if needed
        if self.use_cross_market_correlation:
            self.correlation_symbol = 'BTCUSDT' if symbol != 'BTCUSDT' else 'ETHUSDT'
            self.correlation_data = None
    
    def update_data(self, limit=500):
        """
        Update market data for all timeframes.
        
        Args:
            limit (int): Number of candles to fetch
        """
        logger.info(f"Updating market data for {self.symbol}")
        
        # Fetch data for each timeframe
        for tf_name, tf_value in self.timeframes.items():
            # Convert interval to proper time unit for start_str
            time_unit = tf_value
            if tf_value == '1w':
                time_unit = 'week'
            elif tf_value == '1d':
                time_unit = 'day'
            elif tf_value == '4h' or tf_value == '1h':
                time_unit = 'hour'
            elif tf_value.endswith('m'):
                time_unit = 'minute'
            
            # Adjust limit based on time unit
            adjusted_limit = limit
            if tf_value == '4h':
                adjusted_limit = limit * 4  # 4 hours in a day
            elif tf_value == '1h':
                adjusted_limit = limit * 24  # 24 hours in a day
            elif tf_value == '30m':
                adjusted_limit = limit * 48  # 48 30-min periods in a day
            elif tf_value == '15m':
                adjusted_limit = limit * 96  # 96 15-min periods in a day
            elif tf_value == '5m':
                adjusted_limit = limit * 288  # 288 5-min periods in a day
            elif tf_value == '1m':
                adjusted_limit = limit * 1440  # 1440 1-min periods in a day
            
            # Check if client is initialized
            if self.client is None:
                logger.error(f"Binance client is not initialized for {self.symbol}")
                return
                
            try:
                df = self.client.get_historical_klines(
                    symbol=self.symbol,
                    interval=tf_value,
                    start_str=f"{adjusted_limit} {time_unit}s ago UTC"
                )
            
                if not df.empty:
                    # Calculate TDI indicator
                    df = self.tdi.calculate(df)
                    df = self.tdi.get_signals(df)
                    
                    # Calculate additional indicators
                    df = calculate_vwap(df)
                    df = detect_fractals(df)
                    df = calculate_atr(df)
                    
                    self.data[tf_name] = df
                    logger.debug(f"Updated {tf_name} data with {len(df)} candles")
                else:
                    logger.warning(f"Failed to fetch {tf_name} data for {self.symbol}")
            except Exception as e:
                logger.error(f"Error fetching {tf_name} data for {self.symbol}: {e}")
                # Initialize empty dataframe to avoid NoneType errors
                self.data[tf_name] = pd.DataFrame()
        
        # Update correlation data if needed
        if self.use_cross_market_correlation and self.symbol != self.correlation_symbol:
            # Get the execution timeframe and convert to proper time unit
            exec_tf = self.timeframes['execution']
            time_unit = 'hour'
            if exec_tf == '1d':
                time_unit = 'day'
            elif exec_tf == '1w':
                time_unit = 'week'
            elif exec_tf.endswith('m'):
                time_unit = 'minute'
                
            # Adjust limit based on time unit
            adjusted_limit = limit
            if exec_tf == '4h':
                adjusted_limit = limit * 4  # 4 hours in a day
            elif exec_tf == '1h':
                adjusted_limit = limit * 24  # 24 hours in a day
            elif exec_tf == '30m':
                adjusted_limit = limit * 48  # 48 30-min periods in a day
            elif exec_tf == '15m':
                adjusted_limit = limit * 96  # 96 15-min periods in a day
            elif exec_tf == '5m':
                adjusted_limit = limit * 288  # 288 5-min periods in a day
            elif exec_tf == '1m':
                adjusted_limit = limit * 1440  # 1440 1-min periods in a day
                
            corr_df = self.client.get_historical_klines(
                symbol=self.correlation_symbol,
                interval=exec_tf,
                start_str=f"{adjusted_limit} {time_unit}s ago UTC"
            )
            
            if not corr_df.empty:
                self.correlation_data = corr_df
                
                # Calculate correlation
                if self.data['execution'] is not None:
                    correlation = calculate_correlation(
                        self.data['execution'], 
                        self.correlation_data,
                        window=5
                    )
                    self.data['execution']['correlation'] = correlation
    
    def check_entry_conditions(self):
        """
        Check if entry conditions are met for a new trade.
        
        Returns:
            tuple: (should_enter, direction, entry_price, stop_loss_price)
        """
        # Don't enter if already in a position
        if self.current_position is not None:
            return False, None, None, None
        
        # Ensure we have data for all timeframes
        for tf in self.timeframes.values():
            if tf not in self.data or self.data[tf].empty:
                logger.warning(f"Missing data for {tf} timeframe")
                return False, None, None, None
        
        # Get the latest data for each timeframe
        macro_latest = self.data['macro'].iloc[-1]
        strategy_latest = self.data['strategy'].iloc[-1]
        execution_latest = self.data['execution'].iloc[-1]
        micro_latest = self.data['micro'].iloc[-1]
        
        # Check for long entry
        long_conditions = (
            # Macro trend is bullish (weekly)
            macro_latest['market_baseline'] > 50 and
            macro_latest['mbl_slope'] > 0 and
            
            # Strategy confirmation (daily)
            strategy_latest['channel_expanding'] and
            strategy_latest['rsi'] > strategy_latest['market_baseline'] and
            
            # Execution timing (4h)
            execution_latest['strong_buy_signal'] and
            execution_latest['rsi'] > 45 and
            execution_latest['rsi'] < 70 and
            
            # Micro confirmation (1h)
            micro_latest['fast_cross_above_slow'] and
            micro_latest['close'] < micro_latest['vwap'] and
            micro_latest['volume'] > micro_latest['volume'].rolling(3).mean() * 1.4
        )
        
        # Check for short entry
        short_conditions = (
            # Macro trend is bearish (weekly)
            macro_latest['market_baseline'] < 50 and
            macro_latest['mbl_slope'] < 0 and
            
            # Strategy confirmation (daily)
            strategy_latest['channel_expanding'] and
            strategy_latest['rsi'] < strategy_latest['market_baseline'] and
            
            # Execution timing (4h)
            execution_latest['strong_sell_signal'] and
            execution_latest['rsi'] < 55 and
            execution_latest['rsi'] > 30 and
            
            # Micro confirmation (1h)
            micro_latest['fast_cross_below_slow'] and
            micro_latest['close'] > micro_latest['vwap'] and
            micro_latest['volume'] > micro_latest['volume'].rolling(3).mean() * 1.4
        )
        
        # Apply cross-market correlation filter if enabled
        if self.use_cross_market_correlation and 'correlation' in execution_latest:
            correlation = execution_latest['correlation']
            if abs(correlation) > 0.6:
                logger.info(f"High correlation with {self.correlation_symbol}: {correlation}")
                
                # If correlation is high, signals should align
                if correlation > 0.6:
                    # Positive correlation - both should move in same direction
                    corr_df = self.correlation_data.iloc[-1]
                    if long_conditions and not corr_df['close'] > corr_df['close'].shift(1):
                        logger.info("Long signal rejected due to correlation mismatch")
                        long_conditions = False
                    if short_conditions and not corr_df['close'] < corr_df['close'].shift(1):
                        logger.info("Short signal rejected due to correlation mismatch")
                        short_conditions = False
        
        # Get current price
        current_price = self.client.get_current_price(self.symbol)
        if current_price is None:
            logger.error("Failed to get current price")
            return False, None, None, None
        
        # Check for extreme volatility (avoid trading during flash crashes or pumps)
        execution_atr = execution_latest['atr']
        recent_volatility = abs(execution_latest['close'] - execution_latest['open']) / execution_latest['close']
        if recent_volatility > (execution_atr * 3 / current_price):
            logger.warning(f"Extreme volatility detected: {recent_volatility:.2%}")
            return False, None, None, None
        
        # Determine entry direction and price
        if long_conditions:
            direction = 'long'
            entry_price = current_price
            
            # Calculate stop loss price (using fractal method)
            fractal_stop = calculate_fractal_stop_loss(
                self.data['execution'], 
                len(self.data['execution']) - 1,
                n_fractals=3, 
                is_long=True
            )
            
            # If no fractal stop found, use ATR-based stop
            if fractal_stop is None:
                stop_loss_price = calculate_stop_loss_price(
                    entry_price, 
                    execution_atr, 
                    multiplier=2.0, 
                    is_long=True
                )
            else:
                stop_loss_price = min(fractal_stop, entry_price - execution_atr * 1.5)
            
            logger.info(f"Long entry conditions met at {entry_price}, stop loss at {stop_loss_price}")
            return True, direction, entry_price, stop_loss_price
            
        elif short_conditions:
            direction = 'short'
            entry_price = current_price
            
            # Calculate stop loss price (using fractal method)
            fractal_stop = calculate_fractal_stop_loss(
                self.data['execution'], 
                len(self.data['execution']) - 1,
                n_fractals=3, 
                is_long=False
            )
            
            # If no fractal stop found, use ATR-based stop
            if fractal_stop is None:
                stop_loss_price = calculate_stop_loss_price(
                    entry_price, 
                    execution_atr, 
                    multiplier=2.0, 
                    is_long=False
                )
            else:
                stop_loss_price = max(fractal_stop, entry_price + execution_atr * 1.5)
            
            logger.info(f"Short entry conditions met at {entry_price}, stop loss at {stop_loss_price}")
            return True, direction, entry_price, stop_loss_price
        
        return False, None, None, None
    
    def check_exit_conditions(self):
        """
        Check if exit conditions are met for the current position.
        
        Returns:
            tuple: (should_exit, exit_price, exit_reason)
        """
        # No position to exit
        if self.current_position is None:
            return False, None, None
        
        # Get current price
        current_price = self.client.get_current_price(self.symbol)
        if current_price is None:
            logger.error("Failed to get current price")
            return False, None, None
        
        # Get the latest data
        execution_latest = self.data['execution'].iloc[-1]
        micro_latest = self.data['micro'].iloc[-1]
        
        # Update highest/lowest price since entry
        if self.current_position == 'long':
            self.highest_price_since_entry = max(current_price, self.highest_price_since_entry or current_price)
        else:
            self.lowest_price_since_entry = min(current_price, self.lowest_price_since_entry or current_price)
        
        # Check stop loss
        if self.current_position == 'long' and current_price <= self.stop_loss_price:
            logger.info(f"Stop loss triggered at {current_price}")
            return True, current_price, 'stop_loss'
        
        if self.current_position == 'short' and current_price >= self.stop_loss_price:
            logger.info(f"Stop loss triggered at {current_price}")
            return True, current_price, 'stop_loss'
        
        # Check take profit levels
        if self.take_profit_levels:
            if self.current_position == 'long' and current_price >= self.take_profit_levels[0]:
                logger.info(f"Take profit triggered at {current_price}")
                return True, current_price, 'take_profit'
            
            if self.current_position == 'short' and current_price <= self.take_profit_levels[0]:
                logger.info(f"Take profit triggered at {current_price}")
                return True, current_price, 'take_profit'
        
        # Check for signal reversal
        if self.current_position == 'long':
            if micro_latest['strong_sell_signal'] or (
                execution_latest['fast_cross_below_slow'] and 
                execution_latest['rsi'] < execution_latest['market_baseline']
            ):
                logger.info(f"Exit signal for long position at {current_price}")
                return True, current_price, 'signal_reversal'
        else:  # short position
            if micro_latest['strong_buy_signal'] or (
                execution_latest['fast_cross_above_slow'] and 
                execution_latest['rsi'] > execution_latest['market_baseline']
            ):
                logger.info(f"Exit signal for short position at {current_price}")
                return True, current_price, 'signal_reversal'
        
        # Check trailing stop if in profit
        if self.current_position == 'long':
            # Only activate trailing stop after certain profit threshold
            if current_price > self.position_entry_price * 1.03:
                trailing_stop = calculate_trailing_stop(
                    current_price,
                    self.highest_price_since_entry,
                    execution_latest['atr'],
                    multiplier=2.0,
                    is_long=True
                )
                
                if current_price <= trailing_stop:
                    logger.info(f"Trailing stop triggered at {current_price}")
                    return True, current_price, 'trailing_stop'
        else:  # short position
            # Only activate trailing stop after certain profit threshold
            if current_price < self.position_entry_price * 0.97:
                trailing_stop = calculate_trailing_stop(
                    current_price,
                    self.lowest_price_since_entry,
                    execution_latest['atr'],
                    multiplier=2.0,
                    is_long=False
                )
                
                if current_price >= trailing_stop:
                    logger.info(f"Trailing stop triggered at {current_price}")
                    return True, current_price, 'trailing_stop'
        
        # Check for market baseline slope change
        if self.current_position == 'long' and execution_latest['mbl_slope'] < 0:
            logger.info(f"Market baseline slope turned negative, exiting long at {current_price}")
            return True, current_price, 'trend_change'
        
        if self.current_position == 'short' and execution_latest['mbl_slope'] > 0:
            logger.info(f"Market baseline slope turned positive, exiting short at {current_price}")
            return True, current_price, 'trend_change'
        
        return False, None, None
    
    def enter_position(self, direction, entry_price, stop_loss_price):
        """
        Enter a new trading position.
        
        Args:
            direction (str): 'long' or 'short'
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            
        Returns:
            bool: Success or failure
        """
        # Get account balance
        account_balance = self.client.get_account_balance('USDT')
        if account_balance <= 0:
            logger.error("Insufficient account balance")
            return False
        
        # Calculate dynamic leverage based on volatility
        execution_latest = self.data['execution'].iloc[-1]
        leverage = calculate_dynamic_leverage(
            execution_latest['atr'],
            execution_latest['channel_width_pct'],
            account_balance,
            max_leverage=self.max_leverage
        )
        
        # Set leverage on exchange (for futures)
        if self.symbol.endswith('USDT'):
            self.client.set_leverage(self.symbol, int(leverage))
        
        # Calculate position size
        position_size = calculate_position_size(
            account_balance,
            self.account_risk,
            entry_price,
            stop_loss_price,
            leverage=leverage
        )
        
        # Adjust position size based on correlation if enabled
        if self.use_cross_market_correlation and 'correlation' in execution_latest:
            position_size = adjust_position_for_correlation(
                position_size,
                execution_latest['correlation'],
                max_adjustment=0.5
            )
        
        # Round position size to appropriate precision
        symbol_info = self.client.get_symbol_info(self.symbol)
        if symbol_info:
            for filter_item in symbol_info['filters']:
                if filter_item['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_item['stepSize'])
                    position_size = round(position_size / step_size) * step_size
        
        # Calculate take profit levels
        take_profit_levels = calculate_take_profit_levels(
            entry_price,
            stop_loss_price,
            risk_reward_ratios=[1.5, 2.5, 3.5],
            is_long=(direction == 'long')
        )
        
        # Place market order
        side = 'BUY' if direction == 'long' else 'SELL'
        order = self.client.place_market_order(self.symbol, side, position_size)
        
        if order:
            # Place stop loss order
            stop_side = 'SELL' if direction == 'long' else 'BUY'
            stop_order = self.client.place_stop_loss_order(
                self.symbol,
                stop_side,
                position_size,
                stop_loss_price
            )
            
            # Place take profit order for first level
            if take_profit_levels:
                tp_side = 'SELL' if direction == 'long' else 'BUY'
                tp_order = self.client.place_take_profit_order(
                    self.symbol,
                    tp_side,
                    position_size * 0.5,  # Partial take profit
                    take_profit_levels[0]
                )
            
            # Update position tracking
            self.current_position = direction
            self.position_entry_price = entry_price
            self.position_size = position_size
            self.stop_loss_price = stop_loss_price
            self.take_profit_levels = take_profit_levels
            self.highest_price_since_entry = entry_price if direction == 'long' else None
            self.lowest_price_since_entry = entry_price if direction == 'short' else None
            
            logger.info(f"Entered {direction} position at {entry_price} with size {position_size}")
            logger.info(f"Stop loss at {stop_loss_price}, take profit at {take_profit_levels}")
            
            return True
        else:
            logger.error(f"Failed to enter {direction} position")
            return False
    
    def exit_position(self, exit_price, exit_reason):
        """
        Exit the current trading position.
        
        Args:
            exit_price (float): Exit price
            exit_reason (str): Reason for exit
            
        Returns:
            bool: Success or failure
        """
        if self.current_position is None:
            logger.warning("No position to exit")
            return False
        
        # Cancel all open orders
        self.client.cancel_all_orders(self.symbol)
        
        # Place market order to close position
        side = 'SELL' if self.current_position == 'long' else 'BUY'
        order = self.client.place_market_order(self.symbol, side, self.position_size)
        
        if order:
            # Calculate profit/loss
            if self.current_position == 'long':
                pnl_pct = (exit_price - self.position_entry_price) / self.position_entry_price
            else:
                pnl_pct = (self.position_entry_price - exit_price) / self.position_entry_price
            
            # Record trade
            trade = {
                'entry_time': datetime.now() - timedelta(hours=1),  # Approximate
                'exit_time': datetime.now(),
                'symbol': self.symbol,
                'direction': self.current_position,
                'entry_price': self.position_entry_price,
                'exit_price': exit_price,
                'position_size': self.position_size,
                'pnl_pct': pnl_pct,
                'exit_reason': exit_reason
            }
            self.trades.append(trade)
            
            # Update equity curve
            account_balance = self.client.get_account_balance('USDT')
            self.equity_curve.append((datetime.now(), account_balance))
            
            logger.info(f"Exited {self.current_position} position at {exit_price} ({exit_reason})")
            logger.info(f"P&L: {pnl_pct:.2%}")
            
            # Reset position tracking
            self.current_position = None
            self.position_entry_price = None
            self.position_size = None
            self.stop_loss_price = None
            self.take_profit_levels = []
            self.highest_price_since_entry = None
            self.lowest_price_since_entry = None
            
            return True
        else:
            logger.error(f"Failed to exit {self.current_position} position")
            return False
    
    def run_iteration(self):
        """
        Run a single iteration of the strategy.
        
        Returns:
            str: Action taken ('entered_long', 'entered_short', 'exited', 'no_action')
        """
        # Update market data
        self.update_data()
        
        # Check exit conditions if in a position
        if self.current_position is not None:
            should_exit, exit_price, exit_reason = self.check_exit_conditions()
            if should_exit:
                success = self.exit_position(exit_price, exit_reason)
                return 'exited' if success else 'exit_failed'
        
        # Check entry conditions if not in a position
        else:
            should_enter, direction, entry_price, stop_loss_price = self.check_entry_conditions()
            if should_enter:
                success = self.enter_position(direction, entry_price, stop_loss_price)
                return f"entered_{direction}" if success else 'entry_failed'
        
        return 'no_action'
    
    def get_performance_stats(self):
        """
        Calculate performance statistics.
        
        Returns:
            dict: Performance statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'max_drawdown': 0
            }
        
        # Calculate win rate
        winning_trades = [t for t in self.trades if t['pnl_pct'] > 0]
        win_rate = len(winning_trades) / len(self.trades)
        
        # Calculate average profit
        avg_profit = sum(t['pnl_pct'] for t in self.trades) / len(self.trades)
        
        # Calculate max drawdown
        if len(self.equity_curve) > 1:
            equity_values = [e[1] for e in self.equity_curve]
            max_drawdown = calculate_max_drawdown(pd.Series(equity_values))
        else:
            max_drawdown = 0
        
        return {
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'max_drawdown': max_drawdown
        }
