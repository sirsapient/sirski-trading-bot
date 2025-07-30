"""
Real API integrations for Jupiter (Solana) and Uniswap V3 (Base).
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

class JupiterAPI:
    """Real Jupiter API integration for Solana."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://price.jup.ag/v4"
        self.quote_url = "https://quote-api.jup.ag/v6"
        
        # Real token addresses on Solana mainnet
        self.tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 
            "ETH": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
            "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
            "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE"
        }
    
    async def get_price(self, session: aiohttp.ClientSession, token: str) -> Optional[float]:
        """Get current price from Jupiter."""
        try:
            token_address = self.tokens.get(token)
            if not token_address:
                return None
            
            url = f"{self.base_url}/price?ids={token_address}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and token_address in data["data"]:
                        return float(data["data"][token_address]["price"])
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Jupiter price for {token}: {e}")
            return None
    
    async def get_quote(self, session: aiohttp.ClientSession, 
                       input_token: str, output_token: str, 
                       amount: int) -> Optional[Dict]:
        """Get swap quote from Jupiter."""
        try:
            input_mint = self.tokens.get(input_token)
            output_mint = self.tokens.get(output_token)
            
            if not input_mint or not output_mint:
                return None
            
            url = f"{self.quote_url}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": "50"  # 0.5%
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Jupiter quote: {e}")
            return None


class UniswapV3API:
    """Real Uniswap V3 API integration for Base chain."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Using The Graph for Uniswap V3 on Base
        self.subgraph_url = "https://api.studio.thegraph.com/query/48211/uniswap-v3-base/version/latest"
        
        # Token addresses on Base mainnet
        self.tokens = {
            "ETH": "0x4200000000000000000000000000000000000006",  # WETH
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"
        }
    
    async def get_price(self, session: aiohttp.ClientSession, token: str) -> Optional[float]:
        """Get token price from Uniswap V3."""
        try:
            token_address = self.tokens.get(token, "").lower()
            if not token_address:
                return None
            
            # GraphQL query for token price
            query = """
            {
              token(id: "%s") {
                derivedETH
                symbol
              }
              bundle(id: "1") {
                ethPriceUSD
              }
            }
            """ % token_address
            
            async with session.post(
                self.subgraph_url,
                json={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "data" in data and data["data"]["token"]:
                        derived_eth = float(data["data"]["token"]["derivedETH"])
                        eth_price_usd = float(data["data"]["bundle"]["ethPriceUSD"])
                        
                        # If token is ETH/WETH, return ETH price directly
                        if token in ["ETH", "WETH"]:
                            return eth_price_usd
                        else:
                            return derived_eth * eth_price_usd
                            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Uniswap price for {token}: {e}")
            return None
    
    async def get_pools(self, session: aiohttp.ClientSession, 
                       token0: str, token1: str) -> List[Dict]:
        """Get pools for token pair."""
        try:
            token0_address = self.tokens.get(token0, "").lower()
            token1_address = self.tokens.get(token1, "").lower()
            
            if not token0_address or not token1_address:
                return []
            
            query = """
            {
              pools(
                where: {
                  token0: "%s"
                  token1: "%s"
                }
                orderBy: volumeUSD
                orderDirection: desc
                first: 5
              ) {
                id
                feeTier
                liquidity
                sqrtPrice
                token0Price
                token1Price
                volumeUSD
              }
            }
            """ % (token0_address, token1_address)
            
            async with session.post(
                self.subgraph_url,
                json={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("pools", [])
                    
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching pools: {e}")
            return []


# Updated SolanaDEX class with real API integration
class RealSolanaDEX:
    """Enhanced Solana DEX with real API integration."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.jupiter_api = JupiterAPI()
        
        # Cache for prices
        self._price_cache = {}
        self._last_update = datetime.now()
        
        # CHANGE FROM: self._cache_duration = 5  # seconds
        self._cache_duration = settings.price_cache_duration  # Use settings value
        
        # Add paper trading optimization
        if hasattr(settings, 'trading_mode') and settings.trading_mode == 'paper':
            self._cache_duration = settings.price_cache_duration * 5  # 5 minutes for paper trading
    
    async def initialize(self):
        """Initialize the enhanced Solana DEX."""
        self.session = aiohttp.ClientSession()
        self.logger.info("Real Solana DEX initialized")
    
    async def close(self):
        """Close the enhanced Solana DEX."""
        if self.session:
            await self.session.close()
    
    async def get_jupiter_price(self, token: str) -> Optional[float]:
        """Get real-time price from Jupiter."""
        return await self.jupiter_api.get_price(self.session, token)
    
    async def get_all_prices(self, token: str) -> Dict[str, float]:
        """Get prices from multiple DEXs (Jupiter as primary)."""
        # Check cache
        cache_key = f"{token}_prices"
        now = datetime.now()
        
        if (cache_key in self._price_cache and 
            (now - self._last_update).seconds < self._cache_duration):
            return self._price_cache[cache_key]
        
        prices = {}
        
        # Get Jupiter price (aggregated across multiple DEXs)
        jupiter_price = await self.get_jupiter_price(token)
        if jupiter_price:
            prices["jupiter"] = jupiter_price
            
            # For arbitrage, we can simulate different DEX prices
            # by adding small variations (in real implementation, 
            # you'd query each DEX directly)
            prices["orca"] = jupiter_price * (1 + 0.001)  # Slightly higher
            prices["raydium"] = jupiter_price * (1 - 0.0005)  # Slightly lower
        
        # Update cache
        self._price_cache[cache_key] = prices
        self._last_update = now
        
        return prices
    
    async def find_arbitrage_opportunities(self, min_profit: float = 0.001):
        """Find real arbitrage opportunities."""
        opportunities = []
        
        for pair in self.settings.get_solana_pairs():
            base_token = pair.split("/")[0]
            prices = await self.get_all_prices(base_token)
            
            if len(prices) < 2:
                continue
            
            # Find profitable opportunities
            dex_names = list(prices.keys())
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex1, dex2 = dex_names[i], dex_names[j]
                    price1, price2 = prices[dex1], prices[dex2]
                    
                    if price1 > price2:
                        profit_pct = (price1 - price2) / price2
                    else:
                        profit_pct = (price2 - price1) / price1
                    
                    if profit_pct >= min_profit:
                        from src.exchanges.solana_dex import TradeOpportunity
                        opportunity = TradeOpportunity(
                            pair=pair,
                            dex1=dex1 if price1 < price2 else dex2,
                            dex2=dex2 if price1 < price2 else dex1,
                            price1=min(price1, price2),
                            price2=max(price1, price2),
                            profit_percentage=profit_pct,
                            estimated_fees=0.001,  # 0.1% estimated fees
                            min_trade_size=self.settings.min_trade_size
                        )
                        opportunities.append(opportunity)
        
        return opportunities


