"""
Technical indicators for crypto trading analysis.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """Result of a technical indicator calculation."""
    value: float
    signal: str  # "buy", "sell", "neutral"
    strength: float  # 0.0 to 1.0


class TechnicalIndicators:
    """Technical analysis indicators for trading decisions."""
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> IndicatorResult:
        """Calculate Relative Strength Index (RSI)."""
        try:
            if len(prices) < period + 1:
                return IndicatorResult(50.0, "neutral", 0.0)
            
            # Calculate price changes
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gains = np.mean(gains[-period:])
            avg_losses = np.mean(losses[-period:])
            
            if avg_losses == 0:
                return IndicatorResult(100.0, "sell", 1.0)
            
            # Calculate RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            # Determine signal
            if rsi > 70:
                signal = "sell"
                strength = min(1.0, (rsi - 70) / 30)
            elif rsi < 30:
                signal = "buy"
                strength = min(1.0, (30 - rsi) / 30)
            else:
                signal = "neutral"
                strength = 0.0
            
            return IndicatorResult(rsi, signal, strength)
            
        except Exception as e:
            return IndicatorResult(50.0, "neutral", 0.0)
    
    @staticmethod
    def calculate_ema(prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average (EMA)."""
        try:
            if len(prices) < period:
                return np.mean(prices)
            
            alpha = 2 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = alpha * price + (1 - alpha) * ema
            
            return ema
            
        except Exception as e:
            return np.mean(prices)
    
    @staticmethod
    def calculate_sma(prices: np.ndarray, period: int) -> float:
        """Calculate Simple Moving Average (SMA)."""
        try:
            if len(prices) < period:
                return np.mean(prices)
            
            return np.mean(prices[-period:])
            
        except Exception as e:
            return np.mean(prices)
    
    @staticmethod
    def calculate_macd(prices: np.ndarray, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            if len(prices) < slow_period:
                return 0.0, 0.0, 0.0
            
            # Calculate EMAs
            ema_fast = TechnicalIndicators.calculate_ema(prices, fast_period)
            ema_slow = TechnicalIndicators.calculate_ema(prices, slow_period)
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line (simplified)
            signal_line = macd_line * 0.8  # Simplified calculation
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            return 0.0, 0.0, 0.0
    
    @staticmethod
    def calculate_bollinger_bands(prices: np.ndarray, 
                                period: int = 20, 
                                std_dev: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands."""
        try:
            if len(prices) < period:
                sma = np.mean(prices)
                return sma, sma, sma
            
            sma = TechnicalIndicators.calculate_sma(prices, period)
            std = np.std(prices[-period:])
            
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            return upper_band, sma, lower_band
            
        except Exception as e:
            sma = np.mean(prices)
            return sma, sma, sma
    
    @staticmethod
    def calculate_stochastic(prices: np.ndarray, 
                           period: int = 14) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator."""
        try:
            if len(prices) < period:
                return 50.0, 50.0
            
            # Calculate %K
            highest_high = np.max(prices[-period:])
            lowest_low = np.min(prices[-period:])
            current_price = prices[-1]
            
            if highest_high == lowest_low:
                k_percent = 50.0
            else:
                k_percent = ((current_price - lowest_low) / (highest_high - lowest_low)) * 100
            
            # Calculate %D (simplified as 3-period SMA of %K)
            d_percent = k_percent  # Simplified
            
            return k_percent, d_percent
            
        except Exception as e:
            return 50.0, 50.0
    
    @staticmethod
    def calculate_atr(prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range (ATR)."""
        try:
            if len(prices) < period + 1:
                return 0.0
            
            # Calculate true ranges
            true_ranges = []
            for i in range(1, len(prices)):
                high_low = prices[i] - prices[i-1]
                high_close = abs(prices[i] - prices[i-1])
                low_close = abs(prices[i-1] - prices[i-1])
                
                true_range = max(high_low, high_close, low_close)
                true_ranges.append(true_range)
            
            # Calculate ATR
            atr = np.mean(true_ranges[-period:])
            return atr
            
        except Exception as e:
            return 0.0
    
    @staticmethod
    def calculate_volume_sma(volumes: np.ndarray, period: int = 20) -> float:
        """Calculate Simple Moving Average of volume."""
        try:
            if len(volumes) < period:
                return np.mean(volumes)
            
            return np.mean(volumes[-period:])
            
        except Exception as e:
            return np.mean(volumes)
    
    @staticmethod
    def calculate_price_momentum(prices: np.ndarray, period: int = 10) -> float:
        """Calculate price momentum."""
        try:
            if len(prices) < period:
                return 0.0
            
            current_price = prices[-1]
            past_price = prices[-period]
            
            momentum = ((current_price - past_price) / past_price) * 100
            return momentum
            
        except Exception as e:
            return 0.0
    
    @staticmethod
    def calculate_volatility(prices: np.ndarray, period: int = 20) -> float:
        """Calculate price volatility."""
        try:
            if len(prices) < period:
                return 0.0
            
            returns = np.diff(prices[-period:]) / prices[-period:-1]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            return volatility
            
        except Exception as e:
            return 0.0
    
    @staticmethod
    def generate_trading_signal(indicators: dict) -> Tuple[str, float]:
        """Generate trading signal based on multiple indicators."""
        try:
            buy_signals = 0
            sell_signals = 0
            total_strength = 0.0
            
            # RSI signal
            if "rsi" in indicators:
                rsi_result = indicators["rsi"]
                if rsi_result.signal == "buy":
                    buy_signals += 1
                    total_strength += rsi_result.strength
                elif rsi_result.signal == "sell":
                    sell_signals += 1
                    total_strength += rsi_result.strength
            
            # MACD signal
            if "macd" in indicators:
                macd_line, signal_line, histogram = indicators["macd"]
                if macd_line > signal_line:
                    buy_signals += 1
                    total_strength += 0.5
                else:
                    sell_signals += 1
                    total_strength += 0.5
            
            # EMA crossover signal
            if "ema_short" in indicators and "ema_long" in indicators:
                ema_short = indicators["ema_short"]
                ema_long = indicators["ema_long"]
                if ema_short > ema_long:
                    buy_signals += 1
                    total_strength += 0.5
                else:
                    sell_signals += 1
                    total_strength += 0.5
            
            # Determine final signal
            if buy_signals > sell_signals:
                signal = "buy"
                confidence = min(1.0, total_strength / max(buy_signals, 1))
            elif sell_signals > buy_signals:
                signal = "sell"
                confidence = min(1.0, total_strength / max(sell_signals, 1))
            else:
                signal = "neutral"
                confidence = 0.0
            
            return signal, confidence
            
        except Exception as e:
            return "neutral", 0.0 