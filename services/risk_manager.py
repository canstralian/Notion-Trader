import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from config.grid_configs import RISK_THRESHOLDS, DEFAULT_GRID_CONFIGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    total_equity: float = 0.0
    initial_equity: float = 34000.0
    drawdown_percent: float = 0.0
    api_error_count: int = 0
    api_request_count: int = 0
    volatility_breakers: int = 0
    last_check: datetime = field(default_factory=datetime.utcnow)

@dataclass
class KillSwitchState:
    triggered: bool = False
    reason: Optional[str] = None
    triggered_at: Optional[datetime] = None

class RiskManager:
    
    def __init__(self):
        self.metrics = RiskMetrics()
        self.kill_switch = KillSwitchState()
        self._price_history: Dict[str, List[float]] = {}
        self._error_window: List[datetime] = []
    
    def update_equity(self, total_equity: float):
        self.metrics.total_equity = total_equity
        self.metrics.drawdown_percent = (
            (self.metrics.initial_equity - total_equity) / self.metrics.initial_equity * 100
        )
        self.metrics.last_check = datetime.utcnow()
    
    def record_api_request(self, success: bool):
        self.metrics.api_request_count += 1
        if not success:
            self.metrics.api_error_count += 1
            self._error_window.append(datetime.utcnow())
        
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        self._error_window = [t for t in self._error_window if t > cutoff]
    
    def record_price(self, symbol: str, price: float):
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        self._price_history[symbol].append(price)
        
        if len(self._price_history[symbol]) > 100:
            self._price_history[symbol] = self._price_history[symbol][-100:]
    
    def check_volatility_breaker(self, symbol: str) -> bool:
        if symbol not in self._price_history or len(self._price_history[symbol]) < 10:
            return False
        
        prices = self._price_history[symbol][-10:]
        avg_price = sum(prices) / len(prices)
        max_deviation = max(abs(p - avg_price) / avg_price * 100 for p in prices)
        
        return max_deviation > 5.0
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        config = DEFAULT_GRID_CONFIGS.get(symbol)
        if config and config.stop_loss:
            return current_price <= config.stop_loss
        return False
    
    def check_kill_conditions(self) -> Optional[str]:
        if self.kill_switch.triggered:
            return self.kill_switch.reason
        
        if self.metrics.drawdown_percent >= RISK_THRESHOLDS["max_drawdown_percent"]:
            return f"Max drawdown exceeded: {self.metrics.drawdown_percent:.1f}%"
        
        if self.metrics.api_request_count > 100:
            error_rate = (self.metrics.api_error_count / self.metrics.api_request_count) * 100
            if error_rate >= RISK_THRESHOLDS["max_api_error_rate"]:
                return f"API error rate too high: {error_rate:.1f}%"
        
        breaker_count = sum(
            1 for symbol in self._price_history 
            if self.check_volatility_breaker(symbol)
        )
        if breaker_count >= RISK_THRESHOLDS["volatility_breaker_count"]:
            return f"Volatility breakers triggered: {breaker_count}"
        
        return None
    
    def trigger_kill_switch(self, reason: str):
        self.kill_switch.triggered = True
        self.kill_switch.reason = reason
        self.kill_switch.triggered_at = datetime.utcnow()
        logger.critical(f"KILL SWITCH TRIGGERED: {reason}")
    
    def reset_kill_switch(self):
        self.kill_switch = KillSwitchState()
        logger.info("Kill switch reset")
    
    def get_status(self) -> Dict:
        kill_reason = self.check_kill_conditions()
        
        return {
            "total_equity": self.metrics.total_equity,
            "initial_equity": self.metrics.initial_equity,
            "drawdown_percent": round(self.metrics.drawdown_percent, 2),
            "api_error_rate": (
                round(self.metrics.api_error_count / max(self.metrics.api_request_count, 1) * 100, 2)
            ),
            "volatility_breakers": sum(
                1 for symbol in self._price_history 
                if self.check_volatility_breaker(symbol)
            ),
            "kill_switch_triggered": self.kill_switch.triggered,
            "kill_switch_reason": self.kill_switch.reason,
            "potential_kill_reason": kill_reason,
            "last_check": self.metrics.last_check.isoformat()
        }
    
    def should_trade(self, symbol: str, current_price: float) -> tuple[bool, Optional[str]]:
        if self.kill_switch.triggered:
            return False, self.kill_switch.reason
        
        kill_reason = self.check_kill_conditions()
        if kill_reason:
            self.trigger_kill_switch(kill_reason)
            return False, kill_reason
        
        if self.check_stop_loss(symbol, current_price):
            return False, f"Stop-loss triggered for {symbol}"
        
        if self.check_volatility_breaker(symbol):
            return False, f"Volatility breaker active for {symbol}"
        
        return True, None
