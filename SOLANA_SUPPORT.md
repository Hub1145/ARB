# Solana Support Documentation

## Overview

The Arbitrage API now supports **Solana network** in addition to Ethereum and BSC, with full integration for:
- **Jupiter Aggregator** - Primary DEX aggregator (aggregates all Solana DEXs)
- **Raydium** - Leading Solana AMM
- **Orca** - Concentrated liquidity DEX

---

## Supported Solana DEXs

### 1. Jupiter (Primary)
**What it is:** Jupiter is THE aggregator for Solana DEXs. It automatically finds the best route across all Solana DEXs.

**Why we use it:** 
- ✅ Aggregates ALL major Solana DEXs (Raydium, Orca, Saber, etc.)
- ✅ Best prices automatically
- ✅ Fast API (< 200ms)
- ✅ Free tier: Unlimited requests

**API:**
- Endpoint: `https://quote-api.jup.ag/v6`
- No API key required
- Rate limits: Very generous

### 2. Raydium
**Program ID:** `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`

**Status:** Supported (via Jupiter aggregation)

### 3. Orca
**Program ID:** `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc`

**Status:** Supported (via Jupiter aggregation)

---

## Gas Fees on Solana

### How Solana Fees Work

Solana doesn't use "gas" like Ethereum. Instead:
- **Compute Units**: Measure of computational work
- **Priority Fees**: Optional fees to prioritize transactions
- **Rent**: Account storage (usually refundable)

**Base transaction fee:** ~5,000 lamports = 0.000005 SOL ≈ $0.0005

### Typical Costs

| Operation | Compute Units | Cost (SOL) | Cost (USD @ $100) |
|-----------|---------------|------------|-------------------|
| Simple swap | ~350k | 0.00005 | $0.005 |
| Jupiter swap | ~400k | 0.00006 | $0.006 |
| Triangular (3 swaps) | ~1.2M | 0.00018 | $0.018 |
| Multi-DEX triangular | ~1.5M | 0.00022 | $0.022 |

**Note:** Solana fees are ~1000x cheaper than Ethereum!

### Priority Fees

During network congestion, you can pay priority fees:
- Low: +0.000001 SOL per CU
- Medium: +0.000005 SOL per CU
- High: +0.00001 SOL per CU

**For arbitrage:** Always use Medium-High priority to ensure execution.

---

## Token Addresses (Solana Mints)

All Solana tokens have a "mint address":

```python
SOL_TOKEN_ADDRESSES = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'RAY': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',
    'ORCA': 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
    'BTC': '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',
    'ETH': '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
}
```

---

## Trading Pairs on Solana

Common pairs available:

```python
DEX_PAIRS = {
    'solana': [
        'SOL/USDC', 'SOL/USDT',
        'RAY/SOL', 'RAY/USDC',
        'ORCA/SOL', 'ORCA/USDC',
        'BTC/SOL', 'BTC/USDC',
        'ETH/SOL', 'ETH/USDC',
        'BONK/SOL', 'BONK/USDC',
    ]
}
```

---

## API Endpoints

### Check Gas Fees (Solana)

```bash
GET /gas-fees
```

**Response:**
```json
{
  "solana": {
    "gas_prices": {
      "fast": 0.000001,
      "standard": 0.0000005,
      "slow": 0.0000001
    },
    "native_price_usd": 100,
    "estimated_swap_cost_usd": 0.006
  }
}
```

### Estimate Gas for Solana Trade

```bash
GET /gas-fees/estimate?chain=solana&arbitrage_type=triangular&trade_amount_usd=1000
```

**Response:**
```json
{
  "chain": "solana",
  "arbitrage_type": "triangular",
  "gas_estimate": {
    "gas_cost_usd": 0.018,
    "total_compute_units": 1200000,
    "native_token_cost": 0.00018,
    "native_token": "SOL"
  },
  "minimum_profitable_amount_usd": 3.6
}
```

### Cross-Exchange Arbitrage (CEX-SOL)

```bash
GET /arbitrage/cross-exchange?min_profit_percent=0.3
```

