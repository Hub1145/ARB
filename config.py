"""
Configuration settings for the arbitrage API
"""

# Centralized exchanges to monitor
CEX_EXCHANGES = [
    'binance',
    'kucoin',
    'bybit',
    'okx',
    'phemex',
]

# Decentralized exchange configurations (ETH, BNB, and Solana)
DEX_CONFIGS = {
    # Ethereum DEXs
    'uniswap_v2': {
        'chain': 'ethereum',
        'rpc_url': 'https://eth.public-rpc.com',
        'router_address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'factory_address': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
        'protocol': 'uniswap_v2'
    },
    'uniswap_v3': {
        'chain': 'ethereum',
        'rpc_url': 'https://eth.public-rpc.com',
        'router_address': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
        'factory_address': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
        'protocol': 'uniswap_v3'
    },
    'sushiswap_eth': {
        'chain': 'ethereum',
        'rpc_url': 'https://eth.public-rpc.com',
        'router_address': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
        'factory_address': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange',
        'protocol': 'uniswap_v2'
    },
    'curve_eth': {
        'chain': 'ethereum',
        'rpc_url': 'https://eth.public-rpc.com',
        'router_address': '0x99a58482BD75cbab83b27EC03CA68fF489b5788f',
        'factory_address': None,
        'graph_url': 'https://api.thegraph.com/subgraphs/name/curvefi/curve',
        'protocol': 'curve'
    },
    
    # BSC DEXs
    'pancakeswap_v2': {
        'chain': 'bsc',
        'rpc_url': 'https://bsc-dataseed1.binance.org',
        'router_address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        'factory_address': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v2',
        'protocol': 'uniswap_v2'
    },
    'pancakeswap_v3': {
        'chain': 'bsc',
        'rpc_url': 'https://bsc-dataseed1.binance.org',
        'router_address': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4',
        'factory_address': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-bsc',
        'protocol': 'uniswap_v3'
    },
    'bakeryswap': {
        'chain': 'bsc',
        'rpc_url': 'https://bsc-dataseed1.binance.org',
        'router_address': '0xCDe540d7eAFE93aC5fE6233Bee57E1270D3E330F',
        'factory_address': '0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7',
        'graph_url': None,
        'protocol': 'uniswap_v2'
    },
    'biswap': {
        'chain': 'bsc',
        'rpc_url': 'https://bsc-dataseed1.binance.org',
        'router_address': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
        'factory_address': '0x858E3312ed3A876947EA49d572A7C42DE08af7EE',
        'graph_url': None,
        'protocol': 'uniswap_v2'
    },
    'sushiswap_bsc': {
        'chain': 'bsc',
        'rpc_url': 'https://bsc-dataseed1.binance.org',
        'router_address': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
        'factory_address': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
        'graph_url': None,
        'protocol': 'uniswap_v2'
    },
    
    # Solana DEXs
    'jupiter': {
        'chain': 'solana',
        'rpc_url': 'https://api.mainnet-beta.solana.com',
        'api_url': 'https://quote-api.jup.ag/v6',  # Jupiter API v6
        'protocol': 'jupiter'
    },
    'orca': {
        'chain': 'solana',
        'rpc_url': 'https://api.mainnet-beta.solana.com',
        'program_id': 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc',  # Whirlpool program
        'protocol': 'orca'
    },
    'raydium': {
        'chain': 'solana',
        'rpc_url': 'https://api.mainnet-beta.solana.com',
        'program_id': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',  # Raydium AMM v4
        'protocol': 'raydium'
    },
}

# Common trading pairs to monitor
COMMON_PAIRS = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'SOL/USDT',
    'DOGE/USDT',
    'DOT/USDT',
    'MATIC/USDT',
    'AVAX/USDT',
    'ETH/BTC',
    'BNB/BTC',
    'SOL/BTC',
    'BTC/USD',
    'ETH/USD',
]

# Token addresses for DEX trading (Ethereum)
ETH_TOKEN_ADDRESSES = {
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
    'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    'AAVE': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
    'MATIC': '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0',
    'CRV': '0xD533a949740bb3306d119CC777fa900bA034cd52',
}

# Token addresses for DEX trading (BSC)
BSC_TOKEN_ADDRESSES = {
    'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
    'USDT': '0x55d398326f99059fF775485246999027B3197955',
    'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
    'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
    'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
    'CAKE': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
    'XRP': '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE',
    'ADA': '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47',
    'DOT': '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402',
    'BAKE': '0xE02dF9e3e622DeBdD69fb838bB799E3F168902c5',
}

# Token addresses for DEX trading (Solana) - Mint addresses
SOL_TOKEN_ADDRESSES = {
    'SOL': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'RAY': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',  # Raydium
    'ORCA': 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
    'SRM': 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt',  # Serum
    'MNGO': 'MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac',  # Mango
    'BTC': '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',  # Wrapped BTC
    'ETH': '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',  # Wrapped ETH
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
}

# DEX-specific pairs (for triangular arbitrage on DEXs)
DEX_PAIRS = {
    'ethereum': [
        'WETH/USDT', 'WETH/USDC', 'WETH/DAI',
        'WBTC/USDT', 'WBTC/USDC', 'WBTC/WETH',
        'UNI/WETH', 'LINK/WETH', 'AAVE/WETH',
        'MATIC/WETH', 'CRV/WETH',
    ],
    'bsc': [
        'WBNB/BUSD', 'WBNB/USDT', 'WBNB/USDC',
        'BTCB/BUSD', 'BTCB/USDT', 'BTCB/WBNB',
        'ETH/WBNB', 'CAKE/WBNB', 'ETH/BUSD',
        'BAKE/WBNB', 'BAKE/BUSD',
    ],
    'solana': [
        'SOL/USDC', 'SOL/USDT',
        'RAY/SOL', 'RAY/USDC',
        'ORCA/SOL', 'ORCA/USDC',
        'BTC/SOL', 'BTC/USDC',
        'ETH/SOL', 'ETH/USDC',
        'BONK/SOL', 'BONK/USDC',
    ]
}

# Trading parameters
TRADING_FEE_PERCENT = 0.1  # Average trading fee (0.1%)
MIN_PROFIT_PERCENT = 0.5   # Minimum profit threshold (0.5%)
SLIPPAGE_PERCENT = 0.2     # Expected slippage (0.2%)

# API Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# WebSocket settings
WS_HEARTBEAT_INTERVAL = 30  # seconds

# RPC Endpoints (using public RPCs - upgrade to paid for production)
# Free alternatives with good limits:
# - Alchemy: 300M compute units/month free (recommended)
# - Infura: 100,000 requests/day free
# - QuickNode: Free tier available
# To upgrade: Replace public RPCs in DEX_CONFIGS with your provider URL

# The Graph Protocol
# Free tier: 100,000 queries/month
# No API key required for public subgraphs
# For higher limits: https://thegraph.com/studio/

# Minimum volume thresholds (to avoid low liquidity pairs)
MIN_24H_VOLUME_USD = 100000  # $100k minimum 24h volume
