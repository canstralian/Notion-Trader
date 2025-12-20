import requests
from typing import Dict, List, Optional
import time

COINGECKO_API = "https://api.coingecko.com/api/v3"

COIN_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "MATIC": "matic-network"
}

cache = {}
CACHE_DURATION = 60

def get_cached_data(key: str) -> Optional[Dict]:
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cached_data(key: str, data: Dict):
    cache[key] = (data, time.time())

def get_current_prices(coins: List[str] = None) -> Dict[str, float]:
    if coins is None:
        coins = list(COIN_MAP.keys())
    
    cache_key = f"prices_{'_'.join(sorted(coins))}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    coin_ids = [COIN_MAP.get(coin, coin.lower()) for coin in coins]
    ids_str = ",".join(coin_ids)
    
    try:
        response = requests.get(
            f"{COINGECKO_API}/simple/price",
            params={
                "ids": ids_str,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        for coin in coins:
            coin_id = COIN_MAP.get(coin, coin.lower())
            if coin_id in data:
                prices[coin] = data[coin_id].get("usd", 0)
        
        set_cached_data(cache_key, prices)
        return prices
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return {}

def get_market_data(coins: List[str] = None) -> List[Dict]:
    if coins is None:
        coins = list(COIN_MAP.keys())
    
    cache_key = f"market_{'_'.join(sorted(coins))}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    coin_ids = [COIN_MAP.get(coin, coin.lower()) for coin in coins]
    ids_str = ",".join(coin_ids)
    
    try:
        response = requests.get(
            f"{COINGECKO_API}/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": ids_str,
                "order": "market_cap_desc",
                "sparkline": "false",
                "price_change_percentage": "1h,24h,7d"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        market_data = []
        for item in data:
            symbol = item.get("symbol", "").upper()
            market_data.append({
                "symbol": symbol,
                "name": item.get("name", ""),
                "price": item.get("current_price", 0),
                "market_cap": item.get("market_cap", 0),
                "volume_24h": item.get("total_volume", 0),
                "change_1h": item.get("price_change_percentage_1h_in_currency", 0),
                "change_24h": item.get("price_change_percentage_24h", 0),
                "change_7d": item.get("price_change_percentage_7d_in_currency", 0),
                "high_24h": item.get("high_24h", 0),
                "low_24h": item.get("low_24h", 0),
                "image": item.get("image", "")
            })
        
        set_cached_data(cache_key, market_data)
        return market_data
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return []

def get_coin_history(coin: str, days: int = 30) -> Dict:
    coin_id = COIN_MAP.get(coin, coin.lower())
    cache_key = f"history_{coin_id}_{days}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    try:
        response = requests.get(
            f"{COINGECKO_API}/coins/{coin_id}/market_chart",
            params={
                "vs_currency": "usd",
                "days": days
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        history = {
            "prices": [(p[0], p[1]) for p in data.get("prices", [])],
            "market_caps": [(p[0], p[1]) for p in data.get("market_caps", [])],
            "volumes": [(p[0], p[1]) for p in data.get("total_volumes", [])]
        }
        
        set_cached_data(cache_key, history)
        return history
    except Exception as e:
        print(f"Error fetching coin history: {e}")
        return {"prices": [], "market_caps": [], "volumes": []}

def get_trending_coins() -> List[Dict]:
    cache_key = "trending"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    try:
        response = requests.get(f"{COINGECKO_API}/search/trending", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        trending = []
        for item in data.get("coins", [])[:10]:
            coin = item.get("item", {})
            trending.append({
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "market_cap_rank": coin.get("market_cap_rank", 0),
                "thumb": coin.get("thumb", "")
            })
        
        set_cached_data(cache_key, trending)
        return trending
    except Exception as e:
        print(f"Error fetching trending: {e}")
        return []

def format_currency(value: float) -> str:
    if value is None:
        return "$0.00"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    elif value >= 1:
        return f"${value:.2f}"
    else:
        return f"${value:.6f}"

def format_percent(value: float) -> str:
    if value is None:
        return "0.00%"
    return f"{value:+.2f}%"
