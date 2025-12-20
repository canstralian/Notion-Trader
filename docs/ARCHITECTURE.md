# System Architecture

This document describes the technical architecture of the Crypto Grid Trading Bot, including system design, data flow, and component interactions.

---

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Grid Trading Logic](#grid-trading-logic)
- [Risk Management](#risk-management)
- [Database Schema](#database-schema)
- [Integration Points](#integration-points)

---

## Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────┐              ┌───────────────────────────────┐   │
│  │  Streamlit Dashboard  │              │  TradingView Alerts           │   │
│  │  - Grid monitoring    │              │  - Pine Script signals        │   │
│  │  - Risk metrics       │              │  - Webhook payloads           │   │
│  │  - Bot controls       │              │                               │   │
│  └───────────┬───────────┘              └───────────────┬───────────────┘   │
│              │ HTTP                                      │ HTTP POST        │
└──────────────┼───────────────────────────────────────────┼──────────────────┘
               │                                           │
┌──────────────▼───────────────────────────────────────────▼──────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         FastAPI Server (:8000)                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │ Grid API    │  │ Risk API    │  │ Alert API   │  │ Price API  │  │    │
│  │  │ /api/grids  │  │ /api/risk   │  │ /api/tv-*   │  │ /api/prices│  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
               │                    │                    │
┌──────────────▼────────────────────▼────────────────────▼────────────────────┐
│                            SERVICE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   Grid Engine   │  │  Risk Manager   │  │    Data Ingestion           │  │
│  │  - Order logic  │  │  - Kill switch  │  │    - Price polling          │  │
│  │  - Fill checks  │  │  - Stop-loss    │  │    - WebSocket stream       │  │
│  │  - P/L tracking │  │  - Volatility   │  │    - Cache management       │  │
│  └────────┬────────┘  └─────────────────┘  └──────────────┬──────────────┘  │
│           │                                                │                 │
│  ┌────────▼────────────────────────────────────────────────▼──────────────┐ │
│  │                         Bybit Client                                    │ │
│  │  - REST API wrapper    - WebSocket handler    - Signature generation   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
               │                                           │
┌──────────────▼───────────────────────────────────────────▼──────────────────┐
│                          EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   Bybit API v5  │  │   CoinGecko     │  │   PostgreSQL                │  │
│  │  - Spot trading │  │  - Market data  │  │   - OHLCV storage           │  │
│  │  - Account      │  │  - Trending     │  │   - Trade history           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Streamlit Dashboard (`app.py`)

The primary user interface for monitoring and control.

**Responsibilities:**
- Display real-time grid status and prices
- Show risk metrics and system health
- Provide bot control buttons
- Market overview and trending coins

**Key Features:**
- `@st.cache_resource` for persistent engine instances
- Tabbed interface for organization
- Auto-refresh via polling

**Component Tree:**
```
app.py
├── render_grid_status()      # Grid cards with prices, P/L
├── render_risk_dashboard()   # Drawdown, error rate, kill switch
├── render_controls()         # Start/pause/resume/kill buttons
├── render_market_overview()  # CoinGecko market data
├── render_grid_config()      # Configuration display
├── render_pnl_summary()      # Aggregate P/L table
└── render_notion_trades()    # Legacy Notion integration
```

### 2. FastAPI Backend (`api/main.py`)

RESTful API for programmatic control and webhooks.

**Responsibilities:**
- Expose grid operations via HTTP endpoints
- Handle TradingView webhook alerts
- Manage service lifecycle
- Provide system status

**Lifecycle Management:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    grid_engine = GridEngine()
    grid_engine.initialize_all_grids()
    risk_manager = RiskManager()
    
    yield  # Application runs
    
    # Shutdown
    grid_engine.stop()
    ingestion_service.stop_polling()
```

### 3. Grid Engine (`services/grid_engine.py`)

Core trading logic and order management.

**State Management:**
```python
@dataclass
class GridState:
    symbol: str
    params: GridParameters
    levels: List[GridLevel]
    current_price: float
    status: str  # "stopped" | "running" | "paused"
    total_buys: int
    total_sells: int
    realized_pnl: float
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `initialize_grid()` | Create grid levels from parameters |
| `place_grid_orders()` | Place buy/sell orders at grid levels |
| `check_fills()` | Check for filled orders and update state |
| `cancel_all_orders()` | Cancel all open orders for a symbol |
| `run_loop()` | Main event loop for continuous operation |

### 4. Risk Manager (`services/risk_manager.py`)

Monitors risk metrics and triggers protective actions.

**Kill Switch Conditions:**
```python
# Automatic triggers
if drawdown_percent >= 30.0:      # Max drawdown exceeded
if api_error_rate >= 2.0:         # API reliability issue
if volatility_breakers >= 2:      # Market too volatile
```

**Price Monitoring:**
```python
def record_price(symbol: str, price: float):
    # Maintain rolling window of last 100 prices
    # Calculate volatility for breaker detection
```

### 5. Bybit Client (`services/bybit_client.py`)

API wrapper for Bybit exchange.

**Features:**
- Async HTTP client with `aiohttp`
- HMAC signature generation for authenticated requests
- WebSocket support for real-time data
- Mock client for testing without credentials

**Request Flow:**
```
1. Generate timestamp
2. Create signature: HMAC-SHA256(timestamp + api_key + recv_window + params)
3. Set authentication headers
4. Execute request
5. Validate response code
6. Return result or raise exception
```

### 6. Data Ingestion (`services/data_ingestion.py`)

Real-time price feed management.

**Modes:**
1. **Polling Mode**: REST API calls at configurable intervals
2. **WebSocket Mode**: Real-time streaming (preferred)

**Fallback Behavior:**
```python
async def start_websocket():
    try:
        await client.connect_websocket(symbols, on_message)
    except Exception:
        logger.info("Falling back to polling mode")
        await self.start_polling()
```

---

## Data Flow

### Order Placement Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Dashboard │────▶│  FastAPI    │────▶│ Grid Engine │────▶│ Bybit API   │
│   Button    │     │  Endpoint   │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ Risk Check  │     │ Update State│
                    │ - Kill SW   │     │ - Orders    │
                    │ - Stop Loss │     │ - P/L       │
                    └─────────────┘     └─────────────┘
```

### Price Update Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Bybit WS/   │────▶│   Data      │────▶│   Price     │
│ REST API    │     │   Ingestion │     │   Cache     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Grid Engine │ │Risk Manager │ │ Dashboard   │
    │ (fill check)│ │(volatility) │ │ (display)   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### TradingView Alert Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ TradingView │────▶│  Webhook    │────▶│   Alert     │────▶│ Grid Engine │
│   Alert     │     │  Endpoint   │     │   Handler   │     │   Action    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Validate   │     │ Map to Grid │
                    │  Signature  │     │   Action    │
                    └─────────────┘     └─────────────┘
                    
Alert Actions:
- "buy"/"long"  → Resume grid
- "sell"/"short" → Pause grid
- "close"       → Stop grid
```

---

## Grid Trading Logic

### Grid Level Structure

```
Price: $99,000 ──────────────────────────────── Upper Bound
         │
         │   Grid Level 11: $98,708.33  ────── Sell zone
         │   Grid Level 10: $98,416.67
         │   Grid Level 9:  $98,125.00
         │   Grid Level 8:  $97,833.33
         │   Grid Level 7:  $97,541.67
         │   Grid Level 6:  $97,250.00  ────── Current price
         │   Grid Level 5:  $96,958.33
         │   Grid Level 4:  $96,666.67
         │   Grid Level 3:  $96,375.00
         │   Grid Level 2:  $96,083.33
         │   Grid Level 1:  $95,791.67  ────── Buy zone
         │
Price: $95,500 ──────────────────────────────── Lower Bound

Grid Spacing = (Upper - Lower) / Grid Count
             = ($99,000 - $95,500) / 12
             = $291.67
```

### Order State Machine

```
                    ┌──────────────┐
                    │   INITIAL    │
                    └──────┬───────┘
                           │ price < level
                           ▼
              ┌────────────────────────┐
              │  BUY ORDER PLACED      │
              │  buy_order_id = "..."  │
              └────────────┬───────────┘
                           │ order filled
                           ▼
              ┌────────────────────────┐
              │  HOLDING POSITION      │
              │  buy_filled = true     │
              └────────────┬───────────┘
                           │ price > level + spacing
                           ▼
              ┌────────────────────────┐
              │  SELL ORDER PLACED     │
              │  sell_order_id = "..." │
              └────────────┬───────────┘
                           │ order filled
                           ▼
              ┌────────────────────────┐
              │  PROFIT CAPTURED       │◀───┐
              │  realized_pnl += profit│    │
              └────────────┬───────────┘    │
                           │ reset          │
                           └────────────────┘
```

### Profit Calculation

```python
profit_per_grid = quantity * grid_spacing

# Example for BTC:
# investment_per_grid = $25,000 / 12 = $2,083.33
# quantity = $2,083.33 / $97,000 = 0.02147 BTC
# grid_spacing = $291.67
# profit = 0.02147 * $291.67 = $6.26 per fill
```

---

## Risk Management

### Multi-Layer Protection

```
Layer 1: Pre-Trade Checks
├── Kill switch status
├── Stop-loss price check
├── Volatility breaker check
└── BTC filter (for altcoins)

Layer 2: Runtime Monitoring
├── Drawdown calculation
├── API error rate tracking
├── Price deviation detection
└── Position size limits

Layer 3: Emergency Response
├── Automatic kill switch
├── Cancel all orders
├── Stop all engines
└── Log incident
```

### Volatility Breaker Logic

```python
def check_volatility_breaker(symbol: str) -> bool:
    prices = last_10_prices[symbol]
    avg = sum(prices) / len(prices)
    max_deviation = max(abs(p - avg) / avg * 100 for p in prices)
    return max_deviation > 5.0  # 5% deviation triggers breaker
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   GridConfig    │       │    GridOrder    │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ symbol          │   │   │ grid_config_id  │◀──┘
│ lower_price     │   └──▶│ grid_level      │
│ upper_price     │       │ price           │
│ grid_count      │       │ quantity        │
│ total_investment│       │ side            │
│ stop_loss       │       │ order_id        │
│ status          │       │ status          │
└─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│     Trade       │       │    Position     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ symbol          │       │ symbol (unique) │
│ side            │       │ quantity        │
│ price           │       │ avg_entry_price │
│ quantity        │       │ realized_pnl    │
│ pnl             │       │ unrealized_pnl  │
│ executed_at     │       └─────────────────┘
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│     OHLCV       │       │     Alert       │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ symbol          │       │ source          │
│ timestamp       │       │ symbol          │
│ open/high/low   │       │ alert_type      │
│ close/volume    │       │ message         │
│ interval        │       │ processed       │
└─────────────────┘       └─────────────────┘
```

---

## Integration Points

### Bybit API v5

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v5/market/tickers` | GET | Current price |
| `/v5/market/kline` | GET | OHLCV data |
| `/v5/order/create` | POST | Place order |
| `/v5/order/cancel` | POST | Cancel order |
| `/v5/order/realtime` | GET | Open orders |
| `/v5/account/wallet-balance` | GET | Account balance |

### TradingView Webhooks

**Expected Payload:**
```json
{
  "symbol": "BTCUSDT",
  "action": "buy",
  "price": 97250.00,
  "zone": "support"
}
```

**Response Actions:**
| Action | Grid Operation |
|--------|----------------|
| `buy`, `long` | Resume grid |
| `sell`, `short` | Pause grid |
| `close` | Stop grid |

### CoinGecko API

Used for market overview data (non-trading):
- `/simple/price` - Current prices
- `/coins/markets` - Market data
- `/search/trending` - Trending coins

---

## Scalability Considerations

### Current Limitations

- Single-process architecture
- In-memory state (lost on restart)
- Polling-based updates (configurable interval)

### Future Improvements

1. **State Persistence**: Redis for grid state
2. **Horizontal Scaling**: Queue-based order processing
3. **High Availability**: Leader election for order placement
4. **Performance**: Connection pooling for database

---

## Deployment Architecture

### Single Server (Current)

```
┌─────────────────────────────────────────┐
│              Replit Server              │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Streamlit   │  │ FastAPI         │   │
│  │ :5000       │  │ :8000           │   │
│  └─────────────┘  └─────────────────┘   │
│           │              │              │
│           └──────┬───────┘              │
│                  │                      │
│  ┌───────────────▼───────────────────┐  │
│  │      PostgreSQL (Neon)            │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Production (Recommended)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Load      │────▶│  Dashboard  │────▶│  API Server │
│   Balancer  │     │  Instances  │     │  Instances  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────┐
                    │                          ▼      │
              ┌─────────────┐          ┌─────────────┐│
              │   Redis     │          │ PostgreSQL  ││
              │   (State)   │          │ (Persistent)││
              └─────────────┘          └─────────────┘│
                    └─────────────────────────────────┘
```
