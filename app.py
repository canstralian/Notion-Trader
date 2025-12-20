import streamlit as st
import pandas as pd
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    from notion_service import NotionTradeService
except ImportError:
    NotionTradeService = None

from crypto_api import (
    get_current_prices, get_market_data, get_coin_history,
    get_trending_coins, format_currency, format_percent, COIN_MAP
)
from config.grid_configs import DEFAULT_GRID_CONFIGS, RISK_THRESHOLDS
from services.bybit_client import get_bybit_client, MockBybitClient
from services.grid_engine import GridEngine
from services.risk_manager import RiskManager
from services.data_ingestion import DataIngestionService

st.set_page_config(
    page_title="Crypto Trading Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .main {
        background-color: #FFFFFF;
    }
    
    .stApp {
        background-color: #FFFFFF;
    }
    
    .metric-card {
        background-color: #F7F6F3;
        border-radius: 8px;
        padding: 20px;
        margin: 8px 0;
        border: 1px solid #E8E7E4;
    }
    
    .metric-label {
        color: #37352F;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 4px;
    }
    
    .metric-value {
        color: #000000;
        font-size: 28px;
        font-weight: 600;
    }
    
    .metric-delta-positive {
        color: #0F7B6C;
        font-size: 14px;
    }
    
    .metric-delta-negative {
        color: #E03E3E;
        font-size: 14px;
    }
    
    .section-header {
        color: #000000;
        font-size: 20px;
        font-weight: 600;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #E8E7E4;
    }
    
    .grid-card {
        background-color: #F7F6F3;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #E8E7E4;
    }
    
    .status-running {
        color: #0F7B6C;
        font-weight: 600;
    }
    
    .status-stopped {
        color: #E03E3E;
        font-weight: 600;
    }
    
    .status-paused {
        color: #FFB02E;
        font-weight: 600;
    }
    
    .buy-badge {
        background-color: rgba(15, 123, 108, 0.1);
        color: #0F7B6C;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 12px;
    }
    
    .sell-badge {
        background-color: rgba(224, 62, 62, 0.1);
        color: #E03E3E;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 12px;
    }
    
    .stButton > button {
        background-color: #2EAADC;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #2596BE;
    }
    
    .danger-button > button {
        background-color: #E03E3E !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #F7F6F3;
        border-radius: 6px;
        padding: 8px 16px;
        color: #37352F;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2EAADC !important;
        color: white !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_grid_engine():
    engine = GridEngine()
    engine.initialize_all_grids()
    return engine

@st.cache_resource
def get_risk_manager():
    return RiskManager()

def get_api_status() -> Dict:
    try:
        response = requests.get("http://localhost:8000/api/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except (requests.RequestException, requests.Timeout):
        pass
    return None

def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
    try:
        url = f"http://localhost:8000{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"API error: {e}")
    return None

def render_grid_status():
    st.markdown('<div class="section-header">Grid Trading Status</div>', unsafe_allow_html=True)
    
    engine = get_grid_engine()
    
    cols = st.columns(4)
    
    for idx, (symbol, config) in enumerate(DEFAULT_GRID_CONFIGS.items()):
        with cols[idx % 4]:
            status = engine.get_grid_status(symbol)
            if status:
                status_class = f"status-{status['status']}"
                
                st.markdown(f"""
                <div class="grid-card">
                    <h4 style="margin: 0 0 8px 0;">{symbol.replace('USDT', '/USDT')}</h4>
                    <p class="{status_class}" style="margin: 0;">Status: {status['status'].upper()}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.metric(
                    "Current Price",
                    f"${status['current_price']:,.8f}" if status['current_price'] < 1 else f"${status['current_price']:,.2f}",
                    delta=None
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Buys", status['total_buys'])
                with col2:
                    st.metric("Sells", status['total_sells'])
                
                st.metric("Realized P/L", f"${status['realized_pnl']:,.2f}")
                
                st.caption(f"Range: ${config.lower_price:,.8f}" if config.lower_price < 1 else f"Range: ${config.lower_price:,.2f} - ${config.upper_price:,.2f}")
                st.caption(f"Grids: {config.grid_count} | Investment: ${config.total_investment:,.0f}")

def render_risk_dashboard():
    st.markdown('<div class="section-header">Risk Management</div>', unsafe_allow_html=True)
    
    risk = get_risk_manager()
    status = risk.get_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_color = "normal" if status['drawdown_percent'] < 10 else "inverse"
        st.metric(
            "Drawdown",
            f"{status['drawdown_percent']:.1f}%",
            delta=f"Max: {RISK_THRESHOLDS['max_drawdown_percent']}%",
            delta_color=delta_color
        )
    
    with col2:
        st.metric(
            "Total Equity",
            f"${status['total_equity']:,.2f}",
            delta=f"Initial: ${status['initial_equity']:,.0f}"
        )
    
    with col3:
        st.metric(
            "API Error Rate",
            f"{status['api_error_rate']:.2f}%",
            delta=f"Max: {RISK_THRESHOLDS['max_api_error_rate']}%"
        )
    
    with col4:
        if status['kill_switch_triggered']:
            st.error(f"KILL SWITCH: {status['kill_switch_reason']}")
        elif status['potential_kill_reason']:
            st.warning(f"Warning: {status['potential_kill_reason']}")
        else:
            st.success("System Healthy")

def render_controls():
    st.markdown('<div class="section-header">Bot Controls</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Start All Grids", use_container_width=True):
            for symbol in DEFAULT_GRID_CONFIGS:
                call_api(f"/api/grids/{symbol}/start", "POST")
            st.success("Started all grids")
            st.rerun()
    
    with col2:
        if st.button("Pause All", use_container_width=True):
            call_api("/api/pause", "POST")
            st.info("Paused all grids")
            st.rerun()
    
    with col3:
        if st.button("Resume All", use_container_width=True):
            call_api("/api/resume", "POST")
            st.success("Resumed all grids")
            st.rerun()
    
    with col4:
        st.markdown('<div class="danger-button">', unsafe_allow_html=True)
        if st.button("KILL SWITCH", use_container_width=True, type="primary"):
            call_api("/api/kill", "POST")
            st.error("KILL SWITCH ACTIVATED - All trading stopped")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("**Per-Grid Controls**")
    cols = st.columns(4)
    
    for idx, symbol in enumerate(DEFAULT_GRID_CONFIGS):
        with cols[idx]:
            st.caption(symbol)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Start", key=f"start_{symbol}", use_container_width=True):
                    call_api(f"/api/grids/{symbol}/start", "POST")
                    st.rerun()
            with c2:
                if st.button("Pause", key=f"pause_{symbol}", use_container_width=True):
                    call_api(f"/api/pause/{symbol}", "POST")
                    st.rerun()

def render_market_overview():
    st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)
    
    prices = get_current_prices()
    market_data_list = get_market_data()
    
    market_data = {}
    if market_data_list:
        for item in market_data_list:
            symbol = item.get('symbol', '').upper()
            market_data[symbol] = item
    
    if prices:
        trading_symbols = ["BTC", "DOGE"]
        other_symbols = [s for s in prices.keys() if s not in trading_symbols]
        
        cols = st.columns(len(trading_symbols) + min(4, len(other_symbols)))
        
        for idx, coin in enumerate(trading_symbols + other_symbols[:4]):
            with cols[idx]:
                price = prices.get(coin, 0)
                data = market_data.get(coin, {})
                change = data.get('price_change_24h', 0)
                
                st.metric(
                    coin,
                    format_currency(price),
                    delta=format_percent(change) if change else None,
                    delta_color="normal" if change >= 0 else "inverse"
                )
    else:
        st.warning("Unable to fetch market data")

def render_grid_config():
    st.markdown('<div class="section-header">Grid Configuration</div>', unsafe_allow_html=True)
    
    for symbol, config in DEFAULT_GRID_CONFIGS.items():
        with st.expander(f"{symbol} Configuration"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Lower Price", value=f"{config.lower_price}", key=f"lower_{symbol}", disabled=True)
                st.text_input("Upper Price", value=f"{config.upper_price}", key=f"upper_{symbol}", disabled=True)
                st.text_input("Grid Count", value=f"{config.grid_count}", key=f"count_{symbol}", disabled=True)
            
            with col2:
                st.text_input("Investment", value=f"${config.total_investment:,.0f}", key=f"invest_{symbol}", disabled=True)
                st.text_input("Grid Spacing", value=f"{config.grid_spacing:.8f}", key=f"spacing_{symbol}", disabled=True)
                st.text_input("Stop Loss", value=f"{config.stop_loss or 'None'}", key=f"sl_{symbol}", disabled=True)
            
            grid_prices = config.get_grid_prices()
            st.caption(f"Grid Levels: {', '.join([f'{p:.8f}' if p < 1 else f'{p:.2f}' for p in grid_prices[:5]])}...")

def render_pnl_summary():
    st.markdown('<div class="section-header">P/L Summary</div>', unsafe_allow_html=True)
    
    engine = get_grid_engine()
    
    total_pnl = 0
    total_buys = 0
    total_sells = 0
    
    data = []
    for symbol in DEFAULT_GRID_CONFIGS:
        status = engine.get_grid_status(symbol)
        if status:
            total_pnl += status['realized_pnl']
            total_buys += status['total_buys']
            total_sells += status['total_sells']
            data.append({
                "Symbol": symbol,
                "Status": status['status'],
                "Buys": status['total_buys'],
                "Sells": status['total_sells'],
                "P/L": f"${status['realized_pnl']:,.2f}"
            })
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total P/L", f"${total_pnl:,.2f}")
    with col2:
        st.metric("Total Buys", total_buys)
    with col3:
        st.metric("Total Sells", total_sells)
    
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

def render_notion_trades():
    st.markdown('<div class="section-header">Notion Trade Log (Legacy)</div>', unsafe_allow_html=True)
    
    if NotionTradeService is None:
        st.info("Notion integration not available")
        return
    
    try:
        if 'notion_service' not in st.session_state:
            service = NotionTradeService()
            service.connect()
            service.find_or_create_databases()
            st.session_state['notion_service'] = service
        
        service = st.session_state['notion_service']
        
        if service.client:
            st.success("Notion Connected")
        else:
            st.warning("Notion not connected")
    except Exception as e:
        st.error(f"Notion error: {e}")

def main():
    st.title("🤖 Crypto Trading Bot")
    st.caption("Multi-grid automated trading system with risk management")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Controls", "Grids", "Market", "Settings"])
    
    with tab1:
        render_risk_dashboard()
        render_grid_status()
        render_pnl_summary()
    
    with tab2:
        render_controls()
    
    with tab3:
        render_grid_config()
    
    with tab4:
        render_market_overview()
        
        st.markdown('<div class="section-header">Trending Coins</div>', unsafe_allow_html=True)
        trending = get_trending_coins()
        if trending:
            cols = st.columns(5)
            for idx, coin in enumerate(trending[:5]):
                with cols[idx]:
                    st.markdown(f"**{coin.get('name', 'Unknown')}**")
                    st.caption(coin.get('symbol', ''))
    
    with tab5:
        st.markdown('<div class="section-header">System Settings</div>', unsafe_allow_html=True)
        
        st.subheader("Risk Thresholds")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Max Drawdown %", value=RISK_THRESHOLDS['max_drawdown_percent'], disabled=True)
            st.number_input("Max API Error Rate %", value=RISK_THRESHOLDS['max_api_error_rate'], disabled=True)
        with col2:
            st.number_input("Volatility Breaker Count", value=RISK_THRESHOLDS['volatility_breaker_count'], disabled=True)
            st.number_input("Max Position Size %", value=RISK_THRESHOLDS['max_position_size_percent'], disabled=True)
        
        st.divider()
        
        render_notion_trades()
    
    with st.sidebar:
        st.markdown("### System Status")
        
        api_status = get_api_status()
        if api_status:
            st.success("API: Connected")
        else:
            st.warning("API: Offline (using local engine)")
        
        bybit_client = get_bybit_client()
        if isinstance(bybit_client, MockBybitClient):
            st.info("Bybit: Mock Mode")
        else:
            st.success("Bybit: Connected")
        
        st.divider()
        
        st.markdown("### Quick Actions")
        
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("Rebalance All", use_container_width=True):
            call_api("/api/rebalance", "POST")
            st.success("Rebalanced")
            st.rerun()
        
        st.divider()
        
        st.markdown("### Capital Allocation")
        total_capital = 0
        for symbol, config in DEFAULT_GRID_CONFIGS.items():
            st.caption(f"{symbol}: ${config.total_investment:,.0f}")
            total_capital += config.total_investment
        st.caption(f"**Total: ${total_capital:,.0f}**")
        
        st.divider()
        
        st.markdown("### About")
        st.caption("Multi-grid crypto trading bot with automated order management and risk controls.")
        st.caption("Data: Bybit API v5 + CoinGecko")

if __name__ == "__main__":
    main()
