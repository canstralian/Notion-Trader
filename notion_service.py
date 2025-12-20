import os
import requests
from notion_client import Client
from datetime import datetime
from typing import Optional, List, Dict, Any

connection_settings = None

def get_access_token():
    global connection_settings
    
    if connection_settings and connection_settings.get('settings', {}).get('expires_at'):
        expires_at = connection_settings['settings']['expires_at']
        if datetime.fromisoformat(expires_at.replace('Z', '+00:00')) > datetime.now():
            return connection_settings['settings']['access_token']
    
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        raise Exception('X_REPLIT_TOKEN not found for repl/depl')
    
    response = requests.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=notion',
        headers={
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
    )
    
    data = response.json()
    connection_settings = data.get('items', [{}])[0] if data.get('items') else {}
    
    access_token = (
        connection_settings.get('settings', {}).get('access_token') or
        connection_settings.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
    )
    
    if not connection_settings or not access_token:
        raise Exception('Notion not connected')
    
    return access_token

def get_notion_client():
    access_token = get_access_token()
    return Client(auth=access_token)

class NotionTradeService:
    def __init__(self):
        self.client = None
        self.trades_db_id = None
        self.portfolio_db_id = None
        self.strategies_db_id = None
    
    def connect(self):
        self.client = get_notion_client()
        return True
    
    def find_or_create_databases(self):
        if not self.client:
            self.connect()
        
        search_results = self.client.search()
        
        for item in search_results.get('results', []):
            if item.get('object') == 'database':
                title = item.get('title', [{}])[0].get('plain_text', '') if item.get('title') else ''
                if title == 'Crypto Trades':
                    self.trades_db_id = item['id']
                elif title == 'Crypto Portfolio':
                    self.portfolio_db_id = item['id']
                elif title == 'Trading Strategies':
                    self.strategies_db_id = item['id']
        
        parent_page_id = None
        
        for item in search_results.get('results', []):
            if item.get('object') == 'page':
                if item.get('parent', {}).get('type') == 'workspace':
                    parent_page_id = item['id']
                    break
        
        if not parent_page_id:
            new_page = self.client.pages.create(
                parent={"type": "workspace", "workspace": True},
                properties={
                    "title": [{"type": "text", "text": {"content": "Crypto Trading"}}]
                }
            )
            parent_page_id = new_page['id']
        
        if not self.trades_db_id:
            trades_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": "Crypto Trades"}}],
                properties={
                    "Trade": {"title": {}},
                    "Coin": {"select": {"options": [
                        {"name": "BTC", "color": "orange"},
                        {"name": "ETH", "color": "blue"},
                        {"name": "SOL", "color": "purple"},
                        {"name": "DOGE", "color": "yellow"},
                        {"name": "XRP", "color": "gray"},
                        {"name": "ADA", "color": "green"},
                    ]}},
                    "Type": {"select": {"options": [
                        {"name": "Buy", "color": "green"},
                        {"name": "Sell", "color": "red"}
                    ]}},
                    "Price": {"number": {"format": "dollar"}},
                    "Quantity": {"number": {"format": "number"}},
                    "Total": {"number": {"format": "dollar"}},
                    "Date": {"date": {}},
                    "Notes": {"rich_text": {}},
                    "Status": {"select": {"options": [
                        {"name": "Open", "color": "blue"},
                        {"name": "Closed", "color": "gray"}
                    ]}}
                }
            )
            self.trades_db_id = trades_db['id']
        
        if not self.portfolio_db_id:
            portfolio_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": "Crypto Portfolio"}}],
                properties={
                    "Holding": {"title": {}},
                    "Coin": {"select": {"options": [
                        {"name": "BTC", "color": "orange"},
                        {"name": "ETH", "color": "blue"},
                        {"name": "SOL", "color": "purple"},
                        {"name": "DOGE", "color": "yellow"},
                        {"name": "XRP", "color": "gray"},
                        {"name": "ADA", "color": "green"},
                    ]}},
                    "Quantity": {"number": {"format": "number"}},
                    "Avg Buy Price": {"number": {"format": "dollar"}},
                    "Total Invested": {"number": {"format": "dollar"}},
                    "Current Value": {"number": {"format": "dollar"}},
                    "Profit/Loss": {"number": {"format": "dollar"}},
                    "Profit/Loss %": {"number": {"format": "percent"}}
                }
            )
            self.portfolio_db_id = portfolio_db['id']
        
        if not self.strategies_db_id:
            strategies_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": "Trading Strategies"}}],
                properties={
                    "Strategy": {"title": {}},
                    "Description": {"rich_text": {}},
                    "Target Coins": {"multi_select": {"options": [
                        {"name": "BTC", "color": "orange"},
                        {"name": "ETH", "color": "blue"},
                        {"name": "SOL", "color": "purple"},
                        {"name": "DOGE", "color": "yellow"},
                        {"name": "XRP", "color": "gray"},
                        {"name": "ADA", "color": "green"},
                    ]}},
                    "Risk Level": {"select": {"options": [
                        {"name": "Low", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "red"}
                    ]}},
                    "Status": {"select": {"options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Paused", "color": "yellow"},
                        {"name": "Archived", "color": "gray"}
                    ]}},
                    "Win Rate": {"number": {"format": "percent"}},
                    "Notes": {"rich_text": {}}
                }
            )
            self.strategies_db_id = strategies_db['id']
        
        return True
    
    def log_trade(self, coin: str, trade_type: str, price: float, quantity: float, 
                  notes: str = "", date: Optional[str] = None) -> Dict:
        if not self.trades_db_id:
            self.find_or_create_databases()
        
        trade_date = date or datetime.now().strftime("%Y-%m-%d")
        total = price * quantity
        
        properties = {
            "Trade": {"title": [{"text": {"content": f"{trade_type} {quantity} {coin}"}}]},
            "Coin": {"select": {"name": coin}},
            "Type": {"select": {"name": trade_type}},
            "Price": {"number": price},
            "Quantity": {"number": quantity},
            "Total": {"number": total},
            "Date": {"date": {"start": trade_date}},
            "Status": {"select": {"name": "Open"}}
        }
        
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        result = self.client.pages.create(
            parent={"database_id": self.trades_db_id},
            properties=properties
        )
        
        self._update_portfolio(coin, trade_type, price, quantity)
        
        return result
    
    def _update_portfolio(self, coin: str, trade_type: str, price: float, quantity: float):
        if not self.portfolio_db_id:
            return
        
        results = self.client.data_sources.query(
            data_source_id=self.portfolio_db_id,
            filter={"property": "Coin", "select": {"equals": coin}}
        )
        
        if results.get('results'):
            holding = results['results'][0]
            holding_id = holding['id']
            current_qty = holding['properties']['Quantity']['number'] or 0
            current_invested = holding['properties']['Total Invested']['number'] or 0
            
            if trade_type == "Buy":
                new_qty = current_qty + quantity
                new_invested = current_invested + (price * quantity)
            else:
                new_qty = max(0, current_qty - quantity)
                ratio = quantity / current_qty if current_qty > 0 else 0
                new_invested = max(0, current_invested - (current_invested * ratio))
            
            avg_price = new_invested / new_qty if new_qty > 0 else 0
            
            self.client.pages.update(
                page_id=holding_id,
                properties={
                    "Quantity": {"number": new_qty},
                    "Avg Buy Price": {"number": avg_price},
                    "Total Invested": {"number": new_invested}
                }
            )
        else:
            if trade_type == "Buy":
                self.client.pages.create(
                    parent={"database_id": self.portfolio_db_id},
                    properties={
                        "Holding": {"title": [{"text": {"content": f"{coin} Holdings"}}]},
                        "Coin": {"select": {"name": coin}},
                        "Quantity": {"number": quantity},
                        "Avg Buy Price": {"number": price},
                        "Total Invested": {"number": price * quantity},
                        "Current Value": {"number": 0},
                        "Profit/Loss": {"number": 0},
                        "Profit/Loss %": {"number": 0}
                    }
                )
    
    def get_trades(self, limit: int = 50) -> List[Dict]:
        if not self.trades_db_id:
            self.find_or_create_databases()
        
        if not self.trades_db_id:
            return []
        
        try:
            results = self.client.data_sources.query(
                data_source_id=self.trades_db_id,
                sorts=[{"property": "Date", "direction": "descending"}],
                page_size=limit
            )
        except Exception as e:
            if "Could not find" in str(e):
                self.trades_db_id = None
                self.find_or_create_databases()
                if not self.trades_db_id:
                    return []
                results = self.client.data_sources.query(
                    data_source_id=self.trades_db_id,
                    sorts=[{"property": "Date", "direction": "descending"}],
                    page_size=limit
                )
            else:
                raise
        
        trades = []
        for page in results.get('results', []):
            props = page['properties']
            trades.append({
                'id': page['id'],
                'coin': props.get('Coin', {}).get('select', {}).get('name', ''),
                'type': props.get('Type', {}).get('select', {}).get('name', ''),
                'price': props.get('Price', {}).get('number', 0),
                'quantity': props.get('Quantity', {}).get('number', 0),
                'total': props.get('Total', {}).get('number', 0),
                'date': props.get('Date', {}).get('date', {}).get('start', ''),
                'notes': ''.join([t.get('plain_text', '') for t in props.get('Notes', {}).get('rich_text', [])]),
                'status': props.get('Status', {}).get('select', {}).get('name', '')
            })
        
        return trades
    
    def get_portfolio(self) -> List[Dict]:
        if not self.portfolio_db_id:
            self.find_or_create_databases()
        
        if not self.portfolio_db_id:
            return []
        
        try:
            results = self.client.data_sources.query(data_source_id=self.portfolio_db_id)
        except Exception as e:
            if "Could not find" in str(e):
                self.portfolio_db_id = None
                self.find_or_create_databases()
                if not self.portfolio_db_id:
                    return []
                results = self.client.data_sources.query(data_source_id=self.portfolio_db_id)
            else:
                raise
        
        portfolio = []
        for page in results.get('results', []):
            props = page['properties']
            portfolio.append({
                'id': page['id'],
                'coin': props.get('Coin', {}).get('select', {}).get('name', ''),
                'quantity': props.get('Quantity', {}).get('number', 0),
                'avg_buy_price': props.get('Avg Buy Price', {}).get('number', 0),
                'total_invested': props.get('Total Invested', {}).get('number', 0),
                'current_value': props.get('Current Value', {}).get('number', 0),
                'profit_loss': props.get('Profit/Loss', {}).get('number', 0),
                'profit_loss_pct': props.get('Profit/Loss %', {}).get('number', 0)
            })
        
        return portfolio
    
    def update_portfolio_values(self, current_prices: Dict[str, float]):
        if not self.portfolio_db_id:
            return
        
        results = self.client.data_sources.query(data_source_id=self.portfolio_db_id)
        
        for page in results.get('results', []):
            props = page['properties']
            coin = props.get('Coin', {}).get('select', {}).get('name', '')
            quantity = props.get('Quantity', {}).get('number', 0) or 0
            total_invested = props.get('Total Invested', {}).get('number', 0) or 0
            
            if coin in current_prices and quantity > 0:
                current_value = quantity * current_prices[coin]
                profit_loss = current_value - total_invested
                profit_loss_pct = (profit_loss / total_invested) if total_invested > 0 else 0
                
                self.client.pages.update(
                    page_id=page['id'],
                    properties={
                        "Current Value": {"number": current_value},
                        "Profit/Loss": {"number": profit_loss},
                        "Profit/Loss %": {"number": profit_loss_pct}
                    }
                )
    
    def get_strategies(self) -> List[Dict]:
        if not self.strategies_db_id:
            self.find_or_create_databases()
        
        if not self.strategies_db_id:
            return []
        
        try:
            results = self.client.data_sources.query(data_source_id=self.strategies_db_id)
        except Exception as e:
            if "Could not find" in str(e):
                self.strategies_db_id = None
                self.find_or_create_databases()
                if not self.strategies_db_id:
                    return []
                results = self.client.data_sources.query(data_source_id=self.strategies_db_id)
            else:
                raise
        
        strategies = []
        for page in results.get('results', []):
            props = page['properties']
            strategies.append({
                'id': page['id'],
                'name': ''.join([t.get('plain_text', '') for t in props.get('Strategy', {}).get('title', [])]),
                'description': ''.join([t.get('plain_text', '') for t in props.get('Description', {}).get('rich_text', [])]),
                'target_coins': [opt.get('name', '') for opt in props.get('Target Coins', {}).get('multi_select', [])],
                'risk_level': props.get('Risk Level', {}).get('select', {}).get('name', ''),
                'status': props.get('Status', {}).get('select', {}).get('name', ''),
                'win_rate': props.get('Win Rate', {}).get('number', 0),
                'notes': ''.join([t.get('plain_text', '') for t in props.get('Notes', {}).get('rich_text', [])])
            })
        
        return strategies
    
    def add_strategy(self, name: str, description: str, target_coins: List[str], 
                     risk_level: str, notes: str = "") -> Dict:
        if not self.strategies_db_id:
            self.find_or_create_databases()
        
        properties = {
            "Strategy": {"title": [{"text": {"content": name}}]},
            "Description": {"rich_text": [{"text": {"content": description}}]},
            "Target Coins": {"multi_select": [{"name": coin} for coin in target_coins]},
            "Risk Level": {"select": {"name": risk_level}},
            "Status": {"select": {"name": "Active"}},
            "Win Rate": {"number": 0}
        }
        
        if notes:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        
        result = self.client.pages.create(
            parent={"database_id": self.strategies_db_id},
            properties=properties
        )
        
        return result
