#!/usr/bin/env python3
"""
Main entry point for the crypto trading bot.
Supports paper trading and live trading modes.
"""

import asyncio
import argparse
import logging
from typing import Optional
from pathlib import Path

from src.config.settings import Settings
from src.utils.logger import setup_logging
from src.strategies.arbitrage import ArbitrageStrategy
from src.strategies.swing_trading import SwingTradingStrategy
from src.risk.manager import RiskManager
from src.utils.wallet import WalletManager


class TradingBot:
    """Main trading bot class that orchestrates all strategies."""
    
    def __init__(self, settings: Settings, mode: str = "paper"):
        self.settings = settings
        self.mode = mode
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.wallet_manager = WalletManager(settings)
        self.risk_manager = RiskManager(settings)
        self.arbitrage_strategy = ArbitrageStrategy(settings, self.risk_manager)
        self.swing_strategy = SwingTradingStrategy(settings, self.risk_manager)
        
        self.running = False
    
    async def start(self):
        """Start the trading bot."""
        self.logger.info(f"Starting trading bot in {self.mode} mode")
        self.running = True
        
        try:
            # Initialize wallet connections
            await self.wallet_manager.initialize()
            
            # Start both strategies concurrently
            await asyncio.gather(
                self.arbitrage_strategy.start(),
                self.swing_strategy.start()
            )
            
        except KeyboardInterrupt:
            self.logger.info("Shutting down trading bot...")
        except Exception as e:
            self.logger.error(f"Error in trading bot: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the trading bot."""
        self.running = False
        await self.arbitrage_strategy.stop()
        await self.swing_strategy.stop()
        self.logger.info("Trading bot stopped")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument(
        "--mode", 
        choices=["paper", "live"], 
        default="paper",
        help="Trading mode (paper or live)"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default=".env",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load settings
    settings = Settings.from_env_file(args.config)
    
    # Validate settings
    if args.mode == "live":
        if not settings.validate_live_trading():
            logger.error("Invalid configuration for live trading")
            return
    
    # Create and start trading bot
    bot = TradingBot(settings, args.mode)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main()) 