# BearTech Token Analysis Bot

A comprehensive Telegram bot for analyzing cryptocurrency token contracts with advanced security analysis, market data, and risk assessment.

## 🚀 Features

### Core Functionality

-   **Multi-Chain Support**: Ethereum, Binance Smart Chain (BSC), and Base
-   **Comprehensive Analysis**: Security, market data, liquidity, and risk assessment
-   **Real-Time Data**: Live data from multiple APIs with no "Unknown" values
-   **Honeypot Detection**: Advanced detection of honeypot tokens
-   **Beautiful Formatting**: Well-formatted Telegram messages with emojis and structure

### Security Analysis

-   ✅ Honeypot detection
-   ✅ Contract verification status
-   ✅ Tax analysis (buy/sell taxes)
-   ✅ Security flags (minting, pausing, blacklisting)
-   ✅ Ownership and proxy detection
-   ✅ Anti-whale mechanisms

### Market Data

-   💰 Real-time price and market cap
-   📊 Volume and liquidity analysis
-   📈 Price change tracking
-   🔄 Trading activity monitoring

### Holder Analysis

-   👥 Holder count and distribution
-   🐋 Whale detection
-   📊 Concentration analysis
-   🔍 Top holder percentages

### Deployer Information

-   👤 Deployer address and balance
-   📅 Contract creation history
-   🔍 Deployer verification status
-   ⚠️ Risk assessment

## 🛠️ Installation

### Prerequisites

-   Python 3.8 or higher
-   Telegram Bot Token
-   API keys for external services

### Setup

1. **Clone the repository**

    ```bash
    git clone <repository-url>
    cd BearTech
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables**

    ```bash
    cp .env.example .env
    # Edit .env with your API keys
    ```

4. **Run the bot**
    ```bash
    python -m src.bot.main
    ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# API Keys
GOPLUS_API_KEY=your_goplus_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key
BASESCAN_API_KEY=your_basescan_api_key
MORALIS_API_KEY=your_moralis_api_key

# Optional
REF_TAG=your_referral_tag
```

### API Keys Required

1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/botfather)
2. **GoPlus API Key**: For security analysis - [GoPlus Labs](https://gopluslabs.io/)
3. **Etherscan API Key**: For Ethereum data - [Etherscan](https://etherscan.io/apis)
4. **BSCScan API Key**: For BSC data - [BSCScan](https://bscscan.com/apis)
5. **BaseScan API Key**: For Base data - [BaseScan](https://basescan.org/apis)
6. **Moralis API Key**: For additional data - [Moralis](https://moralis.io/)

## 📱 Usage

### Commands

-   `/start` - Welcome message and bot introduction
-   `/help` - Detailed help and usage instructions
-   `/analyze <address>` - Analyze a specific token contract
-   `/chains` - Show supported blockchain networks
-   `/status` - Show bot status and statistics

### Basic Usage

1. **Start the bot**: Send `/start` to begin
2. **Analyze a token**: Send any contract address (e.g., `0x1234...`)
3. **View results**: Get comprehensive analysis with security, market, and risk data

### Example

```
User: 0x1234567890abcdef1234567890abcdef12345678

Bot: 🔷 TokenName (SYMBOL) ✅
     📋 BASIC INFO
     • Address: 0x1234...5678
     • Chain: Ethereum
     • Decimals: 18
     • Total Supply: 1.00B

     💰 MARKET DATA
     • Price: $0.001234
     • 24h Change: +5.67%
     • Market Cap: $1.23M
     • Liquidity: $456.78K

     🔒 SECURITY ANALYSIS
     • Verified: ✅ Yes
     • Buy Tax: 2.50%
     • Sell Tax: 2.50%
     • Open Source: ✅ Yes

     ⚠️ WARNINGS
     • Low liquidity detected

     💡 RECOMMENDATIONS
     • Token appears safe for trading
