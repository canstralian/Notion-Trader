# Configuration Guide

Complete guide to configuring the Crypto Grid Trading Bot.

---

## Table of Contents

- [Environment Variables](#environment-variables)
- [Grid Parameters](#grid-parameters)
- [Risk Thresholds](#risk-thresholds)
- [Trading Settings](#trading-settings)
- [TradingView Integration](#tradingview-integration)
- [Database Configuration](#database-configuration)
- [Examples](#examples)

---

## Environment Variables

### Required for Live Trading

| Variable | Description | Example |
|----------|-------------|---------|
| `BYBIT_API_KEY` | Bybit API key | `AbC123...` |
| `BYBIT_API_SECRET` | Bybit API secret | `xYz789...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `BYBIT_TESTNET` | Use testnet API | `false` |
| `DATABASE_URL` | PostgreSQL connection | None (in-memory) |
| `TRADINGVIEW_WEBHOOK_SECRET` | Webhook HMAC secret | None (no validation) |

### Setting Environment Variables

**Linux/macOS:**
```bash
export BYBIT_API_KEY="your-api-key"
export BYBIT_API_SECRET="your-api-secret"
```

**Windows (PowerShell):**
```powershell
$env:BYBIT_API_KEY="your-api-key"
$env:BYBIT_API_SECRET="your-api-secret"
```

**Using .env file:**
```bash
# .env
BYBIT_API_KEY=your-api-key
BYBIT_API_SECRET=your-api-secret
BYBIT_TESTNET=true
DATABASE_URL=postgresql://user:pass@localhost:5432/trading
TRADINGVIEW_WEBHOOK_SECRET=random-32-char-secret
```

---

## Grid Parameters

Grid configurations are defined in `config/grid_configs.py`.

### GridParameters Class

```python
@dataclass
class GridParameters:
    symbol: str              # Trading pair (e.g., "BTCUSDT")
    lower_price: float       # Grid lower bound
    upper_price: float       # Grid upper bound
    grid_count: int          # Number of grid levels
    total_investment: float  # Total capital for this grid
    stop_loss: float         # Stop-loss trigger price (optional)
    take_profit: float       # Take-profit price (optional)
    btc_filter_enabled: bool # Pause when BTC volatile (default: False)
```

### Calculated Properties

| Property | Formula |
|----------|---------|
| `grid_spacing` | `(upper_price - lower_price) / grid_count` |
| `investment_per_grid` | `total_investment / grid_count` |
| `quantity_at_price(p)` | `investment_per_grid / p` |

### Default Configurations

```python
DEFAULT_GRID_CONFIGS = {
    "BTCUSDT": GridParameters(
        symbol="BTCUSDT",
        lower_price=95500.0,      # Lower bound
        upper_price=99000.0,      # Upper bound
        grid_count=12,            # 12 grid levels
        total_investment=25000.0, # $25K allocated
        stop_loss=94800.0,        # Stop at $94,800
        take_profit=None,         # No take-profit
        btc_filter_enabled=False  # No filter needed
    ),
    
    "MNTUSDT": GridParameters(
        symbol="MNTUSDT",
        lower_price=1.04,
        upper_price=1.12,
        grid_count=15,
        total_investment=6000.0,
        stop_loss=1.015,
        take_profit=None,
        btc_filter_enabled=False
    ),
    
    "DOGEUSDT": GridParameters(
        symbol="DOGEUSDT",
        lower_price=0.129,
        upper_price=0.145,
        grid_count=18,
        total_investment=1500.0,
        stop_loss=0.120,
        take_profit=None,
        btc_filter_enabled=False
    ),
    
    "PEPEUSDT": GridParameters(
        symbol="PEPEUSDT",
        lower_price=0.00000416,
        upper_price=0.00000479,
        grid_count=24,
        total_investment=1500.0,
        stop_loss=0.00000395,
        take_profit=None,
        btc_filter_enabled=True   # Uses BTC filter
    )
}
```

### Customizing Grid Parameters

To modify grid parameters, edit `config/grid_configs.py`:

```python
# Example: Add a new trading pair
DEFAULT_GRID_CONFIGS["ETHUSDT"] = GridParameters(
    symbol="ETHUSDT",
    lower_price=3200.0,
    upper_price=3800.0,
    grid_count=20,
    total_investment=10000.0,
    stop_loss=3000.0,
    btc_filter_enabled=True
)
```

### Grid Sizing Guidelines

| Market Condition | Recommended Grid Count | Spacing |
|------------------|------------------------|---------|
| Low volatility | 20-30 | Tight |
| Normal | 10-20 | Medium |
| High volatility | 5-10 | Wide |

**Rule of thumb:** Grid spacing should be at least 2x the typical spread to ensure profitability after fees.

---

## Risk Thresholds

Risk parameters are defined in `config/grid_configs.py`.

### RISK_THRESHOLDS

```python
RISK_THRESHOLDS = {
    "max_drawdown_percent": 30.0,      # Kill switch at 30% loss
    "max_api_error_rate": 2.0,         # Kill switch at 2% error rate
    "volatility_breaker_count": 2,     # Kill switch if 2+ pairs volatile
    "max_position_size_percent": 50.0, # Max 50% in single pair
}
```

### Threshold Descriptions

| Threshold | Purpose | Trigger Action |
|-----------|---------|----------------|
| `max_drawdown_percent` | Protect against large losses | Kill switch |
| `max_api_error_rate` | Detect API issues | Kill switch |
| `volatility_breaker_count` | Detect market-wide volatility | Kill switch |
| `max_position_size_percent` | Concentration limit | Block new orders |

### Customizing Risk Thresholds

```python
# More conservative settings
RISK_THRESHOLDS = {
    "max_drawdown_percent": 15.0,      # Tighter loss limit
    "max_api_error_rate": 1.0,         # Stricter API monitoring
    "volatility_breaker_count": 1,     # Single pair can trigger
    "max_position_size_percent": 30.0, # Lower concentration
}

# More aggressive settings
RISK_THRESHOLDS = {
    "max_drawdown_percent": 50.0,      # Wider loss tolerance
    "max_api_error_rate": 5.0,         # More API flexibility
    "volatility_breaker_count": 3,     # Need more pairs volatile
    "max_position_size_percent": 75.0, # Higher concentration allowed
}
```

---

## Trading Settings

Operational settings for trading behavior.

### TRADING_SETTINGS

```python
TRADING_SETTINGS = {
    "rate_limit_per_second": 10,        # Max API calls/second
    "order_timeout_seconds": 30,        # Order placement timeout
    "heartbeat_interval_seconds": 5,    # Main loop interval
    "price_update_interval_seconds": 1, # Price fetch frequency
    "pnl_update_interval_seconds": 60,  # P/L calculation frequency
}
```

### Yield Waterfall (Advanced)

```python
YIELD_WATERFALL = {
    "btc_profit_threshold_percent": 5.0, # Harvest at 5% profit
    "rebalance_trigger_percent": 10.0,   # Rebalance at 10% drift
    "friday_harvest_enabled": True,      # Weekly profit taking
}
```

---

## TradingView Integration

### Webhook Setup

1. **Generate webhook secret:**
   ```bash
   openssl rand -hex 32
   ```

2. **Set environment variable:**
   ```bash
   export TRADINGVIEW_WEBHOOK_SECRET="your-generated-secret"
   ```

3. **Configure TradingView alert:**
   - Webhook URL: `https://your-domain.com/api/tv-alert`
   - Message format: JSON

### Alert Message Format

```json
{
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": {{close}},
  "zone": "{{strategy.order.comment}}"
}
```

### Pine Script Example

```pinescript
//@version=5
strategy("Grid Bot Signals", overlay=true)

// Your strategy logic here
longCondition = crossover(sma(close, 14), sma(close, 28))
shortCondition = crossunder(sma(close, 14), sma(close, 28))

if (longCondition)
    strategy.entry("Long", strategy.long)
    alert('{"symbol":"' + syminfo.ticker + '","action":"buy","price":' + str.tostring(close) + '}', alert.freq_once_per_bar)

if (shortCondition)
    strategy.close("Long")
    alert('{"symbol":"' + syminfo.ticker + '","action":"sell","price":' + str.tostring(close) + '}', alert.freq_once_per_bar)
```

### Action Mapping

| Pine Script Action | Webhook `action` | Grid Bot Response |
|--------------------|------------------|-------------------|
| `strategy.long` | `"buy"` or `"long"` | Resume grid |
| `strategy.short` | `"sell"` or `"short"` | Pause grid |
| `strategy.close` | `"close"` | Cancel all orders |

---

## Database Configuration

### PostgreSQL Setup

1. **Create database:**
   ```sql
   CREATE DATABASE trading;
   CREATE USER tradingbot WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE trading TO tradingbot;
   ```

2. **Set connection string:**
   ```bash
   export DATABASE_URL="postgresql://tradingbot:secure_password@localhost:5432/trading"
   ```

### Schema Initialization

The database schema is automatically created on first run:

```python
from models.database import init_db
init_db()  # Creates all tables
```

### Tables Created

| Table | Purpose |
|-------|---------|
| `ohlcv` | Price candle data |
| `grid_configs` | Grid configuration snapshots |
| `grid_orders` | Individual grid orders |
| `trades` | Executed trades |
| `positions` | Current positions |
| `bot_state` | Bot status and metrics |
| `alerts` | TradingView alert history |
| `system_logs` | Application logs |

### Without Database

The bot functions without a database:
- Grid state stored in memory
- Lost on restart
- No trade history persistence

---

## Examples

### Conservative Setup (Beginners)

```python
# config/grid_configs.py

DEFAULT_GRID_CONFIGS = {
    "BTCUSDT": GridParameters(
        symbol="BTCUSDT",
        lower_price=90000.0,   # Wider range
        upper_price=100000.0,
        grid_count=10,         # Fewer grids
        total_investment=5000.0, # Smaller capital
        stop_loss=85000.0,     # Wider stop
        btc_filter_enabled=False
    ),
}

RISK_THRESHOLDS = {
    "max_drawdown_percent": 10.0,  # Tight stop
    "max_api_error_rate": 1.0,
    "volatility_breaker_count": 1,
    "max_position_size_percent": 25.0,
}
```

### Aggressive Setup (Experienced)

```python
# config/grid_configs.py

DEFAULT_GRID_CONFIGS = {
    "BTCUSDT": GridParameters(
        symbol="BTCUSDT",
        lower_price=96000.0,   # Tight range
        upper_price=98000.0,
        grid_count=20,         # Many grids
        total_investment=50000.0,
        stop_loss=95000.0,     # Tight stop
        btc_filter_enabled=False
    ),
    "PEPEUSDT": GridParameters(
        symbol="PEPEUSDT",
        lower_price=0.00000400,
        upper_price=0.00000500,
        grid_count=30,         # Many grids for volatile asset
        total_investment=5000.0,
        stop_loss=0.00000350,
        btc_filter_enabled=True
    ),
}

RISK_THRESHOLDS = {
    "max_drawdown_percent": 40.0,
    "max_api_error_rate": 3.0,
    "volatility_breaker_count": 3,
    "max_position_size_percent": 60.0,
}
```

### Multi-Exchange (Future)

```python
# Example configuration for multiple exchanges
EXCHANGE_CONFIGS = {
    "bybit": {
        "api_key_env": "BYBIT_API_KEY",
        "api_secret_env": "BYBIT_API_SECRET",
        "testnet": False,
    },
    "binance": {
        "api_key_env": "BINANCE_API_KEY",
        "api_secret_env": "BINANCE_API_SECRET",
        "testnet": False,
    },
}
```

---

## Configuration Checklist

Before going live:

- [ ] API keys set and tested on testnet
- [ ] Grid ranges appropriate for current market
- [ ] Investment amounts verified
- [ ] Stop-losses configured
- [ ] Risk thresholds reviewed
- [ ] Webhook secret generated (if using TradingView)
- [ ] Database connected (for production)
- [ ] Monitoring/alerts configured
