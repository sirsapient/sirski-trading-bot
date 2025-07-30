"""
Swing trading strategy using technical analysis indicators.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np

from src.config.settings import Settings
from src.risk.manager import RiskManager
from src.exchanges.real_apis import RealSolanaDEX, RealBaseDEX
from src.utils.logger import TradeLogger


@dataclass
class SwingSignal:
    """Swing trading signal structure."""
    pair: str
    chain: str
    side: str  # "long" or "short"
    price: float
    confidence: float
    indicators: Dict
    timestamp: datetime


@dataclass
class TechnicalIndicators:
    """Technical indicators for swing trading."""
    rsi: float
    ema_short: float
    ema_long: float
    macd: float
    macd_signal: float
    volume_sma: float
    price_sma: float


class SwingTradingStrategy:
    """Swing trading strategy using technical analysis."""
    
    def __init__(self, settings: Settings, risk_manager: RiskManager):
        self.settings = settings
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(__name__)
        self.trade_logger = TradeLogger("swing_trading_strategy")
        
        # Initialize DEX clients with real APIs
        self.solana_dex = RealSolanaDEX(settings)
        self.base_dex = RealBaseDEX(settings)
        
        # Strategy state
        self.running = False
        self.last_scan = datetime.now()
        
        # CHANGE FROM: self.scan_interval = 60  # This is actually fine
        self.scan_interval = settings.swing_scan_interval  # Use settings value - 5 minutes default
        
        if hasattr(settings, 'trading_mode') and settings.trading_mode == 'paper':
            self.scan_interval = settings.swing_scan_interval * 2  # 10 minutes for paper trading
            self.logger.info("Paper trading mode: Using slower swing scan interval")
        
        # Technical analysis parameters
        self.rsi_period = 14
        self.ema_short_period = 12
        self.ema_long_period = 26
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.volume_sma_period = 20
        self.price_sma_period = 50
        
        # Performance tracking
        self.total_signals = 0
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_pnl = 0.0
        
        # Signal tracking
        self.recent_signals: List[SwingSignal] = []
        self.max_signals_history = 50
        
        # Price history for technical analysis
        self.price_history: Dict[str, List[Dict]] = {}
        self.max_history_length = 200
    
    async def initialize(self):
        """Initialize the swing trading strategy."""
        await self.solana_dex.initialize()
        await self.base_dex.initialize()
        self.logger.info("Swing trading strategy initialized")
    
    async def start(self):
        """Start the swing trading strategy."""
        self.running = True
        self.logger.info("Starting swing trading strategy")
        
        try:
            await self.initialize()
            
            while self.running:
                await self.scan_for_signals()
                await asyncio.sleep(self.scan_interval)
                
        except Exception as e:
            self.logger.error(f"Error in swing trading strategy: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the swing trading strategy."""
        self.running = False
        await self.solana_dex.close()
        await self.base_dex.close()
        self.logger.info("Swing trading strategy stopped")
    
    async def scan_for_signals(self):
        """Scan for swing trading signals on both chains."""
        try:
            # Check Solana pairs
            for pair in self.settings.get_solana_pairs():
                signal = await self.analyze_pair(pair, "solana")
                if signal:
                    await self.process_signal(signal)
            
            # Check Base pairs
            for pair in self.settings.get_base_pairs():
                signal = await self.analyze_pair(pair, "base")
                if signal:
                    await self.process_signal(signal)
            
            self.last_scan = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error scanning for signals: {e}")
    
    async def analyze_pair(self, pair: str, chain: str) -> Optional[SwingSignal]:
        """Analyze a trading pair for swing trading signals."""
        try:
            # Get current price
            base_token = pair.split("/")[0]
            
            if chain == "solana":
                prices = await self.solana_dex.get_all_prices(base_token)
            else:
                prices = await self.base_dex.get_all_prices(base_token)
            
            if not prices:
                return None
            
            # Use average price for analysis
            current_price = sum(prices.values()) / len(prices)
            
            # Update price history
            await self.update_price_history(pair, current_price, chain)
            
            # Calculate technical indicators
            indicators = await self.calculate_indicators(pair)
            if not indicators:
                return None
            
            # Generate signal
            signal = await self.generate_signal(pair, chain, current_price, indicators)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing pair {pair}: {e}")
            return None
    
    async def update_price_history(self, pair: str, price: float, chain: str):
        """Update price history for technical analysis."""
        try:
            if pair not in self.price_history:
                self.price_history[pair] = []
            
            # Add new price data
            price_data = {
                "price": price,
                "timestamp": datetime.now(),
                "chain": chain
            }
            
            self.price_history[pair].append(price_data)
            
            # Keep only recent history
            if len(self.price_history[pair]) > self.max_history_length:
                self.price_history[pair] = self.price_history[pair][-self.max_history_length:]
                
        except Exception as e:
            self.logger.error(f"Error updating price history: {e}")
    
    async def calculate_indicators(self, pair: str) -> Optional[TechnicalIndicators]:
        """Calculate technical indicators for a pair."""
        try:
            if pair not in self.price_history or len(self.price_history[pair]) < 50:
                return None
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(self.price_history[pair])
            prices = df['price'].values
            
            # Calculate RSI
            rsi = self.calculate_rsi(prices, self.rsi_period)
            
            # Calculate EMAs
            ema_short = self.calculate_ema(prices, self.ema_short_period)
            ema_long = self.calculate_ema(prices, self.ema_long_period)
            
            # Calculate MACD
            macd, macd_signal = self.calculate_macd(prices)
            
            # Calculate SMAs
            volume_sma = np.mean(prices[-self.volume_sma_period:]) if len(prices) >= self.volume_sma_period else np.mean(prices)
            price_sma = np.mean(prices[-self.price_sma_period:]) if len(prices) >= self.price_sma_period else np.mean(prices)
            
            return TechnicalIndicators(
                rsi=rsi,
                ema_short=ema_short,
                ema_long=ema_long,
                macd=macd,
                macd_signal=macd_signal,
                volume_sma=volume_sma,
                price_sma=price_sma
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return None
    
    def calculate_rsi(self, prices: np.ndarray, period: int) -> float:
        """Calculate RSI indicator."""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gains = np.mean(gains[-period:])
            avg_losses = np.mean(losses[-period:])
            
            if avg_losses == 0:
                return 100.0
            
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average."""
        try:
            if len(prices) < period:
                return np.mean(prices)
            
            alpha = 2 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = alpha * price + (1 - alpha) * ema
            
            return ema
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return np.mean(prices)
    
    def calculate_macd(self, prices: np.ndarray) -> Tuple[float, float]:
        """Calculate MACD indicator."""
        try:
            if len(prices) < self.macd_slow:
                return 0.0, 0.0
            
            ema_fast = self.calculate_ema(prices, self.macd_fast)
            ema_slow = self.calculate_ema(prices, self.macd_slow)
            
            macd = ema_fast - ema_slow
            
            # Calculate MACD signal line (simplified)
            macd_signal = macd * 0.8  # Simplified signal line
            
            return macd, macd_signal
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return 0.0, 0.0
    
    async def generate_signal(self, 
                            pair: str,
                            chain: str,
                            price: float,
                            indicators: TechnicalIndicators) -> Optional[SwingSignal]:
        """Generate swing trading signal based on technical indicators."""
        try:
            signal_side = None
            confidence = 0.0
            
            # RSI conditions
            rsi_oversold = indicators.rsi < 30
            rsi_overbought = indicators.rsi > 70
            
            # EMA crossover
            ema_bullish = indicators.ema_short > indicators.ema_long
            ema_bearish = indicators.ema_short < indicators.ema_long
            
            # MACD conditions
            macd_bullish = indicators.macd > indicators.macd_signal
            macd_bearish = indicators.macd < indicators.macd_signal
            
            # Price vs SMA
            price_above_sma = price > indicators.price_sma
            price_below_sma = price < indicators.price_sma
            
            # Generate long signal
            long_conditions = (
                rsi_oversold and
                ema_bullish and
                macd_bullish and
                price_above_sma
            )
            
            # Generate short signal
            short_conditions = (
                rsi_overbought and
                ema_bearish and
                macd_bearish and
                price_below_sma
            )
            
            if long_conditions:
                signal_side = "long"
                confidence = min(1.0, (70 - indicators.rsi) / 40)  # Higher confidence for lower RSI
            elif short_conditions:
                signal_side = "short"
                confidence = min(1.0, (indicators.rsi - 30) / 40)  # Higher confidence for higher RSI
            
            if signal_side and confidence > 0.3:  # Minimum confidence threshold
                return SwingSignal(
                    pair=pair,
                    chain=chain,
                    side=signal_side,
                    price=price,
                    confidence=confidence,
                    indicators={
                        "rsi": indicators.rsi,
                        "ema_short": indicators.ema_short,
                        "ema_long": indicators.ema_long,
                        "macd": indicators.macd,
                        "macd_signal": indicators.macd_signal,
                        "price_sma": indicators.price_sma
                    },
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None
    
    async def process_signal(self, signal: SwingSignal):
        """Process a swing trading signal."""
        try:
            # Log signal
            self.logger.info(f"Swing signal: {signal.side} {signal.pair} on {signal.chain} "
                           f"(confidence: {signal.confidence:.2f})")
            
            # Store signal
            self.recent_signals.append(signal)
            if len(self.recent_signals) > self.max_signals_history:
                self.recent_signals.pop(0)
            
            self.total_signals += 1
            
            # Check if we should execute
            if await self.should_execute_swing(signal):
                await self.execute_swing_trade(signal)
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
    
    async def should_execute_swing(self, signal: SwingSignal) -> bool:
        """Determine if we should execute a swing trade."""
        try:
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
                            (datetime.now() - s.timestamp).seconds < 3600]  # 1 hour
            
            if len(recent_signals) > 2:  # Max 2 signals per hour per pair
                return False
            
            # Check confidence threshold
            if signal.confidence < 0.5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking swing execution conditions: {e}")
            return False
    
    async def execute_swing_trade(self, signal: SwingSignal):
        """Execute a swing trade."""
        try:
            self.logger.info(f"Executing swing trade: {signal.side} {signal.pair} on {signal.chain}")
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                signal.pair,
                signal.price,
                signal.confidence
            )
            
            if position_size <= 0:
                self.logger.warning("Invalid position size calculated")
                return
            
            # Execute trade
            trade_id = await self.execute_trade(
                signal.pair,
                signal.side,
                position_size,
                signal.price,
                signal.chain
            )
            
            if not trade_id:
                self.logger.error("Failed to execute swing trade")
                return
            
            # Update tracking
            self.total_trades += 1
            
            # Log trade
            self.trade_logger.log_trade(
                strategy="swing_trading",
                pair=signal.pair,
                side=signal.side,
                amount=position_size,
                price=signal.price,
                chain=signal.chain,
                trade_id=trade_id
            )
            
            self.logger.info(f"Swing trade executed: {signal.side} {position_size:.4f} {signal.pair}")
            
        except Exception as e:
            self.logger.error(f"Error executing swing trade: {e}")
    
    async def execute_trade(self, 
                          pair: str,
                          side: str,
                          amount: float,
                          price: float,
                          chain: str) -> Optional[str]:
        """Execute a trade on the specified chain."""
        try:
            if chain == "solana":
                return await self.solana_dex.execute_trade(pair, side, amount, "jupiter")
            elif chain == "base":
                return await self.base_dex.execute_trade(pair, side, amount, "uniswap_v3")
            else:
                self.logger.error(f"Unknown chain: {chain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
    
    def get_performance_metrics(self) -> Dict:
        """Get swing trading strategy performance metrics."""
        win_rate = self.profitable_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        return {
            "total_signals": self.total_signals,
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "average_profit_per_trade": self.total_pnl / self.total_trades if self.total_trades > 0 else 0.0,
            "recent_signals": len(self.recent_signals)
        } 