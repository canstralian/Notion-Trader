<div align="center">

# Crypto Grid Trading Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A production-grade multi-grid cryptocurrency trading system with real-time monitoring, risk management, and automated order execution.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Configuration](#-configuration) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

---

## Overview

This trading bot implements an automated grid trading strategy across multiple cryptocurrency pairs on Bybit. It features a real-time Streamlit dashboard for monitoring, a FastAPI backend for control operations, and comprehensive risk management including kill switches, stop-losses, and volatility breakers.

### What is Grid Trading?

Grid trading places buy and sell orders at preset price intervals within a defined range. When the price drops, buy orders are triggered. When the price rises, sell orders capture profit. This strategy excels in ranging/sideways markets.

```
Upper Bound ─────────────────── $99,000  ← Sell Zone
    │ ══════════════ Grid Level 12
    │ ══════════════ Grid Level 11
    │ ══════════════ Grid Level 10
    │        ...
    │ ══════════════ Grid Level 2
    │ ══════════════ Grid Level 1
Lower Bound ─────────────────── $95,500  ← Buy Zone
```

---

## ✨ Features

### Trading Engine
- **Multi-Pair Support** - Trade BTC, MNT, DOGE, PEPE simultaneously
- **Configurable Grids** - Customizable price ranges, grid counts, and investment per pair
- **Smart Order Placement** - Automatic buy/sell order management based on price movement
- **BTC Filter** - Optional filter to pause altcoin trading when BTC is volatile

### Risk Management
- **Kill Switch** - Emergency stop for all trading activity
- **Stop-Loss Triggers** - Per-pair stop-loss price monitoring
- **Volatility Breakers** - Automatic pause when price deviation exceeds thresholds
- **API Error Rate Monitoring** - Kill switch triggers if API failures exceed 2%
- **Drawdown Protection** - Maximum 30% drawdown limit

### Real-Time Dashboard
- **Live Grid Status** - Current prices, filled orders, P/L per pair
- **Risk Metrics** - Drawdown, error rates, system health indicators
- **Bot Controls** - Start, pause, resume, kill switch buttons
- **Market Overview** - Trending coins, 24h changes via CoinGecko

### Integrations
- **Bybit API v5** - REST + WebSocket for spot trading
- **TradingView Webhooks** - Signal-based trading triggers
- **Notion** - Legacy trade logging and portfolio tracking
- **PostgreSQL** - TimescaleDB-style OHLCV storage

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, for persistent storage)
- Bybit API credentials (for live trading)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crypto-grid-bot.git
   cd crypto-grid-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Start the dashboard**
   ```bash
   streamlit run app.py --server.port 5000
   ```

