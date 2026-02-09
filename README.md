# Crypto Arbitrage API

A comprehensive REST API and WebSocket service for detecting real-time cryptocurrency arbitrage opportunities across centralized (CEX) and decentralized (DEX) exchanges.

## Features

### Three Types of Arbitrage Detection

1. **Cross-Exchange Arbitrage** - Buy on one exchange, sell on another
   - CEX-to-CEX (e.g., Binance → Bybit)
   - DEX-to-DEX (e.g., Uniswap → SushiSwap)  
   - CEX-to-DEX (e.g., Binance → Uniswap)

2. **Intra-Exchange Triangular** - Within a single exchange
   - CEX: BTC/USDT → ETH/BTC → ETH/USDT on Binance
   - DEX: WETH/USDT → WBTC/WETH → WBTC/USDT on Uniswap

3. **Multi-DEX Triangular** - Across multiple DEXs on same chain
   - Use different DEXs for each leg of triangular arbitrage
   - Higher gas costs but potentially better prices

### Gas Fee Calculations ⛽

- **Real-time fee fetching** from Ethereum, BSC, and Solana networks
- **Automatic cost deduction** from DEX arbitrage profits
- **Profitability analysis** - only shows opportunities profitable after fees
- **Multiple speed options** - Fast, Standard, Slow
- **Minimum trade amount** calculations based on network fees

**Fee Comparison:**
- **Ethereum:** $10-50 per arbitrage (high, but deep liquidity)
- **BSC:** $1-5 per arbitrage (low fees, good for smaller trades)
- **Solana:** $0.01-0.10 per arbitrage (ultra-low fees!)

### Exchange Support

**Centralized Exchanges (CEX):**
- Binance
- KuCoin
- Bybit
- OKX
- Phemex

**Decentralized Exchanges (DEX):**
- **Ethereum:** Uniswap V2/V3, SushiSwap, Curve
- **BSC:** PancakeSwap V2/V3, BakerySwap, Biswap, SushiSwap
- **Solana:** Jupiter (aggregator), Orca, Raydium

### Additional Features
- **Real-time Price Tracking**: Live prices across all exchanges
- **WebSocket Support**: Real-time streaming of opportunities
- **RESTful API**: Easy-to-use HTTP endpoints
- **Order Book Analysis**: Deep market analysis
- **The Graph Integration**: Fast, efficient DEX data fetching

## Architecture

```
arbitrage-api/
├── main.py                 # FastAPI application and endpoints
├── exchange_manager.py     # Exchange connection handler
├── arbitrage_detector.py   # Arbitrage detection algorithms
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `config.py`:
   - Add your Infura API key for DEX support
   - Adjust trading pairs to monitor
   - Set minimum profit thresholds

4. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /
Health check endpoint

### GET /exchanges
List all connected exchanges
```bash
curl http://localhost:8000/exchanges
```

### GET /prices/{symbol}
Get current prices for a symbol across all exchanges
```bash
curl http://localhost:8000/prices/BTC/USDT
```

### GET /arbitrage/cross-exchange
Get cross-exchange arbitrage opportunities (between different exchanges)
```bash
# All opportunities
curl http://localhost:8000/arbitrage/cross-exchange

# Filter by minimum profit
curl http://localhost:8000/arbitrage/cross-exchange?min_profit_percent=0.5

# Check specific symbols
curl http://localhost:8000/arbitrage/cross-exchange?symbols=BTC/USDT,ETH/USDT
```

**Response Example:**
```json
{
  "timestamp": "2024-02-08T10:30:00",
  "count": 2,
  "opportunities": [
    {
      "type": "cross_exchange",
      "sub_type": "cex_to_cex",
      "symbol": "BTC/USDT",
      "buy_exchange": "binance",
      "sell_exchange": "bybit",
      "buy_price": 43500.50,
      "sell_price": 43750.25,
      "profit_percent": 0.47,
      "involves_dex": false
    },
    {
      "type": "cross_exchange",
      "sub_type": "dex_to_dex",
      "symbol": "WETH/USDT",
      "buy_exchange": "uniswap_v2",
      "sell_exchange": "sushiswap",
      "gross_profit_percent": 0.85,
      "gas_cost_usd": 12.50,
      "net_profit_percent": 0.60,
      "net_profit_usd": 60.00,
      "chain": "ethereum",
      "involves_dex": true
    }
  ]
}
```

### GET /arbitrage/triangular
Get triangular arbitrage opportunities within a single exchange
```bash
# All exchanges
curl http://localhost:8000/arbitrage/triangular

