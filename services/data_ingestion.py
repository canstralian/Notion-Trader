import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging

from services.bybit_client import BybitClient, get_bybit_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    timestamp: datetime

class DataIngestionService:
    
    def __init__(self, client: Optional[BybitClient] = None):
        self.client = client or get_bybit_client()
        self._price_cache: Dict[str, PriceData] = {}
        self._subscribers: List[Callable] = []
        self._running = False
        self._symbols = ["BTCUSDT", "MNTUSDT", "DOGEUSDT", "PEPEUSDT"]
    
    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        self._subscribers.remove(callback)
    
    async def _notify_subscribers(self, data: PriceData):
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def fetch_price(self, symbol: str) -> Optional[PriceData]:
        try:
            ticker = await self.client.get_ticker(symbol)
            if ticker.get("list"):
                t = ticker["list"][0]
                data = PriceData(
                    symbol=symbol,
                    price=float(t["lastPrice"]),
                    bid=float(t.get("bid1Price", t["lastPrice"])),
                    ask=float(t.get("ask1Price", t["lastPrice"])),
                    volume_24h=float(t.get("volume24h", 0)),
                    timestamp=datetime.utcnow()
                )
                self._price_cache[symbol] = data
                return data
            else:
                logger.warning(f"No price data returned for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}", exc_info=True)
        return None
    
    async def fetch_all_prices(self) -> Dict[str, PriceData]:
        tasks = [self.fetch_price(symbol) for symbol in self._symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failed_symbols = []
        for i, result in enumerate(results):
            if isinstance(result, PriceData):
                await self._notify_subscribers(result)
            elif isinstance(result, Exception):
                failed_symbols.append(self._symbols[i])
                logger.error(f"Failed to fetch {self._symbols[i]}: {result}")
        
        if failed_symbols:
            logger.warning(f"Price fetch failed for: {', '.join(failed_symbols)}")
        
        return self._price_cache
    
    def get_cached_price(self, symbol: str) -> Optional[PriceData]:
        return self._price_cache.get(symbol)
    
    def get_all_cached_prices(self) -> Dict[str, PriceData]:
        return self._price_cache.copy()
    
    async def fetch_klines(self, symbol: str, interval: str = "1", limit: int = 100) -> List[Dict]:
        try:
            klines = await self.client.get_klines(symbol, interval, limit)
            return [
                {
                    "timestamp": datetime.fromtimestamp(int(k[0]) / 1000),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                }
                for k in klines
            ]
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []
    
    async def start_polling(self, interval_seconds: float = 1.0):
        self._running = True
        logger.info(f"Starting price polling for {self._symbols}")
        
        while self._running:
            await self.fetch_all_prices()
            await asyncio.sleep(interval_seconds)
    
    def stop_polling(self):
        self._running = False
        logger.info("Price polling stopped")
    
    async def start_websocket(self):
        async def on_message(data: Dict):
            if data.get("topic", "").startswith("tickers."):
                symbol = data["topic"].replace("tickers.", "")
                tick = data.get("data", {})
                
                price_data = PriceData(
                    symbol=symbol,
                    price=float(tick.get("lastPrice", 0)),
                    bid=float(tick.get("bid1Price", 0)),
                    ask=float(tick.get("ask1Price", 0)),
                    volume_24h=float(tick.get("volume24h", 0)),
                    timestamp=datetime.utcnow()
                )
                
                self._price_cache[symbol] = price_data
                await self._notify_subscribers(price_data)
        
        try:
            await self.client.connect_websocket(self._symbols, on_message)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            logger.info("Falling back to polling mode")
            await self.start_polling()
    
    async def stop_websocket(self):
        await self.client.disconnect_websocket()


_ingestion_service: Optional[DataIngestionService] = None

def get_ingestion_service() -> DataIngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DataIngestionService()
    return _ingestion_service
