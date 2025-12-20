import json
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging
import hmac
import hashlib
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradingViewAlert:
    symbol: str
    action: str
    price: float
    zone: str
    timestamp: datetime
    raw_payload: Dict
    validated: bool = False

class AlertHandler:
    
    def __init__(self):
        self.webhook_secret = os.environ.get("TRADINGVIEW_WEBHOOK_SECRET", "")
        self._alert_history: List[TradingViewAlert] = []
        self._max_history = 1000
    
    def validate_webhook(self, payload: str, signature: str) -> bool:
        if not self.webhook_secret:
            return True
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_alert(self, payload: Dict) -> Optional[TradingViewAlert]:
        try:
            symbol = payload.get("symbol", "").upper()
            if not symbol.endswith("USDT"):
                symbol = f"{symbol}USDT"
            
            action = payload.get("action", "").lower()
            if action not in ["buy", "sell", "long", "short", "close"]:
                logger.warning(f"Unknown action: {action}")
                action = "buy" if "buy" in str(payload).lower() else "sell"
            
            price = float(payload.get("price", 0))
            zone = payload.get("zone", "unknown")
            
            alert = TradingViewAlert(
                symbol=symbol,
                action=action,
                price=price,
                zone=zone,
                timestamp=datetime.utcnow(),
                raw_payload=payload,
                validated=True
            )
            
            self._alert_history.append(alert)
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]
            
            logger.info(f"Parsed alert: {symbol} {action} at {price}")
            return alert
            
        except Exception as e:
            logger.error(f"Error parsing alert: {e}")
            return None
    
    def should_execute(self, alert: TradingViewAlert, current_price: float) -> tuple[bool, str]:
        if not alert.validated:
            return False, "Alert not validated"
        
        if alert.price > 0:
            price_diff = abs(current_price - alert.price) / current_price * 100
            if price_diff > 1.0:
                return False, f"Price deviation too high: {price_diff:.2f}%"
        
        age_seconds = (datetime.utcnow() - alert.timestamp).total_seconds()
        if age_seconds > 60:
            return False, f"Alert too old: {age_seconds:.0f}s"
        
        return True, "OK"
    
    def get_action_for_grid(self, alert: TradingViewAlert) -> Optional[str]:
        action = alert.action.lower()
        
        if action in ["buy", "long"]:
            return "resume"
        elif action in ["sell", "short"]:
            return "pause"
        elif action == "close":
            return "stop"
        
        return None
    
    def get_recent_alerts(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        alerts = self._alert_history
        if symbol:
            alerts = [a for a in alerts if a.symbol == symbol]
        
        return [
            {
                "symbol": a.symbol,
                "action": a.action,
                "price": a.price,
                "zone": a.zone,
                "timestamp": a.timestamp.isoformat(),
                "validated": a.validated
            }
            for a in reversed(alerts[-limit:])
        ]
    
    def get_stats(self) -> Dict:
        if not self._alert_history:
            return {"total": 0, "by_symbol": {}, "by_action": {}}
        
        by_symbol = {}
        by_action = {}
        
        for alert in self._alert_history:
            by_symbol[alert.symbol] = by_symbol.get(alert.symbol, 0) + 1
            by_action[alert.action] = by_action.get(alert.action, 0) + 1
        
        return {
            "total": len(self._alert_history),
            "by_symbol": by_symbol,
            "by_action": by_action,
            "last_alert": self._alert_history[-1].timestamp.isoformat() if self._alert_history else None
        }


_alert_handler: Optional[AlertHandler] = None

def get_alert_handler() -> AlertHandler:
    global _alert_handler
    if _alert_handler is None:
        _alert_handler = AlertHandler()
    return _alert_handler
