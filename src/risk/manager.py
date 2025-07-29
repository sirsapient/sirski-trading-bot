"""
Risk management for the crypto trading bot.
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

from src.config.settings import Settings


@dataclass
class Position:
    """Position information."""
    pair: str
    side: str  # "long" or "short"
    amount: float
    entry_price: float
    current_price: float
    pnl: float
    timestamp: datetime
    trade_id: str


@dataclass
class RiskMetrics:
    """Risk metrics for the portfolio."""
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    current_positions: int
    portfolio_value: float


class RiskManager:
    """Risk management for position sizing, stop losses, and daily limits."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Risk limits
        self.max_position_size = settings.max_position_size
        self.max_daily_loss = settings.max_daily_loss
        self.stop_loss_pct = settings.stop_loss_percentage
        self.take_profit_pct = settings.take_profit_percentage
        
        # Portfolio tracking
        self.portfolio_value = 0.0
        self.initial_portfolio_value = 0.0
        
        # Performance tracking
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_portfolio_value = 0.0
    
    def set_initial_portfolio_value(self, value: float):
        """Set the initial portfolio value."""
        self.initial_portfolio_value = value
        self.portfolio_value = value
        self.peak_portfolio_value = value
        self.logger.info(f"Initial portfolio value set to: ${value:,.2f}")
    
    def calculate_position_size(self, 
                              pair: str,
                              price: float,
                              confidence: float = 1.0) -> float:
        """Calculate position size based on risk parameters."""
        try:
            # Base position size as percentage of portfolio
            base_size = self.portfolio_value * self.max_position_size
            
            # Adjust for confidence (0.0 to 1.0)
            adjusted_size = base_size * confidence
            
            # Ensure minimum trade size
            min_trade_value = self.settings.min_trade_size
            if adjusted_size < min_trade_value:
                adjusted_size = min_trade_value
            
            # Calculate token amount
            token_amount = adjusted_size / price
            
            self.logger.info(f"Calculated position size for {pair}: {token_amount:.4f} tokens (${adjusted_size:.2f})")
            return token_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def can_open_position(self, 
                         pair: str,
                         side: str,
                         amount: float,
                         price: float) -> bool:
        """Check if we can open a new position."""
        try:
            # Check daily loss limit
            if self.daily_pnl <= -(self.portfolio_value * self.max_daily_loss):
                self.logger.warning("Daily loss limit reached")
                return False
            
            # Check if we already have a position in this pair
            if pair in self.positions:
                self.logger.warning(f"Already have position in {pair}")
                return False
            
            # Check position size limit
            position_value = amount * price
            max_position_value = self.portfolio_value * self.max_position_size
            
            if position_value > max_position_value:
                self.logger.warning(f"Position size too large: ${position_value:.2f} > ${max_position_value:.2f}")
                return False
            
            # Check if we have enough portfolio value
            if position_value > self.portfolio_value * 0.8:  # Leave 20% buffer
                self.logger.warning("Insufficient portfolio value for position")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking position limits: {e}")
            return False
    
    def open_position(self, 
                     pair: str,
                     side: str,
                     amount: float,
                     price: float,
                     trade_id: str) -> bool:
        """Open a new position."""
        try:
            if not self.can_open_position(pair, side, amount, price):
                return False
            
            position = Position(
                pair=pair,
                side=side,
                amount=amount,
                entry_price=price,
                current_price=price,
                pnl=0.0,
                timestamp=datetime.now(),
                trade_id=trade_id
            )
            
            self.positions[pair] = position
            self.daily_trades += 1
            
            self.logger.info(f"Opened {side} position for {amount:.4f} {pair} at ${price:.4f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return False
    
    def update_position_price(self, pair: str, current_price: float):
        """Update position with current price and check stop loss/take profit."""
        try:
            if pair not in self.positions:
                return
            
            position = self.positions[pair]
            position.current_price = current_price
            
            # Calculate PnL
            if position.side == "long":
                position.pnl = (current_price - position.entry_price) * position.amount
            else:  # short
                position.pnl = (position.entry_price - current_price) * position.amount
            
            # Check stop loss
            if position.pnl < 0:
                loss_pct = abs(position.pnl) / (position.entry_price * position.amount)
                if loss_pct >= self.stop_loss_pct:
                    self.logger.warning(f"Stop loss triggered for {pair}: {loss_pct:.2%}")
                    return "stop_loss"
            
            # Check take profit
            if position.pnl > 0:
                profit_pct = position.pnl / (position.entry_price * position.amount)
                if profit_pct >= self.take_profit_pct:
                    self.logger.info(f"Take profit triggered for {pair}: {profit_pct:.2%}")
                    return "take_profit"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating position price: {e}")
            return None
    
    def close_position(self, pair: str, close_price: float, reason: str = "manual") -> Optional[float]:
        """Close a position and return the PnL."""
        try:
            if pair not in self.positions:
                return None
            
            position = self.positions[pair]
            
            # Calculate final PnL
            if position.side == "long":
                final_pnl = (close_price - position.entry_price) * position.amount
            else:  # short
                final_pnl = (position.entry_price - close_price) * position.amount
            
            # Update tracking
            self.total_pnl += final_pnl
            self.daily_pnl += final_pnl
            self.closed_positions.append(position)
            
            # Update portfolio value
            self.portfolio_value += final_pnl
            
            # Update peak and drawdown
            if self.portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = self.portfolio_value
            else:
                current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
                if current_drawdown > self.max_drawdown:
                    self.max_drawdown = current_drawdown
            
            # Remove from active positions
            del self.positions[pair]
            
            self.logger.info(f"Closed {position.side} position for {pair}: PnL ${final_pnl:.2f} ({reason})")
            return final_pnl
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics."""
        try:
            # Calculate win rate
            profitable_trades = len([p for p in self.closed_positions if p.pnl > 0])
            total_trades = len(self.closed_positions)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0
            
            return RiskMetrics(
                total_pnl=self.total_pnl,
                daily_pnl=self.daily_pnl,
                max_drawdown=self.max_drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                profitable_trades=profitable_trades,
                current_positions=len(self.positions),
                portfolio_value=self.portfolio_value
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0)
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of new day)."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.logger.info("Daily metrics reset")
    
    def check_daily_reset(self):
        """Check if we need to reset daily metrics."""
        now = datetime.now()
        if now.date() > self.daily_start.date():
            self.reset_daily_metrics()
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary."""
        metrics = self.get_risk_metrics()
        
        return {
            "portfolio_value": self.portfolio_value,
            "total_pnl": self.total_pnl,
            "daily_pnl": self.daily_pnl,
            "max_drawdown": self.max_drawdown,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "current_positions": len(self.positions),
            "daily_trades": self.daily_trades,
            "daily_loss_limit": self.portfolio_value * self.max_daily_loss,
            "remaining_daily_loss": self.portfolio_value * self.max_daily_loss + self.daily_pnl
        }
    
    def emergency_stop(self) -> bool:
        """Emergency stop all trading."""
        try:
            self.logger.warning("EMERGENCY STOP: Closing all positions")
            
            # Close all positions at current prices
            for pair in list(self.positions.keys()):
                position = self.positions[pair]
                self.close_position(pair, position.current_price, "emergency_stop")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
            return False 