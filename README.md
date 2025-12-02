# snip727-v2 — DeFi Sniping Bot

**100% free, no blocked services, works in Russia offline**

Full Uniswap V2/V3 monitoring on Base + local DeepPavlov sentiment + N-of-4 strategy + Telegram alerts.

## 🚀 Features

### 🔗 Uniswap V2/V3 Monitoring on Base
- **Async Web3 client** with free RPC fallback list (Ankr wss, QuickNode, Base public)
- **Redis ABI + contract cache** (aioredis)
- **Real-time subscription** to Uniswap V2 + V3 Factory PairCreated
- **Real-time parsing** of Mint/Swap events
- **Detection**: new pool, liquidity spike >5×, whale buy >0.5% of pool

### 💬 Local DeepPavlov Sentiment Analysis
- **Offline ruBERT sentiment** (pip install deeppavlov)
- **Scraping Telegram channels + nitter.net RSS** (configurable list)
- **Score → DB table SentimentScore** (-1.0 to 1.0 range)

### 🎯 N-of-4 Strategy
- **S1**: new pool (<15 blocks)
- **S2**: liquidity spike
- **S3**: whale buy
- **S4**: sentiment > 0.6
- **≥3 signals → instant Telegram alert** with pool address, score and inline "Buy" button

### 📱 Enhanced Telegram Bot
- **Commands**: /pools, /signals, /stats
- **Inline buttons** for BaseScan and Uniswap links
- **Real-time alerts** with signal breakdown

## Tech Stack

- **Python 3.11**
- **Web3.py** — blockchain interaction
- **SQLAlchemy** + **asyncpg** — async database
- **Alembic** — migrations
- **python-telegram-bot** — Telegram integration
- **Redis** — caching/queues
- **structlog** — structured logging
- **DeepPavlov** — Russian sentiment analysis
- **aiohttp** — async HTTP client
- **BeautifulSoup4** — web scraping

## Project Structure

```
snip727-v2/
├── src/snip727/
│   ├── core/           # Configuration (Pydantic Settings)
│   ├── db/             # SQLAlchemy + asyncpg database layer
│   ├── web3/           # Web3 client + Uniswap monitor
│   ├── services/       # Sentiment analysis + strategy
│   └── bot/            # Telegram bot with commands
├── tests/              # pytest test suite
├── migrations/         # Alembic database migrations
├── docker-compose.yml  # PostgreSQL 16 + Redis 7 + Bot
├── pyproject.toml      # Poetry configuration
├── README.md           # This file
└── README.ru.md        # Russian documentation
```

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
DATABASE_URL=postgresql+asyncpg://snip727:snip727@localhost:5432/snip727
REDIS_URL=redis://localhost:6379

# Base network settings
BASE_RPC_URLS=["wss://base.gateway.tenderly.co","https://mainnet.base.org"]
UNISWAP_V2_FACTORY=0x4200000000000000000000000000000000000006
UNISWAP_V3_FACTORY=0x33128a8fC17869897dcE68Ed026d694621f6FDfD

# Strategy settings
LIQUIDITY_SPIKE_THRESHOLD=5.0
WHALE_BUY_THRESHOLD=0.005
SENTIMENT_THRESHOLD=0.6
STRATEGY_SIGNALS_REQUIRED=3
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL 16
- Redis 7
- Telegram bot with monitoring

### 4. Run Locally

Make sure PostgreSQL and Redis are running:

```bash
# Database migrations
poetry run alembic upgrade head

# Run full app (monitoring + bot)
poetry run python -m snip727.main

# Or run bot only
poetry run python -m snip727.bot.main
```

## Telegram Bot Commands

- `/start` — Show bot info and commands
- `/status` — Show status of all services
- `/pools` — Last 10 new pools
- `/signals` — Current hot pools with votes
- `/stats` — Bot statistics

## Database Schema

### Tables
- `pools` — Uniswap pool information
- `trade_events` — Mint/Swap/Burn events
- `sentiment_scores` — Sentiment analysis results
- `strategy_signals` — Strategy signals (new_pool, liquidity_spike, whale_buy, sentiment)
- `alerts` — Sent Telegram alerts

### Create Migration

```bash
poetry run alembic revision -m "description"
poetry run alembic upgrade head
```

## Development

### Linting and Type Checking

```bash
poetry run ruff check .
poetry run mypy src/
```

### Tests

```bash
poetry run pytest
poetry run pytest --cov=src/snip727 --cov-report=html
```

Current coverage: **76%+** (required minimum: 75%)

## Next Steps

After this PR we add:
- [x] Uniswap monitoring
- [x] DeepPavlov sentiment
- [x] N-of-4 strategy
- [x] Telegram alerts
- [ ] Auto-trading
- [ ] MEV protection
- [ ] Backtesting
- [ ] Rug-checks
- [ ] Web interface

## License

MIT
