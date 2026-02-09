"""
Gas Fee Estimator - Calculate gas costs for DEX trades
Critical for determining if DEX arbitrage is actually profitable
"""
from web3 import Web3
from typing import Dict, Optional
import asyncio
import aiohttp

class GasFeeEstimator:
    def __init__(self):
        # Gas units required for different operations
        self.GAS_ESTIMATES = {
            'ethereum': {
                'swap': 150000,  # Uniswap V2 swap
                'swap_v3': 180000,  # Uniswap V3 swap (higher)
                'approval': 46000,  # ERC20 approval
                'transfer': 21000,  # ETH transfer
            },
            'bsc': {
                'swap': 120000,  # PancakeSwap swap (cheaper on BSC)
                'swap_v3': 150000,  # PancakeSwap V3 swap
                'approval': 46000,  # BEP20 approval
                'transfer': 21000,  # BNB transfer
            },
            'solana': {
                'swap': 5000,  # Base compute units per instruction
                'swap_jupiter': 200000,  # Jupiter aggregated swap (higher)
                'approval': 0,  # No approval needed on Solana
                'transfer': 5000,  # SOL transfer
            }
        }
        
        # Native token prices (USD) - will be updated from oracles
        self.native_prices = {
            'ethereum': 2500,  # ETH price in USD (placeholder)
            'bsc': 300,  # BNB price in USD (placeholder)
            'solana': 100,  # SOL price in USD (placeholder)
        }
        
        # RPC endpoints for gas price
        self.rpc_endpoints = {
            'ethereum': 'https://eth.public-rpc.com',
            'bsc': 'https://bsc-dataseed1.binance.org',
            'solana': 'https://api.mainnet-beta.solana.com',
        }
        
        # Gas price APIs (Solana doesn't have one, we'll fetch from RPC)
        self.gas_apis = {
            'ethereum': 'https://api.etherscan.io/api?module=gastracker&action=gasoracle',
            'bsc': 'https://api.bscscan.com/api?module=gastracker&action=gasoracle',
            'solana': None,  # Fetch from RPC directly
        }
        
        self.web3_connections: Dict[str, Web3] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connections"""
        for chain, rpc_url in self.rpc_endpoints.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    print(f"✓ Gas estimator connected to {chain.upper()}")
            except Exception as e:
                print(f"✗ Gas estimator failed to connect to {chain}: {e}")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_current_gas_price(self, chain: str) -> Optional[Dict]:
        """
        Get current gas price for a chain
        Returns: {
            'fast': gas_price_gwei,
            'standard': gas_price_gwei,
            'slow': gas_price_gwei
        }
        """
        # Try API first for more accurate data
        gas_data = await self._fetch_gas_from_api(chain)
        if gas_data:
            return gas_data
        
        # Fallback to RPC
        return await self._fetch_gas_from_rpc(chain)
    
    async def _fetch_gas_from_api(self, chain: str) -> Optional[Dict]:
        """Fetch gas prices from Etherscan/BscScan API"""
        await self._ensure_session()
        
        api_url = self.gas_apis.get(chain)
        if not api_url:
            return None
        
        try:
            async with self.session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1' and data.get('result'):
                        result = data['result']
                        return {
                            'fast': float(result.get('FastGasPrice', 0)),
                            'standard': float(result.get('ProposeGasPrice', 0)),
                            'slow': float(result.get('SafeGasPrice', 0))
                        }
        except Exception as e:
            print(f"Error fetching gas from API ({chain}): {e}")
        
        return None
    
    async def _fetch_gas_from_rpc(self, chain: str) -> Optional[Dict]:
        """Fallback: Fetch gas price from RPC"""
        if chain == 'solana':
            return await self._fetch_solana_fees()
        
        w3 = self.web3_connections.get(chain)
        if not w3:
            return None
        
        try:
            gas_price_wei = w3.eth.gas_price
            gas_price_gwei = w3.from_wei(gas_price_wei, 'gwei')
            
            # Estimate fast/standard/slow based on current price
            return {
                'fast': gas_price_gwei * 1.2,  # 20% higher for fast
                'standard': gas_price_gwei,
                'slow': gas_price_gwei * 0.8  # 20% lower for slow
            }
        except Exception as e:
            print(f"Error fetching gas from RPC ({chain}): {e}")
            return None
    
    async def _fetch_solana_fees(self) -> Optional[Dict]:
        """Fetch Solana transaction fees (in lamports per signature)"""
        await self._ensure_session()
        
        try:
            # Call Solana RPC to get recent fees
            async with self.session.post(
                self.rpc_endpoints['solana'],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getRecentPrioritizationFees",
                    "params": []
                },
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'result' in data and len(data['result']) > 0:
                        # Get average of recent fees
                        fees = [item['prioritizationFee'] for item in data['result']]
                        avg_fee = sum(fees) / len(fees) if fees else 5000
                        
                        # Solana fees are in micro-lamports per compute unit
                        # Convert to lamports per transaction (typical ~200k compute units)
                        base_fee = 5000  # Base fee per signature (~5000 lamports)
                        priority_fee = avg_fee * 200000 / 1000000  # Priority fee
                        
                        total_fee_lamports = base_fee + priority_fee
                        
                        return {
                            'fast': total_fee_lamports * 2,  # Higher priority
                            'standard': total_fee_lamports,
                            'slow': base_fee  # Just base fee, no priority
                        }
        except Exception as e:
            print(f"Error fetching Solana fees: {e}")
        
        # Fallback to typical fees
        return {
            'fast': 15000,  # ~0.000015 SOL
            'standard': 10000,  # ~0.00001 SOL
            'slow': 5000  # ~0.000005 SOL (base fee only)
        }
    
    async def update_native_prices(self, eth_price: float = None, bnb_price: float = None, sol_price: float = None):
        """Update native token prices (should be called periodically)"""
        if eth_price:
            self.native_prices['ethereum'] = eth_price
        if bnb_price:
            self.native_prices['bsc'] = bnb_price
        if sol_price:
            self.native_prices['solana'] = sol_price
    
    async def estimate_swap_cost(
        self,
        chain: str,
        num_swaps: int = 1,
        use_v3: bool = False,
        needs_approval: bool = False,
        speed: str = 'standard'
    ) -> Dict:
        """
        Estimate the cost of DEX swap(s) in USD
        
        Args:
            chain: 'ethereum', 'bsc', or 'solana'
            num_swaps: Number of swaps in the transaction
            use_v3: Whether using V3 (higher gas) - N/A for Solana
            needs_approval: Whether token approval is needed - N/A for Solana
            speed: 'fast', 'standard', or 'slow'
        
        Returns:
            {
                'gas_cost_usd': float,
                'gas_price_gwei': float (or lamports for Solana),
                'total_gas_units': int (or lamports for Solana),
                'native_token_cost': float
            }
        """
        # Handle Solana separately (different fee structure)
        if chain == 'solana':
            return await self._estimate_solana_swap_cost(num_swaps, speed)
        
        # EVM chains (Ethereum, BSC)
        # Get current gas prices
        gas_prices = await self.get_current_gas_price(chain)
        if not gas_prices:
            # Use fallback estimates
            gas_prices = {
                'ethereum': {'fast': 50, 'standard': 30, 'slow': 20},
                'bsc': {'fast': 5, 'standard': 3, 'slow': 2}
            }.get(chain, {'fast': 30, 'standard': 20, 'slow': 15})
        
        gas_price_gwei = gas_prices.get(speed, gas_prices['standard'])
        
        # Calculate total gas units
        swap_type = 'swap_v3' if use_v3 else 'swap'
        gas_per_swap = self.GAS_ESTIMATES[chain][swap_type]
        approval_gas = self.GAS_ESTIMATES[chain]['approval'] if needs_approval else 0
        
        total_gas_units = (gas_per_swap * num_swaps) + approval_gas
        
        # Convert to native token cost
        gas_price_wei = int(gas_price_gwei * 1e9)  # Convert gwei to wei
        native_token_cost = (total_gas_units * gas_price_wei) / 1e18
        
        # Convert to USD
        native_price_usd = self.native_prices[chain]
        gas_cost_usd = native_token_cost * native_price_usd
        
        return {
            'gas_cost_usd': round(gas_cost_usd, 2),
            'gas_price_gwei': gas_price_gwei,
            'total_gas_units': total_gas_units,
            'native_token_cost': round(native_token_cost, 6),
            'native_token': 'ETH' if chain == 'ethereum' else 'BNB'
        }
    
    async def _estimate_solana_swap_cost(self, num_swaps: int, speed: str = 'standard') -> Dict:
        """
        Estimate Solana transaction fees
        Solana fees are measured in lamports (1 SOL = 1 billion lamports)
        """
        # Get current Solana fees
        fees = await self.get_current_gas_price('solana')
        if not fees:
            fees = {'fast': 15000, 'standard': 10000, 'slow': 5000}
        
        fee_per_tx_lamports = fees.get(speed, fees['standard'])
        
        # On Solana, each swap is typically 1-2 transactions
        # Jupiter can bundle multiple swaps in one transaction sometimes
        if num_swaps == 1:
            total_lamports = fee_per_tx_lamports
        elif num_swaps == 2:
            total_lamports = fee_per_tx_lamports * 1.5  # Some bundling
        else:
            total_lamports = fee_per_tx_lamports * num_swaps * 0.8  # Better bundling
        
        # Convert to SOL
        sol_cost = total_lamports / 1e9
        
        # Convert to USD
        sol_price_usd = self.native_prices['solana']
        cost_usd = sol_cost * sol_price_usd
        
        return {
            'gas_cost_usd': round(cost_usd, 2),
            'gas_price_gwei': fee_per_tx_lamports,  # Actually lamports, but keeping field name
            'total_gas_units': int(total_lamports),  # Total lamports
            'native_token_cost': round(sol_cost, 6),
            'native_token': 'SOL'
        }
    
    async def calculate_triangular_gas_cost(
        self,
        chain: str,
        dex_protocol: str = 'v2',
        speed: str = 'standard'
    ) -> Dict:
        """
        Calculate gas cost for triangular arbitrage (3 swaps)
        
        Args:
            chain: 'ethereum' or 'bsc'
            dex_protocol: 'v2' or 'v3'
            speed: 'fast', 'standard', or 'slow'
        
        Returns: Gas cost estimation
        """
        use_v3 = dex_protocol == 'v3'
        
        # Triangular arbitrage = 3 swaps
        # First swap usually needs approval (unless using native token)
        return await self.estimate_swap_cost(
            chain=chain,
            num_swaps=3,
            use_v3=use_v3,
            needs_approval=True,
            speed=speed
        )
    
    async def calculate_cross_dex_gas_cost(
        self,
        chain: str,
        num_dexs: int = 2,
        speed: str = 'standard'
    ) -> Dict:
        """
        Calculate gas cost for multi-DEX arbitrage on same chain
        
        Args:
            chain: 'ethereum' or 'bsc'
            num_dexs: Number of different DEXs used
            speed: 'fast', 'standard', or 'slow'
        
        Returns: Gas cost estimation
        """
        # Each DEX might need approval
        # Simple case: Buy on DEX1, Sell on DEX2 = 2 swaps + 2 approvals
        return await self.estimate_swap_cost(
            chain=chain,
            num_swaps=num_dexs,
            use_v3=False,
            needs_approval=True,  # Conservative estimate
            speed=speed
        )
    
    def get_minimum_profitable_amount(
        self,
        gas_cost_usd: float,
        profit_percent: float
    ) -> float:
        """
        Calculate minimum trade amount for profitability
        
        Args:
            gas_cost_usd: Gas cost in USD
            profit_percent: Expected profit percentage (e.g., 1.0 for 1%)
        
        Returns: Minimum trade amount in USD
        """
        # For profitability: (amount * profit_percent / 100) > gas_cost_usd
        # Solving for amount: amount > (gas_cost_usd * 100 / profit_percent)
        
        min_amount = (gas_cost_usd * 100) / profit_percent
        return round(min_amount, 2)
    
    async def is_dex_arbitrage_profitable(
        self,
        chain: str,
        trade_amount_usd: float,
        profit_percent: float,
        arbitrage_type: str = 'simple',  # 'simple', 'triangular', 'cross_dex'
        speed: str = 'fast'
    ) -> Dict:
        """
        Check if a DEX arbitrage opportunity is profitable after gas
        
        Returns:
            {
                'is_profitable': bool,
                'gross_profit_usd': float,
                'gas_cost_usd': float,
                'net_profit_usd': float,
                'net_profit_percent': float,
                'roi': float  # Return on investment
            }
        """
        # Calculate gas cost based on arbitrage type
        if arbitrage_type == 'triangular':
            gas_info = await self.calculate_triangular_gas_cost(chain, speed=speed)
        elif arbitrage_type == 'cross_dex':
            gas_info = await self.calculate_cross_dex_gas_cost(chain, speed=speed)
        else:  # simple
            gas_info = await self.estimate_swap_cost(chain, num_swaps=2, speed=speed)
        
        gas_cost_usd = gas_info['gas_cost_usd']
        
        # Calculate profits
        gross_profit_usd = trade_amount_usd * (profit_percent / 100)
        net_profit_usd = gross_profit_usd - gas_cost_usd
        
        is_profitable = net_profit_usd > 0
        net_profit_percent = (net_profit_usd / trade_amount_usd) * 100 if trade_amount_usd > 0 else 0
        roi = (net_profit_usd / trade_amount_usd) * 100 if trade_amount_usd > 0 else 0
        
        return {
            'is_profitable': is_profitable,
            'gross_profit_usd': round(gross_profit_usd, 2),
            'gas_cost_usd': gas_cost_usd,
            'net_profit_usd': round(net_profit_usd, 2),
            'net_profit_percent': round(net_profit_percent, 2),
            'roi': round(roi, 2),
            'gas_info': gas_info
        }
    
    async def get_gas_price_summary(self) -> Dict:
        """Get current gas prices for all supported chains"""
        eth_gas = await self.get_current_gas_price('ethereum')
        bsc_gas = await self.get_current_gas_price('bsc')
        sol_gas = await self.get_current_gas_price('solana')
        
        return {
            'ethereum': {
                'gas_prices': eth_gas,
                'native_price_usd': self.native_prices['ethereum'],
                'estimated_swap_cost_usd': (
                    await self.estimate_swap_cost('ethereum', speed='standard')
                )['gas_cost_usd'] if eth_gas else None
            },
            'bsc': {
                'gas_prices': bsc_gas,
                'native_price_usd': self.native_prices['bsc'],
                'estimated_swap_cost_usd': (
                    await self.estimate_swap_cost('bsc', speed='standard')
                )['gas_cost_usd'] if bsc_gas else None
            },
            'solana': {
                'gas_prices': sol_gas,
                'native_price_usd': self.native_prices['solana'],
                'estimated_swap_cost_usd': (
                    await self.estimate_swap_cost('solana', speed='standard')
                )['gas_cost_usd'] if sol_gas else None
            }
        }
