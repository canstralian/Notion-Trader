# Crypto Trading Bot & Dashboard

## Overview
A production-grade multi-grid crypto trading system integrating Bybit API v5, PostgreSQL with TimescaleDB-style storage, and a real-time Streamlit dashboard for automated grid trading across multiple cryptocurrency pairs.

## Workflow Policy
**All enhancements or improvements to this project must be initiated by raising an issue first.** No development work should begin without a documented issue describing the enhancement/improvement.

## Core Features
- **Bybit API Integration**: REST + WebSocket for real-time market data and order execution
- **Multi-Grid Trading**: Automated grid trading across 4 pairs (BTC, MNT, DOGE, PEPE)
- **Real-time Dashboard**: Live monitoring of grid status, PnL, and system health
- **Risk Management**: Stop-loss triggers, kill switches, and position limits
- **TradingView Integration**: Webhook alerts for signal-based trading
- **Notion Integration**: Legacy trade logging and portfolio tracking (from v1)

## Capital Allocation
- **Total Capital**: 34K USDT
- **BTC/USDT**: 25K (95.5K-99K range, 12 grids)
- **MNT/USDT**: 6K (1.04-1.12 range, 15 grids)
- **DOGE/USDT**: Dynamic (0.129-0.145 range, 18 grids)
- **PEPE/USDT**: Dynamic (0.00000416-0.00000479 range, 24 grids, BTC filter critical)

## Project Structure
```
├── app.py                    # Main Streamlit dashboard
├── api/
│   └── main.py               # FastAPI backend with control endpoints
├── services/
│   ├── bybit_client.py       # Bybit API v5 integration
│   ├── grid_engine.py        # Grid trading logic
│   ├── data_ingestion.py     # Real-time OHLCV ingestion
│   ├── risk_manager.py       # Risk management & kill switches
│   └── alert_handler.py      # TradingView webhook handler
├── models/
│   └── database.py           # Database models and schema
├── config/
│   └── grid_configs.py       # Grid parameters for each pair
├── crypto_api.py             # CoinGecko API (market overview)
├── notion_service.py         # Notion integration (legacy)
└── replit.md                 # Project documentation
```

## Tech Stack
- **Frontend**: Streamlit (dashboard)
- **Backend**: FastAPI (API endpoints, WebSocket)
- **Database**: PostgreSQL with TimescaleDB-style hypertables
- **Cache**: In-memory with optional Redis
- **Exchange**: Bybit API v5
- **Signals**: TradingView Pine Script v5 webhooks
- **Language**: Python 3.11 (async patterns)

## Grid Trading Parameters

### BTC/USDT
- Price Range: 95,500 - 99,000 USDT
- Grid Count: 12
- Capital: 25,000 USDT
- Grid Spacing: ~291 USDT

### MNT/USDT
- Price Range: 1.04 - 1.12 USDT
- Grid Count: 15
- Capital: 6,000 USDT
- Grid Spacing: ~0.0053 USDT

### DOGE/USDT
- Price Range: 0.129 - 0.145 USDT
- Grid Count: 18
- Grid Spacing: ~0.00089 USDT

### PEPE/USDT
- Price Range: 0.00000416 - 0.00000479 USDT
- Grid Count: 24
- BTC Filter: Critical (only trade when BTC stable)
- Grid Spacing: ~0.0000000263 USDT

## Risk Management
- **Stop-Loss Triggers**: BTC <94.8K, MNT <1.015, PEPE <0.00000395
- **Kill Switches**: 2+ volatility breakers, API errors >2%, equity <-30%
- **Position Limits**: Per-pair and total exposure caps

## Target Metrics
- Fills/Day: 8-15 per bot
- Profit Capture: >85%
- APR Target: 80-120%
- Monthly Profit: 3-5%
- Latency: <500ms order execution

## API Endpoints
- `POST /api/kill` - Emergency stop all trading
- `POST /api/pause` - Pause specific bot
- `POST /api/resume` - Resume trading
- `POST /api/deploy` - Deploy new grid config
- `POST /api/rebalance` - Rebalance positions
- `POST /api/tv-alert` - TradingView webhook receiver

## Style Guide
- Primary: #000000 (Notion black)
- Secondary: #37352F (warm grey)
- Accent: #2EAADC (crypto blue)
- Success: #0F7B6C (green)
- Warning: #FFB02E (gold)
- Danger: #E03E3E (red)
- Background: #FFFFFF (white)
- Cards: #F7F6F3 (off-white)

## Environment Variables
- `BYBIT_API_KEY` - Bybit API key
- `BYBIT_API_SECRET` - Bybit API secret
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection (optional)
- `TRADINGVIEW_WEBHOOK_SECRET` - Webhook authentication

## Running the App
```bash
# Dashboard
streamlit run app.py --server.port 5000

# API Server (separate process)
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Recent Changes
- 2025-01-20: Initial crypto tracking dashboard with Notion integration
- 2025-01-20: Issue raised - Master Trading Bot & Dashboard System