# Specific exchange
curl http://localhost:8000/arbitrage/triangular?exchange=binance

# With profit filter
curl http://localhost:8000/arbitrage/triangular?exchange=uniswap_v2&min_profit_percent=0.8
```

**Response Example:**
```json
{
  "timestamp": "2024-02-08T10:30:00",
  "count": 1,
  "opportunities": [
    {
      "type": "intra_exchange_triangular",
      "exchange_type": "dex",
      "exchange": "uniswap_v2",
      "chain": "ethereum",
      "start_currency": "USDT",
      "path": ["WETH/USDT", "WBTC/WETH", "WBTC/USDT"],
      "gross_profit_percent": 1.2,
      "gas_cost_usd": 28.00,
      "net_profit_percent": 0.92,
      "trade_amount_usd": 10000,
      "net_profit_usd": 92.00
    }
  ]
}
```

### GET /arbitrage/multi-dex-triangular
Get triangular arbitrage using multiple DEXs on the same chain
```bash
# Ethereum
curl http://localhost:8000/arbitrage/multi-dex-triangular?chain=ethereum&min_profit_percent=1.0

# BSC
curl http://localhost:8000/arbitrage/multi-dex-triangular?chain=bsc&min_profit_percent=0.5
```

**Response Example:**
```json
{
  "type": "multi_dex_triangular",
  "chain": "ethereum",
  "dexs_used": ["uniswap_v2", "sushiswap"],
  "num_dexs": 2,
  "path": ["uniswap_v2:WETH/USDT", "sushiswap:WBTC/WETH", "uniswap_v2:WBTC/USDT"],
  "gross_profit_percent": 1.8,
  "gas_cost_usd": 35.00,
  "net_profit_percent": 1.45,
  "net_profit_usd": 145.00
}
```

### GET /gas-fees
Get current gas prices for ETH and BSC
```bash
curl http://localhost:8000/gas-fees
```

### GET /gas-fees/estimate
Estimate gas cost for a specific arbitrage type
```bash
curl "http://localhost:8000/gas-fees/estimate?chain=ethereum&arbitrage_type=triangular&trade_amount_usd=5000&speed=fast"
```

**Response:**
```json
{
  "chain": "ethereum",
  "arbitrage_type": "triangular",
  "gas_estimate": {
    "gas_cost_usd": 33.75,
    "gas_price_gwei": 45,
    "total_gas_units": 450000,
    "native_token_cost": 0.0135
  },
  "minimum_profitable_amount_usd": 6750
}
```

### GET /market-depth/{exchange}/{symbol}
Get order book depth for analysis
```bash
curl http://localhost:8000/market-depth/binance/BTC/USDT?limit=10
```

### WebSocket /ws
Real-time streaming of arbitrage opportunities
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New opportunities:', data);
};
```

## Usage Examples

### Python Client Example
```python
import requests

# Get simple arbitrage opportunities
response = requests.get('http://localhost:8000/arbitrage/simple?min_profit_percent=0.5')
opportunities = response.json()

for opp in opportunities['opportunities']:
    print(f"Opportunity: Buy {opp['symbol']} on {opp['buy_exchange']} at {opp['buy_price']}")
    print(f"           Sell on {opp['sell_exchange']} at {opp['sell_price']}")
    print(f"           Expected profit: {opp['profit_percent']}%\n")
```

### WebSocket Client Example
```python
import asyncio
import websockets
import json

async def listen_to_arbitrage():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(listen_to_arbitrage())
```

## Configuration

Edit `config.py` to customize:

- **CEX_EXCHANGES**: List of centralized exchanges to monitor
- **DEX_CONFIGS**: DEX configurations with RPC URLs and contract addresses
- **COMMON_PAIRS**: Trading pairs to track
- **TRADING_FEE_PERCENT**: Expected trading fees (default 0.1%)
- **MIN_PROFIT_PERCENT**: Minimum profit threshold (default 0.5%)
- **SLIPPAGE_PERCENT**: Expected slippage (default 0.2%)

