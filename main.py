"""
Arbitrage API - Main FastAPI Application
Provides real-time CEX and DEX arbitrage opportunities
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import asyncio
import uvicorn
from datetime import datetime
import json

from arbitrage_detector import ArbitrageDetector
from exchange_manager import ExchangeManager

app = FastAPI(
    title="Crypto Arbitrage API",
    description="Real-time CEX and DEX arbitrage opportunity detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
exchange_manager = ExchangeManager()
arbitrage_detector = ArbitrageDetector(exchange_manager)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize exchange connections and start monitoring"""
    await exchange_manager.initialize()
    asyncio.create_task(arbitrage_monitor())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await exchange_manager.close_all()

async def arbitrage_monitor():
    """Background task to continuously detect and broadcast arbitrage opportunities"""
    while True:
        try:
            # Detect cross-exchange arbitrage
            cross_exchange_opps = await arbitrage_detector.detect_cross_exchange_arbitrage()
            
            # Detect intra-exchange triangular arbitrage
            triangular_opps = await arbitrage_detector.detect_intra_exchange_triangular()
            
            # Broadcast opportunities
            if cross_exchange_opps or triangular_opps:
                await manager.broadcast({
                    "timestamp": datetime.utcnow().isoformat(),
                    "cross_exchange_arbitrage": cross_exchange_opps[:10],  # Top 10
                    "intra_exchange_triangular": triangular_opps[:10]  # Top 10
                })
            
            await asyncio.sleep(2)  # Check every 2 seconds
        except Exception as e:
            print(f"Error in arbitrage monitor: {e}")
            await asyncio.sleep(5)

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "message": "Crypto Arbitrage API",
        "version": "1.0.0"
    }

@app.get("/exchanges")
async def get_exchanges():
    """Get list of connected exchanges"""
    return {
        "cex": exchange_manager.get_cex_list(),
        "dex": exchange_manager.get_dex_list()
    }

@app.get("/prices/{symbol}")
async def get_prices(symbol: str):
    """Get current prices for a symbol across all exchanges"""
    try:
        prices = await exchange_manager.get_prices(symbol)
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "prices": prices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage/cross-exchange")
async def get_cross_exchange_arbitrage(
    min_profit_percent: Optional[float] = 0.5,
    symbols: Optional[str] = None
):
    """
    Get cross-exchange arbitrage opportunities (buy on one exchange, sell on another)
    Works for CEX-to-CEX, DEX-to-DEX, and CEX-to-DEX
    
    - min_profit_percent: Minimum profit percentage to filter (default 0.5%)
    - symbols: Comma-separated list of symbols to check (e.g., "BTC/USDT,ETH/USDT")
    
    Note: For DEX arbitrage, profit is calculated AFTER gas fees
    """
    try:
        symbol_list = symbols.split(",") if symbols else None
        opportunities = await arbitrage_detector.detect_cross_exchange_arbitrage(
            min_profit_percent=min_profit_percent,
            symbols=symbol_list
        )
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(opportunities),
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage/triangular")
async def get_intra_exchange_triangular(
    min_profit_percent: Optional[float] = 0.5,
    exchange: Optional[str] = None
):
    """
    Get triangular arbitrage opportunities within a SINGLE exchange
    
    - min_profit_percent: Minimum profit percentage to filter (default 0.5%)
    - exchange: Specific exchange to check (optional)
    
    Works for both CEX and DEX. For DEX, profit is calculated AFTER gas fees.
    """
    try:
        opportunities = await arbitrage_detector.detect_intra_exchange_triangular(
            min_profit_percent=min_profit_percent,
            exchange=exchange
        )
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(opportunities),
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage/multi-dex-triangular")
async def get_multi_dex_triangular(
    chain: str,
    min_profit_percent: Optional[float] = 0.5
):
    """
    Get triangular arbitrage using multiple DEXs on the SAME blockchain
    
    - chain: 'ethereum', 'bsc', or 'solana'
    - min_profit_percent: Minimum profit percentage to filter (default 0.5%)
    
    Example: Buy on Uniswap, swap on SushiSwap, sell back on Uniswap
    Note: Higher gas costs due to multiple contract interactions
    """
    try:
        if chain not in ['ethereum', 'bsc', 'solana']:
            raise HTTPException(status_code=400, detail="Chain must be 'ethereum', 'bsc', or 'solana'")
        
        opportunities = await arbitrage_detector.detect_multi_dex_triangular(
            chain=chain,
            min_profit_percent=min_profit_percent
        )
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "chain": chain,
            "count": len(opportunities),
            "opportunities": opportunities
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gas-fees")
async def get_gas_fees():
    """
    Get current gas prices and estimated costs for DEX trading
    
    Returns gas prices for Ethereum and BSC networks with cost estimates
    """
    try:
        gas_summary = await arbitrage_detector.gas_estimator.get_gas_price_summary()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "gas_data": gas_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gas-fees/estimate")
async def estimate_gas_cost(
    chain: str,
    arbitrage_type: str = 'simple',
    trade_amount_usd: float = 10000,
    speed: str = 'standard'
):
    """
    Estimate gas cost for a DEX arbitrage trade
    
    - chain: 'ethereum', 'bsc', or 'solana'
    - arbitrage_type: 'simple', 'triangular', or 'cross_dex'
    - trade_amount_usd: Trade amount in USD (default 10000)
    - speed: 'fast', 'standard', or 'slow'
    """
    try:
        if chain not in ['ethereum', 'bsc', 'solana']:
            raise HTTPException(status_code=400, detail="Chain must be 'ethereum', 'bsc', or 'solana'")
        
        if arbitrage_type not in ['simple', 'triangular', 'cross_dex']:
            raise HTTPException(status_code=400, detail="Invalid arbitrage_type")
        
        if speed not in ['fast', 'standard', 'slow']:
            raise HTTPException(status_code=400, detail="Speed must be 'fast', 'standard', or 'slow'")
        
        # Estimate gas cost
        if arbitrage_type == 'triangular':
            gas_info = await arbitrage_detector.gas_estimator.calculate_triangular_gas_cost(
                chain=chain,
                speed=speed
            )
        elif arbitrage_type == 'cross_dex':
            gas_info = await arbitrage_detector.gas_estimator.calculate_cross_dex_gas_cost(
                chain=chain,
                speed=speed
            )
        else:  # simple
            gas_info = await arbitrage_detector.gas_estimator.estimate_swap_cost(
                chain=chain,
                num_swaps=2,
                speed=speed
            )
        
        # Calculate minimum profitable amount
        min_amount = arbitrage_detector.gas_estimator.get_minimum_profitable_amount(
            gas_cost_usd=gas_info['gas_cost_usd'],
            profit_percent=0.5  # 0.5% profit threshold
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "chain": chain,
            "arbitrage_type": arbitrage_type,
            "speed": speed,
            "gas_estimate": gas_info,
            "minimum_profitable_amount_usd": min_amount
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time arbitrage opportunities
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/market-depth/{exchange}/{symbol}")
async def get_market_depth(exchange: str, symbol: str, limit: int = 20):
    """Get order book depth for a specific exchange and symbol"""
    try:
        depth = await exchange_manager.get_order_book(exchange, symbol, limit)
        return {
            "exchange": exchange,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "depth": depth
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
