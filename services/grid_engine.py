import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from config.grid_configs import GridParameters, DEFAULT_GRID_CONFIGS
from services.bybit_client import BybitClient, get_bybit_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GridLevel:
    level: int
    price: float
    quantity: float
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    buy_filled: bool = False
    sell_filled: bool = False
    
@dataclass
class GridState:
    symbol: str
    params: GridParameters
    levels: List[GridLevel] = field(default_factory=list)
    current_price: float = 0.0
    status: str = "stopped"
    total_buys: int = 0
    total_sells: int = 0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class GridEngine:
    
    def __init__(self, client: Optional[BybitClient] = None):
        self.client = client or get_bybit_client()
        self.grids: Dict[str, GridState] = {}
        self._running = False
        self._btc_price: float = 0.0
    
    def initialize_grid(self, params: GridParameters) -> GridState:
        grid_prices = params.get_grid_prices()
        levels = []
        
        for i, price in enumerate(grid_prices[:-1]):
            quantity = params.get_quantity_at_price(price)
            levels.append(GridLevel(
                level=i,
                price=price,
                quantity=quantity
            ))
        
        state = GridState(
            symbol=params.symbol,
            params=params,
            levels=levels,
            status="initialized"
        )
        
        self.grids[params.symbol] = state
        logger.info(f"Initialized grid for {params.symbol} with {len(levels)} levels")
        return state
    
    def initialize_all_grids(self) -> Dict[str, GridState]:
        for symbol, params in DEFAULT_GRID_CONFIGS.items():
            self.initialize_grid(params)
        return self.grids
    
    async def update_price(self, symbol: str) -> float:
        try:
            ticker = await self.client.get_ticker(symbol)
            if ticker.get("list"):
                price = float(ticker["list"][0]["lastPrice"])
                if symbol in self.grids:
                    self.grids[symbol].current_price = price
                    self.grids[symbol].last_update = datetime.utcnow()
                if symbol == "BTCUSDT":
                    self._btc_price = price
                return price
        except Exception as e:
            logger.error(f"Error updating price for {symbol}: {e}")
        return 0.0
    
    def _check_btc_filter(self, symbol: str) -> bool:
        if symbol not in self.grids:
            return True
        
        params = self.grids[symbol].params
        if not params.btc_filter_enabled:
            return True
        
        btc_config = DEFAULT_GRID_CONFIGS.get("BTCUSDT")
        if not btc_config:
            return True
        
        if self._btc_price == 0:
            return False
        
        return btc_config.lower_price <= self._btc_price <= btc_config.upper_price
    
    def _check_stop_loss(self, symbol: str) -> bool:
        if symbol not in self.grids:
            return False
        
        state = self.grids[symbol]
        params = state.params
        
        if params.stop_loss and state.current_price > 0:
            if state.current_price <= params.stop_loss:
                logger.warning(f"Stop-loss triggered for {symbol}: {state.current_price} <= {params.stop_loss}")
                return True
        
        return False
    
    async def place_grid_orders(self, symbol: str) -> Dict:
        if symbol not in self.grids:
            return {"error": "Grid not initialized"}
        
        state = self.grids[symbol]
        
        if not self._check_btc_filter(symbol):
            logger.info(f"BTC filter blocked trading for {symbol}")
            return {"error": "BTC filter active"}
        
        if self._check_stop_loss(symbol):
            state.status = "stopped"
            return {"error": "Stop-loss triggered"}
        
        current_price = state.current_price
        if current_price == 0:
            await self.update_price(symbol)
            current_price = state.current_price
        
        orders_placed = 0
        
        for level in state.levels:
            if level.price < current_price and not level.buy_filled:
                try:
                    result = await self.client.place_order(
                        symbol=symbol,
                        side="Buy",
                        order_type="Limit",
                        qty=str(round(level.quantity, 8)),
                        price=str(round(level.price, 8))
                    )
                    level.buy_order_id = result.get("orderId")
                    orders_placed += 1
                    logger.info(f"Placed buy order for {symbol} at {level.price}")
                except Exception as e:
                    logger.error(f"Error placing buy order: {e}")
            
            elif level.price > current_price and level.buy_filled and not level.sell_filled:
                sell_price = level.price + state.params.grid_spacing
                try:
                    result = await self.client.place_order(
                        symbol=symbol,
                        side="Sell",
                        order_type="Limit",
                        qty=str(round(level.quantity, 8)),
                        price=str(round(sell_price, 8))
                    )
                    level.sell_order_id = result.get("orderId")
                    orders_placed += 1
                    logger.info(f"Placed sell order for {symbol} at {sell_price}")
                except Exception as e:
                    logger.error(f"Error placing sell order: {e}")
        
        state.status = "running"
        return {"orders_placed": orders_placed}
    
    async def check_fills(self, symbol: str) -> Dict:
        if symbol not in self.grids:
            return {"error": "Grid not initialized"}
        
        state = self.grids[symbol]
        new_fills = {"buys": 0, "sells": 0}
        
        try:
            orders = await self.client.get_open_orders(symbol)
            open_order_ids = {o["orderId"] for o in orders}
            
            for level in state.levels:
                if level.buy_order_id and level.buy_order_id not in open_order_ids:
                    if not level.buy_filled:
                        level.buy_filled = True
                        state.total_buys += 1
                        new_fills["buys"] += 1
                        logger.info(f"Buy filled for {symbol} at level {level.level}")
                
                if level.sell_order_id and level.sell_order_id not in open_order_ids:
                    if not level.sell_filled:
                        level.sell_filled = True
                        state.total_sells += 1
                        profit = level.quantity * state.params.grid_spacing
                        state.realized_pnl += profit
                        new_fills["sells"] += 1
                        logger.info(f"Sell filled for {symbol} at level {level.level}, profit: {profit}")
                        level.buy_filled = False
                        level.sell_filled = False
                        level.buy_order_id = None
                        level.sell_order_id = None
        
        except Exception as e:
            logger.error(f"Error checking fills for {symbol}: {e}")
        
        return new_fills
    
    async def cancel_all_orders(self, symbol: str) -> Dict:
        if symbol not in self.grids:
            return {"error": "Grid not initialized"}
        
        state = self.grids[symbol]
        cancelled = 0
        
        try:
            orders = await self.client.get_open_orders(symbol)
            for order in orders:
                await self.client.cancel_order(symbol, order["orderId"])
                cancelled += 1
            
            for level in state.levels:
                level.buy_order_id = None
                level.sell_order_id = None
            
            state.status = "stopped"
            logger.info(f"Cancelled {cancelled} orders for {symbol}")
        
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
        
        return {"cancelled": cancelled}
    
    async def pause_grid(self, symbol: str) -> Dict:
        if symbol not in self.grids:
            return {"error": "Grid not initialized"}
        
        await self.cancel_all_orders(symbol)
        self.grids[symbol].status = "paused"
        return {"status": "paused"}
    
    async def resume_grid(self, symbol: str) -> Dict:
        if symbol not in self.grids:
            return {"error": "Grid not initialized"}
        
        await self.update_price(symbol)
        result = await self.place_grid_orders(symbol)
        self.grids[symbol].status = "running"
        return result
    
    def get_grid_status(self, symbol: str) -> Optional[Dict]:
        if symbol not in self.grids:
            return None
        
        state = self.grids[symbol]
        params = state.params
        
        filled_levels = sum(1 for l in state.levels if l.buy_filled)
        pending_buys = sum(1 for l in state.levels if l.buy_order_id and not l.buy_filled)
        pending_sells = sum(1 for l in state.levels if l.sell_order_id and not l.sell_filled)
        
        return {
            "symbol": symbol,
            "status": state.status,
            "current_price": state.current_price,
            "lower_price": params.lower_price,
            "upper_price": params.upper_price,
            "grid_count": params.grid_count,
            "filled_levels": filled_levels,
            "pending_buys": pending_buys,
            "pending_sells": pending_sells,
            "total_buys": state.total_buys,
            "total_sells": state.total_sells,
            "realized_pnl": state.realized_pnl,
            "last_update": state.last_update.isoformat()
        }
    
    def get_all_status(self) -> Dict:
        return {symbol: self.get_grid_status(symbol) for symbol in self.grids}
    
    async def run_loop(self, interval_seconds: float = 5.0):
        self._running = True
        logger.info("Starting grid engine loop")
        
        while self._running:
            for symbol in list(self.grids.keys()):
                state = self.grids[symbol]
                if state.status == "running":
                    await self.update_price(symbol)
                    await self.check_fills(symbol)
                    await self.place_grid_orders(symbol)
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        self._running = False
        logger.info("Grid engine stopped")
