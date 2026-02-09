"""
Solana DEX Fetcher - Get prices from Solana DEXs
Supports Jupiter, Raydium, Orca
"""
import aiohttp
from typing import Dict, Optional, List
import json
from config import SOL_TOKEN_ADDRESSES, DEX_PAIRS

class SolanaDexFetcher:
    def __init__(self):
        self.jupiter_api = 'https://quote-api.jup.ag/v6'
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_jupiter_price(
        self,
        input_mint: str,
        output_mint: str,
        amount: int = 1000000  # 1 USDC (6 decimals)
    ) -> Optional[Dict]:
        """
        Fetch price from Jupiter aggregator
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Amount in smallest unit (lamports for SOL, etc.)
        
        Returns:
            {
                'price': float,
                'input_amount': int,
                'output_amount': int,
                'price_impact': float,
                'route': list
            }
        """
        await self._ensure_session()
        
        try:
            # Get quote from Jupiter
            quote_url = f"{self.jupiter_api}/quote"
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': amount,
                'slippageBps': 50  # 0.5% slippage
            }
            
            async with self.session.get(
                quote_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data:
                        in_amount = int(data.get('inAmount', 0))
                        out_amount = int(data.get('outAmount', 0))
                        
                        # Calculate price
                        if in_amount > 0:
                            price = out_amount / in_amount
                        else:
                            price = 0
                        
                        return {
                            'price': price,
                            'input_amount': in_amount,
                            'output_amount': out_amount,
                            'price_impact': float(data.get('priceImpactPct', 0)),
                            'route': data.get('routePlan', [])
                        }
        except Exception as e:
            print(f"Error fetching Jupiter price: {e}")
        
        return None
    
    async def fetch_all_jupiter_prices(self, pairs: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch prices for multiple pairs from Jupiter
        
        Args:
            pairs: List of pairs in format 'TOKEN1/TOKEN2' (e.g., 'SOL/USDC')
        
        Returns:
            {pair: price_data}
        """
        if pairs is None:
            pairs = DEX_PAIRS.get('solana', [])
        
        prices = {}
        
        for pair in pairs:
            try:
                # Parse pair
                base, quote = pair.split('/')
                
                # Get mint addresses
                base_mint = SOL_TOKEN_ADDRESSES.get(base)
                quote_mint = SOL_TOKEN_ADDRESSES.get(quote)
                
                if not base_mint or not quote_mint:
                    continue
                
                # Determine amount based on quote token
                # USDC/USDT use 6 decimals, SOL uses 9
                if quote in ['USDC', 'USDT']:
                    amount = 1000000  # 1 USDC/USDT
                elif quote == 'SOL':
                    amount = 1000000000  # 1 SOL
                else:
                    amount = 1000000  # Default to 1M smallest units
                
                # Fetch price
                price_data = await self.fetch_jupiter_price(
                    input_mint=quote_mint,
                    output_mint=base_mint,
                    amount=amount
                )
                
                if price_data:
                    prices[pair] = {
                        'price': price_data['price'],
                        'price_impact': price_data['price_impact'],
                        'liquidity_indicator': 'high' if price_data['price_impact'] < 0.5 else 'low'
                    }
                    
            except Exception as e:
                print(f"Error fetching {pair} from Jupiter: {e}")
                continue
        
        return prices
    
    async def get_token_price_in_usd(self, token_symbol: str) -> Optional[float]:
        """
        Get token price in USD using Jupiter
        
        Args:
            token_symbol: Token symbol (e.g., 'SOL', 'RAY')
        
        Returns:
            Price in USD
        """
        # Get token mint
        token_mint = SOL_TOKEN_ADDRESSES.get(token_symbol)
        usdc_mint = SOL_TOKEN_ADDRESSES.get('USDC')
        
        if not token_mint or not usdc_mint:
            return None
        
        # Determine amount based on token
        if token_symbol == 'SOL':
            amount = 1000000000  # 1 SOL
        elif token_symbol in ['USDC', 'USDT']:
            return 1.0  # Stablecoins = $1
        else:
            amount = 1000000  # 1 token (assuming 6 decimals)
        
        # Get quote
        price_data = await self.fetch_jupiter_price(
            input_mint=token_mint,
            output_mint=usdc_mint,
            amount=amount
        )
        
        if price_data:
            return price_data['price']
        
        return None
    
    async def fetch_raydium_price(self, pair: str) -> Optional[Dict]:
        """
        Fetch price from Raydium (placeholder - would need Raydium SDK integration)
        
        For now, falls back to Jupiter
        """
        # In production, you would integrate with Raydium's SDK
        # For now, use Jupiter as it aggregates Raydium
        return None
    
    async def fetch_orca_price(self, pair: str) -> Optional[Dict]:
        """
        Fetch price from Orca (placeholder - would need Orca SDK integration)
        
        For now, falls back to Jupiter
        """
        # In production, you would integrate with Orca's SDK
        # For now, use Jupiter as it aggregates Orca
        return None
    
    async def get_all_sol_dex_prices(self) -> Dict[str, Dict]:
        """
        Get prices from all Solana DEXs
        
        Currently uses Jupiter which aggregates all major Solana DEXs
        """
        return {
            'jupiter': await self.fetch_all_jupiter_prices()
        }
