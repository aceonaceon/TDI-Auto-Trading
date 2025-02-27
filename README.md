# TDI Auto Trading System

An automated cryptocurrency trading system based on the Traders Dynamic Index (TDI) indicator, with advanced risk management and multi-timeframe analysis.

## Features

- **TDI Indicator Implementation**: Optimized for cryptocurrency markets with adjustable parameters
- **Multi-Timeframe Analysis**: Combines weekly, daily, 4-hour, and 1-hour timeframes for robust signal confirmation
- **Advanced Risk Management**: Dynamic position sizing, fractal-based stop losses, and trailing stops
- **Volatility Filtering**: Avoids trading during extreme market conditions
- **Cross-Market Correlation**: Adjusts position sizes based on correlations with major cryptocurrencies
- **Binance API Integration**: Connects to Binance for real-time data and order execution
- **Configurable Parameters**: Easily adjust trading parameters through environment variables

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/aceonaceon/TDI-Auto-Trading.git
cd TDI-Auto-Trading
```

2. Install TA-Lib (required for technical analysis):
   - For macOS:
     ```bash
     brew install ta-lib
     ```
   - For Ubuntu/Debian:
     ```bash
     wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
     tar -xzf ta-lib-0.4.0-src.tar.gz
     cd ta-lib/
     ./configure --prefix=/usr
     make
     sudo make install
     cd ..
     rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
     ```
   - For Windows:
     Download and install the pre-built binary from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the template:
```bash
cp .env.template .env
```

5. Edit the `.env` file with your Binance API credentials and desired trading parameters.

### Docker Installation

#### Prerequisites

1. Install Docker:
   - For macOS: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - For Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - For Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. Install Docker Compose:
   - Docker Desktop for Mac and Windows already includes Docker Compose
   - For Linux, follow the [Docker Compose installation guide](https://docs.docker.com/compose/install/linux/)

#### Setup and Run

1. Clone the repository:
```bash
git clone https://github.com/aceonaceon/TDI-Auto-Trading.git
cd TDI-Auto-Trading
```

2. Create a `.env` file based on the template:
```bash
cp .env.template .env
```

3. Edit the `.env` file with your Binance API credentials and desired trading parameters.

4. Make the helper script executable:
```bash
chmod +x docker-run.sh
```

5. Build and run the Docker container:
```bash
./docker-run.sh start
```

This will build the Docker image and start the container in detached mode.

#### Docker Helper Script

The project includes a helper script `docker-run.sh` that simplifies Docker operations:

```bash
# Start the trading system
./docker-run.sh start

# View logs
./docker-run.sh logs

# Check status
./docker-run.sh status

# Stop the trading system
./docker-run.sh stop

# Restart the trading system
./docker-run.sh restart

# Run a backtest
./docker-run.sh backtest 2023-01-01 2023-12-31

# Rebuild the Docker image
./docker-run.sh rebuild

# Show help
./docker-run.sh help
```

## Configuration

The system is highly configurable through environment variables in the `.env` file:

### API Configuration
- `BINANCE_API_KEY`: Your Binance API key
- `BINANCE_API_SECRET`: Your Binance API secret
- `USE_TESTNET`: Set to "True" to use Binance testnet (recommended for testing)

### Trading Parameters
- `TRADING_SYMBOLS`: Comma-separated list of trading pairs (e.g., "BTCUSDT,ETHUSDT")
- `BASE_ORDER_QUANTITY`: Base order quantity for BTC (adjusted for other assets)
- `MAX_LEVERAGE`: Maximum leverage to use
- `ACCOUNT_RISK_PER_TRADE`: Percentage of account to risk per trade (e.g., 0.02 for 2%)

### TDI Parameters
- `TDI_RSI_LENGTH`: Period for RSI calculation (default: 8)
- `TDI_FAST_MA`: Period for fast moving average (default: 2)
- `TDI_SLOW_MA`: Period for slow moving average (default: 7)
- `TDI_VOLATILITY_BAND_LENGTH`: Period for volatility bands (default: 20)
- `TDI_STD_DEV_MULTIPLIER`: Multiplier for standard deviation (default: 2.2)

### Risk Management
- `MAX_DRAWDOWN`: Maximum allowed drawdown before trading is paused
- `TRAILING_STOP_ACTIVATION`: Profit percentage to activate trailing stop
- `PARTIAL_TAKE_PROFIT`: Profit percentage to take partial profits

### Advanced Features
- `USE_ML_FILTER`: Enable machine learning signal filtering
- `USE_SENTIMENT_ANALYSIS`: Enable sentiment analysis (not implemented yet)
- `USE_CROSS_MARKET_CORRELATION`: Enable cross-market correlation adjustments

## Usage

### Live Trading

#### Standard Method
Run the system in live trading mode:

```bash
python main.py
```

By default, the system will check for trading signals every 60 minutes. You can adjust this interval:

```bash
python main.py --interval 30  # Check every 30 minutes
```

#### Using Docker
The Docker container will automatically run the system in live trading mode:

```bash
./docker-run.sh start
```

To view logs:
```bash
./docker-run.sh logs
```

To check if the system is running:
```bash
./docker-run.sh status
```

### Backtesting

#### Standard Method
Run the system in backtest mode:

```bash
python main.py --backtest --start-date 2023-01-01 --end-date 2023-12-31
```

#### Using Docker
You can run a backtest using the helper script:

```bash
./docker-run.sh backtest 2023-01-01 2023-12-31
```

Or modify the docker-compose.yml file to uncomment the command line for backtesting, then run:

```bash
docker-compose up -d
```

## Trading Strategy

The TDI Auto Trading System implements a sophisticated multi-timeframe approach:

1. **Macro Trend Analysis (Weekly)**: Determines the overall market direction
2. **Strategy Confirmation (Daily)**: Confirms trend strength and volatility conditions
3. **Execution Timing (4-Hour)**: Identifies optimal entry and exit points
4. **Fine-Tuning (1-Hour)**: Confirms signals and filters out noise

Entry signals require alignment across all timeframes, with additional filters for:
- Volume confirmation
- VWAP relationship
- Channel width expansion
- Cross-market correlation
- Extreme volatility rejection

Risk management includes:
- Dynamic position sizing based on volatility
- Fractal-based stop losses
- Multiple take-profit levels
- Trailing stops activated after initial profit
- Market baseline slope monitoring for trend changes

## Project Structure

```
TDI-Auto-Trading/
├── main.py                  # Main script to run the system
├── requirements.txt         # Python dependencies
├── .env.template            # Template for environment variables
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── .dockerignore            # Files to exclude from Docker build
├── src/
│   ├── api/
│   │   └── binance_client.py # Binance API wrapper
│   ├── config/
│   │   └── config.py        # Configuration from environment variables
│   ├── indicators/
│   │   └── tdi.py           # TDI indicator implementation
│   ├── strategies/
│   │   └── tdi_strategy.py  # TDI trading strategy
│   └── utils/
│       ├── data_utils.py    # Data handling utilities
│       └── risk_utils.py    # Risk management utilities
```

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves significant risk. Use this system at your own risk. The authors are not responsible for any financial losses incurred from using this software.

## License

MIT License
