# Contributing to Crypto Grid Trading Bot

First off, thank you for considering contributing to this project! Your help makes this trading bot better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- PostgreSQL (optional, for database features)

### Development Setup

1. **Fork the repository**
   
   Click the "Fork" button on GitHub to create your own copy.

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/crypto-grid-bot.git
   cd crypto-grid-bot
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development tools
   ```

5. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Create a branch for your work**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Workflow

### Running the Application

```bash
# Start the Streamlit dashboard
streamlit run app.py --server.port 5000

# In a separate terminal, start the API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=api --cov-report=html

# Run specific test file
pytest tests/test_grid_engine.py

# Run tests matching a pattern
pytest -k "test_risk"
```

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy services/ api/
```

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these additions:

- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for strings
- **Imports**: Grouped (stdlib, third-party, local) and sorted alphabetically
- **Type hints**: Required for all public functions

### Example Function

```python
from typing import Dict, Optional
from datetime import datetime

async def place_grid_order(
    symbol: str,
    price: float,
    quantity: float,
    side: str = "Buy",
) -> Dict[str, any]:
    """
    Place a grid order on the exchange.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        price: Order price in quote currency
        quantity: Order quantity in base currency
        side: Order side, either "Buy" or "Sell"

    Returns:
        Dictionary containing order ID and status

    Raises:
        ValueError: If price or quantity is non-positive
        ExchangeError: If the API request fails
    """
    if price <= 0 or quantity <= 0:
        raise ValueError("Price and quantity must be positive")

    result = await client.place_order(
        symbol=symbol,
        side=side,
        order_type="Limit",
        qty=str(quantity),
        price=str(price),
    )
    return result
```

### Documentation

- All modules must have a docstring explaining their purpose
- All public functions/methods require docstrings (Google style)
- Complex algorithms should have inline comments
- Update README.md if adding new features

### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = await client.place_order(...)
except aiohttp.ClientError as e:
    logger.error(f"Network error placing order for {symbol}: {e}")
    raise OrderPlacementError(f"Failed to place order: {e}") from e

# Bad: Bare except
try:
    result = await client.place_order(...)
except:
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed debugging info")
logger.info("General operational info")
logger.warning("Something unexpected but not critical")
logger.error("Error that needs attention", exc_info=True)
logger.critical("System-wide failure")
```

---

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, semicolons) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process or auxiliary tools |

### Examples

```bash
feat(grid-engine): add support for trailing stop-loss

fix(risk-manager): correct drawdown calculation for negative equity

docs(readme): update installation instructions for Python 3.11

refactor(bybit-client): extract signature generation to separate method
```

---

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
   ```bash
   pytest
   ```

2. **Format your code**
   ```bash
   black . && isort .
   ```

3. **Update documentation** if needed

4. **Write meaningful commit messages**

### PR Template

When creating a PR, please include:

- **Description**: What does this PR do?
- **Motivation**: Why is this change needed?
- **Testing**: How was this tested?
- **Checklist**:
  - [ ] Tests pass locally
  - [ ] Code follows style guidelines
  - [ ] Documentation updated
  - [ ] No secrets or API keys included

### Review Process

1. A maintainer will review your PR within 3 business days
2. Address any requested changes
3. Once approved, your PR will be merged
4. Celebrate! 🎉

---

## Issue Guidelines

### Bug Reports

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Relevant logs or screenshots

### Feature Requests

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- Problem you're trying to solve
- Proposed solution
- Alternatives considered
- Additional context

### Questions

For questions about usage or implementation:

1. Check existing documentation first
2. Search closed issues for similar questions
3. Open a new issue with the "question" label

---

## Financial Code Guidelines

Since this project handles financial operations, extra care is required:

### Critical Areas

- **Order placement**: Always validate inputs, handle partial fills
- **Price calculations**: Use Decimal for precision when needed
- **Risk checks**: Never bypass risk management logic
- **API credentials**: Never log or expose secrets

### Testing Requirements

- All order-related code must have unit tests
- Risk management changes require integration tests
- Mock external APIs in tests (never hit real endpoints)

### Review Requirements

Changes to these files require extra scrutiny:

- `services/grid_engine.py`
- `services/risk_manager.py`
- `services/bybit_client.py`
- `config/grid_configs.py`

---

## Recognition

Contributors will be recognized in:

- The project README
- Release notes for significant contributions
- GitHub contributors page

Thank you for helping make this project better! 🚀
