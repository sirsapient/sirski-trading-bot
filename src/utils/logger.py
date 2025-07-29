"""
Logging utilities for the crypto trading bot.
"""

import logging
import structlog
from typing import Optional
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup structured logging for the trading bot."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


class TradeLogger:
    """Specialized logger for trade events."""
    
    def __init__(self, name: str = "trade_logger"):
        self.logger = structlog.get_logger(name)
    
    def log_trade(self, 
                  strategy: str,
                  pair: str,
                  side: str,
                  amount: float,
                  price: float,
                  chain: str,
                  trade_id: str,
                  profit_loss: Optional[float] = None,
                  fees: Optional[float] = None):
        """Log a trade event."""
        self.logger.info(
            "Trade executed",
            strategy=strategy,
            pair=pair,
            side=side,
            amount=amount,
            price=price,
            chain=chain,
            trade_id=trade_id,
            profit_loss=profit_loss,
            fees=fees
        )
    
    def log_arbitrage_opportunity(self,
                                 pair: str,
                                 dex1: str,
                                 dex2: str,
                                 price1: float,
                                 price2: float,
                                 profit_percentage: float,
                                 estimated_fees: float):
        """Log an arbitrage opportunity."""
        self.logger.info(
            "Arbitrage opportunity found",
            pair=pair,
            dex1=dex1,
            dex2=dex2,
            price1=price1,
            price2=price2,
            profit_percentage=profit_percentage,
            estimated_fees=estimated_fees
        )
    
    def log_error(self, error: str, context: dict = None):
        """Log an error event."""
        self.logger.error(
            "Error occurred",
            error=error,
            context=context or {}
        )


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, name: str = "performance_logger"):
        self.logger = structlog.get_logger(name)
    
    def log_daily_pnl(self, 
                      date: str,
                      total_pnl: float,
                      win_rate: float,
                      total_trades: int,
                      profitable_trades: int):
        """Log daily performance metrics."""
        self.logger.info(
            "Daily performance",
            date=date,
            total_pnl=total_pnl,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades
        )
    
    def log_portfolio_update(self,
                           total_value: float,
                           solana_value: float,
                           base_value: float,
                           cash_value: float):
        """Log portfolio value update."""
        self.logger.info(
            "Portfolio update",
            total_value=total_value,
            solana_value=solana_value,
            base_value=base_value,
            cash_value=cash_value
        ) 