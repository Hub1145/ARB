"""
Example client for the Arbitrage API
Demonstrates how to use the REST API and WebSocket endpoints
"""
import requests
import asyncio
import websockets
import json
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000"

def get_exchanges():
    """Get list of connected exchanges"""
    response = requests.get(f"{BASE_URL}/exchanges")
    data = response.json()
    print("\n=== Connected Exchanges ===")
    print(f"CEX: {', '.join(data['cex'])}")
    print(f"DEX: {', '.join(data['dex'])}")
    return data

def get_prices(symbol="BTC/USDT"):
    """Get current prices for a symbol"""
    response = requests.get(f"{BASE_URL}/prices/{symbol}")
    data = response.json()
    print(f"\n=== Prices for {symbol} ===")
    for exchange, price_data in data['prices'].items():
        print(f"{exchange:15} - Bid: ${price_data['bid']:,.2f} | Ask: ${price_data['ask']:,.2f}")
    return data

def get_simple_arbitrage(min_profit=0.5, symbols=None):
    """Get simple arbitrage opportunities"""
    params = {"min_profit_percent": min_profit}
    if symbols:
        params["symbols"] = symbols
    
    response = requests.get(f"{BASE_URL}/arbitrage/simple", params=params)
    data = response.json()
    
    print(f"\n=== Simple Arbitrage Opportunities (Min {min_profit}% profit) ===")
    print(f"Found {data['count']} opportunities\n")
    
    for i, opp in enumerate(data['opportunities'][:5], 1):  # Show top 5
        print(f"{i}. {opp['symbol']}")
        print(f"   Buy on:  {opp['buy_exchange']:15} @ ${opp['buy_price']:,.2f}")
        print(f"   Sell on: {opp['sell_exchange']:15} @ ${opp['sell_price']:,.2f}")
        print(f"   Profit:  {opp['profit_percent']}% | Spread: {opp['spread_percent']}%")
        print()
    
    return data

def get_triangular_arbitrage(min_profit=0.5, exchange=None):
    """Get triangular arbitrage opportunities"""
    params = {"min_profit_percent": min_profit}
    if exchange:
        params["exchange"] = exchange
    
    response = requests.get(f"{BASE_URL}/arbitrage/triangular", params=params)
    data = response.json()
    
    print(f"\n=== Triangular Arbitrage Opportunities (Min {min_profit}% profit) ===")
    print(f"Found {data['count']} opportunities\n")
    
    for i, opp in enumerate(data['opportunities'][:3], 1):  # Show top 3
        print(f"{i}. {opp['exchange'].upper()} - Starting with {opp['start_amount']} {opp['start_currency']}")
        print(f"   Path: {' -> '.join(opp['path'])}")
        print(f"   End amount: {opp['end_amount']} {opp['start_currency']}")
        print(f"   Profit: {opp['profit_amount']} {opp['start_currency']} ({opp['profit_percent']}%)")
        print()
    
    return data

def get_market_depth(exchange="binance", symbol="BTC/USDT", limit=5):
    """Get order book depth"""
    response = requests.get(f"{BASE_URL}/market-depth/{exchange}/{symbol}", params={"limit": limit})
    data = response.json()
    
    print(f"\n=== Order Book Depth: {exchange} - {symbol} ===")
    depth = data['depth']
    
    print("\nAsks (Sell Orders):")
    for price, amount in reversed(depth['asks'][:limit]):
        print(f"  ${price:,.2f}  |  {amount:.8f}")
    
    print("\n" + "-" * 40)
    
    print("\nBids (Buy Orders):")
    for price, amount in depth['bids'][:limit]:
        print(f"  ${price:,.2f}  |  {amount:.8f}")
    
    return data

async def websocket_client():
    """Connect to WebSocket for real-time updates"""
    uri = "ws://localhost:8000/ws"
    print("\n=== WebSocket: Real-time Arbitrage Opportunities ===")
    print("Listening for opportunities... (Press Ctrl+C to stop)\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send initial ping
            await websocket.send("ping")
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                timestamp = data.get('timestamp', '')
                simple = data.get('simple_arbitrage', [])
                triangular = data.get('triangular_arbitrage', [])
                
                if simple or triangular:
                    print(f"[{timestamp}] New opportunities detected!")
                    
                    if simple:
                        print(f"  Simple: {len(simple)} opportunities")
                        # Show best one
                        best = max(simple, key=lambda x: x['profit_percent'])
                        print(f"    Best: {best['symbol']} - {best['profit_percent']}% profit")
                    
                    if triangular:
                        print(f"  Triangular: {len(triangular)} opportunities")
                        # Show best one
                        best = max(triangular, key=lambda x: x['profit_percent'])
                        print(f"    Best: {best['exchange']} - {best['profit_percent']}% profit")
                    
                    print()
    
    except KeyboardInterrupt:
        print("\nWebSocket connection closed.")
    except Exception as e:
        print(f"WebSocket error: {e}")

def run_demo():
    """Run a complete demonstration of the API"""
    print("=" * 60)
    print("CRYPTO ARBITRAGE API - DEMO CLIENT")
    print("=" * 60)
    
    try:
        # 1. Check exchanges
        get_exchanges()
        
        # 2. Get prices for BTC
        get_prices("BTC/USDT")
        
        # 3. Find simple arbitrage
        get_simple_arbitrage(min_profit=0.3)
        
        # 4. Find triangular arbitrage
        get_triangular_arbitrage(min_profit=0.3)
        
        # 5. Check order book
        get_market_depth("binance", "BTC/USDT", limit=5)
        
        print("\n" + "=" * 60)
        print("Demo complete! Starting WebSocket listener...")
        print("=" * 60)
        
        # 6. Start WebSocket listener
        asyncio.run(websocket_client())
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API.")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_demo()
