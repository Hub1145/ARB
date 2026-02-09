"""
Arbitrage Detector - Detects arbitrage opportunities
Implements three types:
1. Cross-Exchange Arbitrage: Between different exchanges (CEX-CEX, DEX-DEX, CEX-DEX)
2. Intra-Exchange Triangular: Within a single exchange (CEX or DEX)
3. Multi-DEX Triangular: Triangular across multiple DEXs on same chain
"""
from typing import List, Dict, Optional
import asyncio
from itertools import combinations, permutations
from decimal import Decimal
import math

from exchange_manager import ExchangeManager
from gas_estimator import GasFeeEstimator
from config import COMMON_PAIRS, TRADING_FEE_PERCENT, MIN_PROFIT_PERCENT, DEX_CONFIGS

class ArbitrageDetector:
    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.gas_estimator = GasFeeEstimator()
        self.trading_fee = TRADING_FEE_PERCENT / 100  # Convert to decimal
        
        # Categorize exchanges
        self.cex_exchanges = self.exchange_manager.get_cex_list()
        self.dex_exchanges = self.exchange_manager.get_dex_list()
        
        # Default trade amounts for gas calculation
        self.default_trade_amounts = {
            'ethereum': 10000,  # $10k USD
            'bsc': 5000,  # $5k USD (cheaper gas)
            'solana': 3000,  # $3k USD (very cheap fees)
        }
    
    async def detect_cross_exchange_arbitrage(
        self,
        min_profit_percent: float = MIN_PROFIT_PERCENT,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Detect cross-exchange arbitrage (buy on one exchange, sell on another)
        Works for: CEX-to-CEX, DEX-to-DEX, and CEX-to-DEX
        
        Returns list of opportunities with gas fees calculated for DEX trades
        """
        opportunities = []
        
        # Use provided symbols or default common pairs
        symbols_to_check = symbols if symbols else self.exchange_manager.get_common_symbols()
        
        # Fetch prices for all symbols
        for symbol in symbols_to_check:
            try:
                prices = await self.exchange_manager.get_prices(symbol)
                
                if len(prices) < 2:
                    continue
                
                # Find arbitrage opportunities
                opps = await self._find_cross_exchange_in_prices(symbol, prices, min_profit_percent)
                opportunities.extend(opps)
                
            except Exception as e:
                print(f"Error checking {symbol}: {e}")
                continue
        
        # Sort by net profit (after gas for DEX)
        opportunities.sort(key=lambda x: x.get('net_profit_percent', x['profit_percent']), reverse=True)
        return opportunities
    
    async def _find_cross_exchange_in_prices(
        self,
        symbol: str,
        prices: Dict[str, Dict],
        min_profit_percent: float
    ) -> List[Dict]:
        """Find cross-exchange arbitrage opportunities with gas fee consideration"""
        opportunities = []
        
        exchanges = list(prices.keys())
        
        # Check all exchange pairs
        for buy_exchange, sell_exchange in combinations(exchanges, 2):
            buy_data = prices[buy_exchange]
            sell_data = prices[sell_exchange]
            
            # Skip if missing price data
            if not buy_data.get('ask') or not sell_data.get('bid'):
                continue
            
            # Calculate profit buying on buy_exchange and selling on sell_exchange
            buy_price = buy_data['ask']
            sell_price = sell_data['bid']
            
            profit_percent = self._calculate_profit_percent(buy_price, sell_price)
            
            # Check if involves DEX and calculate gas fees
            involves_dex = self._is_dex(buy_exchange) or self._is_dex(sell_exchange)
            
            if involves_dex:
                # Determine chain
                chain = self._get_chain_for_dex(buy_exchange if self._is_dex(buy_exchange) else sell_exchange)
                
                if chain:
                    # Calculate gas fees
                    trade_amount = self.default_trade_amounts.get(chain, 10000)
                    gas_analysis = await self.gas_estimator.is_dex_arbitrage_profitable(
                        chain=chain,
                        trade_amount_usd=trade_amount,
                        profit_percent=profit_percent,
                        arbitrage_type='simple',
                        speed='fast'
                    )
                    
                    # Use net profit after gas
                    if gas_analysis['is_profitable'] and gas_analysis['net_profit_percent'] >= min_profit_percent:
                        opportunities.append({
                            'type': 'cross_exchange',
                            'sub_type': f"{self._get_exchange_type(buy_exchange)}_to_{self._get_exchange_type(sell_exchange)}",
                            'symbol': symbol,
                            'buy_exchange': buy_exchange,
                            'sell_exchange': sell_exchange,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'gross_profit_percent': round(profit_percent, 2),
                            'gas_cost_usd': gas_analysis['gas_cost_usd'],
                            'net_profit_percent': gas_analysis['net_profit_percent'],
                            'profit_percent': gas_analysis['net_profit_percent'],  # For sorting
                            'trade_amount_usd': trade_amount,
                            'net_profit_usd': gas_analysis['net_profit_usd'],
                            'chain': chain,
                            'involves_dex': True,
                            'volume': min(buy_data.get('volume', 0), sell_data.get('volume', 0))
                        })
            else:
                # Pure CEX arbitrage - no gas fees
                if profit_percent >= min_profit_percent:
                    opportunities.append({
                        'type': 'cross_exchange',
                        'sub_type': 'cex_to_cex',
                        'symbol': symbol,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_percent': round(profit_percent, 2),
                        'spread_percent': round(((sell_price - buy_price) / buy_price) * 100, 2),
                        'involves_dex': False,
                        'volume': min(buy_data.get('volume', 0), sell_data.get('volume', 0))
                    })
            
            # Also check the reverse
            reverse_profit = self._calculate_profit_percent(sell_data['ask'], buy_data['bid'])
            
            if involves_dex and chain:
                trade_amount = self.default_trade_amounts.get(chain, 10000)
                gas_analysis = await self.gas_estimator.is_dex_arbitrage_profitable(
                    chain=chain,
                    trade_amount_usd=trade_amount,
                    profit_percent=reverse_profit,
                    arbitrage_type='simple',
                    speed='fast'
                )
                
                if gas_analysis['is_profitable'] and gas_analysis['net_profit_percent'] >= min_profit_percent:
                    opportunities.append({
                        'type': 'cross_exchange',
                        'sub_type': f"{self._get_exchange_type(sell_exchange)}_to_{self._get_exchange_type(buy_exchange)}",
                        'symbol': symbol,
                        'buy_exchange': sell_exchange,
                        'sell_exchange': buy_exchange,
                        'buy_price': sell_data['ask'],
                        'sell_price': buy_data['bid'],
                        'gross_profit_percent': round(reverse_profit, 2),
                        'gas_cost_usd': gas_analysis['gas_cost_usd'],
                        'net_profit_percent': gas_analysis['net_profit_percent'],
                        'profit_percent': gas_analysis['net_profit_percent'],
                        'trade_amount_usd': trade_amount,
                        'net_profit_usd': gas_analysis['net_profit_usd'],
                        'chain': chain,
                        'involves_dex': True,
                        'volume': min(buy_data.get('volume', 0), sell_data.get('volume', 0))
                    })
            elif reverse_profit >= min_profit_percent:
                opportunities.append({
                    'type': 'cross_exchange',
                    'sub_type': 'cex_to_cex',
                    'symbol': symbol,
                    'buy_exchange': sell_exchange,
                    'sell_exchange': buy_exchange,
                    'buy_price': sell_data['ask'],
                    'sell_price': buy_data['bid'],
                    'profit_percent': round(reverse_profit, 2),
                    'spread_percent': round(((buy_data['bid'] - sell_data['ask']) / sell_data['ask']) * 100, 2),
                    'involves_dex': False,
                    'volume': min(buy_data.get('volume', 0), sell_data.get('volume', 0))
                })
        
        return opportunities
    
    def _calculate_profit_percent(self, buy_price: float, sell_price: float) -> float:
        """Calculate profit percentage after trading fees"""
        if buy_price <= 0:
            return -100
        
        # Account for fees on both buy and sell
        effective_buy_price = buy_price * (1 + self.trading_fee)
        effective_sell_price = sell_price * (1 - self.trading_fee)
        
        profit_percent = ((effective_sell_price - effective_buy_price) / effective_buy_price) * 100
        return profit_percent
    
    def _is_dex(self, exchange: str) -> bool:
        """Check if exchange is a DEX"""
        return exchange in self.dex_exchanges
    
    def _get_exchange_type(self, exchange: str) -> str:
        """Get exchange type (cex or dex)"""
        return 'dex' if self._is_dex(exchange) else 'cex'
    
    def _get_chain_for_dex(self, dex_name: str) -> Optional[str]:
        """Get blockchain network for a DEX"""
        config = DEX_CONFIGS.get(dex_name)
        return config.get('chain') if config else None
    
    async def detect_intra_exchange_triangular(
        self,
        min_profit_percent: float = MIN_PROFIT_PERCENT,
        exchange: Optional[str] = None
    ) -> List[Dict]:
        """
        Detect triangular arbitrage within a SINGLE exchange (CEX or DEX)
        
        Example: 
        - CEX: BTC/USDT -> ETH/BTC -> ETH/USDT on Binance
        - DEX: WETH/USDT -> WBTC/WETH -> WBTC/USDT on Uniswap
        
        Returns list of opportunities with gas fees for DEX
        """
        opportunities = []
        
        # Check specific exchange or all exchanges
        exchanges_to_check = [exchange] if exchange else (self.cex_exchanges + self.dex_exchanges)
        
        for exch in exchanges_to_check:
            try:
                is_dex = self._is_dex(exch)
                
                # Get available symbols
                if is_dex:
                    # For DEX, use predefined pairs
                    chain = self._get_chain_for_dex(exch)
                    symbols = self._get_dex_symbols_for_chain(chain) if chain else []
                else:
                    # For CEX, query available markets
                    symbols = self.exchange_manager.get_available_symbols(exch)
                
                if not symbols:
                    continue
                
                # Find triangular paths
                triangular_paths = self._find_triangular_paths(symbols)
                
                # Check each path for arbitrage
                for path in triangular_paths:
                    opportunity = await self._check_triangular_path(
                        exch, 
                        path, 
                        min_profit_percent,
                        is_dex
                    )
                    if opportunity:
                        opportunities.append(opportunity)
                
            except Exception as e:
                print(f"Error checking triangular arbitrage on {exch}: {e}")
                continue
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x.get('net_profit_percent', x['profit_percent']), reverse=True)
        return opportunities
    
    def _get_dex_symbols_for_chain(self, chain: str) -> List[str]:
        """Get DEX trading pairs for a specific chain"""
        from config import DEX_PAIRS
        return DEX_PAIRS.get(chain, [])
    
    async def detect_multi_dex_triangular(
        self,
        chain: str,
        min_profit_percent: float = MIN_PROFIT_PERCENT
    ) -> List[Dict]:
        """
        Detect triangular arbitrage using multiple DEXs on the SAME chain
        
        Example on Ethereum:
        - Buy WETH/USDT on Uniswap
        - Swap WETH for WBTC on SushiSwap  
        - Sell WBTC/USDT back on Uniswap
        
        This is more complex and has higher gas costs (3 different contracts)
        """
        opportunities = []
        
        # Get all DEXs on this chain
        chain_dexs = [dex for dex in self.dex_exchanges if self._get_chain_for_dex(dex) == chain]
        
        if len(chain_dexs) < 2:
            return opportunities
        
        # Get symbols for this chain
        symbols = self._get_dex_symbols_for_chain(chain)
        
        if not symbols:
            return opportunities
        
        # Find multi-DEX triangular paths
        paths = self._find_multi_dex_triangular_paths(chain_dexs, symbols)
        
        # Check each path
        for path_info in paths:
            try:
                opportunity = await self._check_multi_dex_path(
                    chain,
                    path_info,
                    min_profit_percent
                )
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                print(f"Error checking multi-DEX path: {e}")
                continue
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x['net_profit_percent'], reverse=True)
        return opportunities
    
    def _find_multi_dex_triangular_paths(
        self,
        dexs: List[str],
        symbols: List[str]
    ) -> List[Dict]:
        """Find possible multi-DEX triangular paths"""
        paths = []
        
        # Build currency graph
        currency_pairs = {}
        for symbol in symbols:
            try:
                base, quote = symbol.split('/')
                if base not in currency_pairs:
                    currency_pairs[base] = []
                if quote not in currency_pairs:
                    currency_pairs[quote] = []
                currency_pairs[base].append((quote, symbol))
                currency_pairs[quote].append((base, symbol))
            except:
                continue
        
        # Find triangular paths with DEX assignments
        start_currencies = ['USDT', 'USDC', 'BUSD']
        
        for start_currency in start_currencies:
            if start_currency not in currency_pairs:
                continue
            
            # Create paths using different DEXs
            for dex1 in dexs:
                for dex2 in dexs:
                    for dex3 in dexs:
                        # At least 2 different DEXs required
                        if len(set([dex1, dex2, dex3])) < 2:
                            continue
                        
                        # Simple triangular: A -> B -> C -> A
                        for currency_b, pair_ab in currency_pairs[start_currency]:
                            if currency_b not in currency_pairs:
                                continue
                            
                            for currency_c, pair_bc in currency_pairs[currency_b]:
                                if currency_c == start_currency or currency_c not in currency_pairs:
                                    continue
                                
                                for currency_a, pair_ca in currency_pairs[currency_c]:
                                    if currency_a == start_currency:
                                        paths.append({
                                            'start': start_currency,
                                            'trades': [
                                                {'dex': dex1, 'pair': pair_ab, 'to': currency_b},
                                                {'dex': dex2, 'pair': pair_bc, 'to': currency_c},
                                                {'dex': dex3, 'pair': pair_ca, 'to': start_currency}
                                            ]
                                        })
        
        # Limit paths
        return paths[:50]
    
    async def _check_multi_dex_path(
        self,
        chain: str,
        path: Dict,
        min_profit_percent: float
    ) -> Optional[Dict]:
        """Check multi-DEX triangular path profitability"""
        try:
            start_amount = 1000
            current_amount = start_amount
            
            trade_details = []
            dexs_used = []
            
            # Execute theoretical trades
            for trade in path['trades']:
                dex_name = trade['dex']
                symbol = trade['pair']
                dexs_used.append(dex_name)
                
                # Fetch prices from this specific DEX
                # This is simplified - in production, fetch from dex_fetcher
                prices = await self.exchange_manager.get_prices(symbol)
                
                if dex_name not in prices:
                    return None
                
                price_data = prices[dex_name]
                price = price_data.get('last', 0)
                
                if price <= 0:
                    return None
                
                # Apply trading fee and execute trade
                current_amount = (current_amount / price) * (1 - self.trading_fee)
                
                trade_details.append({
                    'dex': dex_name,
                    'pair': symbol,
                    'price': price,
                    'amount': current_amount
                })
            
            # Calculate gross profit
            gross_profit = current_amount - start_amount
            gross_profit_percent = (gross_profit / start_amount) * 100
            
            # Calculate gas fees (higher for multi-DEX)
            trade_amount = self.default_trade_amounts.get(chain, 10000)
            num_different_dexs = len(set(dexs_used))
            
            gas_analysis = await self.gas_estimator.is_dex_arbitrage_profitable(
                chain=chain,
                trade_amount_usd=trade_amount,
                profit_percent=gross_profit_percent,
                arbitrage_type='cross_dex',
                speed='fast'
            )
            
            if gas_analysis['is_profitable'] and gas_analysis['net_profit_percent'] >= min_profit_percent:
                return {
                    'type': 'multi_dex_triangular',
                    'chain': chain,
                    'start_currency': path['start'],
                    'dexs_used': list(set(dexs_used)),
                    'num_dexs': num_different_dexs,
                    'path': [f"{t['dex']}:{t['pair']}" for t in path['trades']],
                    'trade_details': trade_details,
                    'start_amount': start_amount,
                    'end_amount': round(current_amount, 8),
                    'gross_profit_percent': round(gross_profit_percent, 2),
                    'gas_cost_usd': gas_analysis['gas_cost_usd'],
                    'net_profit_percent': gas_analysis['net_profit_percent'],
                    'profit_percent': gas_analysis['net_profit_percent'],
                    'trade_amount_usd': trade_amount,
                    'net_profit_usd': gas_analysis['net_profit_usd']
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking multi-DEX path: {e}")
            return None
    
    def _find_triangular_paths(self, symbols: List[str]) -> List[List[str]]:
        """
        Find potential triangular arbitrage paths
        Example: ['BTC/USDT', 'ETH/BTC', 'ETH/USDT']
        """
        paths = []
        
        # Build a graph of available currencies and their pairs
        currency_pairs = {}
        for symbol in symbols:
            try:
                base, quote = symbol.split('/')
                if base not in currency_pairs:
                    currency_pairs[base] = []
                if quote not in currency_pairs:
                    currency_pairs[quote] = []
                currency_pairs[base].append((quote, symbol, 'sell'))
                currency_pairs[quote].append((base, symbol, 'buy'))
            except:
                continue
        
        # Find triangular paths starting from major quote currencies
        start_currencies = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'BUSD']
        
        for start_currency in start_currencies:
            if start_currency not in currency_pairs:
                continue
            
            # Find paths: A -> B -> C -> A
            for currency_b, pair_ab, direction_ab in currency_pairs[start_currency]:
                if currency_b not in currency_pairs:
                    continue
                
                for currency_c, pair_bc, direction_bc in currency_pairs[currency_b]:
                    if currency_c == start_currency or currency_c not in currency_pairs:
                        continue
                    
                    for currency_a, pair_ca, direction_ca in currency_pairs[currency_c]:
                        if currency_a == start_currency:
                            # Found a triangular path
                            path = {
                                'start': start_currency,
                                'trades': [
                                    {'pair': pair_ab, 'direction': direction_ab, 'to': currency_b},
                                    {'pair': pair_bc, 'direction': direction_bc, 'to': currency_c},
                                    {'pair': pair_ca, 'direction': direction_ca, 'to': start_currency}
                                ]
                            }
                            paths.append(path)
        
        # Limit to reasonable number of paths
        return paths[:100]
    
    async def _check_triangular_path(
        self,
        exchange: str,
        path: Dict,
        min_profit_percent: float,
        is_dex: bool
    ) -> Optional[Dict]:
        """Check if a triangular path has arbitrage opportunity"""
        try:
            start_amount = 1000  # Start with 1000 units of base currency
            current_amount = start_amount
            
            trade_details = []
            
            # Execute theoretical trades
            for trade in path['trades']:
                symbol = trade['pair']
                direction = trade['direction']
                
                # Fetch current price
                prices = await self.exchange_manager.get_prices(symbol)
                if exchange not in prices:
                    return None
                
                price_data = prices[exchange]
                
                # Determine price based on direction
                if direction == 'buy':
                    price = price_data.get('ask', 0)
                    if price <= 0:
                        return None
                    # Buying: divide by price and account for fee
                    current_amount = (current_amount / price) * (1 - self.trading_fee)
                else:  # sell
                    price = price_data.get('bid', 0)
                    if price <= 0:
                        return None
                    # Selling: multiply by price and account for fee
                    current_amount = (current_amount * price) * (1 - self.trading_fee)
                
                trade_details.append({
                    'pair': symbol,
                    'direction': direction,
                    'price': price,
                    'amount': current_amount
                })
            
            # Calculate profit
            profit_amount = current_amount - start_amount
            gross_profit_percent = (profit_amount / start_amount) * 100
            
            # For DEX, subtract gas fees
            if is_dex:
                chain = self._get_chain_for_dex(exchange)
                if not chain:
                    return None
                
                trade_amount = self.default_trade_amounts.get(chain, 10000)
                gas_analysis = await self.gas_estimator.is_dex_arbitrage_profitable(
                    chain=chain,
                    trade_amount_usd=trade_amount,
                    profit_percent=gross_profit_percent,
                    arbitrage_type='triangular',
                    speed='fast'
                )
                
                if gas_analysis['is_profitable'] and gas_analysis['net_profit_percent'] >= min_profit_percent:
                    return {
                        'type': 'intra_exchange_triangular',
                        'exchange_type': 'dex',
                        'exchange': exchange,
                        'chain': chain,
                        'start_currency': path['start'],
                        'path': [t['pair'] for t in path['trades']],
                        'trade_details': trade_details,
                        'start_amount': start_amount,
                        'end_amount': round(current_amount, 8),
                        'gross_profit_percent': round(gross_profit_percent, 2),
                        'gas_cost_usd': gas_analysis['gas_cost_usd'],
                        'net_profit_percent': gas_analysis['net_profit_percent'],
                        'profit_percent': gas_analysis['net_profit_percent'],
                        'trade_amount_usd': trade_amount,
                        'net_profit_usd': gas_analysis['net_profit_usd']
                    }
            else:
                # CEX - no gas fees
                if gross_profit_percent >= min_profit_percent:
                    return {
                        'type': 'intra_exchange_triangular',
                        'exchange_type': 'cex',
                        'exchange': exchange,
                        'start_currency': path['start'],
                        'path': [t['pair'] for t in path['trades']],
                        'trade_details': trade_details,
                        'start_amount': start_amount,
                        'end_amount': round(current_amount, 8),
                        'profit_amount': round(profit_amount, 8),
                        'profit_percent': round(gross_profit_percent, 2)
                    }
            
            return None
            
        except Exception as e:
            print(f"Error checking triangular path: {e}")
            return None
