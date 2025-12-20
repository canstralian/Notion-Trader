import os
import asyncio
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, get_db, SessionLocal
from services.grid_engine import GridEngine
from services.risk_manager import RiskManager
from services.data_ingestion import DataIngestionService, get_ingestion_service
from services.alert_handler import AlertHandler, get_alert_handler
from config.grid_configs import DEFAULT_GRID_CONFIGS

grid_engine: Optional[GridEngine] = None
risk_manager: Optional[RiskManager] = None
ingestion_service: Optional[DataIngestionService] = None
alert_handler: Optional[AlertHandler] = None
background_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global grid_engine, risk_manager, ingestion_service, alert_handler, background_task
    
    try:
        init_db()
    except Exception as e:
        print(f"Database init warning: {e}")
    
    grid_engine = GridEngine()
    grid_engine.initialize_all_grids()
    
    risk_manager = RiskManager()
    ingestion_service = get_ingestion_service()
    alert_handler = get_alert_handler()
    
    yield
    
    if grid_engine:
        grid_engine.stop()
    if ingestion_service:
        ingestion_service.stop_polling()

app = FastAPI(
    title="Crypto Trading Bot API",
    description="Multi-grid cryptocurrency trading bot with risk management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GridConfigUpdate(BaseModel):
    symbol: str
    lower_price: Optional[float] = None
    upper_price: Optional[float] = None
    grid_count: Optional[int] = None
    total_investment: Optional[float] = None

class AlertPayload(BaseModel):
    symbol: str
    action: str
    price: Optional[float] = 0
    zone: Optional[str] = "unknown"

@app.get("/")
async def root():
    return {"status": "running", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "grid_engine": grid_engine is not None,
        "risk_manager": risk_manager is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
async def get_status():
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    return {
        "grids": grid_engine.get_all_status(),
        "risk": risk_manager.get_status() if risk_manager else None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/grids")
async def get_grids():
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    return grid_engine.get_all_status()

@app.get("/api/grids/{symbol}")
async def get_grid(symbol: str):
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    status = grid_engine.get_grid_status(symbol.upper())
    if not status:
        raise HTTPException(status_code=404, detail=f"Grid not found: {symbol}")
    return status

@app.post("/api/grids/{symbol}/start")
async def start_grid(symbol: str, background_tasks: BackgroundTasks):
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    symbol = symbol.upper()
    if symbol not in grid_engine.grids:
        raise HTTPException(status_code=404, detail=f"Grid not found: {symbol}")
    
    await grid_engine.update_price(symbol)
    result = await grid_engine.place_grid_orders(symbol)
    
    return {"status": "started", "symbol": symbol, "result": result}

@app.post("/api/pause")
async def pause_all():
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    results = {}
    for symbol in grid_engine.grids:
        results[symbol] = await grid_engine.pause_grid(symbol)
    
    return {"status": "paused", "results": results}

@app.post("/api/pause/{symbol}")
async def pause_grid(symbol: str):
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    result = await grid_engine.pause_grid(symbol.upper())
    return {"status": "paused", "symbol": symbol, "result": result}

@app.post("/api/resume")
async def resume_all():
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    results = {}
    for symbol in grid_engine.grids:
        results[symbol] = await grid_engine.resume_grid(symbol)
    
    return {"status": "resumed", "results": results}

@app.post("/api/resume/{symbol}")
async def resume_grid(symbol: str):
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    result = await grid_engine.resume_grid(symbol.upper())
    return {"status": "resumed", "symbol": symbol, "result": result}

@app.post("/api/kill")
async def kill_switch():
    if not grid_engine or not risk_manager:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    risk_manager.trigger_kill_switch("Manual kill switch activated")
    
    results = {}
    for symbol in grid_engine.grids:
        results[symbol] = await grid_engine.cancel_all_orders(symbol)
    
    grid_engine.stop()
    
    return {"status": "killed", "results": results}

@app.post("/api/reset-kill")
async def reset_kill():
    if not risk_manager:
        raise HTTPException(status_code=503, detail="Risk manager not initialized")
    
    risk_manager.reset_kill_switch()
    return {"status": "reset"}

@app.get("/api/risk")
async def get_risk_status():
    if not risk_manager:
        raise HTTPException(status_code=503, detail="Risk manager not initialized")
    return risk_manager.get_status()

@app.get("/api/prices")
async def get_prices():
    if not ingestion_service:
        raise HTTPException(status_code=503, detail="Ingestion service not initialized")
    
    await ingestion_service.fetch_all_prices()
    prices = ingestion_service.get_all_cached_prices()
    
    return {
        symbol: {
            "price": data.price,
            "bid": data.bid,
            "ask": data.ask,
            "volume_24h": data.volume_24h,
            "timestamp": data.timestamp.isoformat()
        }
        for symbol, data in prices.items()
    }

@app.post("/api/tv-alert")
async def tradingview_alert(payload: AlertPayload, request: Request):
    if not alert_handler or not grid_engine:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    signature = request.headers.get("X-Webhook-Signature", "")
    
    alert = alert_handler.parse_alert(payload.dict())
    if not alert:
        raise HTTPException(status_code=400, detail="Failed to parse alert")
    
    action = alert_handler.get_action_for_grid(alert)
    result = {"alert": alert.symbol, "action": action}
    
    if action == "resume":
        result["grid_result"] = await grid_engine.resume_grid(alert.symbol)
    elif action == "pause":
        result["grid_result"] = await grid_engine.pause_grid(alert.symbol)
    elif action == "stop":
        result["grid_result"] = await grid_engine.cancel_all_orders(alert.symbol)
    
    return result

@app.get("/api/alerts")
async def get_alerts(symbol: Optional[str] = None, limit: int = 50):
    if not alert_handler:
        raise HTTPException(status_code=503, detail="Alert handler not initialized")
    
    return {
        "alerts": alert_handler.get_recent_alerts(symbol, limit),
        "stats": alert_handler.get_stats()
    }

@app.post("/api/deploy")
async def deploy_grid(config: GridConfigUpdate):
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    symbol = config.symbol.upper()
    if symbol not in DEFAULT_GRID_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {symbol}")
    
    return {"status": "deployed", "symbol": symbol, "config": config.dict()}

@app.post("/api/rebalance")
async def rebalance():
    if not grid_engine:
        raise HTTPException(status_code=503, detail="Grid engine not initialized")
    
    results = {}
    for symbol in grid_engine.grids:
        await grid_engine.cancel_all_orders(symbol)
        await grid_engine.update_price(symbol)
        results[symbol] = await grid_engine.place_grid_orders(symbol)
    
    return {"status": "rebalanced", "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
