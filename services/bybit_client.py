import os
import time
import hmac
import hashlib
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BybitCredentials:
    api_key: str
    api_secret: str
    testnet: bool = False

class BybitClient:
    
    MAINNET_REST = "https://api.bybit.com"
    TESTNET_REST = "https://api-testnet.bybit.com"
    MAINNET_WS = "wss://stream.bybit.com/v5/public/spot"
    TESTNET_WS = "wss://stream-testnet.bybit.com/v5/public/spot"
    
    def __init__(self, credentials: Optional[BybitCredentials] = None):
        if credentials:
            self.api_key = credentials.api_key
            self.api_secret = credentials.api_secret
            self.testnet = credentials.testnet
        else:
            self.api_key = os.environ.get("BYBIT_API_KEY", "")
            self.api_secret = os.environ.get("BYBIT_API_SECRET", "")
            self.testnet = os.environ.get("BYBIT_TESTNET", "false").lower() == "true"
        
        self.base_url = self.TESTNET_REST if self.testnet else self.MAINNET_REST
        self.ws_url = self.TESTNET_WS if self.testnet else self.MAINNET_WS
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
    
    RECV_WINDOW_MS = "5000"
    
    def _generate_signature(self, timestamp: int, params: Dict) -> str:
        param_str = str(timestamp) + self.api_key + self.RECV_WINDOW_MS
        if params:
            param_str += "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: Dict = None) -> Dict:
        timestamp = int(time.time() * 1000)
        signature = self._generate_signature(timestamp, params or {})
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": self.RECV_WINDOW_MS,
            "Content-Type": "application/json"
        }
    
    async def _ensure_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        if self.ws and not self.ws.closed:
            await self.ws.close()
    
    async def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"
        
        headers = self._get_headers(params) if signed else {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                async with self.session.get(url, params=params, headers=headers) as resp:
                    data = await resp.json()
            else:
                async with self.session.post(url, json=params, headers=headers) as resp:
                    data = await resp.json()
            
            if data.get("retCode") != 0:
                logger.error(f"Bybit API error: {data}")
                raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
            
            return data.get("result", {})
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
    
    async def get_ticker(self, symbol: str) -> Dict:
        return await self._request("GET", "/v5/market/tickers", {
            "category": "spot",
            "symbol": symbol
        })
    
    async def get_klines(self, symbol: str, interval: str = "1", limit: int = 200) -> List:
        result = await self._request("GET", "/v5/market/kline", {
            "category": "spot",
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        })
        return result.get("list", [])
    
    async def get_orderbook(self, symbol: str, limit: int = 25) -> Dict:
        return await self._request("GET", "/v5/market/orderbook", {
            "category": "spot",
            "symbol": symbol,
            "limit": limit
        })
    
    async def get_wallet_balance(self) -> Dict:
        return await self._request("GET", "/v5/account/wallet-balance", {
            "accountType": "UNIFIED"
        }, signed=True)
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        price: Optional[str] = None,
        time_in_force: str = "GTC"
    ) -> Dict:
        params = {
            "category": "spot",
            "symbol": symbol,
            "side": side.capitalize(),
            "orderType": order_type.capitalize(),
            "qty": qty,
            "timeInForce": time_in_force
        }
        if price and order_type.lower() == "limit":
            params["price"] = price
        
        return await self._request("POST", "/v5/order/create", params, signed=True)
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        return await self._request("POST", "/v5/order/cancel", {
            "category": "spot",
            "symbol": symbol,
            "orderId": order_id
        }, signed=True)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List:
        params = {"category": "spot"}
        if symbol:
            params["symbol"] = symbol
        result = await self._request("GET", "/v5/order/realtime", params, signed=True)
        return result.get("list", [])
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> List:
        params = {"category": "spot", "limit": limit}
        if symbol:
            params["symbol"] = symbol
        result = await self._request("GET", "/v5/order/history", params, signed=True)
        return result.get("list", [])
    
    async def connect_websocket(self, symbols: List[str], on_message: Callable):
        await self._ensure_session()
        
        try:
            self.ws = await self.session.ws_connect(self.ws_url)
            self._running = True
            
            topics = [f"tickers.{s}" for s in symbols]
            subscribe_msg = {
                "op": "subscribe",
                "args": topics
            }
            await self.ws.send_json(subscribe_msg)
            logger.info(f"Subscribed to: {topics}")
            
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if "topic" in data:
                        await on_message(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg}")
                    break
                    
                if not self._running:
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    async def disconnect_websocket(self):
        self._running = False
        if self.ws:
            await self.ws.close()


class MockBybitClient(BybitClient):
    
    def __init__(self):
        super().__init__(BybitCredentials("mock", "mock", True))
        self._mock_prices = {
            "BTCUSDT": 97250.0,
            "MNTUSDT": 1.08,
            "DOGEUSDT": 0.137,
            "PEPEUSDT": 0.00000445
        }
    
    async def get_ticker(self, symbol: str) -> Dict:
        price = self._mock_prices.get(symbol, 1.0)
        return {
            "list": [{
                "symbol": symbol,
                "lastPrice": str(price),
                "bid1Price": str(price * 0.9999),
                "ask1Price": str(price * 1.0001),
                "volume24h": "1000000",
                "turnover24h": str(price * 1000000)
            }]
        }
    
    async def place_order(self, *args, **kwargs) -> Dict:
        return {"orderId": f"mock_{int(time.time()*1000)}"}
    
    async def cancel_order(self, *args, **kwargs) -> Dict:
        return {"success": True}
    
    async def get_wallet_balance(self) -> Dict:
        return {
            "list": [{
                "accountType": "UNIFIED",
                "coin": [
                    {"coin": "USDT", "walletBalance": "34000", "availableBalance": "30000"},
                    {"coin": "BTC", "walletBalance": "0.5", "availableBalance": "0.5"}
                ]
            }]
        }


def get_bybit_client() -> BybitClient:
    api_key = os.environ.get("BYBIT_API_KEY")
    if not api_key:
        logger.warning("No Bybit API key found, using mock client")
        return MockBybitClient()
    return BybitClient()
