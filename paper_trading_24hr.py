#!/usr/bin/env python3
"""
24-Hour Paper Trading Bot with Real Multi-DEX Arbitrage
This script runs extended paper trading using real Solana DEX arbitrage opportunities.
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Import the new multi-DEX scanner
from src.exchanges.real_solana_multi_dex import RealSolanaMultiDEX, ArbitrageOpportunity

# Setup logging with rotation
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Setup logging with rotation (10MB max file size, keep 5 files)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/paper_trading_24hr.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExtendedPaperTradingBot:
    """Extended paper trading bot for 24-hour testing with real multi-DEX arbitrage."""
    
    def __init__(self, config_file="paper_trading.env"):
        load_dotenv(config_file)
        
        # Paper trading settings with gradual scaling
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
        self.hourly_stats = {}
        
        # Scaling parameters
        self.current_phase = 1
        self.phases = {
            1: {"duration_hours": 2, "min_trade_size": 50, "max_position_size": 0.1},   # Conservative start
            2: {"duration_hours": 4, "min_trade_size": 75, "max_position_size": 0.15},  # Moderate
            3: {"duration_hours": 6, "min_trade_size": 100, "max_position_size": 0.2},  # Normal
            4: {"duration_hours": 12, "min_trade_size": 150, "max_position_size": 0.25} # Aggressive
        }
        
        # Initialize the real multi-DEX scanner
        self.multi_dex_scanner = RealSolanaMultiDEX()
        
        # Supported tokens for arbitrage
        self.supported_tokens = ["SOL", "RAY", "ORCA"]
        
        logger.info(f"24-Hour Paper Trading Bot initialized with ${self.portfolio_value} portfolio")
        logger.info(f"Using Real Multi-DEX Arbitrage Scanner (Jupiter, Orca, Raydium, Meteora, Saber)")
        logger.info(f"Starting Phase 1: Conservative settings")
    
    def update_phase_settings(self, phase):
        """Update trading parameters based on current phase."""
        if phase in self.phases:
            phase_config = self.phases[phase]
            self.min_trade_size = phase_config["min_trade_size"]
            self.max_position_size = phase_config["max_position_size"]
            logger.info(f"Switching to Phase {phase}: Trade size ${self.min_trade_size}, Position size {self.max_position_size:.0%}")
    
    async def get_real_arbitrage_opportunities(self):
        """Get real arbitrage opportunities from multi-DEX scanner."""
        try:
            # Initialize the scanner if not already done
            if not hasattr(self, '_scanner_initialized'):
                await self.multi_dex_scanner.initialize()
                self._scanner_initialized = True
            
            all_opportunities = []
            
            # Scan all supported tokens for arbitrage opportunities
            for token in self.supported_tokens:
                try:
                    opportunities = await self.multi_dex_scanner.scan_all_dexs(token)
                    all_opportunities.extend(opportunities)
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities for {token}")
                except Exception as e:
                    logger.error(f"Error scanning {token}: {e}")
            
            # Convert to the format expected by the trading bot
            formatted_opportunities = []
            for opp in all_opportunities:
                if opp.profit_percentage >= self.min_arbitrage_profit and opp.confidence_score > 0.3:
                    formatted_opportunities.append({
                        "token": opp.token_pair.split('/')[0],
                        "buy_exchange": opp.buy_dex.dex_name.title(),
                        "sell_exchange": opp.sell_dex.dex_name.title(),
                        "buy_price": opp.buy_dex.price,
                        "sell_price": opp.sell_dex.price,
                        "profit_pct": opp.profit_percentage,
                        "estimated_profit": opp.estimated_profit,
                        "confidence_score": opp.confidence_score,
                        "required_capital": opp.required_capital,
                        "liquidity": min(opp.buy_dex.liquidity, opp.sell_dex.liquidity)
                    })
            
            # Sort by profit percentage
            formatted_opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)
            
            logger.info(f"Total real arbitrage opportunities found: {len(formatted_opportunities)}")
            return formatted_opportunities
            
        except Exception as e:
            logger.error(f"Error getting real arbitrage opportunities: {e}")
            return []
    
    async def get_token_prices(self, session):
        """Get current token prices from real DEXs (for compatibility)."""
        try:
            # Use the multi-DEX scanner to get current prices
            if not hasattr(self, '_scanner_initialized'):
                await self.multi_dex_scanner.initialize()
                self._scanner_initialized = True
            
            prices = {}
            for token in self.supported_tokens:
                try:
                    # Get Jupiter price as reference
                    jupiter_price = await self.multi_dex_scanner._get_jupiter_aggregated_price(token)
                    if jupiter_price:
                        prices[token] = jupiter_price.price
                except Exception as e:
                    logger.error(f"Error getting {token} price: {e}")
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return None
    
    def calculate_arbitrage_opportunities(self, prices):
        """Calculate potential arbitrage opportunities (legacy method - now uses real data)."""
        # This method is kept for compatibility but now returns empty list
        # Real arbitrage opportunities are handled by get_real_arbitrage_opportunities()
        return []
    
    def execute_paper_trade(self, opportunity):
        """Execute a paper trade with real arbitrage data."""
        trade_id = f"trade_{self.total_trades + 1}_{int(time.time())}"
        
        # Calculate position size based on confidence and liquidity
        confidence_score = opportunity.get("confidence_score", 0.5)
        liquidity = opportunity.get("liquidity", 0)
        
        # Adjust position size based on confidence and liquidity
        base_position_size = min(self.min_trade_size, self.portfolio_value * self.max_position_size)
        confidence_multiplier = min(1.5, confidence_score * 2)  # Max 1.5x for high confidence
        liquidity_multiplier = min(1.2, liquidity / 100000)  # Max 1.2x for high liquidity
        
        position_size = base_position_size * confidence_multiplier * liquidity_multiplier
        
        # Simulate trade execution with slippage and fees
        estimated_profit = opportunity["estimated_profit"]
        slippage_factor = 0.95  # 5% slippage
        fee_factor = 0.99  # 1% fees
        actual_profit = estimated_profit * slippage_factor * fee_factor
        
        # Update portfolio
        self.portfolio_value += actual_profit
        self.daily_pnl += actual_profit
        self.total_trades += 1
        
        if actual_profit > 0:
            self.winning_trades += 1
        
        # Record trade with enhanced data
        trade_record = {
            "id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase,
            "token": opportunity["token"],
            "buy_exchange": opportunity["buy_exchange"],
            "sell_exchange": opportunity["sell_exchange"],
            "buy_price": opportunity["buy_price"],
            "sell_price": opportunity["sell_price"],
            "position_size": position_size,
            "estimated_profit": estimated_profit,
            "actual_profit": actual_profit,
            "profit_pct": opportunity["profit_pct"],
            "confidence_score": confidence_score,
            "liquidity": liquidity,
            "required_capital": opportunity.get("required_capital", 0)
        }
        
        self.positions[trade_id] = trade_record
        
        logger.info(f"PAPER TRADE [Phase {self.current_phase}]: {opportunity['token']} "
                   f"({opportunity['buy_exchange']} -> {opportunity['sell_exchange']}) "
                   f"Profit: ${actual_profit:.2f} ({opportunity['profit_pct']:.3%}) "
                   f"Confidence: {confidence_score:.2f} Liquidity: ${liquidity:,.0f}")
        
        return trade_record
    
    def print_hourly_summary(self, hour):
        """Print hourly performance summary."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        logger.info("=" * 80)
        logger.info(f"HOUR {hour} SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Portfolio Value: ${self.portfolio_value:.2f}")
        logger.info(f"Daily PnL: ${self.daily_pnl:.2f}")
        logger.info(f"Total Trades: {self.total_trades}")
        logger.info(f"Winning Trades: {self.winning_trades}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Total Return: {((self.portfolio_value - 5000) / 5000 * 100):.2f}%")
        logger.info(f"Current Phase: {self.current_phase}")
        logger.info(f"Trade Size: ${self.min_trade_size}")
        logger.info(f"Position Size: {self.max_position_size:.0%}")
        logger.info("=" * 80)
        
        # Save hourly stats
        self.hourly_stats[hour] = {
            "portfolio_value": self.portfolio_value,
            "daily_pnl": self.daily_pnl,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": win_rate,
            "total_return_pct": (self.portfolio_value - 5000) / 5000 * 100,
            "current_phase": self.current_phase
        }
    
    def should_advance_phase(self, elapsed_hours):
        """Determine if we should advance to the next phase."""
        if self.current_phase < 4:
            phase_config = self.phases[self.current_phase]
            if elapsed_hours >= phase_config["duration_hours"]:
                # Check if performance is good enough to advance
                win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                total_return_pct = (self.portfolio_value - 5000) / 5000 * 100
                
                # Advance if win rate > 60% and positive return
                if win_rate > 60 and total_return_pct > 0:
                    return True
                else:
                    logger.warning(f"Performance criteria not met for phase advancement. Win rate: {win_rate:.1f}%, Return: {total_return_pct:.2f}%")
        
        return False
    
    async def run_24hr_paper_trading(self):
        """Run 24-hour paper trading simulation with gradual scaling."""
        logger.info("Starting 24-Hour Paper Trading Simulation")
        logger.info(f"Starting Portfolio: ${self.portfolio_value}")
        logger.info(f"Min Profit Threshold: {self.min_arbitrage_profit:.3%}")
        
        start_time = time.time()
        end_time = start_time + (24 * 60 * 60)  # 24 hours
        
        # Initialize phase settings
        self.update_phase_settings(1)
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                try:
                    elapsed_hours = (time.time() - start_time) / 3600
                    
                    # Check if we should advance phases
                    if self.should_advance_phase(elapsed_hours):
                        self.current_phase += 1
                        self.update_phase_settings(self.current_phase)
                    
                    # Get real arbitrage opportunities from multi-DEX scanner
                    opportunities = await self.get_real_arbitrage_opportunities()
                    
                    # Execute trades for profitable opportunities
                    for opportunity in opportunities:
                        if self.daily_pnl > -(self.portfolio_value * self.max_daily_loss):
                            # Add confidence score to opportunity for better decision making
                            if opportunity.get("confidence_score", 0) > 0.3:
                                self.execute_paper_trade(opportunity)
                        else:
                            logger.warning("Daily loss limit reached, stopping trades")
                            break
                    
                    # Print hourly summary
                    current_hour = int(elapsed_hours)
                    if current_hour > 0 and current_hour not in self.hourly_stats:
                        self.print_hourly_summary(current_hour)
                    
                    # Wait before next scan (30 seconds)
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(60)
        
        # Final summary
        logger.info("24-Hour Paper Trading Simulation Complete!")
        self.print_hourly_summary(24)
        
        # Save comprehensive results
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
            "final_phase": self.current_phase,
            "hourly_stats": self.hourly_stats,
            "trades": list(self.positions.values())
        }
        
        with open("paper_trading_24hr_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("Results saved to paper_trading_24hr_results.json")
        
        # Print final recommendations
        self.print_final_recommendations(results)
    
    def print_final_recommendations(self, results):
        """Print final recommendations based on results."""
        logger.info("=" * 80)
        logger.info("FINAL RECOMMENDATIONS")
        logger.info("=" * 80)
        
        win_rate = results["win_rate"]
        total_return_pct = results["total_return_pct"]
        total_trades = results["total_trades"]
        
        if win_rate >= 70 and total_return_pct >= 5:
            logger.info("EXCELLENT PERFORMANCE - Ready for live trading!")
            logger.info("Recommendation: Start with $100-200 live trading")
        elif win_rate >= 60 and total_return_pct >= 2:
            logger.info("GOOD PERFORMANCE - Consider live trading with caution")
            logger.info("Recommendation: Start with $50-100 live trading")
        elif win_rate >= 50 and total_return_pct >= 0:
            logger.info("ACCEPTABLE PERFORMANCE - Needs optimization")
            logger.info("Recommendation: Adjust parameters and retest")
        else:
            logger.info("POOR PERFORMANCE - Needs significant improvement")
            logger.info("Recommendation: Review strategy and parameters")
        
        logger.info(f"Key Metrics:")
        logger.info(f"  - Win Rate: {win_rate:.1f}%")
        logger.info(f"  - Total Return: {total_return_pct:.2f}%")
        logger.info(f"  - Total Trades: {total_trades}")
        logger.info(f"  - Final Phase: {results['final_phase']}")
        logger.info("=" * 80)

async def main():
    """Main entry point."""
    bot = ExtendedPaperTradingBot()
    try:
        await bot.run_24hr_paper_trading()
    finally:
        # Clean up the multi-DEX scanner
        if hasattr(bot, 'multi_dex_scanner'):
            await bot.multi_dex_scanner.close()
            logger.info("Multi-DEX scanner closed successfully")

if __name__ == "__main__":
    asyncio.run(main()) 