5. **Start the API server** (separate terminal)
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BYBIT_API_KEY` | Bybit API key | For live trading |
| `BYBIT_API_SECRET` | Bybit API secret | For live trading |
| `DATABASE_URL` | PostgreSQL connection string | Optional |
| `TRADINGVIEW_WEBHOOK_SECRET` | Webhook authentication | Optional |

> **Note:** Without Bybit credentials, the bot runs in mock mode with simulated prices.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard (:5000)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Grid Status │  │ Risk Panel  │  │ Bot Controls            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend (:8000)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Grid Engine  │  │ Risk Manager │  │ Alert Handler          │ │
│  └──────┬───────┘  └──────────────┘  └────────────────────────┘ │
└─────────┼───────────────────────────────────────────────────────┘
          │ REST/WebSocket
┌─────────▼───────────────────────────────────────────────────────┐
│                        Bybit API v5                              │
│         Spot Trading • Market Data • Account Balance            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | File | Description |
|-----------|------|-------------|
| **Dashboard** | `app.py` | Streamlit UI for monitoring and control |
| **API Server** | `api/main.py` | FastAPI endpoints for bot operations |
| **Grid Engine** | `services/grid_engine.py` | Core trading logic and order management |
| **Risk Manager** | `services/risk_manager.py` | Kill switches, stop-losses, volatility checks |
| **Data Ingestion** | `services/data_ingestion.py` | Real-time price feeds from Bybit |
| **Bybit Client** | `services/bybit_client.py` | API wrapper for Bybit v5 |
| **Alert Handler** | `services/alert_handler.py` | TradingView webhook processing |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

---

## ⚙️ Configuration

### Default Grid Parameters

| Pair | Price Range | Grids | Investment | Stop-Loss |
|------|-------------|-------|------------|-----------|
| BTC/USDT | $95,500 - $99,000 | 12 | $25,000 | $94,800 |
| MNT/USDT | $1.04 - $1.12 | 15 | $6,000 | $1.015 |
| DOGE/USDT | $0.129 - $0.145 | 18 | $1,500 | $0.120 |
| PEPE/USDT | $0.00000416 - $0.00000479 | 24 | $1,500 | $0.00000395 |

### Risk Thresholds

| Threshold | Value | Description |
|-----------|-------|-------------|
| Max Drawdown | 30% | Kill switch triggers if equity drops 30% |
| API Error Rate | 2% | Kill switch triggers if errors exceed 2% |
| Volatility Breakers | 2 | Kill switch if 2+ pairs show high volatility |
| Max Position Size | 50% | Single pair cannot exceed 50% of capital |

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for full configuration reference.

---

## 📡 API Reference

### Core Endpoints

```http
GET  /api/status          # Get system status
GET  /api/grids           # Get all grid states
POST /api/grids/{symbol}/start  # Start a specific grid
POST /api/pause           # Pause all trading
POST /api/resume          # Resume all trading
POST /api/kill            # Emergency stop (kill switch)
POST /api/rebalance       # Cancel and replace all orders
POST /api/tv-alert        # TradingView webhook receiver
```

### Example: Start a Grid

```bash
curl -X POST http://localhost:8000/api/grids/BTCUSDT/start
```

```json
{
  "status": "started",
  "symbol": "BTCUSDT",
  "result": {"orders_placed": 6}
}
```

See [docs/API.md](docs/API.md) for complete API documentation.

---

## 🎯 Target Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Fills/Day | 8-15 per bot | Order fill rate |
| Profit Capture | >85% | Percentage of moves captured |
| APR Target | 80-120% | Annual percentage return |
| Monthly Profit | 3-5% | Conservative monthly target |
| Order Latency | <500ms | Time to execute orders |

---

## 🛡 Security

This project handles sensitive financial operations. Please review our [Security Policy](SECURITY.md) for:

- Vulnerability reporting procedures
- API key management best practices
- Network security recommendations

**Never commit API keys or secrets to the repository.**

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

### Development Setup

```bash
# Clone and install dev dependencies
git clone https://github.com/yourusername/crypto-grid-bot.git
cd crypto-grid-bot
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black .
isort .
```

---

## 📁 Project Structure

```
crypto-grid-bot/
├── app.py                    # Streamlit dashboard
├── api/
│   └── main.py               # FastAPI backend
├── services/
│   ├── grid_engine.py        # Grid trading logic
│   ├── risk_manager.py       # Risk management
│   ├── bybit_client.py       # Bybit API wrapper
│   ├── data_ingestion.py     # Price feed service
│   └── alert_handler.py      # TradingView webhooks
├── models/
│   └── database.py           # SQLAlchemy models
├── config/
│   └── grid_configs.py       # Trading parameters
├── docs/
│   ├── ARCHITECTURE.md       # System design
│   ├── API.md                # API reference
│   └── CONFIGURATION.md      # Config guide
└── tests/                    # Test suite
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

**This software is for educational purposes only. Cryptocurrency trading carries significant financial risk. Past performance does not guarantee future results. Always do your own research and never trade with money you cannot afford to lose.**

The authors are not responsible for any financial losses incurred through the use of this software.

---

<div align="center">

**Built with ❤️ for the crypto trading community**

[Report Bug](../../issues/new?template=bug_report.md) • [Request Feature](../../issues/new?template=feature_request.md)

</div>