## Important Notes

### Gas/Transaction Fees for DEX Arbitrage ⚠️

**Critical:** DEX arbitrage profitability depends heavily on network fees!

The API automatically:
- Fetches real-time fees from ETH, BSC, and Solana networks
- Calculates transaction costs for each DEX operation
- **Deducts fees from profit calculations**
- Only shows opportunities that are profitable AFTER fees

**Fee Cost Ranges:**
- **Ethereum:** $10-50 per arbitrage (varies with network congestion)
- **BSC:** $1-5 per arbitrage (much cheaper)
- **Solana:** $0.01-0.10 per arbitrage (ultra-low transaction fees!)

**Minimum Trade Amounts:**
- **Ethereum Simple:** ~$2,000+ to be profitable at 0.5%
- **Ethereum Triangular:** ~$6,000+ to be profitable at 0.5%
- **BSC Simple:** ~$200+ to be profitable at 0.5%
- **BSC Triangular:** ~$600+ to be profitable at 0.5%
- **Solana Simple:** ~$20+ to be profitable at 0.5% (ultra-low barrier!)
- **Solana Triangular:** ~$60+ to be profitable at 0.5%

**Solana Advantage:** Solana's ultra-low fees (~$0.0001-0.001 per transaction) make it ideal for:
- High-frequency arbitrage
- Smaller trade amounts
- Testing strategies with minimal cost

See `ARBITRAGE_TYPES_GUIDE.md` for detailed fee analysis.

### Trading Fees and Slippage
The API accounts for:
- Trading fees on both buy and sell sides
- Does NOT account for withdrawal/deposit fees between CEX exchanges
- Does NOT account for slippage in the profit calculation (you should add buffer)
- **Does account for gas fees on all DEX operations**

### DEX Integration

The API includes **full DEX support for Ethereum and Binance Smart Chain**:

**Supported DEXs:**
- **Ethereum:** Uniswap V2/V3, SushiSwap
- **BSC:** PancakeSwap V2/V3, Biswap

**Data Sources:**
1. **The Graph Protocol** (primary) - Fast, indexed data with 100k free queries/month
2. **Direct on-chain queries** (fallback) - Uses public RPC endpoints

**No setup required** - Works out of the box with free public APIs!

For production or higher volume:
- Upgrade to Alchemy (300M free compute units/month)
- Upgrade to Infura (100k requests/day free)
- See `DEX_INTEGRATION.md` for detailed setup

The Graph free tier is **more than sufficient** for testing and small-scale production (100,000 queries/month = ~3,300 queries/day).

### Rate Limiting
The API respects exchange rate limits:

**CEX Exchanges:**
- Built-in rate limiting via ccxt library
- Each exchange has different limits

**DEX Data:**
- The Graph: 100,000 queries/month free (sufficient for most use cases)
- Public RPCs: ~100 requests/minute
- Upgrade to Alchemy/Infura for higher limits (see `DEX_INTEGRATION.md`)

For high-frequency monitoring:
- Use WebSocket streams from CEX exchanges
- Implement Redis caching (Docker setup included)
- Consider paid RPC providers for production

## Production Considerations

Before deploying to production:

1. **Security**:
   - Use environment variables for API keys
   - Implement authentication for your API
   - Enable HTTPS/WSS

2. **Performance**:
   - Add Redis for caching
   - Implement connection pooling
   - Use WebSocket feeds from exchanges instead of REST polling

3. **Monitoring**:
   - Add logging and monitoring
   - Set up alerts for opportunities above threshold
   - Track API health and latency

4. **Risk Management**:
   - Always verify opportunities before trading
   - Account for withdrawal limits and times
   - Monitor for exchange maintenance windows
   - Consider minimum profitable amounts (accounting for fixed fees)

## Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t arbitrage-api .
docker run -p 8000:8000 arbitrage-api
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT License - feel free to use and modify for your own projects.

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading carries significant risk. Always do your own research and never trade with money you cannot afford to lose. The authors are not responsible for any financial losses incurred through use of this software.

## Support

For issues or questions, please open an issue on the repository.
