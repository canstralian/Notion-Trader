from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class GridParameters:
    symbol: str
    lower_price: float
    upper_price: float
    grid_count: int
    total_investment: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    btc_filter_enabled: bool = False
    
    @property
    def grid_spacing(self) -> float:
        return (self.upper_price - self.lower_price) / self.grid_count
    
    @property
    def investment_per_grid(self) -> float:
        return self.total_investment / self.grid_count
    
    def get_grid_prices(self) -> List[float]:
        prices = []
        for i in range(self.grid_count + 1):
            price = self.lower_price + (i * self.grid_spacing)
            prices.append(round(price, 8))
        return prices
    
    def get_quantity_at_price(self, price: float) -> float:
        return self.investment_per_grid / price

DEFAULT_GRID_CONFIGS: Dict[str, GridParameters] = {
    "BTCUSDT": GridParameters(
        symbol="BTCUSDT",
        lower_price=95500.0,
        upper_price=99000.0,
        grid_count=12,
        total_investment=25000.0,
        stop_loss=94800.0,
        take_profit=None,
        btc_filter_enabled=False
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
        btc_filter_enabled=True
    )
}

RISK_THRESHOLDS = {
    "max_drawdown_percent": 30.0,
    "max_api_error_rate": 2.0,
    "volatility_breaker_count": 2,
    "max_position_size_percent": 50.0,
}

TRADING_SETTINGS = {
    "rate_limit_per_second": 10,
    "order_timeout_seconds": 30,
    "heartbeat_interval_seconds": 5,
    "price_update_interval_seconds": 1,
    "pnl_update_interval_seconds": 60,
}

YIELD_WATERFALL = {
    "btc_profit_threshold_percent": 5.0,
    "rebalance_trigger_percent": 10.0,
    "friday_harvest_enabled": True,
}
