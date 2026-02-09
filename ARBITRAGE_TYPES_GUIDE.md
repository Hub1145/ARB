# Arbitrage Types & Gas Fees Guide

## Three Types of Arbitrage

This API detects **three distinct types** of arbitrage opportunities, each with different characteristics and profitability considerations.

---

## 1. Cross-Exchange Arbitrage

**Definition:** Buy on one exchange, sell on another exchange.

**Endpoint:** `GET /arbitrage/cross-exchange`

### Variants

#### CEX-to-CEX
Buy on one centralized exchange, sell on another.

**Example:**
```
Buy BTC on Binance @ $43,500
Sell BTC on Bybit @ $43,750
Gross Profit: 0.57%
```

**Considerations:**
- ✅ No gas fees
- ✅ Fast execution
- ⚠️ Withdrawal fees between exchanges
- ⚠️ Transfer time (can take minutes to hours)
- ⚠️ Requires balances on both exchanges

#### DEX-to-DEX (Same Chain)
Buy on one DEX, sell on another DEX on the **same blockchain**.

**Example:**
```
Buy WETH/USDT on Uniswap @ $2,500
Sell WETH/USDT on SushiSwap @ $2,515
Gross Profit: 0.6%
Gas Cost: $15
Net Profit: $45 (on $10k trade)
```

**Considerations:**
- ⚠️ **Gas fees apply** - deducted from profit
- ✅ Instant execution (same transaction possible)
- ✅ No withdrawal/deposit needed
- ⚠️ Requires enough profit to cover 2 swaps worth of gas

#### CEX-to-DEX (Cross-Platform)
Buy on CEX, sell on DEX or vice versa.

**Example:**
```
Buy WBTC on Binance @ $43,500
Sell WBTC on Uniswap @ $43,750
```

**Considerations:**
- ⚠️ Gas fees for DEX side
- ⚠️ Withdrawal from CEX to blockchain
- ⚠️ Time delay for transfers
- ⚠️ More complex execution

### Response Example
```json
{
  "type": "cross_exchange",
  "sub_type": "cex_to_cex",
  "symbol": "BTC/USDT",
  "buy_exchange": "binance",
  "sell_exchange": "bybit",
  "buy_price": 43500,
  "sell_price": 43750,
  "profit_percent": 0.47,
  "involves_dex": false
}
```

With DEX:
```json
{
  "type": "cross_exchange",
  "sub_type": "dex_to_dex",
  "symbol": "WETH/USDT",
  "buy_exchange": "uniswap_v2",
  "sell_exchange": "sushiswap",
  "gross_profit_percent": 0.75,
  "gas_cost_usd": 18.50,
  "net_profit_percent": 0.57,
  "trade_amount_usd": 10000,
  "net_profit_usd": 57.00,
  "chain": "ethereum",
  "involves_dex": true
}
```

---

## 2. Intra-Exchange Triangular Arbitrage

**Definition:** Execute a cycle of 3 trades within a **SINGLE exchange** to profit from price discrepancies.

**Endpoint:** `GET /arbitrage/triangular`

### How It Works

Start and end with the same currency by trading through 2 intermediate currencies.

**CEX Example (Binance):**
```
Start: 1000 USDT
1. Buy BTC with USDT  → 0.0229 BTC
2. Buy ETH with BTC   → 0.444 ETH
3. Sell ETH for USDT  → 1007.50 USDT
Profit: 7.50 USDT (0.75%)
```

**DEX Example (Uniswap):**
```
Start: 1000 USDT
1. Buy WETH with USDT → 0.4 WETH
2. Buy WBTC with WETH → 0.0092 WBTC
3. Sell WBTC for USDT → 1015 USDT
Gross Profit: 1.5%
Gas Cost: $25 (for 3 swaps)
Net Profit: $15 - $25 = -$10 (NOT PROFITABLE!)
```

### Gas Fee Impact on DEX

Triangular arbitrage on DEX requires **3 swap transactions**:
- Higher gas costs than simple arbitrage
- Typical cost: $20-50 on Ethereum, $2-5 on BSC
- Need higher profit % to be viable

**Profitability Threshold:**

| Chain | Typical Gas Cost | Min Profitable Trade |
|-------|-----------------|---------------------|
| Ethereum | $30 (3 swaps) | ~$6,000 @ 0.5% profit |
| BSC | $3 (3 swaps) | ~$600 @ 0.5% profit |

### Response Example

CEX:
```json
{
  "type": "intra_exchange_triangular",
  "exchange_type": "cex",
  "exchange": "binance",
  "start_currency": "USDT",
  "path": ["BTC/USDT", "ETH/BTC", "ETH/USDT"],
  "start_amount": 1000,
  "end_amount": 1007.50,
  "profit_percent": 0.75
}
```

DEX:
```json
{
  "type": "intra_exchange_triangular",
  "exchange_type": "dex",
  "exchange": "uniswap_v2",
  "chain": "ethereum",
  "start_currency": "USDT",
  "path": ["WETH/USDT", "WBTC/WETH", "WBTC/USDT"],
  "gross_profit_percent": 1.5,
  "gas_cost_usd": 25.00,
  "net_profit_percent": 1.25,
  "trade_amount_usd": 10000,
  "net_profit_usd": 125.00
}
```

