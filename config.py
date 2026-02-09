"""
Configuration settings for the arbitrage API
Loads from config.json
"""
import json
import os

# Load config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # Default empty config if file doesn't exist (should not happen in production)
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

_config = load_config()

# Alchemy API Keys for rotation
ALCHEMY_KEYS = _config.get('ALCHEMY_KEYS', [])

# Centralized exchanges to monitor
CEX_EXCHANGES = _config.get('CEX_EXCHANGES', [
    'binance',
    'kucoin',
    'bybit',
    'okx',
    'phemex',
])

# Decentralized exchange configurations
# Note: RPC URLs will be constructed dynamically using Alchemy keys
DEX_CONFIGS = {
    # Ethereum DEXs
    'uniswap_v2': {
        'chain': 'ethereum',
        'router_address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'factory_address': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
        'protocol': 'uniswap_v2'
    },
    'uniswap_v3': {
        'chain': 'ethereum',
        'router_address': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984', # Simplified for V3
        'factory_address': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
        'protocol': 'uniswap_v3'
    },
    'sushiswap_eth': {
        'chain': 'ethereum',
        'router_address': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
        'factory_address': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange',
        'protocol': 'uniswap_v2'
    },
    
    # BSC DEXs
    'pancakeswap_v2': {
        'chain': 'bsc',
        'router_address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        'factory_address': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v2',
        'protocol': 'uniswap_v2'
    },
    'pancakeswap_v3': {
        'chain': 'bsc',
        'router_address': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4',
        'factory_address': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
        'graph_url': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-bsc',
        'protocol': 'uniswap_v3'
    },
    
    # Solana DEXs
    'jupiter': {
        'chain': 'solana',
        'api_url': 'https://quote-api.jup.ag/v6',
        'protocol': 'jupiter'
    }
}

# Common trading pairs to monitor
COMMON_PAIRS = _config.get('COMMON_PAIRS', [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'ETH/BTC',
])

# Token addresses for DEX trading
ETH_TOKEN_ADDRESSES = _config.get('ETH_TOKENS', {})
BSC_TOKEN_ADDRESSES = _config.get('BSC_TOKENS', {})
SOL_TOKEN_ADDRESSES = _config.get('SOL_TOKENS', {})

# DEX-specific pairs
DEX_PAIRS = _config.get('DEX_PAIRS', {})

# Trading parameters
TRADING_FEE_PERCENT = _config.get('TRADING_FEE_PERCENT', 0.1)
MIN_PROFIT_PERCENT = _config.get('MIN_PROFIT_PERCENT', 0.5)
SLIPPAGE_PERCENT = _config.get('SLIPPAGE_PERCENT', 0.2)

# Function to get Alchemy RPC URL for a chain with rotated keys
import random

def get_rpc_url(chain):
    if not ALCHEMY_KEYS:
        # Fallback to public RPCs if no keys provided
        fallbacks = {
            'ethereum': 'https://eth.public-rpc.com',
            'bsc': 'https://bsc-dataseed1.binance.org',
            'solana': 'https://api.mainnet-beta.solana.com'
        }
        return fallbacks.get(chain)

    key = random.choice(ALCHEMY_KEYS)

    if chain == 'ethereum':
        return f"https://eth-mainnet.g.alchemy.com/v2/{key}"
    elif chain == 'bsc':
        return f"https://bnb-mainnet.g.alchemy.com/v2/{key}"
    elif chain == 'solana':
        return f"https://solana-mainnet.g.alchemy.com/v2/{key}"

    return None
