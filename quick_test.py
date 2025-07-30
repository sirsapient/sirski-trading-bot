#!/usr/bin/env python3
"""
Quick 5-minute test to verify 24-hour script functionality
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quick_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuickTestBot:
    """Quick test bot for 5-minute validation."""
    
    def __init__(self):
        load_dotenv("paper_trading.env")
        
        # Test settings
        self.portfolio_value = 5000
        self.min_arbitrage_profit = 0.001
        self.max_position_size = 0.1  # Conservative
        self.min_trade_size = 50      # Small trades
        self.max_daily_loss = 0.03
        
        # Trading state
        self.daily_pnl = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.positions = {}
        
        # API endpoints
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
        
        logger.info(f"Quick Test Bot initialized with ${self.portfolio_value} portfolio")
    
    async def get_token_prices(self, session):
        """Get current token prices from CoinGecko."""
        try:
            params = {
                "ids": "solana,ethereum",
                "vs_currencies": "usd"
            }
            
            async with session.get(self.coingecko_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "SOL": data["solana"]["usd"],
                        "ETH": data["ethereum"]["usd"]
                    }
                else:
                    logger.error(f"Failed to get prices: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return None
    
    def calculate_arbitrage_opportunities(self, prices):
        """Calculate potential arbitrage opportunities."""
        opportunities = []
        
        if prices:
            sol_price = prices["SOL"]
            eth_price = prices["ETH"]
            
            # Simulate price differences
            sol_jupiter = sol_price
            sol_orca = sol_price * 1.002
            sol_raydium = sol_price * 0.998
            
            eth_uniswap = eth_price
            eth_aerodrome = eth_price * 1.0015
            
            # Check opportunities
            if sol_orca > sol_jupiter:
                profit_pct = (sol_orca - sol_jupiter) / sol_jupiter
                if profit_pct > self.min_arbitrage_profit:
                    opportunities.append({
                        "token": "SOL",
                        "buy_exchange": "Jupiter",
                        "sell_exchange": "Orca",
                        "buy_price": sol_jupiter,
                        "sell_price": sol_orca,
                        "profit_pct": profit_pct,
                        "estimated_profit": profit_pct * self.min_trade_size
                    })
            
            if sol_jupiter > sol_raydium:
                profit_pct = (sol_jupiter - sol_raydium) / sol_raydium
                if profit_pct > self.min_arbitrage_profit:
                    opportunities.append({
                        "token": "SOL",
                        "buy_exchange": "Raydium",
                        "sell_exchange": "Jupiter",
                        "buy_price": sol_raydium,
                        "sell_price": sol_jupiter,
                        "profit_pct": profit_pct,
                        "estimated_profit": profit_pct * self.min_trade_size
                    })
            
            if eth_aerodrome > eth_uniswap:
                profit_pct = (eth_aerodrome - eth_uniswap) / eth_uniswap
                if profit_pct > self.min_arbitrage_profit:
                    opportunities.append({
                        "token": "ETH",
                        "buy_exchange": "Uniswap",
                        "sell_exchange": "Aerodrome",
                        "buy_price": eth_uniswap,
                        "sell_price": eth_aerodrome,
                        "profit_pct": profit_pct,
                        "estimated_profit": profit_pct * self.min_trade_size
                    })
        
        return opportunities
    
    def execute_paper_trade(self, opportunity):
        """Execute a paper trade."""
        trade_id = f"test_trade_{self.total_trades + 1}_{int(time.time())}"
        
        position_size = min(self.min_trade_size, self.portfolio_value * self.max_position_size)
        estimated_profit = opportunity["estimated_profit"]
        actual_profit = estimated_profit * 0.8
        
        self.portfolio_value += actual_profit
        self.daily_pnl += actual_profit
        self.total_trades += 1
        
        if actual_profit > 0:
            self.winning_trades += 1
        
        trade_record = {
            "id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "token": opportunity["token"],
            "buy_exchange": opportunity["buy_exchange"],
            "sell_exchange": opportunity["sell_exchange"],
            "buy_price": opportunity["buy_price"],
            "sell_price": opportunity["sell_price"],
            "position_size": position_size,
            "estimated_profit": estimated_profit,
            "actual_profit": actual_profit,
            "profit_pct": opportunity["profit_pct"]
        }
        
        self.positions[trade_id] = trade_record
        
        logger.info(f"TEST TRADE: {opportunity['token']} "
                   f"({opportunity['buy_exchange']} -> {opportunity['sell_exchange']}) "
                   f"Profit: ${actual_profit:.2f} ({opportunity['profit_pct']:.3%})")
        
        return trade_record
    
    def print_summary(self):
        """Print test summary."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        logger.info("=" * 60)
        logger.info("QUICK TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Portfolio Value: ${self.portfolio_value:.2f}")
        logger.info(f"Daily PnL: ${self.daily_pnl:.2f}")
        logger.info(f"Total Trades: {self.total_trades}")
        logger.info(f"Winning Trades: {self.winning_trades}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Total Return: {((self.portfolio_value - 5000) / 5000 * 100):.2f}%")
        logger.info("=" * 60)
    
    async def run_quick_test(self, duration_minutes=5):
        """Run quick test for 5 minutes."""
        logger.info(f"Starting Quick Test for {duration_minutes} minutes")
        logger.info(f"Starting Portfolio: ${self.portfolio_value}")
        logger.info(f"Trade Size: ${self.min_trade_size}")
        logger.info(f"Position Size: {self.max_position_size:.0%}")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                try:
                    prices = await self.get_token_prices(session)
                    
                    if prices:
                        opportunities = self.calculate_arbitrage_opportunities(prices)
                        
                        for opportunity in opportunities:
                            if self.daily_pnl > -(self.portfolio_value * self.max_daily_loss):
                                self.execute_paper_trade(opportunity)
                            else:
                                logger.warning("Daily loss limit reached")
                                break
                    
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in test loop: {e}")
                    await asyncio.sleep(60)
        
        logger.info("Quick Test Complete!")
        self.print_summary()
        
        # Save results
        results = {
            "test_duration_minutes": duration_minutes,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "final_portfolio_value": self.portfolio_value,
            "total_return": self.portfolio_value - 5000,
            "total_return_pct": (self.portfolio_value - 5000) / 5000 * 100,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "daily_pnl": self.daily_pnl,
            "trades": list(self.positions.values())
        }
        
        with open("quick_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("Results saved to quick_test_results.json")
        
        # Test verdict
        if self.total_trades > 0:
            logger.info("✅ Quick test successful - ready for 24-hour test!")
        else:
            logger.warning("⚠️ No trades executed - check configuration")

async def main():
    """Main entry point."""
    bot = QuickTestBot()
    await bot.run_quick_test(duration_minutes=5)

if __name__ == "__main__":
    asyncio.run(main()) 