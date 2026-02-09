"""
DEX Price Fetcher - Get prices from Ethereum, BSC, and Solana DEXs
Uses The Graph Protocol and direct on-chain queries for EVM chains
Uses Jupiter API for Solana
"""
import aiohttp
from web3 import Web3
from typing import Dict, Optional, List
import json
from decimal import Decimal

from config import DEX_CONFIGS, ETH_TOKEN_ADDRESSES, BSC_TOKEN_ADDRESSES, DEX_PAIRS, get_rpc_url
from solana_dex_fetcher import SolanaDexFetcher

# Uniswap V2 Pair ABI (minimal for getReserves)
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Uniswap V2 Factory ABI (minimal for getPair)
FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]


class DexPriceFetcher:
    def __init__(self):
        self.web3_connections: Dict[str, Web3] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.solana_fetcher = SolanaDexFetcher()
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connections for ETH and BSC using Alchemy"""
        # Unique chains from config
        chains = list(set(config['chain'] for config in DEX_CONFIGS.values()))
        
        # Create Web3 instances
        for chain in chains:
            if chain == 'solana':
                continue # Solana handled by SolanaDexFetcher

            rpc_url = get_rpc_url(chain)
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    print(f"✓ Connected to {chain.upper()} RPC via Alchemy")
                else:
                    print(f"✗ Failed to connect to {chain.upper()} RPC via Alchemy")
            except Exception as e:
                print(f"✗ Error connecting to {chain}: {e}")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
        await self.solana_fetcher.close()
    
    async def fetch_dex_prices(self, dex_name: str, pairs: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch prices from a specific DEX
        Returns: {pair: {'price': float, 'liquidity': float}}
        """
        config = DEX_CONFIGS.get(dex_name)
        if not config:
            return {}
        
        chain = config['chain']
        
        # Handle Solana DEXs separately
        if chain == 'solana':
            return await self._fetch_from_solana(dex_name, config, pairs)
        
        # Use The Graph if available, otherwise on-chain for EVM chains
        if config.get('graph_url'):
            return await self._fetch_from_graph(dex_name, config, pairs)
        else:
            return await self._fetch_from_chain(dex_name, config, pairs)
    
    async def _fetch_from_solana(self, dex_name: str, config: Dict, pairs: Optional[List[str]]) -> Dict:
        """Fetch prices from Solana DEXs using Jupiter API"""
        # For Jupiter (aggregator), fetch all Solana pairs
        if dex_name == 'jupiter':
            if pairs is None:
                pairs = DEX_PAIRS.get('solana', [])
            
            return await self.solana_fetcher.fetch_all_jupiter_prices(pairs)
        
        # For other Solana DEXs, Jupiter aggregates them anyway
        # So we can use Jupiter as the source
        return {}
    
    async def _fetch_from_graph(self, dex_name: str, config: Dict, pairs: Optional[List[str]]) -> Dict:
        """Fetch prices using The Graph Protocol subgraph"""
        await self._ensure_session()
        
        graph_url = config['graph_url']
        chain = config['chain']
        
        # Get relevant pairs for this chain
        if pairs is None:
            pairs = DEX_PAIRS.get(chain, [])
        
        # Build GraphQL query
        query = self._build_graph_query(config['protocol'], pairs, chain)
        
        try:
            async with self.session.post(
                graph_url,
                json={'query': query},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_graph_response(data, config['protocol'], chain)
                else:
                    print(f"Graph query failed for {dex_name}: {response.status}")
                    return {}
        except Exception as e:
            print(f"Error fetching from The Graph ({dex_name}): {e}")
            return {}
    
    def _build_graph_query(self, protocol: str, pairs: List[str], chain: str) -> str:
        """Build GraphQL query based on protocol version"""
        if protocol == 'uniswap_v2':
            # Query for Uniswap V2 style DEXs
            return """
            {
              pairs(first: 100, orderBy: reserveUSD, orderDirection: desc) {
                id
                token0 {
                  symbol
                  id
                }
                token1 {
                  symbol
                  id
                }
                reserve0
                reserve1
                reserveUSD
                token0Price
                token1Price
                volumeUSD
              }
            }
            """
        elif protocol == 'uniswap_v3':
            # Query for Uniswap V3 style DEXs
            return """
            {
              pools(first: 100, orderBy: totalValueLockedUSD, orderDirection: desc) {
                id
                token0 {
                  symbol
                  id
                }
                token1 {
                  symbol
                  id
                }
                token0Price
                token1Price
                totalValueLockedUSD
                volumeUSD
              }
            }
            """
        return ""
    
    def _parse_graph_response(self, data: Dict, protocol: str, chain: str) -> Dict[str, Dict]:
        """Parse The Graph response into standard format"""
        prices = {}
        
        try:
            if protocol == 'uniswap_v2':
                pairs = data.get('data', {}).get('pairs', [])
                for pair in pairs:
                    token0 = pair['token0']['symbol']
                    token1 = pair['token1']['symbol']
                    pair_name = f"{token0}/{token1}"
                    
                    prices[pair_name] = {
                        'price': float(pair['token0Price']),
                        'inverse_price': float(pair['token1Price']),
                        'liquidity_usd': float(pair['reserveUSD']),
                        'volume_24h': float(pair.get('volumeUSD', 0)),
                        'reserve0': float(pair['reserve0']),
                        'reserve1': float(pair['reserve1']),
                    }
            
            elif protocol == 'uniswap_v3':
                pools = data.get('data', {}).get('pools', [])
                for pool in pools:
                    token0 = pool['token0']['symbol']
                    token1 = pool['token1']['symbol']
                    pair_name = f"{token0}/{token1}"
                    
                    prices[pair_name] = {
                        'price': float(pool['token0Price']),
                        'inverse_price': float(pool['token1Price']),
                        'liquidity_usd': float(pool['totalValueLockedUSD']),
                        'volume_24h': float(pool.get('volumeUSD', 0)),
                    }
        
        except Exception as e:
            print(f"Error parsing Graph response: {e}")
        
        return prices
    
    async def _fetch_from_chain(self, dex_name: str, config: Dict, pairs: Optional[List[str]]) -> Dict:
        """Fetch prices directly from blockchain"""
        chain = config['chain']
        w3 = self.web3_connections.get(chain)
        
        if not w3:
            return {}
        
        # Get token addresses for this chain
        token_addresses = ETH_TOKEN_ADDRESSES if chain == 'ethereum' else BSC_TOKEN_ADDRESSES
        
        # Get relevant pairs
        if pairs is None:
            pairs = DEX_PAIRS.get(chain, [])
        
        prices = {}
        factory_address = config['factory_address']
        factory_contract = w3.eth.contract(
            address=w3.to_checksum_address(factory_address),
            abi=FACTORY_ABI
        )
        
        for pair_str in pairs:
            try:
                # Parse pair string (e.g., "WETH/USDT")
                token0_symbol, token1_symbol = pair_str.split('/')
                
                # Get token addresses
                token0_addr = token_addresses.get(token0_symbol)
                token1_addr = token_addresses.get(token1_symbol)
                
                if not token0_addr or not token1_addr:
                    continue
                
                # Get pair address from factory
                pair_address = factory_contract.functions.getPair(
                    w3.to_checksum_address(token0_addr),
                    w3.to_checksum_address(token1_addr)
                ).call()
                
                if pair_address == '0x0000000000000000000000000000000000000000':
                    continue
                
                # Get pair contract
                pair_contract = w3.eth.contract(
                    address=w3.to_checksum_address(pair_address),
                    abi=PAIR_ABI
                )
                
                # Get reserves
                reserves = pair_contract.functions.getReserves().call()
                reserve0 = reserves[0]
                reserve1 = reserves[1]
                
                # Get token order (token0 vs token1)
                pair_token0 = pair_contract.functions.token0().call()
                
                # Calculate price
                if pair_token0.lower() == token0_addr.lower():
                    # token0 is the base
                    price = reserve1 / reserve0 if reserve0 > 0 else 0
                    inverse_price = reserve0 / reserve1 if reserve1 > 0 else 0
                else:
                    # token1 is the base
                    price = reserve0 / reserve1 if reserve1 > 0 else 0
                    inverse_price = reserve1 / reserve0 if reserve0 > 0 else 0
                
                prices[pair_str] = {
                    'price': price,
                    'inverse_price': inverse_price,
                    'reserve0': reserve0,
                    'reserve1': reserve1,
                    'pair_address': pair_address
                }
            
            except Exception as e:
                print(f"Error fetching {pair_str} from {dex_name}: {e}")
                continue
        
        return prices
    
    async def get_all_dex_prices(self) -> Dict[str, Dict]:
        """
        Get prices from all configured DEXs
        Returns: {dex_name: {pair: price_data}}
        """
        all_prices = {}
        
        for dex_name in DEX_CONFIGS.keys():
            prices = await self.fetch_dex_prices(dex_name)
            if prices:
                all_prices[dex_name] = prices
        
        return all_prices
    
    def get_price_for_pair(self, all_prices: Dict, pair: str) -> Dict[str, float]:
        """
        Get prices for a specific pair across all DEXs
        Returns: {dex_name: price}
        """
        pair_prices = {}
        
        for dex_name, dex_prices in all_prices.items():
            if pair in dex_prices:
                pair_prices[dex_name] = dex_prices[pair]['price']
        
        return pair_prices