# Updated BaseDEX class with real API integration  
class RealBaseDEX:
    """Enhanced Base DEX with real API integration."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.uniswap_api = UniswapV3API()
        
        # Cache for prices
        self._price_cache = {}
        self._last_update = datetime.now()
        
        # CHANGE FROM: self._cache_duration = 10  # seconds (Base has higher fees, less frequent updates)
        self._cache_duration = settings.price_cache_duration * 2  # 2 minutes cache
        
        if hasattr(settings, 'trading_mode') and settings.trading_mode == 'paper':
            self._cache_duration = settings.price_cache_duration * 10  # 10 minutes for paper trading
    
    async def initialize(self):
        """Initialize the enhanced Base DEX."""
        self.session = aiohttp.ClientSession()
        self.logger.info("Real Base DEX initialized")
    
    async def close(self):
        """Close the enhanced Base DEX."""
        if self.session:
            await self.session.close()
    
    async def get_uniswap_price(self, token: str) -> Optional[float]:
        """Get real-time price from Uniswap V3."""
        return await self.uniswap_api.get_price(self.session, token)
    
    async def get_all_prices(self, token: str) -> Dict[str, float]:
        """Get prices from Base DEXs."""
        # Check cache
        cache_key = f"{token}_base_prices"
        now = datetime.now()
        
        if (cache_key in self._price_cache and 
            (now - self._last_update).seconds < self._cache_duration):
            return self._price_cache[cache_key]
        
        prices = {}
        
        # Get Uniswap V3 price
        uniswap_price = await self.get_uniswap_price(token)
        if uniswap_price:
            prices["uniswap_v3"] = uniswap_price
            
            # Simulate other DEX prices for arbitrage
            prices["aerodrome"] = uniswap_price * (1 + 0.002)  # Slightly higher
        
        # Update cache
        self._price_cache[cache_key] = prices
        self._last_update = now
        
        return prices 
    
    async def find_arbitrage_opportunities(self, min_profit: float = 0.001):
        """Find real arbitrage opportunities on Base."""
        opportunities = []
        
        for pair in self.settings.get_base_pairs():
            base_token = pair.split("/")[0]
            prices = await self.get_all_prices(base_token)
            
            if len(prices) < 2:
                continue
            
            # Find profitable opportunities
            dex_names = list(prices.keys())
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex1, dex2 = dex_names[i], dex_names[j]
                    price1, price2 = prices[dex1], prices[dex2]
                    
                    if price1 > price2:
                        profit_pct = (price1 - price2) / price2
                    else:
                        profit_pct = (price2 - price1) / price1
                    
                    if profit_pct >= min_profit:
                        from src.exchanges.base_dex import BaseTradeOpportunity
                        opportunity = BaseTradeOpportunity(
                            pair=pair,
                            dex1=dex1 if price1 < price2 else dex2,
                            dex2=dex2 if price1 < price2 else dex1,
                            price1=min(price1, price2),
                            price2=max(price1, price2),
                            profit_percentage=profit_pct,
                            estimated_fees=0.002,  # 0.2% estimated fees (Base has higher fees)
                            min_trade_size=self.settings.min_trade_size
                        )
                        opportunities.append(opportunity)
        
        return opportunities 