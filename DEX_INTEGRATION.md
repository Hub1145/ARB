# DEX Integration Guide - ETH & BNB Networks

This guide explains how the API fetches prices from DEXs on Ethereum and Binance Smart Chain.

## Overview

The API uses **two methods** to fetch DEX prices:

1. **The Graph Protocol** - For Uniswap, SushiSwap, PancakeSwap (faster, more reliable)
2. **Direct On-Chain Queries** - Fallback method for DEXs without Graph support

## Supported DEXs

### Ethereum Network
- ✅ **Uniswap V2** - Via The Graph
- ✅ **Uniswap V3** - Via The Graph  
- ✅ **SushiSwap** - Via The Graph

### Binance Smart Chain (BSC)
- ✅ **PancakeSwap V2** - Via The Graph
- ✅ **PancakeSwap V3** - Via The Graph
- ✅ **Biswap** - Via direct on-chain queries

## The Graph Protocol

### What is The Graph?
The Graph is an indexing protocol for querying blockchain data. It's much faster than direct RPC calls and provides structured data.

### Free Tier Limits
- **100,000 queries per month** (free)
- No API key required for public subgraphs
- Rate limit: ~1,000 queries per day
- Perfect for testing and small-scale production

### Upgrade Options
If you need more than 100k queries/month:
1. Create a free account at https://thegraph.com/studio/
2. Generate an API key
3. Update the Graph URLs in `config.py`:
```python
'graph_url': 'https://gateway.thegraph.com/api/[YOUR-API-KEY]/subgraphs/id/...'
```

**Paid tiers start at $10/month** for unlimited queries.

## RPC Providers

### Current Setup (Public RPCs)
The API uses **free public RPC endpoints**:

**Ethereum:**
- `https://eth.public-rpc.com`
- No registration needed
- Rate limits: ~100 requests/minute

**BSC:**
- `https://bsc-dataseed1.binance.org`
- Official Binance endpoint
- Rate limits: Variable, usually sufficient

### When to Upgrade RPC Providers

Upgrade to paid RPC if you experience:
- ❌ Rate limit errors
- ❌ Slow response times
- ❌ Connection timeouts
- ❌ Need for production reliability

### Recommended RPC Providers (Free Tiers)

#### 1. Alchemy (Recommended)
**Free Tier:**
- 300M compute units/month
- ~100k requests/month equivalent
- WebSocket support
- Dashboard analytics

**Setup:**
```bash
# Sign up: https://alchemy.com
# Get API key
# Update config.py:
'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY'
```

**Paid Plans:** Start at $49/month for 5B compute units

#### 2. Infura
**Free Tier:**
- 100,000 requests/day
- 3M requests/month
- WebSocket support
- Very reliable

**Setup:**
```bash
# Sign up: https://infura.io
# Create project, get API key
# Update config.py:
'rpc_url': 'https://mainnet.infura.io/v3/YOUR_KEY'
```

**Paid Plans:** Start at $50/month for 100M requests

#### 3. QuickNode
**Free Tier:**
- Limited requests (check current limits)
- Single endpoint
- Good for testing

**Setup:**
```bash
# Sign up: https://quicknode.com
# Create endpoint
# Update config.py with your endpoint URL
```

**Paid Plans:** Start at $9/month

## Configuration

### Using Environment Variables (Recommended)

1. Copy `.env.example` to `.env`
2. Add your keys:
```bash
# For Alchemy
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BSC_RPC_URL=https://bsc-mainnet.g.alchemy.com/v2/YOUR_KEY

# For Infura
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
```

