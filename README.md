# Crypto Trading Bot - Dual Strategy Trading System

A sophisticated crypto trading bot that implements high-frequency arbitrage and swing trading strategies on Solana and Base chain DEXs.

## 🚀 Features

### Dual Strategy Approach
- **High-Frequency Arbitrage**: 0.1-0.5% profit per trade, multiple trades/minute
- **Swing Trading**: 2-10% profit per trade, 1-5 trades/day using technical analysis

### Supported Chains & DEXs
- **Solana**: Jupiter aggregator, Orca, Raydium
- **Base**: Uniswap V3, Aerodrome

### Risk Management
- Position sizing based on portfolio percentage
- Stop losses and take profit levels
- Daily loss limits
- Maximum drawdown protection
- Slippage protection

### Technical Analysis
- RSI (Relative Strength Index)
- EMA (Exponential Moving Average)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume analysis
- Price momentum indicators

## 📋 Prerequisites

- Python 3.9+
- Solana wallet with SOL for gas fees
- Base wallet with ETH for gas fees
- Small capital for testing ($100-500 recommended)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd crypto-trading-bot
```

### 2. Create Virtual Environment
```bash
python -m venv crypto-bot-env
source crypto-bot-env/bin/activate  # On Windows: crypto-bot-env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate Wallets (Optional)
```bash
python generate_wallets.py
```
This will create test wallets and a `.env` file template.

### 5. Configure Environment
Copy the environment template and configure your settings:
```bash
cp env.example .env
# Edit .env with your wallet keys and settings
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Wallet Configuration
SOLANA_PRIVATE_KEY=your_solana_private_key_here
BASE_PRIVATE_KEY=your_base_private_key_here

# RPC Endpoints
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BASE_RPC_URL=https://mainnet.base.org

# Trading Parameters
MIN_ARBITRAGE_PROFIT=0.001    # 0.1%
MAX_POSITION_SIZE=0.3         # 30% of portfolio
MIN_TRADE_SIZE=500           # $500 minimum
MAX_DAILY_LOSS=0.05          # 5% daily loss limit

# Risk Management
STOP_LOSS_PERCENTAGE=0.03    # 3% stop loss
TAKE_PROFIT_PERCENTAGE=0.05  # 5% take profit
MAX_SLIPPAGE=0.005          # 0.5% max slippage

# Trading Pairs
SOLANA_PAIRS=SOL/USDC,ETH/USDC,RAY/USDC
BASE_PAIRS=ETH/USDC,WETH/USDC
```

## 🚀 Usage

### Paper Trading (Recommended First)
```bash
python src/main.py --mode=paper --log-level=INFO
```

### Live Trading (After Successful Paper Trading)
```bash
python src/main.py --mode=live --log-level=INFO
```

### Command Line Options
```bash
python src/main.py --help
```

Options:
- `--mode`: paper or live trading
- `--config`: path to configuration file
- `--log-level`: DEBUG, INFO, WARNING, ERROR

## 📊 Performance Targets

### Arbitrage Strategy
- **Target Profit**: 0.1-0.5% per trade
- **Win Rate**: >70%
- **Execution Speed**: <500ms
- **Min Trade Size**: $500 (Solana), $1000 (Base)

### Swing Trading Strategy
- **Target Profit**: 2-10% per trade
- **Win Rate**: >55%
- **Risk per Trade**: Max 3% loss
- **Hold Time**: 1-5 days

### Overall Targets
- **Monthly Return**: 5-15%
- **Maximum Drawdown**: <20%
- **Sharpe Ratio**: >1.0

## 🏗️ Project Structure

```
crypto-trading-bot/
├── src/
│   ├── main.py                 # Main trading bot entry point
│   ├── config/
│   │   └── settings.py         # Configuration management
│   ├── exchanges/
│   │   ├── solana_dex.py      # Jupiter, Orca, Raydium
│   │   └── base_dex.py        # Uniswap V3, Aerodrome
│   ├── strategies/
│   │   ├── arbitrage.py       # High-frequency arbitrage
│   │   └── swing_trading.py   # Technical analysis swing trades
│   ├── indicators/
│   │   └── technical.py       # RSI, EMA, MACD calculations
│   ├── risk/
│   │   └── manager.py         # Position sizing, stop losses
│   └── utils/
│       ├── wallet.py          # Wallet management
│       └── logger.py          # Performance tracking
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
├── generate_wallets.py       # Wallet generation script
├── env.example              # Environment template
└── README.md               # This file
```

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
```

### Adding New DEXs
1. Create new DEX class in `src/exchanges/`
2. Implement price fetching and trade execution
3. Add to strategy modules
4. Update configuration

### Adding New Indicators
1. Add indicator calculation in `src/indicators/technical.py`
2. Update swing trading strategy
3. Test with historical data

## ⚠️ Important Notes

### Security
- **Never commit private keys** to version control
- Use environment variables for sensitive data
- Start with small amounts for testing
- Monitor the bot continuously

### Risk Warnings
- Crypto trading involves significant risk
- Past performance doesn't guarantee future results
- Start with paper trading
- Only use funds you can afford to lose

### Gas Costs
- Solana: ~$0.001 per transaction
- Base: ~$0.50-2.00 per transaction
- Factor gas costs into profit calculations

## 📈 Monitoring

### Logs
The bot provides detailed logging for:
- Trade executions
- Arbitrage opportunities
- Technical signals
- Risk management events
- Performance metrics

### Performance Tracking
- Daily PnL tracking
- Win rate calculations
- Maximum drawdown monitoring
- Portfolio value updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for educational purposes. Use at your own risk.

## 🆘 Support

For issues and questions:
1. Check the logs for error messages
2. Verify your configuration
3. Ensure sufficient wallet balances
4. Test with paper trading first

## 🚨 Disclaimer

This software is provided "as is" without warranty. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.

---

**Happy Trading! 🚀** 