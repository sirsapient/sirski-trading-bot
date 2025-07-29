"""
High-frequency arbitrage strategy for Solana and Base DEXs.
"""

import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.config.settings import Settings
from src.risk.manager import RiskManager
from src.exchanges.solana_dex import SolanaDEX, TradeOpportunity
from src.exchanges.base_dex import BaseDEX, BaseTradeOpportunity
from src.utils.logger import TradeLogger


@dataclass
class ArbitrageSignal:
    """Arbitrage signal structure."""
    pair: str
    chain: str
    dex1: str
    dex2: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    estimated_fees: float
    confidence: float
    timestamp: datetime


class ArbitrageStrategy:
    """High-frequency arbitrage strategy."""
    
    def __init__(self, settings: Settings, risk_manager: RiskManager):
        self.settings = settings
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(__name__)
        self.trade_logger = TradeLogger("arbitrage_strategy")
        
        # Initialize DEX clients
        self.solana_dex = SolanaDEX(settings)
        self.base_dex = BaseDEX(settings)
        
        # Strategy state
        self.running = False
        self.last_scan = datetime.now()
        self.scan_interval = 5  # seconds
        self.min_profit_threshold = settings.min_arbitrage_profit
        
        # Performance tracking
        self.total_opportunities = 0
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_pnl = 0.0
        
        # Signal tracking
        self.recent_signals: List[ArbitrageSignal] = []
        self.max_signals_history = 100
    
    async def initialize(self):
        """Initialize the arbitrage strategy."""
        await self.solana_dex.initialize()
        await self.base_dex.initialize()
        self.logger.info("Arbitrage strategy initialized")
    
    async def start(self):
        """Start the arbitrage strategy."""
        self.running = True
        self.logger.info("Starting arbitrage strategy")
        
        try:
            await self.initialize()
            
            while self.running:
                await self.scan_for_opportunities()
                await asyncio.sleep(self.scan_interval)
                
        except Exception as e:
            self.logger.error(f"Error in arbitrage strategy: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the arbitrage strategy."""
        self.running = False
        await self.solana_dex.close()
        await self.base_dex.close()
        self.logger.info("Arbitrage strategy stopped")
    
    async def scan_for_opportunities(self):
        """Scan for arbitrage opportunities on both chains."""
        try:
            # Scan Solana opportunities
            solana_opportunities = await self.solana_dex.find_arbitrage_opportunities(
                min_profit=self.min_profit_threshold
            )
            
            # Scan Base opportunities
            base_opportunities = await self.base_dex.find_arbitrage_opportunities(
                min_profit=self.min_profit_threshold
            )
            
            # Process Solana opportunities
            for opp in solana_opportunities:
                await self.process_opportunity(opp, "solana")
            
            # Process Base opportunities
            for opp in base_opportunities:
                await self.process_opportunity(opp, "base")
            
            self.last_scan = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error scanning for opportunities: {e}")
    
    async def process_opportunity(self, opportunity, chain: str):
        """Process an arbitrage opportunity."""
        try:
            # Calculate confidence based on profit and volume
            confidence = min(1.0, opportunity.profit_percentage / 0.01)  # Scale to 1% max
            
            # Create signal
            signal = ArbitrageSignal(
                pair=opportunity.pair,
                chain=chain,
                dex1=opportunity.dex1,
                dex2=opportunity.dex2,
                buy_price=opportunity.price1,
                sell_price=opportunity.price2,
                profit_percentage=opportunity.profit_percentage,
                estimated_fees=opportunity.estimated_fees,
                confidence=confidence,
                timestamp=datetime.now()
            )
            
            # Log opportunity
            self.trade_logger.log_arbitrage_opportunity(
                pair=opportunity.pair,
                dex1=opportunity.dex1,
                dex2=opportunity.dex2,
                price1=opportunity.price1,
                price2=opportunity.price2,
                profit_percentage=opportunity.profit_percentage,
                estimated_fees=opportunity.estimated_fees
            )
            
            # Store signal
            self.recent_signals.append(signal)
            if len(self.recent_signals) > self.max_signals_history:
                self.recent_signals.pop(0)
            
            self.total_opportunities += 1
            
            # Check if we should execute
            if await self.should_execute_arbitrage(signal):
                await self.execute_arbitrage(signal)
            
        except Exception as e:
            self.logger.error(f"Error processing opportunity: {e}")
    
    async def should_execute_arbitrage(self, signal: ArbitrageSignal) -> bool:
        """Determine if we should execute an arbitrage trade."""
        try:
            # Check if profit exceeds fees significantly
            net_profit = signal.profit_percentage - signal.estimated_fees
            if net_profit < self.min_profit_threshold:
                return False
            
            # Check if we have sufficient portfolio value
            if self.risk_manager.portfolio_value < self.settings.min_trade_size:
                return False
            
            # Check daily loss limit
            if self.risk_manager.daily_pnl <= -(self.risk_manager.portfolio_value * self.settings.max_daily_loss):
                return False
            
            # Check if we already have a position in this pair
            if signal.pair in self.risk_manager.positions:
                return False
            
            # Check recent signals to avoid over-trading
            recent_signals = [s for s in self.recent_signals 
                            if s.pair == signal.pair and 
                            (datetime.now() - s.timestamp).seconds < 60]
            
            if len(recent_signals) > 3:  # Max 3 signals per minute per pair
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking execution conditions: {e}")
            return False
    
    async def execute_arbitrage(self, signal: ArbitrageSignal):
        """Execute an arbitrage trade."""
        try:
            self.logger.info(f"Executing arbitrage for {signal.pair} on {signal.chain}")
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                signal.pair,
                signal.buy_price,
                signal.confidence
            )
            
            if position_size <= 0:
                self.logger.warning("Invalid position size calculated")
                return
            
            # Execute buy order
            buy_trade_id = await self.execute_trade(
                signal.pair,
                "buy",
                position_size,
                signal.buy_price,
                signal.dex1,
                signal.chain
            )
            
            if not buy_trade_id:
                self.logger.error("Failed to execute buy order")
                return
            
            # Execute sell order
            sell_trade_id = await self.execute_trade(
                signal.pair,
                "sell",
                position_size,
                signal.sell_price,
                signal.dex2,
                signal.chain
            )
            
            if not sell_trade_id:
                self.logger.error("Failed to execute sell order")
                # TODO: Handle failed sell order (try to sell on different DEX)
                return
            
            # Calculate actual profit
            buy_value = position_size * signal.buy_price
            sell_value = position_size * signal.sell_price
            actual_profit = sell_value - buy_value
            
            # Update tracking
            self.total_trades += 1
            self.total_pnl += actual_profit
            
            if actual_profit > 0:
                self.profitable_trades += 1
            
            # Log trade
            self.trade_logger.log_trade(
                strategy="arbitrage",
                pair=signal.pair,
                side="arbitrage",
                amount=position_size,
                price=signal.buy_price,
                chain=signal.chain,
                trade_id=f"{buy_trade_id}_{sell_trade_id}",
                profit_loss=actual_profit,
                fees=signal.estimated_fees * buy_value
            )
            
            self.logger.info(f"Arbitrage completed: ${actual_profit:.2f} profit")
            
        except Exception as e:
            self.logger.error(f"Error executing arbitrage: {e}")
    
    async def execute_trade(self, 
                          pair: str,
                          side: str,
                          amount: float,
                          price: float,
                          dex: str,
                          chain: str) -> Optional[str]:
        """Execute a trade on the specified chain and DEX."""
        try:
            if chain == "solana":
                return await self.solana_dex.execute_trade(pair, side, amount, dex)
            elif chain == "base":
                return await self.base_dex.execute_trade(pair, side, amount, dex)
            else:
                self.logger.error(f"Unknown chain: {chain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
    
    def get_performance_metrics(self) -> Dict:
        """Get arbitrage strategy performance metrics."""
        win_rate = self.profitable_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        return {
            "total_opportunities": self.total_opportunities,
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "average_profit_per_trade": self.total_pnl / self.total_trades if self.total_trades > 0 else 0.0,
            "recent_signals": len(self.recent_signals)
        }
    
    async def get_market_data(self, pair: str, chain: str) -> Dict:
        """Get market data for a specific pair."""
        try:
            if chain == "solana":
                base_token = pair.split("/")[0]
                prices = await self.solana_dex.get_all_prices(base_token)
                return {
                    "chain": chain,
                    "pair": pair,
                    "prices": prices,
                    "timestamp": datetime.now()
                }
            elif chain == "base":
                base_token = pair.split("/")[0]
                prices = await self.base_dex.get_all_prices(base_token)
                return {
                    "chain": chain,
                    "pair": pair,
                    "prices": prices,
                    "timestamp": datetime.now()
                }
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return {} 