3. Update `config.py` to read from environment:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DEX_CONFIGS = {
    'uniswap_v2': {
        'rpc_url': os.getenv('ETH_RPC_URL', 'https://eth.public-rpc.com'),
        # ... rest of config
    }
}
```

## Rate Limit Management

### Current Approach
The API caches DEX prices to minimize RPC calls:
- Prices refreshed every 1-2 seconds
- The Graph queries batched efficiently
- On-chain queries only for non-Graph DEXs

### Optimization Tips

1. **Use The Graph when possible** - Much higher limits than RPC
2. **Batch queries** - Already implemented in `dex_fetcher.py`
3. **Cache aggressively** - Implemented in `exchange_manager.py`
4. **Filter pairs** - Only monitor high-liquidity pairs in `config.py`

### Monitoring Rate Limits

Add to your code:
```python
# In dex_fetcher.py, add response header checking
headers = response.headers
remaining = headers.get('X-RateLimit-Remaining', 'unknown')
print(f"Rate limit remaining: {remaining}")
```

## Data Quality

### The Graph Advantages
- ✅ Indexed, structured data
- ✅ Fast queries (< 100ms)
- ✅ Historical data available
- ✅ 24h volume, liquidity metrics
- ✅ No blockchain parsing needed

### Direct RPC Advantages
- ✅ Always up-to-date (block-level)
- ✅ Works for any DEX
- ✅ No dependency on indexers
- ❌ Slower (1-2 seconds per query)
- ❌ Requires contract ABIs

## Token Addresses

### Adding New Tokens

Edit `config.py`:

```python
ETH_TOKEN_ADDRESSES = {
    'NEW_TOKEN': '0x...address...',
}

DEX_PAIRS = {
    'ethereum': [
        'NEW_TOKEN/WETH',
        'NEW_TOKEN/USDT',
    ]
}
```

### Finding Token Addresses

1. **Etherscan:** https://etherscan.io
2. **BSCscan:** https://bscscan.com
3. **CoinGecko:** Has contract addresses for most tokens

## Production Checklist

Before deploying to production:

- [ ] Upgrade to paid RPC provider (Alchemy/Infura)
- [ ] Get The Graph API key if >100k queries/month
- [ ] Monitor rate limit usage
- [ ] Implement retry logic for failed queries
- [ ] Add alerting for API errors
- [ ] Use environment variables for all keys
- [ ] Enable HTTPS/WSS for API
- [ ] Set up Redis for better caching
- [ ] Monitor DEX liquidity before trading

## Troubleshooting

### Issue: "Failed to connect to RPC"
**Solutions:**
1. Check if public RPC is down (try in browser)
2. Upgrade to Alchemy/Infura
3. Try alternative public endpoints

### Issue: "The Graph query failed"
**Solutions:**
1. Check subgraph status: https://thegraph.com/hosted-service
2. Verify subgraph URL is correct
3. Use direct on-chain queries as fallback

### Issue: "Rate limit exceeded"
**Solutions:**
1. Reduce query frequency
2. Upgrade RPC provider plan
3. Implement request queuing
4. Cache more aggressively

### Issue: "Price data is stale"
**Solutions:**
1. Reduce cache TTL
2. Use WebSocket connections (Alchemy/Infura)
3. Check if DEX has liquidity

## Cost Estimation

### Free Tier (Current Setup)
- The Graph: 100k queries/month
- Public RPC: ~100k requests/month
- **Total Cost: $0**
- **Suitable for:** Testing, small bots (<1000 users)

### Low Volume Production
- The Graph: Free tier (100k)
- Alchemy: Free tier (300M CU)
- **Total Cost: $0**
- **Suitable for:** Small production (<5000 requests/day)

### Medium Volume
- The Graph: Paid ($10/month)
- Alchemy: Growth ($49/month)
- **Total Cost: ~$60/month**
- **Suitable for:** Medium bots (50k-500k requests/day)

### High Volume
- The Graph: Enterprise (custom)
- Alchemy: Scale ($199+/month)
- **Total Cost: $200+/month**
- **Suitable for:** Large trading operations (1M+ requests/day)

## Additional Resources

- **The Graph Docs:** https://thegraph.com/docs/
- **Alchemy Docs:** https://docs.alchemy.com/
- **Infura Docs:** https://docs.infura.io/
- **Uniswap Subgraph:** https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2
- **Web3.py Docs:** https://web3py.readthedocs.io/

## Support

For issues with:
- **The Graph:** https://discord.gg/graphprotocol
- **Alchemy:** https://docs.alchemy.com/reference/
- **RPC errors:** Check provider status pages
