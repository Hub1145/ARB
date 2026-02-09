"""
Exchange Manager - Handles connections to CEX and DEX
Supports multiple exchanges and provides unified interface for price fetching
"""
import ccxt.async_support as ccxt
from web3 import Web3
from typing import Dict, List, Optional
import asyncio
from decimal import Decimal
import json

from config import (
    CEX_EXCHANGES, DEX_CONFIGS, COMMON_PAIRS,
)
from dex_fetcher import DexPriceFetcher

class ExchangeManager:
    def __init__(self):
        self.cex_exchanges: Dict[str, ccxt.Exchange] = {}
        self.dex_fetcher = DexPriceFetcher()
        self.prices_cache: Dict[str, Dict[str, float]] = {}
        self.dex_prices_cache: Dict[str, Dict] = {}
        
    async def initialize(self):
        """Initialize all exchange connections"""
        await self._initialize_cex()
        # DEX connections are initialized in DexPriceFetcher
        print("✓ All exchanges initialized")
    
    async def _initialize_cex(self):
        """Initialize centralized exchange connections"""
        for exchange_id in CEX_EXCHANGES:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.cex_exchanges[exchange_id] = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                })
                await self.cex_exchanges[exchange_id].load_markets()
                print(f"✓ Connected to {exchange_id}")
            except Exception as e:
                print(f"✗ Failed to connect to {exchange_id}: {e}")
    
    
    async def get_prices(self, symbol: str) -> Dict[str, Dict]:
        """
        Get current prices for a symbol across all exchanges
        Returns: {exchange_name: {'bid': price, 'ask': price, 'last': price}}
        """
        prices = {}
        
        # Get CEX prices
        tasks = []
        for exchange_id, exchange in self.cex_exchanges.items():
            tasks.append(self._fetch_cex_price(exchange_id, exchange, symbol))
        
        cex_prices = await asyncio.gather(*tasks, return_exceptions=True)
        
        for exchange_id, price_data in zip(self.cex_exchanges.keys(), cex_prices):
            if not isinstance(price_data, Exception) and price_data:
                prices[exchange_id] = price_data
        
        # Get DEX prices - convert symbol format (BTC/USDT -> WBTC/USDT for ETH, BTCB/USDT for BSC)
        dex_symbol = self._convert_symbol_for_dex(symbol)
        if dex_symbol:
            dex_prices = await self._fetch_all_dex_prices(dex_symbol)
            prices.update(dex_prices)
        
        # Update cache
        self.prices_cache[symbol] = prices
        return prices
    
    def _convert_symbol_for_dex(self, symbol: str) -> Optional[str]:
        """Convert CEX symbol to DEX symbol (e.g., BTC/USDT -> WBTC/USDT or BTCB/USDT)"""
        # Map common CEX symbols to DEX token symbols
        conversion_map = {
            'BTC/USDT': ['WBTC/USDT', 'BTCB/USDT'],
            'ETH/USDT': ['WETH/USDT'],
            'BNB/USDT': ['WBNB/USDT'],
            'ETH/BTC': ['WETH/WBTC'],
        }
        
        # Return first match or None
        return conversion_map.get(symbol, [None])[0]
    
    async def _fetch_all_dex_prices(self, symbol: str) -> Dict[str, Dict]:
        """Fetch prices from all DEXs for a symbol"""
        dex_prices = {}
        
        # Get all DEX prices (cached internally by dex_fetcher)
        all_dex_data = await self.dex_fetcher.get_all_dex_prices()
        
        # Extract prices for specific symbol
        for dex_name, pairs_data in all_dex_data.items():
            if symbol in pairs_data:
                price_data = pairs_data[symbol]
                price = price_data.get('price', 0)
                
                # Format as CEX-style price data for compatibility
                dex_prices[dex_name] = {
                    'bid': price * 0.999,  # Simulate bid with small spread
                    'ask': price * 1.001,  # Simulate ask with small spread
                    'last': price,
                    'volume': price_data.get('liquidity_usd', 0),
                    'timestamp': 0
                }
        
        return dex_prices
    
    async def _fetch_cex_price(self, exchange_id: str, exchange: ccxt.Exchange, symbol: str) -> Optional[Dict]:
        """Fetch price from a centralized exchange"""
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return {
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'last': ticker.get('last', 0),
                'volume': ticker.get('baseVolume', 0),
                'timestamp': ticker.get('timestamp', 0)
            }
        except Exception as e:
            # Symbol might not be available on this exchange
            return None
    
    async def get_order_book(self, exchange: str, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book for a specific exchange and symbol"""
        try:
            if exchange in self.cex_exchanges:
                order_book = await self.cex_exchanges[exchange].fetch_order_book(symbol, limit)
                return {
                    'bids': order_book['bids'][:limit],
                    'asks': order_book['asks'][:limit],
                    'timestamp': order_book.get('timestamp', 0)
                }
        except Exception as e:
            print(f"Error fetching order book from {exchange}: {e}")
            return None
    
    def get_cex_list(self) -> List[str]:
        """Get list of connected CEX exchanges"""
        return list(self.cex_exchanges.keys())
    
    def get_dex_list(self) -> List[str]:
        """Get list of connected DEX exchanges"""
        return list(DEX_CONFIGS.keys())
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange in self.cex_exchanges.values():
            await exchange.close()
        await self.dex_fetcher.close()
        print("✓ All exchanges closed")
    
    def get_available_symbols(self, exchange: str) -> List[str]:
        """Get list of available trading symbols for an exchange"""
        if exchange in self.cex_exchanges:
            return list(self.cex_exchanges[exchange].markets.keys())
        return []
    
    def get_common_symbols(self) -> List[str]:
        """Get list of symbols available on multiple exchanges"""
        if not self.cex_exchanges:
            return COMMON_PAIRS
        
        # Find symbols available on at least 2 exchanges
        symbol_counts = {}
        for exchange_id in self.cex_exchanges:
            symbols = self.get_available_symbols(exchange_id)
            for symbol in symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        common = [symbol for symbol, count in symbol_counts.items() if count >= 2]
        return common if common else COMMON_PAIRS