---

## 3. Multi-DEX Triangular Arbitrage

**Definition:** Triangular arbitrage using **multiple DEXs** on the **SAME blockchain**.

**Endpoint:** `GET /arbitrage/multi-dex-triangular?chain=ethereum`

### How It Works

Similar to regular triangular, but spread across different DEXs on one chain.

**Example (Ethereum):**
```
Start: 1000 USDT
1. Buy WETH/USDT on Uniswap   → 0.4 WETH
2. Buy WBTC/WETH on SushiSwap → 0.0092 WBTC
3. Sell WBTC/USDT on Uniswap  → 1020 USDT
Gross Profit: 2.0%
Gas Cost: $35 (higher - 3 different contracts)
Net Profit: $200 - $35 = $165 (1.65%)
```

### Why Multi-DEX?

Each DEX has different liquidity pools and prices. Sometimes the best path involves multiple DEXs:
- Uniswap might have best WETH/USDT price
- SushiSwap might have best WETH/WBTC price
- Better overall profit despite higher gas

### Higher Gas Costs

Multi-DEX arbitrage costs **MORE gas** because:
- Each DEX is a different smart contract
- May require multiple token approvals
- Typically 20-30% higher than single-DEX triangular

**Cost Comparison:**

| Type | Gas Cost (ETH) | Gas Cost (BSC) |
|------|----------------|----------------|
| Single DEX Triangular | ~$25 | ~$2.50 |
| Multi-DEX Triangular | ~$35 | ~$3.50 |

### When It's Worth It

Multi-DEX is profitable when:
- Price differences between DEXs are large
- Single DEX doesn't have all needed pairs
- Liquidity is better spread across DEXs

### Response Example

```json
{
  "type": "multi_dex_triangular",
  "chain": "ethereum",
  "start_currency": "USDT",
  "dexs_used": ["uniswap_v2", "sushiswap"],
  "num_dexs": 2,
  "path": [
    "uniswap_v2:WETH/USDT",
    "sushiswap:WBTC/WETH",
    "uniswap_v2:WBTC/USDT"
  ],
  "gross_profit_percent": 2.0,
  "gas_cost_usd": 35.00,
  "net_profit_percent": 1.65,
  "trade_amount_usd": 10000,
  "net_profit_usd": 165.00
}
```

---

## Gas Fee Calculations

### How Gas Fees Are Calculated

For all DEX operations, the API automatically:

1. **Fetches current gas prices** from the blockchain
2. **Estimates gas units** needed for the operation
3. **Converts to USD** using current ETH/BNB prices
4. **Deducts from gross profit** to show net profit

### Gas Price Tiers

```
Fast:     Higher gas, faster confirmation (~15 sec)
Standard: Normal gas, typical confirmation (~30 sec)
Slow:     Lower gas, slower confirmation (~1-2 min)
```

The API uses **Fast** by default for arbitrage calculations since speed matters.

### Gas Unit Estimates

| Operation | ETH Gas Units | BSC Gas Units |
|-----------|--------------|---------------|
| Single Swap | 150,000 | 120,000 |
| Token Approval | 46,000 | 46,000 |
| Triangular (3 swaps) | 450,000 | 360,000 |
| Multi-DEX (3 swaps) | 540,000 | 432,000 |

### Real-Time Gas Costs

Check current gas prices:

```bash
GET /gas-fees
```

Response:
```json
{
  "ethereum": {
    "gas_prices": {
      "fast": 45,
      "standard": 30,
      "slow": 20
    },
    "native_price_usd": 2500,
    "estimated_swap_cost_usd": 11.25
  },
  "bsc": {
    "gas_prices": {
      "fast": 5,
      "standard": 3,
      "slow": 2
    },
    "native_price_usd": 300,
    "estimated_swap_cost_usd": 1.08
  }
}
```

### Estimate Gas for Your Trade

```bash
GET /gas-fees/estimate?chain=ethereum&arbitrage_type=triangular&trade_amount_usd=5000
```

Response:
```json
{
  "chain": "ethereum",
  "arbitrage_type": "triangular",
  "speed": "standard",
  "gas_estimate": {
    "gas_cost_usd": 33.75,
    "gas_price_gwei": 30,
    "total_gas_units": 450000,
    "native_token_cost": 0.0135,
    "native_token": "ETH"
  },
  "minimum_profitable_amount_usd": 6750
}
```

---

## Profitability Analysis

### Minimum Trade Amounts

To be profitable, your trade must generate enough profit to cover gas:

**Formula:**
```
min_trade_amount = (gas_cost_usd * 100) / profit_percent
```

**Examples:**

| Gas Cost | Profit % | Min Trade Amount |
|----------|----------|------------------|
| $10 | 0.5% | $2,000 |
| $25 | 0.5% | $5,000 |
| $50 | 1.0% | $5,000 |

### Profitability by Chain

