import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Enum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class OrderSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

class BotStatus(enum.Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class OHLCV(Base):
    __tablename__ = "ohlcv"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    interval = Column(String(10), default="1m")
    
    __table_args__ = (
        Index('idx_ohlcv_symbol_time', 'symbol', 'timestamp'),
    )

class GridConfig(Base):
    __tablename__ = "grid_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True)
    lower_price = Column(Float, nullable=False)
    upper_price = Column(Float, nullable=False)
    grid_count = Column(Integer, nullable=False)
    total_investment = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    btc_filter_enabled = Column(Boolean, default=False)
    status = Column(String(20), default="stopped")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = relationship("GridOrder", back_populates="grid_config")

class GridOrder(Base):
    __tablename__ = "grid_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    grid_config_id = Column(Integer, ForeignKey("grid_configs.id"), nullable=False)
    grid_level = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)
    order_id = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    filled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    grid_config = relationship("GridConfig", back_populates="orders")
    
    __table_args__ = (
        Index('idx_grid_orders_config_level', 'grid_config_id', 'grid_level'),
    )

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    order_id = Column(String(100), nullable=True)
    exchange_trade_id = Column(String(100), nullable=True)
    pnl = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_trades_symbol_time', 'symbol', 'executed_at'),
    )

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Float, default=0.0)
    avg_entry_price = Column(Float, default=0.0)
    total_invested = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BotState(Base):
    __tablename__ = "bot_state"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    status = Column(String(20), default="stopped")
    last_heartbeat = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    metrics = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=True)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    payload = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_alerts_source_time', 'source', 'created_at'),
    )

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    component = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def get_db():
    if not SessionLocal:
        raise Exception("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    if engine:
        Base.metadata.create_all(bind=engine)
        return True
    return False
