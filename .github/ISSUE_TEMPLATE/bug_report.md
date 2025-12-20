---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Execute command '...'
4. See error

## Expected Behavior

A clear description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Screenshots

If applicable, add screenshots to help explain your problem.

## Environment

- **OS**: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- **Python Version**: [e.g., 3.11.5]
- **Bot Version**: [e.g., 1.0.0 or commit hash]
- **Bybit Mode**: [Mainnet / Testnet / Mock]
- **Database**: [PostgreSQL version or "None"]

## Logs

```
Paste relevant log output here.
Use the logs from the Streamlit console or API server.
```

## Configuration

If relevant, share your grid configuration (without API keys!):

```python
# Example
GridParameters(
    symbol="BTCUSDT",
    lower_price=95500.0,
    upper_price=99000.0,
    grid_count=12,
    ...
)
```

## Additional Context

Add any other context about the problem here.

## Checklist

- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have removed any API keys or secrets from logs/configuration
- [ ] I have tested on the latest version
- [ ] I have included relevant logs and error messages
