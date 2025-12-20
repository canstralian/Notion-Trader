# Security Policy

## Overview

This project handles sensitive financial operations and API credentials. Security is a top priority. This document outlines our security practices and how to report vulnerabilities.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

### Do NOT

- Open a public GitHub issue for security vulnerabilities
- Share vulnerability details in public forums
- Exploit vulnerabilities for personal gain

### Do

1. **Email us privately** at [security@yourdomain.com] with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any suggested fixes

2. **Allow 48 hours** for initial response

3. **Work with us** to understand and resolve the issue

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Depends on severity (critical: 24-72 hours)
- **Credit**: Public acknowledgment (if desired) after fix is deployed

---

## Security Best Practices

### API Credentials

#### Storage

```bash
# GOOD: Use environment variables
export BYBIT_API_KEY="your-key-here"
export BYBIT_API_SECRET="your-secret-here"

# BAD: Never hardcode in source files
api_key = "abc123"  # NEVER DO THIS
```

#### Bybit API Setup

1. **Create API keys with minimal permissions**
   - Enable: Spot Trading
   - Disable: Withdrawals, Transfers, Sub-account access

2. **Use IP whitelisting**
   - Restrict API access to your server's IP only
   - Update whitelist when infrastructure changes

3. **Rotate keys regularly**
   - Generate new keys every 90 days
   - Revoke old keys immediately after rotation

### Environment Configuration

#### Required Secrets

| Variable | Purpose | Notes |
|----------|---------|-------|
| `BYBIT_API_KEY` | Exchange authentication | Read-only if possible |
| `BYBIT_API_SECRET` | Request signing | Never log this |
| `TRADINGVIEW_WEBHOOK_SECRET` | Webhook validation | Use strong random string |
| `DATABASE_URL` | Database connection | Use SSL in production |

#### Example .env File

```bash
# .env (NEVER COMMIT THIS FILE)
BYBIT_API_KEY=your-api-key
BYBIT_API_SECRET=your-api-secret
BYBIT_TESTNET=true  # Use testnet for development
DATABASE_URL=postgresql://user:pass@localhost:5432/trading
TRADINGVIEW_WEBHOOK_SECRET=random-32-char-string
```

#### .gitignore Entry

```gitignore
# Environment files
.env
.env.local
.env.production
*.env

# Secrets
secrets/
*.pem
*.key
```

---

## Network Security

### Production Deployment

1. **Use HTTPS only**
   - TLS 1.2 or higher
   - Valid SSL certificates
   - HSTS headers enabled

2. **Firewall Rules**
   ```
   # Allow only necessary ports
   - 443/tcp (HTTPS)
   - 22/tcp (SSH, restricted IPs)
   
   # Block direct database access from internet
   - 5432/tcp (PostgreSQL, internal only)
   ```

3. **API Security**
   - Rate limiting enabled
   - CORS restricted to known origins
   - Authentication required for sensitive endpoints

### Webhook Security

```python
# Validate TradingView webhooks
import hmac
import hashlib

def validate_webhook(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Code Security

### Input Validation

```python
# Always validate external inputs
def place_order(symbol: str, price: float, quantity: float):
    # Validate symbol format
    if not re.match(r'^[A-Z]{3,10}USDT$', symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    # Validate numeric ranges
    if price <= 0:
        raise ValueError("Price must be positive")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    
    # Proceed with order
    ...
```

### Logging Safety

```python
# GOOD: Log safely without secrets
logger.info(f"Placing order for {symbol}")
logger.debug(f"Order details: price={price}, qty={quantity}")

# BAD: Never log sensitive data
logger.info(f"API Key: {api_key}")  # NEVER
logger.debug(f"Request headers: {headers}")  # May contain auth
```

### Dependency Security

1. **Keep dependencies updated**
   ```bash
   pip install pip-audit
   pip-audit  # Check for known vulnerabilities
   ```

2. **Pin versions in requirements.txt**
   ```
   fastapi==0.104.1
   aiohttp==3.9.0
   sqlalchemy==2.0.23
   ```

3. **Review new dependencies before adding**

---

## Risk Controls

### Kill Switch

The kill switch is a critical safety feature:

```python
# Trigger conditions (automatic)
- Drawdown exceeds 30%
- API error rate exceeds 2%
- 2+ pairs show extreme volatility

# Manual trigger
POST /api/kill  # Emergency stop
```

### Order Limits

```python
# Built-in protections
MAX_POSITION_SIZE_PERCENT = 50  # Single pair limit
MAX_ORDER_VALUE = 10000  # USD per order
MAX_DAILY_ORDERS = 1000  # Rate limit
```

### Monitoring Alerts

Set up alerts for:

- [ ] Kill switch activation
- [ ] Stop-loss triggers
- [ ] API authentication failures
- [ ] Unusual order patterns
- [ ] Balance changes > threshold

---

## Incident Response

### If You Suspect a Breach

1. **Immediately**
   - Trigger kill switch: `POST /api/kill`
   - Revoke API keys on Bybit
   - Disable webhook endpoints

2. **Within 1 Hour**
   - Review access logs
   - Check for unauthorized orders
   - Assess financial impact

3. **Within 24 Hours**
   - Full security audit
   - Generate new credentials
   - Notify affected parties

### Contact

- **Security Issues**: security@yourdomain.com
- **Emergency**: [Emergency contact number]

---

## Compliance Notes

### Data Handling

- Trade data may be subject to financial regulations
- Implement appropriate data retention policies
- Consider GDPR if serving EU users

### Audit Trail

All trading actions are logged with:

- Timestamp (UTC)
- Action type
- Parameters
- Result
- User/system identifier

---

## Security Checklist

Before deploying to production:

- [ ] All secrets in environment variables (not in code)
- [ ] API keys have minimal required permissions
- [ ] IP whitelisting enabled on exchange
- [ ] HTTPS only (no HTTP)
- [ ] CORS properly configured
- [ ] Webhook signature validation enabled
- [ ] Kill switch tested and functional
- [ ] Logging does not expose secrets
- [ ] Dependencies audited for vulnerabilities
- [ ] Firewall rules configured
- [ ] Monitoring and alerts set up

---

## Acknowledgments

We thank the security researchers who have helped improve this project's security:

- *Your name could be here*

---

**Remember**: Security is everyone's responsibility. When in doubt, ask. It's better to be cautious than to expose user funds to risk.