**Ethereum:**
- Higher gas costs ($10-50 per arbitrage)
- Need larger trades ($5k-20k)
- Best for high-value opportunities (>1% profit)

**BSC:**
- Lower gas costs ($1-5 per arbitrage)
- Viable for smaller trades ($500-2k)
- Can profit on smaller opportunities (>0.3%)

### When to Execute

An opportunity is worth executing when:

```
Net Profit (after gas) > 0
AND
Net Profit % > Your minimum threshold
AND
Trade Amount > Minimum profitable amount
```

The API automatically filters opportunities to show only profitable ones after gas.

---

## API Usage Examples

### 1. Find CEX Arbitrage (No Gas Fees)

```bash
curl "http://localhost:8000/arbitrage/cross-exchange?min_profit_percent=0.3"
```

Shows opportunities between Binance, Bybit, OKX, KuCoin, Phemex.

### 2. Find DEX Arbitrage (With Gas Fees)

```bash
curl "http://localhost:8000/arbitrage/cross-exchange?min_profit_percent=0.5"
```

Includes DEX-DEX and CEX-DEX opportunities. Profit shown is **after gas fees**.

### 3. Find Triangular on Specific Exchange

```bash
# CEX
curl "http://localhost:8000/arbitrage/triangular?exchange=binance&min_profit_percent=0.5"

# DEX
curl "http://localhost:8000/arbitrage/triangular?exchange=uniswap_v2&min_profit_percent=0.8"
```

### 4. Find Multi-DEX Opportunities

```bash
# Ethereum
curl "http://localhost:8000/arbitrage/multi-dex-triangular?chain=ethereum&min_profit_percent=1.0"

# BSC
curl "http://localhost:8000/arbitrage/multi-dex-triangular?chain=bsc&min_profit_percent=0.5"
```

### 5. Check Current Gas Prices

```bash
curl "http://localhost:8000/gas-fees"
```

### 6. Estimate Gas for Your Trade

```bash
curl "http://localhost:8000/gas-fees/estimate?chain=ethereum&arbitrage_type=triangular&trade_amount_usd=10000&speed=fast"
```

---

## Best Practices

### For CEX Arbitrage
1. Monitor withdrawal/deposit fees
2. Consider transfer times
3. Maintain balances on multiple exchanges
4. Watch for maintenance windows

### For DEX Arbitrage
1. **Always check gas fees first**
2. Use larger trade amounts on Ethereum (>$5k)
3. BSC is better for smaller trades ($500-5k)
4. Monitor gas prices - execute during low gas periods
5. Consider MEV protection for large trades

### For Triangular Arbitrage
1. Higher profit threshold needed (>0.8% on ETH)
2. Best during high volatility
3. Monitor liquidity on all pairs in the path
4. CEX triangular is usually more profitable than DEX

### For Multi-DEX
1. Highest gas costs - need strong opportunities (>1.5%)
2. Best when price discrepancies are large
3. Check liquidity on each DEX
4. More complex execution - higher risk

---

## Common Questions

**Q: Why does the API show negative profit on some DEX opportunities?**

A: Gas fees exceeded the gross profit. The API shows these to demonstrate that the opportunity exists but isn't profitable after gas.

**Q: How often are gas prices updated?**

A: Real-time. Each arbitrage calculation fetches current gas prices from the blockchain or gas oracles.

**Q: Can I use lower gas prices to save money?**

A: Yes, but slower confirmation means higher risk of the opportunity disappearing. For arbitrage, "fast" is recommended.

**Q: Why is BSC cheaper?**

A: BSC has faster block times and lower validator costs, resulting in much lower gas fees (typically 10-20x cheaper than Ethereum).

**Q: What if gas prices spike during execution?**

A: Always add a buffer to your calculations. Gas can spike 2-3x during high network congestion.

---

## Advanced: Simulating Profitability

Check if an opportunity is worth it:

```python
import requests

# Get opportunity
opp = requests.get('http://localhost:8000/arbitrage/cross-exchange').json()
opportunity = opp['opportunities'][0]

if opportunity.get('involves_dex'):
    # DEX - profit already includes gas
    net_profit = opportunity['net_profit_usd']
    is_profitable = net_profit > 0
else:
    # CEX - add your withdrawal fees
    gross_profit = opportunity['profit_percent'] * trade_amount / 100
    withdrawal_fee = 20  # Your actual fee
    net_profit = gross_profit - withdrawal_fee
    is_profitable = net_profit > 0

print(f"Profitable: {is_profitable}, Net: ${net_profit}")
```

---

## Summary

| Arbitrage Type | Exchanges | Gas Fees | Best For |
|----------------|-----------|----------|----------|
| **Cross-Exchange** | Different | Only if DEX involved | Quick wins, CEX-CEX easiest |
| **Intra-Exchange Triangular** | Single | Yes (if DEX) | High volatility periods |
| **Multi-DEX Triangular** | Multiple DEXs, same chain | Yes (highest) | Large price discrepancies |

**Key Takeaway:** For DEX arbitrage, gas fees are **critical**. The API automatically calculates and deducts them to show real, actionable opportunities.
