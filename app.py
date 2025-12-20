import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from notion_service import NotionTradeService
from crypto_api import (
    get_current_prices, get_market_data, get_coin_history,
    get_trending_coins, format_currency, format_percent, COIN_MAP
)

st.set_page_config(
    page_title="Crypto Trading Dashboard",
    page_icon="📈",
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
    
    .trade-row {
        background-color: #F7F6F3;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 6px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .coin-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 12px;
    }
    
    .buy-badge {
        background-color: rgba(15, 123, 108, 0.1);
        color: #0F7B6C;
    }
    
    .sell-badge {
        background-color: rgba(224, 62, 62, 0.1);
        color: #E03E3E;
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
    
    .sidebar .stSelectbox label, .sidebar .stNumberInput label {
        color: #37352F;
        font-weight: 500;
    }
    
    div[data-testid="stDataFrame"] {
        border: 1px solid #E8E7E4;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F7F6F3;
        padding: 4px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #37352F;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .price-up {
        color: #0F7B6C;
    }
    
    .price-down {
        color: #E03E3E;
    }
    
    h1 {
        color: #000000;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #000000;
        font-weight: 600;
    }
    
    .stMetric label {
        color: #37352F !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_notion_service():
    if 'notion_service' not in st.session_state:
        service = NotionTradeService()
        try:
            service.connect()
            service.find_or_create_databases()
            st.session_state['notion_service'] = service
        except Exception as e:
            st.error(f"Failed to connect to Notion: {e}")
            return NotionTradeService()
    return st.session_state['notion_service']

def reset_notion_service():
    if 'notion_service' in st.session_state:
        del st.session_state['notion_service']

def render_market_overview():
    st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)
    
    market_data = get_market_data()
    
    if not market_data:
        st.warning("Unable to fetch market data. Please try again later.")
        return
    
    cols = st.columns(5)
    for i, coin in enumerate(market_data[:5]):
        with cols[i]:
            change = coin.get('change_24h', 0) or 0
            delta_color = "normal" if change >= 0 else "inverse"
            st.metric(
                label=f"{coin['symbol']}",
                value=format_currency(coin['price']),
                delta=format_percent(change),
                delta_color=delta_color
            )

def render_portfolio_summary(notion_service):
    st.markdown('<div class="section-header">Portfolio Summary</div>', unsafe_allow_html=True)
    
    try:
        portfolio = notion_service.get_portfolio()
        prices = get_current_prices()
        
        if prices:
            notion_service.update_portfolio_values(prices)
            portfolio = notion_service.get_portfolio()
    except Exception as e:
        st.warning(f"Could not load portfolio: {e}")
        portfolio = []
    
    total_invested = sum(h.get('total_invested', 0) or 0 for h in portfolio)
    total_value = sum(h.get('current_value', 0) or 0 for h in portfolio)
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invested", format_currency(total_invested))
    with col2:
        st.metric("Current Value", format_currency(total_value))
    with col3:
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("Total P/L", format_currency(total_pnl), delta=format_percent(total_pnl_pct), delta_color=delta_color)
    with col4:
        st.metric("Holdings", str(len([h for h in portfolio if h.get('quantity', 0) > 0])))
    
    if portfolio:
        st.markdown("#### Holdings")
        holdings_data = []
        for h in portfolio:
            if h.get('quantity', 0) > 0:
                holdings_data.append({
                    "Coin": h.get('coin', ''),
                    "Quantity": f"{h.get('quantity', 0):.6f}",
                    "Avg Price": format_currency(h.get('avg_buy_price', 0)),
                    "Current Value": format_currency(h.get('current_value', 0)),
                    "P/L": format_currency(h.get('profit_loss', 0)),
                    "P/L %": format_percent(h.get('profit_loss_pct', 0) * 100)
                })
        
        if holdings_data:
            df = pd.DataFrame(holdings_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def render_trade_form(notion_service):
    st.markdown('<div class="section-header">Log Trade</div>', unsafe_allow_html=True)
    
    with st.form("trade_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            coin = st.selectbox("Coin", list(COIN_MAP.keys()))
            trade_type = st.selectbox("Type", ["Buy", "Sell"])
            price = st.number_input("Price (USD)", min_value=0.0, format="%.6f")
        
        with col2:
            quantity = st.number_input("Quantity", min_value=0.0, format="%.8f")
            trade_date = st.date_input("Date", value=datetime.now())
            notes = st.text_input("Notes (optional)")
        
        total = price * quantity
        st.markdown(f"**Total:** {format_currency(total)}")
        
        submitted = st.form_submit_button("Log Trade", use_container_width=True)
        
        if submitted:
            if price > 0 and quantity > 0:
                try:
                    notion_service.log_trade(
                        coin=coin,
                        trade_type=trade_type,
                        price=price,
                        quantity=quantity,
                        notes=notes,
                        date=trade_date.strftime("%Y-%m-%d")
                    )
                    st.success(f"Trade logged: {trade_type} {quantity} {coin} at {format_currency(price)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to log trade: {e}")
            else:
                st.warning("Please enter valid price and quantity")

def render_trade_history(notion_service):
    st.markdown('<div class="section-header">Trade History</div>', unsafe_allow_html=True)
    
    try:
        trades = notion_service.get_trades()
    except Exception as e:
        st.warning(f"Could not load trades: {e}")
        trades = []
    
    if trades:
        trades_data = []
        for t in trades:
            trades_data.append({
                "Date": t.get('date', ''),
                "Type": t.get('type', ''),
                "Coin": t.get('coin', ''),
                "Quantity": f"{t.get('quantity', 0):.6f}",
                "Price": format_currency(t.get('price', 0)),
                "Total": format_currency(t.get('total', 0)),
                "Status": t.get('status', ''),
                "Notes": t.get('notes', '')
            })
        
        df = pd.DataFrame(trades_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No trades logged yet. Use the form above to log your first trade!")

def render_strategies(notion_service):
    st.markdown('<div class="section-header">Trading Strategies</div>', unsafe_allow_html=True)
    
    with st.expander("Add New Strategy", expanded=False):
        with st.form("strategy_form", clear_on_submit=True):
            name = st.text_input("Strategy Name")
            description = st.text_area("Description")
            target_coins = st.multiselect("Target Coins", list(COIN_MAP.keys()))
            risk_level = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            notes = st.text_input("Notes (optional)")
            
            if st.form_submit_button("Add Strategy", use_container_width=True):
                if name and description:
                    try:
                        notion_service.add_strategy(
                            name=name,
                            description=description,
                            target_coins=target_coins,
                            risk_level=risk_level,
                            notes=notes
                        )
                        st.success(f"Strategy '{name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add strategy: {e}")
                else:
                    st.warning("Please enter strategy name and description")
    
    try:
        strategies = notion_service.get_strategies()
    except Exception as e:
        st.warning(f"Could not load strategies: {e}")
        strategies = []
    
    if strategies:
        for s in strategies:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{s.get('name', 'Unnamed')}**")
                    st.caption(s.get('description', ''))
                with col2:
                    coins = ", ".join(s.get('target_coins', []))
                    st.caption(f"Coins: {coins}")
                with col3:
                    risk = s.get('risk_level', 'Unknown')
                    status = s.get('status', 'Unknown')
                    risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk, "⚪")
                    st.caption(f"{risk_color} {risk} | {status}")
                st.divider()
    else:
        st.info("No strategies defined yet. Add your first trading strategy!")

def render_market_details():
    st.markdown('<div class="section-header">Market Details</div>', unsafe_allow_html=True)
    
    market_data = get_market_data()
    
    if market_data:
        data = []
        for coin in market_data:
            data.append({
                "Coin": f"{coin['name']} ({coin['symbol']})",
                "Price": format_currency(coin['price']),
                "1h": format_percent(coin.get('change_1h', 0)),
                "24h": format_percent(coin.get('change_24h', 0)),
                "7d": format_percent(coin.get('change_7d', 0)),
                "Market Cap": format_currency(coin.get('market_cap', 0)),
                "Volume 24h": format_currency(coin.get('volume_24h', 0)),
                "24h High": format_currency(coin.get('high_24h', 0)),
                "24h Low": format_currency(coin.get('low_24h', 0))
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("#### Trending Coins")
    trending = get_trending_coins()
    
    if trending:
        cols = st.columns(5)
        for i, coin in enumerate(trending[:5]):
            with cols[i]:
                st.markdown(f"**{coin['symbol']}**")
                st.caption(f"{coin['name']}")
                st.caption(f"Rank #{coin.get('market_cap_rank', 'N/A')}")

def main():
    st.title("📈 Crypto Trading Dashboard")
    st.caption("Track your trades, portfolio, and strategies with Notion integration")
    
    notion_service = get_notion_service()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Trade", "Market", "Strategies"])
    
    with tab1:
        render_market_overview()
        render_portfolio_summary(notion_service)
        render_trade_history(notion_service)
    
    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            render_trade_form(notion_service)
        with col2:
            st.markdown('<div class="section-header">Quick Prices</div>', unsafe_allow_html=True)
            prices = get_current_prices()
            if prices:
                for coin, price in prices.items():
                    st.metric(coin, format_currency(price))
    
    with tab3:
        render_market_details()
    
    with tab4:
        render_strategies(notion_service)
    
    with st.sidebar:
        st.markdown("### Quick Actions")
        
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("Reset Notion Connection", use_container_width=True):
            reset_notion_service()
            st.rerun()
        
        st.divider()
        
        st.markdown("### Connection Status")
        try:
            if notion_service.client:
                notion_service.client.users.me()
                st.success("Notion: Connected")
                if notion_service.trades_db_id:
                    st.caption(f"Databases: Ready")
                else:
                    st.warning("Databases: Not initialized")
            else:
                st.error("Notion: Not connected")
        except:
            st.error("Notion: Disconnected")
        
        st.divider()
        
        st.markdown("### About")
        st.caption("Cryptocurrency trading dashboard with Notion integration for persistent data storage.")
        st.caption("Data powered by CoinGecko API")

if __name__ == "__main__":
    main()
