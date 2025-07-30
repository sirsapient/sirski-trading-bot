"""
Configuration settings for the crypto trading bot.
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Settings:
    """Configuration settings for the trading bot."""
    
    # Wallet Configuration
    solana_private_key: str
    base_private_key: str
    
    # RPC Endpoints
    solana_rpc_url: str
    base_rpc_url: str
    
    # Trading Parameters
    min_arbitrage_profit: float
    max_position_size: float
    min_trade_size: float
    max_daily_loss: float
    
    # API Endpoints
    jupiter_api_url: str
    uniswap_v3_api_url: str
    
    # Trading Pairs
    solana_pairs: List[str]
    base_pairs: List[str]
    
    # Risk Management
    stop_loss_percentage: float
    take_profit_percentage: float
    max_slippage: float
    
    # Monitoring
    discord_webhook_url: Optional[str] = None
    
    # RPC optimization settings
    arbitrage_scan_interval: int = 30
    swing_scan_interval: int = 300
    price_cache_duration: int = 60
    balance_check_interval: int = 3600
    trading_mode: str = "paper"  # or "live"
    
    @classmethod
    def from_env_file(cls, env_file: str = ".env") -> "Settings":
        """Load settings from environment file."""
        load_dotenv(env_file)
        
        return cls(
            # Wallet Configuration
            solana_private_key=os.getenv("SOLANA_PRIVATE_KEY", ""),
            base_private_key=os.getenv("BASE_PRIVATE_KEY", ""),
            
            # RPC Endpoints
            solana_rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"),
            base_rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
            
            # Trading Parameters
            min_arbitrage_profit=float(os.getenv("MIN_ARBITRAGE_PROFIT", "0.001")),
            max_position_size=float(os.getenv("MAX_POSITION_SIZE", "0.3")),
            min_trade_size=float(os.getenv("MIN_TRADE_SIZE", "500")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "0.05")),
            
            # API Endpoints
            jupiter_api_url=os.getenv("JUPITER_API_URL", "https://price.jup.ag/v4"),
            uniswap_v3_api_url=os.getenv("UNISWAP_V3_API_URL", 
                                        "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"),
            
            # Trading Pairs
            solana_pairs=os.getenv("SOLANA_PAIRS", "SOL/USDC,ETH/USDC,RAY/USDC").split(","),
            base_pairs=os.getenv("BASE_PAIRS", "ETH/USDC,WETH/USDC").split(","),
            
            # Risk Management
            stop_loss_percentage=float(os.getenv("STOP_LOSS_PERCENTAGE", "0.03")),
            take_profit_percentage=float(os.getenv("TAKE_PROFIT_PERCENTAGE", "0.05")),
            max_slippage=float(os.getenv("MAX_SLIPPAGE", "0.005")),
            
            # Monitoring
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            
            # Add RPC settings
            arbitrage_scan_interval=int(os.getenv("ARBITRAGE_SCAN_INTERVAL", "30")),
            swing_scan_interval=int(os.getenv("SWING_SCAN_INTERVAL", "300")),
            price_cache_duration=int(os.getenv("PRICE_CACHE_DURATION", "60")),
            balance_check_interval=int(os.getenv("BALANCE_CHECK_INTERVAL", "3600")),
            trading_mode=os.getenv("TRADING_MODE", "paper"),
        )
    
    def validate_live_trading(self) -> bool:
        """Validate settings for live trading."""
        if not self.solana_private_key or self.solana_private_key == "your_solana_private_key_here":
            print("ERROR: SOLANA_PRIVATE_KEY not set")
            return False
        
        if not self.base_private_key or self.base_private_key == "your_base_private_key_here":
            print("ERROR: BASE_PRIVATE_KEY not set")
            return False
        
        if self.min_trade_size < 100:
            print("WARNING: MIN_TRADE_SIZE is very low for live trading")
        
        if self.max_daily_loss > 0.1:
            print("WARNING: MAX_DAILY_LOSS is very high")
        
        return True
    
    def get_solana_pairs(self) -> List[str]:
        """Get Solana trading pairs."""
        return [pair.strip() for pair in self.solana_pairs if pair.strip()]
    
    def get_base_pairs(self) -> List[str]:
        """Get Base trading pairs."""
        return [pair.strip() for pair in self.base_pairs if pair.strip()] 