#!/usr/bin/env python3
"""
Simplified Paper Trading Demo
This script demonstrates paper trading functionality without complex dependencies.
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaperTradingBot:
    """Simplified paper trading bot for demonstration."""
    
    def __init__(self, config_file="paper_trading.env"):
        load_dotenv(config_file)
        
        # Paper trading settings
        self.portfolio_value = 5000  # $5000 starting portfolio
        self.min_arbitrage_profit = float(os.getenv("MIN_ARBITRAGE_PROFIT", "0.001"))
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", "0.2"))
        self.min_trade_size = float(os.getenv("MIN_TRADE_SIZE", "100"))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", "0.03"))
        
        # Trading state
        self.daily_pnl = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.positions = {}
        
        # API endpoints
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
        
        logger.info(f"Paper Trading Bot initialized with ${self.portfolio_value} portfolio")
    
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
        
        # Simulate price differences between exchanges
        if prices:
            sol_price = prices["SOL"]
            eth_price = prices["ETH"]
            
            # Simulate different prices on different DEXs
            sol_jupiter = sol_price
            sol_orca = sol_price * 1.002  # 0.2% higher
            sol_raydium = sol_price * 0.998  # 0.2% lower
            
            eth_uniswap = eth_price
            eth_aerodrome = eth_price * 1.0015  # 0.15% higher
            
            # Check SOL arbitrage opportunities
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
            
            # Check ETH arbitrage opportunities
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
        trade_id = f"trade_{self.total_trades + 1}_{int(time.time())}"
        
        # Calculate position size
        position_size = min(self.min_trade_size, self.portfolio_value * self.max_position_size)
        
        # Simulate trade execution
        estimated_profit = opportunity["estimated_profit"]
        actual_profit = estimated_profit * 0.8  # 80% of estimated profit (realistic)
        
        # Update portfolio
        self.portfolio_value += actual_profit
        self.daily_pnl += actual_profit
        self.total_trades += 1
        
        if actual_profit > 0:
            self.winning_trades += 1
        
        # Record trade
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
        
        logger.info(f"📈 Paper Trade Executed: {opportunity['token']} "
                   f"({opportunity['buy_exchange']} → {opportunity['sell_exchange']}) "
                   f"Profit: ${actual_profit:.2f} ({opportunity['profit_pct']:.3%})")
        
        return trade_record
    
    def print_portfolio_summary(self):
        """Print current portfolio status."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 PORTFOLIO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"💰 Portfolio Value: ${self.portfolio_value:.2f}")
        logger.info(f"📈 Daily PnL: ${self.daily_pnl:.2f}")
        logger.info(f"🔄 Total Trades: {self.total_trades}")
        logger.info(f"✅ Winning Trades: {self.winning_trades}")
        logger.info(f"📊 Win Rate: {win_rate:.1f}%")
        logger.info(f"📈 Total Return: {((self.portfolio_value - 5000) / 5000 * 100):.2f}%")
        logger.info("=" * 60)
    
    async def run_paper_trading(self, duration_minutes=30):
        """Run paper trading simulation."""
        logger.info(f"🚀 Starting Paper Trading Simulation for {duration_minutes} minutes")
        logger.info(f"💰 Starting Portfolio: ${self.portfolio_value}")
        logger.info(f"🎯 Min Profit Threshold: {self.min_arbitrage_profit:.3%}")
        logger.info(f"📊 Max Position Size: {self.max_position_size:.0%}")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                try:
                    # Get current prices
                    prices = await self.get_token_prices(session)
                    
                    if prices:
                        # Find arbitrage opportunities
                        opportunities = self.calculate_arbitrage_opportunities(prices)
                        
                        # Execute trades for profitable opportunities
                        for opportunity in opportunities:
                            if self.daily_pnl > -(self.portfolio_value * self.max_daily_loss):
                                self.execute_paper_trade(opportunity)
                            else:
                                logger.warning("⚠️ Daily loss limit reached, stopping trades")
                                break
                        
                        # Print summary every 5 minutes
                        if self.total_trades % 10 == 0 and self.total_trades > 0:
                            self.print_portfolio_summary()
                    
                    # Wait before next scan
                    await asyncio.sleep(30)  # 30 second intervals
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(60)
        
        # Final summary
        logger.info("🏁 Paper Trading Simulation Complete!")
        self.print_portfolio_summary()
        
        # Save results
        results = {
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
        
        with open("paper_trading_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("📄 Results saved to paper_trading_results.json")

async def main():
    """Main entry point."""
    bot = PaperTradingBot()
    await bot.run_paper_trading(duration_minutes=30)  # 30 minute simulation

if __name__ == "__main__":
    asyncio.run(main()) 