**Example Response:**
```json
{
  "opportunities": [
    {
      "type": "cross_exchange",
      "sub_type": "cex_to_dex",
      "symbol": "SOL/USDT",
      "buy_exchange": "binance",
      "sell_exchange": "jupiter",
      "buy_price": 99.50,
      "sell_price": 100.25,
      "gross_profit_percent": 0.75,
      "gas_cost_usd": 0.006,
      "net_profit_percent": 0.74,
      "net_profit_usd": 7.40,
      "chain": "solana",
      "involves_dex": true
    }
  ]
}
```

### Triangular on Solana DEXs

```bash
GET /arbitrage/triangular?exchange=jupiter&min_profit_percent=0.3
```

**Example Response:**
```json
{
  "type": "intra_exchange_triangular",
  "exchange_type": "dex",
  "exchange": "jupiter",
  "chain": "solana",
  "start_currency": "USDC",
  "path": ["SOL/USDC", "RAY/SOL", "RAY/USDC"],
  "gross_profit_percent": 0.85,
  "gas_cost_usd": 0.018,
  "net_profit_percent": 0.83,
  "net_profit_usd": 8.30
}
```

### Multi-DEX on Solana

```bash
GET /arbitrage/multi-dex-triangular?chain=solana&min_profit_percent=0.5
```

This finds triangular arbitrage using multiple DEXs via Jupiter's routing.

---

## Profitability Analysis

### Why Solana is Great for Arbitrage

**Ultra-Low Fees:**
- Ethereum: $10-50 per arbitrage
- BSC: $1-5 per arbitrage  
- **Solana: $0.005-0.025 per arbitrage** ✅

**Minimum Profitable Trades:**

| Arbitrage Type | Gas Cost | Min Trade @ 0.5% | Min Trade @ 0.3% |
|----------------|----------|------------------|------------------|
| Simple | $0.006 | $1.20 | $2.00 |
| Triangular | $0.018 | $3.60 | $6.00 |
| Multi-DEX | $0.022 | $4.40 | $7.33 |

**Conclusion:** You can profitably arbitrage with as little as $2-10 on Solana!

### Speed Comparison

| Chain | Block Time | Finality | Best For |
|-------|-----------|----------|----------|
| Ethereum | ~12s | ~15min | Large trades |
| BSC | ~3s | ~15s | Medium trades |
| **Solana** | ~0.4s | ~1s | **Fast arbitrage** ✅ |

Solana's 400ms block time means near-instant execution!

---

## Example: Complete Solana Arbitrage

### Scenario
Find arbitrage between Binance (CEX) and Jupiter (Solana DEX)

```python
import requests

# 1. Check current gas fees
gas = requests.get('http://localhost:8000/gas-fees').json()
sol_gas = gas['gas_data']['solana']['estimated_swap_cost_usd']
print(f"Solana gas cost: ${sol_gas}")
# Output: Solana gas cost: $0.006

# 2. Find opportunities
opps = requests.get(
    'http://localhost:8000/arbitrage/cross-exchange?min_profit_percent=0.3'
).json()

# 3. Filter for Solana DEX opportunities
sol_opps = [
    opp for opp in opps['opportunities']
    if opp.get('chain') == 'solana'
]

# 4. Check best opportunity
if sol_opps:
    best = sol_opps[0]
    print(f"Buy SOL on {best['buy_exchange']} @ ${best['buy_price']}")
    print(f"Sell on {best['sell_exchange']} @ ${best['sell_price']}")
    print(f"Net profit: {best['net_profit_percent']}% after gas")
    print(f"Net profit USD: ${best['net_profit_usd']}")
```

**Output:**
```
Solana gas cost: $0.006
Buy SOL on binance @ $99.50
Sell on jupiter @ $100.25
Net profit: 0.74% after gas
Net profit USD: $7.40
```

---

## Integration Details

### File Structure

```
arbitrage-api/
├── solana_dex_fetcher.py    # NEW: Solana DEX price fetcher
├── gas_estimator.py          # UPDATED: Added Solana compute units
├── config.py                 # UPDATED: Solana DEX configs + token mints
├── arbitrage_detector.py     # UPDATED: Solana chain support
├── exchange_manager.py       # UPDATED: Integrates Solana DEXs
└── requirements.txt          # UPDATED: Added solana==0.30.2
```

