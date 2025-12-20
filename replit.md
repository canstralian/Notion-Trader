# Crypto Trading Dashboard

## Overview
A web-based cryptocurrency trading application that integrates with Notion as a database to track trades, portfolio performance, and trading strategies.

## Core Features
- **Notion Integration**: Store and retrieve trading data (trades, portfolio holdings, profit/loss)
- **Real-time Crypto Prices**: Display cryptocurrency prices and market data via CoinGecko API
- **Trade Logging**: Log trades with details (coin, buy/sell price, quantity, date, notes) directly to Notion
- **Portfolio Summary**: View portfolio performance metrics pulled from Notion data
- **Trading Strategies**: Track and manage trading strategies

## Project Structure
```
├── app.py              # Main Streamlit application
├── notion_service.py   # Notion API integration service
├── crypto_api.py       # CoinGecko API integration for crypto prices
├── .streamlit/
│   └── config.toml     # Streamlit server configuration
└── replit.md           # Project documentation
```

## Tech Stack
- **Frontend**: Streamlit
- **Database**: Notion (via Notion API)
- **Crypto Data**: CoinGecko API (free tier)
- **Language**: Python 3.11

## Key Files

### app.py
Main Streamlit application with 4 tabs:
- Dashboard: Market overview, portfolio summary, trade history
- Trade: Log new trades with quick price reference
- Market: Detailed market data and trending coins
- Strategies: Manage trading strategies

### notion_service.py
Notion API service that:
- Authenticates via Replit's Notion connector
- Creates/manages three databases: Crypto Trades, Crypto Portfolio, Trading Strategies
- Provides CRUD operations for trades, portfolio, and strategies

### crypto_api.py
CoinGecko API integration:
- Fetches current prices for supported coins
- Gets market data (price changes, volume, market cap)
- 60-second caching to avoid rate limits

## Supported Cryptocurrencies
BTC, ETH, SOL, DOGE, XRP, ADA, DOT, AVAX, LINK, MATIC

## Style Guide
- Primary: #000000 (Notion black)
- Secondary: #37352F (warm grey)
- Accent: #2EAADC (crypto blue)
- Success: #0F7B6C (green)
- Warning: #FFB02E (gold)
- Background: #FFFFFF (white)
- Cards: #F7F6F3 (off-white)

## Running the App
```bash
streamlit run app.py --server.port 5000
```

## Recent Changes
- 2025-01-20: Initial implementation with full Notion integration
