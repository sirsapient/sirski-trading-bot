"""
Trading strategies for the crypto trading bot.
"""

from .arbitrage import ArbitrageStrategy
from .swing_trading import SwingTradingStrategy

__all__ = ["ArbitrageStrategy", "SwingTradingStrategy"] 