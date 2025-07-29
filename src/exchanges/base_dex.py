"""
Base chain DEX integration for Uniswap V3 and Aerodrome.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.config.settings import Settings


@dataclass
class BasePriceData:
    """Price data structure for Base tokens."""
    token: str
    price: float
    volume_24h: float
    dex: str
    timestamp: datetime


@dataclass
class BaseTradeOpportunity:
    """Arbitrage opportunity structure for Base."""
    pair: str
    dex1: str
    dex2: str
    price1: float
    price2: float
    profit_percentage: float
    estimated_fees: float
    min_trade_size: float


class BaseDEX:
    """Base chain DEX integration for price data and trading."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Uniswap V3 API endpoints
        self.uniswap_v3_url = settings.uniswap_v3_api_url
        
        # Token addresses (Base mainnet)
        self.token_addresses = {
            "ETH": "0x4200000000000000000000000000000000000006",  # WETH on Base
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"
        }
        
        # Price cache
        self._price_cache: Dict[str, BasePriceData] = {}
        self._last_update = datetime.now()
    
    async def initialize(self):
        """Initialize the Base DEX client."""
        self.session = aiohttp.ClientSession()
        self.logger.info("Base DEX client initialized")
    
    async def close(self):
        """Close the Base DEX client."""
        if self.session:
            await self.session.close()
        self.logger.info("Base DEX client closed")
    
    async def get_uniswap_v3_price(self, token: str) -> Optional[float]:
        """Get token price from Uniswap V3 on Base."""
        try:
            if not self.session:
                return None
            
            token_address = self.token_addresses.get(token)
            if not token_address:
                self.logger.warning(f"Unknown token: {token}")
                return None
            
            # GraphQL query for Uniswap V3 price
            query = """
            {
                token(id: "%s") {
                    derivedETH
                }
                bundle(id: "1") {
                    ethPrice
                }
            }
            """ % token_address.lower()
            
            async with self.session.post(
                self.uniswap_v3_url,
                json={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data", {}).get("token"):
                        derived_eth = float(data["data"]["token"]["derivedETH"])
                        eth_price = float(data["data"]["bundle"]["ethPrice"])
                        return derived_eth * eth_price
                
                self.logger.warning(f"Failed to get Uniswap V3 price for {token}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting Uniswap V3 price for {token}: {e}")
            return None
    
    async def get_aerodrome_price(self, token: str) -> Optional[float]:
        """Get token price from Aerodrome DEX."""
        try:
            if not self.session:
                return None
            
            # Aerodrome API endpoint (simplified)
            # In practice, you'd need to query Aerodrome's specific pools
            aerodrome_url = f"https://api.aerodrome.fi/v1/pools/{token}/price"
            async with self.session.get(aerodrome_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get("price", 0))
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting Aerodrome price for {token}: {e}")
            return None
    
    async def get_all_prices(self, token: str) -> Dict[str, float]:
        """Get prices from all DEXs for a token."""
        prices = {}
        
        # Get prices concurrently
        tasks = [
            self.get_uniswap_v3_price(token),
            self.get_aerodrome_price(token)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        dex_names = ["uniswap_v3", "aerodrome"]
        for i, result in enumerate(results):
            if isinstance(result, (int, float)) and result > 0:
                prices[dex_names[i]] = result
        
        return prices
    
    async def find_arbitrage_opportunities(self, 
                                         min_profit: float = 0.001) -> List[BaseTradeOpportunity]:
        """Find arbitrage opportunities across Base DEXs."""
        opportunities = []
        
        # Check each trading pair
        for pair in self.settings.get_base_pairs():
            base_token = pair.split("/")[0]
            
            # Get prices from all DEXs
            prices = await self.get_all_prices(base_token)
            
            if len(prices) < 2:
                continue
            
            # Find price differences
            dex_names = list(prices.keys())
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex1, dex2 = dex_names[i], dex_names[j]
                    price1, price2 = prices[dex1], prices[dex2]
                    
                    # Calculate profit percentage
                    if price1 > price2:
                        profit_pct = (price1 - price2) / price2
                        buy_dex, sell_dex = dex2, dex1
                        buy_price, sell_price = price2, price1
                    else:
                        profit_pct = (price2 - price1) / price1
                        buy_dex, sell_dex = dex1, dex2
                        buy_price, sell_price = price1, price2
                    
                    # Check if profit exceeds minimum
                    if profit_pct >= min_profit:
                        # Estimate fees (simplified)
                        estimated_fees = 0.003  # 0.3% estimated fees for Base
                        
                        opportunity = BaseTradeOpportunity(
                            pair=pair,
                            dex1=buy_dex,
                            dex2=sell_dex,
                            price1=buy_price,
                            price2=sell_price,
                            profit_percentage=profit_pct,
                            estimated_fees=estimated_fees,
                            min_trade_size=self.settings.min_trade_size
                        )
                        
                        opportunities.append(opportunity)
        
        return opportunities
    
    async def execute_trade(self, 
                          pair: str,
                          side: str,
                          amount: float,
                          dex: str = "uniswap_v3") -> Optional[str]:
        """Execute a trade on the specified DEX."""
        try:
            # This is a simplified implementation
            # In practice, you'd need to implement actual trade execution
            self.logger.info(f"Executing {side} trade for {amount} {pair} on {dex}")
            
            # Simulate trade execution
            trade_id = f"{dex}_{pair}_{side}_{datetime.now().timestamp()}"
            
            # In a real implementation, you would:
            # 1. Get quote from DEX
            # 2. Build transaction
            # 3. Sign and send transaction
            # 4. Wait for confirmation
            
            return trade_id
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
    
    async def get_quote(self, 
                       input_token: str,
                       output_token: str,
                       amount: float,
                       dex: str = "uniswap_v3") -> Optional[Dict]:
        """Get a quote for a trade."""
        try:
            if not self.session:
                return None
            
            input_address = self.token_addresses.get(input_token)
            output_address = self.token_addresses.get(output_token)
            
            if not input_address or not output_address:
                return None
            
            # Get quote from Uniswap V3
            query = """
            {
                quote(inputToken: "%s", outputToken: "%s", amount: "%s", fee: 3000) {
                    amountOut
                    priceImpact
                    gasEstimate
                }
            }
            """ % (input_address.lower(), output_address.lower(), str(int(amount * 1e6)))
            
            async with self.session.post(
                self.uniswap_v3_url,
                json={"query": query}
            ) as response:
                if response.status == 200:
                    return await response.json()
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting quote: {e}")
            return None
    
    async def get_gas_estimate(self) -> Optional[float]:
        """Get current gas price estimate for Base."""
        try:
            if not self.session:
                return None
            
            # Get gas price from Base RPC
            gas_url = f"{self.settings.base_rpc_url}"
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_gasPrice",
                "params": [],
                "id": 1
            }
            
            async with self.session.post(gas_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("result"):
                        gas_price_wei = int(data["result"], 16)
                        gas_price_gwei = gas_price_wei / 1e9
                        return gas_price_gwei
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting gas estimate: {e}")
            return None 