### Key Components

**1. Jupiter API Integration** (`solana_dex_fetcher.py`)
```python
class SolanaDexFetcher:
    async def fetch_jupiter_price(input_mint, output_mint, amount):
        # Fetches best price from Jupiter aggregator
        # Aggregates all Solana DEXs automatically
```

**2. Compute Unit Calculation** (`gas_estimator.py`)
```python
'solana': {
    'swap': 350000,  # Compute units for swap
    'swap_jupiter': 400000,  # Jupiter aggregator
    'approval': 0,  # No approval needed
}
```

**3. Solana Token Mints** (`config.py`)
```python
SOL_TOKEN_ADDRESSES = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    # ... more tokens
}
```

---

## Jupiter API Details

### Advantages
- ✅ **Free**: No API key, no rate limits
- ✅ **Fast**: ~100-200ms response
- ✅ **Best prices**: Aggregates ALL Solana DEXs
- ✅ **Smart routing**: Finds optimal multi-hop paths

### How It Works

1. **Quote Request:**
```javascript
GET https://quote-api.jup.ag/v6/quote?inputMint=SOL&outputMint=USDC&amount=1000000000
```

2. **Response:**
```json
{
  "inputMint": "So11...",
  "outputMint": "EPjF...",
  "inAmount": "1000000000",
  "outAmount": "100250000",
  "priceImpactPct": 0.05,
  "routePlan": [...]
}
```

3. **Price Calculation:**
```python
price = outAmount / inAmount
# 100.25 USDC per 1 SOL
```

### Rate Limits

**Official limits:** None stated

**Recommended:** 
- Max 10 requests/second
- Use caching for frequently queried pairs

---

## Best Practices for Solana

### 1. Use Jupiter for All Solana DEX Queries
Jupiter aggregates all DEXs, so you always get the best price.

### 2. Smaller Trade Sizes are Viable
With fees < $0.02, you can profit on $5-20 trades!

### 3. Speed Matters
Solana is FAST (400ms blocks). Execute quickly.

### 4. Priority Fees for Arbitrage
Always use Medium-High priority fees to ensure transactions land.

### 5. Monitor Compute Units
If transactions fail, you might be hitting compute limits. Optimize or split trades.

---

## Troubleshooting

### Issue: "Jupiter API timeout"
**Solution:** 
- Jupiter might be under load
- Retry with backoff
- Check https://status.jup.ag

### Issue: "Token mint not found"
**Solution:**
- Verify token address in `config.py`
- Check token exists on Solana
- Use Solana Explorer to verify

### Issue: "Compute budget exceeded"
**Solution:**
- Transaction is too complex
- Reduce number of hops
- Split into multiple transactions

### Issue: "Transaction failed"
**Solution:**
- Price changed (slippage)
- Increase slippage tolerance
- Use faster execution

---

## Comparison: Ethereum vs BSC vs Solana

| Feature | Ethereum | BSC | Solana |
|---------|----------|-----|--------|
| **Block Time** | 12s | 3s | **0.4s** ✅ |
| **Gas Cost** | $10-50 | $1-5 | **$0.005-0.025** ✅ |
| **Min Profitable Trade** | $2,000+ | $200+ | **$2-10** ✅ |
| **Finality** | ~15min | ~15s | **~1s** ✅ |
| **DEX Liquidity** | Very High | High | Medium-High |
| **Best For** | Large trades | Medium trades | **Small, fast arbitrage** ✅ |

---

## Summary

**Solana support adds:**
- ✅ 3 new DEXs (Jupiter, Raydium, Orca)
- ✅ ~1000x cheaper fees than Ethereum
- ✅ 30x faster execution than Ethereum
- ✅ Viable arbitrage on trades as small as $2
- ✅ Full gas fee calculations
- ✅ All 3 arbitrage types supported

**Get started:**
```bash
# Run the API
python main.py

# Check Solana opportunities
curl "http://localhost:8000/arbitrage/cross-exchange?min_profit_percent=0.3"

# Filter for Solana in response
grep -A 10 "solana"
```

**Solana makes arbitrage accessible to everyone!** 🚀
