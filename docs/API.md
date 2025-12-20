# API Reference

Complete reference for the Crypto Grid Trading Bot REST API.

**Base URL:** `http://localhost:8000`

---

## Table of Contents

- [Authentication](#authentication)
- [Response Format](#response-format)
- [Endpoints](#endpoints)
  - [Health & Status](#health--status)
  - [Grid Operations](#grid-operations)
  - [Risk Management](#risk-management)
  - [Price Data](#price-data)
  - [TradingView Alerts](#tradingview-alerts)
- [Error Codes](#error-codes)
- [Rate Limits](#rate-limits)

---

## Authentication

Currently, the API does not require authentication for local development. For production deployments, implement API key authentication.

### Webhook Authentication

TradingView webhooks validate using HMAC-SHA256 signatures:

```http
X-Webhook-Signature: <hmac_sha256_signature>
```

---

## Response Format

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-01-20T12:00:00Z"
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Endpoints

### Health & Status

#### GET /

Root endpoint. Returns basic server status.

**Response:**
```json
{
  "status": "running",
  "timestamp": "2024-01-20T12:00:00.000Z"
}
```

---

#### GET /health

Health check endpoint for load balancers and monitoring.

**Response:**
```json
{
  "status": "healthy",
  "grid_engine": true,
  "risk_manager": true,
  "timestamp": "2024-01-20T12:00:00.000Z"
}
```

---

#### GET /api/status

Comprehensive system status including all grids and risk metrics.

**Response:**
```json
{
  "grids": {
    "BTCUSDT": {
      "symbol": "BTCUSDT",
      "status": "running",
      "current_price": 97250.00,
      "lower_price": 95500.00,
      "upper_price": 99000.00,
      "grid_count": 12,
      "filled_levels": 3,
      "pending_buys": 4,
      "pending_sells": 2,
      "total_buys": 15,
      "total_sells": 12,
      "realized_pnl": 75.50,
      "last_update": "2024-01-20T12:00:00.000Z"
    }
  },
  "risk": {
    "total_equity": 34250.00,
    "initial_equity": 34000.00,
    "drawdown_percent": -0.74,
    "api_error_rate": 0.12,
    "volatility_breakers": 0,
    "kill_switch_triggered": false,
    "kill_switch_reason": null
  },
  "timestamp": "2024-01-20T12:00:00.000Z"
}
```

---

### Grid Operations

#### GET /api/grids

Get status of all configured grids.

**Response:**
```json
{
  "BTCUSDT": {
    "symbol": "BTCUSDT",
    "status": "running",
    "current_price": 97250.00,
    "total_buys": 15,
    "total_sells": 12,
    "realized_pnl": 75.50
  },
  "MNTUSDT": { ... },
  "DOGEUSDT": { ... },
  "PEPEUSDT": { ... }
}
```

---

#### GET /api/grids/{symbol}

Get status of a specific grid.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `symbol` | path | Trading pair (e.g., `BTCUSDT`) |

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "status": "running",
  "current_price": 97250.00,
  "lower_price": 95500.00,
  "upper_price": 99000.00,
  "grid_count": 12,
  "filled_levels": 3,
  "pending_buys": 4,
  "pending_sells": 2,
  "total_buys": 15,
  "total_sells": 12,
  "realized_pnl": 75.50,
  "last_update": "2024-01-20T12:00:00.000Z"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 404 | Grid not found |
| 503 | Grid engine not initialized |

---

#### POST /api/grids/{symbol}/start

Start trading for a specific grid. Places initial grid orders.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `symbol` | path | Trading pair (e.g., `BTCUSDT`) |

**Response:**
```json
{
  "status": "started",
  "symbol": "BTCUSDT",
  "result": {
    "orders_placed": 6
  }
}
```

**Blocked Response (Risk Check Failed):**
```json
{
  "status": "blocked",
  "symbol": "BTCUSDT",
  "reason": "Stop-loss triggered for BTCUSDT"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 403 | Kill switch active |
| 404 | Grid not found |
| 503 | Grid engine not initialized |

---

#### POST /api/pause

Pause all grids. Cancels all open orders.

**Response:**
```json
{
  "status": "paused",
  "results": {
    "BTCUSDT": { "status": "paused" },
    "MNTUSDT": { "status": "paused" },
    "DOGEUSDT": { "status": "paused" },
    "PEPEUSDT": { "status": "paused" }
  }
}
```

---

#### POST /api/pause/{symbol}

Pause a specific grid.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `symbol` | path | Trading pair |

**Response:**
```json
{
  "status": "paused",
  "symbol": "BTCUSDT",
  "result": { "status": "paused" }
}
```

---

#### POST /api/resume

Resume all paused grids. Re-places grid orders.

**Response:**
```json
{
  "status": "resumed",
  "results": {
    "BTCUSDT": { "orders_placed": 6 },
    "MNTUSDT": { "orders_placed": 8 }
  }
}
```

---

#### POST /api/resume/{symbol}

Resume a specific grid.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `symbol` | path | Trading pair |

**Response:**
```json
{
  "status": "resumed",
  "symbol": "BTCUSDT",
  "result": { "orders_placed": 6 }
}
```

---

#### POST /api/rebalance

Cancel all orders and re-place based on current prices.

**Response:**
```json
{
  "status": "rebalanced",
  "results": {
    "BTCUSDT": { "orders_placed": 6 },
    "MNTUSDT": { "orders_placed": 8 },
    "DOGEUSDT": { "orders_placed": 9 },
    "PEPEUSDT": { "orders_placed": 12 }
  }
}
```

---

#### POST /api/deploy

Deploy or update grid configuration.

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "lower_price": 95000.00,
  "upper_price": 100000.00,
  "grid_count": 15,
  "total_investment": 30000.00
}
```

**Response:**
```json
{
  "status": "deployed",
  "symbol": "BTCUSDT",
  "config": {
    "symbol": "BTCUSDT",
    "lower_price": 95000.00,
    "upper_price": 100000.00,
    "grid_count": 15,
    "total_investment": 30000.00
  }
}
```

---

### Risk Management

#### GET /api/risk

Get current risk metrics and status.

**Response:**
```json
{
  "total_equity": 34250.00,
  "initial_equity": 34000.00,
  "drawdown_percent": -0.74,
  "api_error_rate": 0.12,
  "volatility_breakers": 0,
  "kill_switch_triggered": false,
  "kill_switch_reason": null,
  "potential_kill_reason": null,
  "last_check": "2024-01-20T12:00:00.000Z"
}
```

---

#### POST /api/kill

**EMERGENCY** - Activate kill switch. Stops all trading immediately.

**Response:**
```json
{
  "status": "killed",
  "results": {
    "BTCUSDT": { "cancelled": 6 },
    "MNTUSDT": { "cancelled": 8 },
    "DOGEUSDT": { "cancelled": 9 },
    "PEPEUSDT": { "cancelled": 12 }
  }
}
```

**⚠️ Warning:** This action:
- Cancels ALL open orders
- Stops ALL grid engines
- Requires manual reset to resume

---

#### POST /api/reset-kill

Reset the kill switch to allow trading to resume.

**Response:**
```json
{
  "status": "reset"
}
```

---

### Price Data

#### GET /api/prices

Get current prices for all configured pairs.

**Response:**
```json
{
  "BTCUSDT": {
    "price": 97250.00,
    "bid": 97248.50,
    "ask": 97251.50,
    "volume_24h": 15234567890.00,
    "timestamp": "2024-01-20T12:00:00.000Z"
  },
  "MNTUSDT": { ... },
  "DOGEUSDT": { ... },
  "PEPEUSDT": { ... }
}
```

---

### TradingView Alerts

#### POST /api/tv-alert

Receive and process TradingView webhook alerts.

**Headers:**
```http
Content-Type: application/json
X-Webhook-Signature: <hmac_sha256_hex>  (optional, if secret configured)
```

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "action": "buy",
  "price": 97250.00,
  "zone": "support"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Trading pair |
| `action` | string | Yes | `buy`, `sell`, `long`, `short`, `close` |
| `price` | float | No | Current price when alert triggered |
| `zone` | string | No | Price zone identifier |

**Response:**
```json
{
  "alert": "BTCUSDT",
  "action": "resume",
  "grid_result": { "orders_placed": 6 }
}
```

**Action Mapping:**
| Alert Action | Grid Operation |
|--------------|----------------|
| `buy`, `long` | Resume grid |
| `sell`, `short` | Pause grid |
| `close` | Stop grid (cancel all orders) |

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Failed to parse alert |
| 401 | Invalid webhook signature |
| 403 | Kill switch active |
| 503 | Services not initialized |

---

#### GET /api/alerts

Get recent alert history and statistics.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `symbol` | query | Filter by symbol (optional) |
| `limit` | query | Max alerts to return (default: 50) |

**Response:**
```json
{
  "alerts": [
    {
      "symbol": "BTCUSDT",
      "action": "buy",
      "price": 97250.00,
      "zone": "support",
      "timestamp": "2024-01-20T12:00:00.000Z",
      "validated": true
    }
  ],
  "stats": {
    "total": 150,
    "by_symbol": {
      "BTCUSDT": 80,
      "MNTUSDT": 40,
      "DOGEUSDT": 30
    },
    "by_action": {
      "buy": 85,
      "sell": 65
    },
    "last_alert": "2024-01-20T12:00:00.000Z"
  }
}
```

---

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid signature |
| 403 | Forbidden - Kill switch active |
| 404 | Not Found - Resource doesn't exist |
| 503 | Service Unavailable - Service not initialized |

### Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

---

## Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Read operations | 100/minute |
| Write operations | 20/minute |
| Webhook alerts | 60/minute |

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705754400
```

---

## Examples

### cURL

**Get system status:**
```bash
curl http://localhost:8000/api/status
```

**Start a grid:**
```bash
curl -X POST http://localhost:8000/api/grids/BTCUSDT/start
```

**Trigger kill switch:**
```bash
curl -X POST http://localhost:8000/api/kill
```

**Send TradingView alert:**
```bash
curl -X POST http://localhost:8000/api/tv-alert \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "action": "buy", "price": 97250}'
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get status
response = requests.get(f"{BASE_URL}/api/status")
status = response.json()
print(f"BTC Grid: {status['grids']['BTCUSDT']['status']}")

# Start grid
response = requests.post(f"{BASE_URL}/api/grids/BTCUSDT/start")
result = response.json()
print(f"Orders placed: {result['result']['orders_placed']}")

# Emergency stop
response = requests.post(f"{BASE_URL}/api/kill")
print("Kill switch activated!")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000';

// Get status
const status = await fetch(`${BASE_URL}/api/status`).then(r => r.json());
console.log(`BTC Grid: ${status.grids.BTCUSDT.status}`);

// Start grid
const result = await fetch(`${BASE_URL}/api/grids/BTCUSDT/start`, {
  method: 'POST'
}).then(r => r.json());
console.log(`Orders placed: ${result.result.orders_placed}`);
```