```

## 🏗️ Architecture

### Project Structure

```
BearTech/
├── src/
│   ├── config.py              # Configuration and API keys
│   ├── bot/
│   │   ├── main.py            # Bot entry point
│   │   └── handlers.py        # Message handlers
│   ├── services/
│   │   ├── goplus.py          # GoPlus Security API
│   │   ├── dexscreener.py     # DexScreener API
│   │   ├── explorer.py        # Explorer APIs (Etherscan, BSCScan, BaseScan)
│   │   ├── moralis.py         # Moralis API
│   │   ├── rpc.py             # RPC services
│   │   └── token_analyzer.py  # Main analysis orchestrator
│   ├── models/
│   │   ├── token.py           # Token data models
│   │   └── response.py        # Response formatting
│   └── utils/
│       ├── chain_detector.py  # Chain detection logic
│       ├── formatters.py      # Data formatting utilities
│       └── cache.py           # Caching mechanism
├── tests/
├── requirements.txt
├── .env
└── README.md
```

### API Integration

The bot integrates with multiple APIs in priority order:

1. **GoPlus** (Primary): Security analysis, honeypot detection, taxes
2. **DexScreener** (Fallback): Market data, supply, holders
3. **Explorer APIs**: Contract verification, age, deployer info
4. **Moralis** (Backup): Additional liquidity analysis
5. **RPC** (Last Resort): Basic contract info

### Data Flow

1. **Input Validation**: Validate contract address format
2. **Chain Detection**: Auto-detect blockchain network
3. **API Calls**: Concurrent calls to multiple APIs
4. **Data Aggregation**: Combine and validate results
5. **Risk Assessment**: Calculate risk levels and factors
6. **Response Formatting**: Create beautiful Telegram message
7. **Caching**: Store results for future requests

## 🔒 Security Features

### Honeypot Detection

-   Zero liquidity detection
-   High tax analysis
-   Trading restriction detection
-   Contract security flags

### Risk Assessment

-   **Safe**: Low risk, verified contract
-   **Low**: Minor concerns, proceed with caution
-   **Medium**: Moderate risk, consider carefully
-   **High**: High risk, avoid trading
-   **Honeypot**: Confirmed honeypot, DO NOT BUY

### Security Checks

-   Contract verification status
-   Owner privileges analysis
-   Minting capabilities
-   Pause functionality
-   Blacklist features
-   Proxy detection

## 📊 Performance

### Caching

-   In-memory caching with TTL
-   Separate caches for different data types
-   Automatic cleanup of expired entries
-   Configurable cache sizes

### Response Times

-   Average analysis time: < 10 seconds
-   Cached responses: < 1 second
-   Concurrent API calls for efficiency
-   Timeout handling and fallbacks

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Test Coverage

-   Unit tests for all services
-   Integration tests for API calls
-   Mock tests for external dependencies
-   Error handling tests

## 🚀 Deployment

### Local Development

```bash
python -m src.bot.main
```

### Production Deployment

1. **Using systemd** (Linux)

    ```bash
    sudo systemctl enable beartech-bot
    sudo systemctl start beartech-bot
    ```

2. **Using Docker**

    ```bash
    docker build -t beartech-bot .
    docker run -d --name beartech-bot beartech-bot
    ```

3. **Using PM2** (Node.js process manager)
    ```bash
    pm2 start src/bot/main.py --name beartech-bot
    ```

## 📈 Monitoring

### Logging

-   Structured logging with timestamps
-   Log levels: DEBUG, INFO, WARNING, ERROR
-   File and console output
-   Error tracking and reporting

### Metrics

-   Cache hit rates
-   API response times
-   Error rates
-   User activity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black src/
flake8 src/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Issues

-   Report bugs via GitHub Issues
-   Include logs and error messages
-   Provide steps to reproduce

### Contact

-   Telegram: [@YourBotUsername](https://t.me/YourBotUsername)
-   Email: support@beartech.com

## 🔄 Updates

### Version History

-   **v1.0.0**: Initial release with core functionality
-   **v1.1.0**: Added Base chain support
-   **v1.2.0**: Enhanced security analysis
-   **v1.3.0**: Improved caching and performance

### Roadmap

-   [ ] Additional blockchain support
-   [ ] Advanced charting features
-   [ ] Portfolio tracking
-   [ ] Price alerts
-   [ ] Social sentiment analysis

## ⚠️ Disclaimer

This bot is for informational purposes only. Always do your own research before making investment decisions. The bot's analysis should not be considered as financial advice.

## 🙏 Acknowledgments

-   GoPlus Labs for security analysis
-   DexScreener for market data
-   Etherscan, BSCScan, BaseScan for blockchain data
-   Moralis for additional token information
-   Python-Telegram-Bot library

---

**Made with ❤️ by the BearTech Team**



