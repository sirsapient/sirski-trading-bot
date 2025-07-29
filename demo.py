#!/usr/bin/env python3
"""
Demo script for the crypto trading bot.
This script demonstrates the basic functionality without executing real trades.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.utils.logger import setup_logging
from src.utils.wallet import WalletManager
from src.risk.manager import RiskManager
from src.exchanges.solana_dex import SolanaDEX
from src.exchanges.base_dex import BaseDEX
from src.strategies.arbitrage import ArbitrageStrategy
from src.strategies.swing_trading import SwingTradingStrategy


async def demo_price_fetching():
    """Demonstrate price fetching from DEXs."""
    print("\n=== Price Fetching Demo ===")
    
    # Create settings
    settings = Settings(
        solana_private_key="demo",
        base_private_key="demo",
        solana_rpc_url="https://api.mainnet-beta.solana.com",
        base_rpc_url="https://mainnet.base.org",
        min_arbitrage_profit=0.001,
        max_position_size=0.3,
        min_trade_size=500,
        max_daily_loss=0.05,
        jupiter_api_url="https://price.jup.ag/v4",
        uniswap_v3_api_url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        solana_pairs=["SOL/USDC", "ETH/USDC"],
        base_pairs=["ETH/USDC"],
        stop_loss_percentage=0.03,
        take_profit_percentage=0.05,
        max_slippage=0.005
    )
    
    # Initialize DEX clients
    solana_dex = SolanaDEX(settings)
    base_dex = BaseDEX(settings)
    
    await solana_dex.initialize()
    await base_dex.initialize()
    
    try:
        # Get Solana prices
        print("Fetching Solana prices...")
        sol_prices = await solana_dex.get_all_prices("SOL")
        print(f"SOL prices: {sol_prices}")
        
        # Get Base prices
        print("Fetching Base prices...")
        eth_prices = await base_dex.get_all_prices("ETH")
        print(f"ETH prices: {eth_prices}")
        
        # Find arbitrage opportunities
        print("\nScanning for arbitrage opportunities...")
        solana_opportunities = await solana_dex.find_arbitrage_opportunities()
        base_opportunities = await base_dex.find_arbitrage_opportunities()
        
        print(f"Found {len(solana_opportunities)} Solana opportunities")
        print(f"Found {len(base_opportunities)} Base opportunities")
        
        for opp in solana_opportunities[:3]:  # Show first 3
            print(f"  {opp.pair}: {opp.dex1} -> {opp.dex2}, Profit: {opp.profit_percentage:.3%}")
        
    finally:
        await solana_dex.close()
        await base_dex.close()


async def demo_technical_analysis():
    """Demonstrate technical analysis indicators."""
    print("\n=== Technical Analysis Demo ===")
    
    from src.indicators.technical import TechnicalIndicators
    import numpy as np
    
    # Create sample price data
    prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113])
    
    print(f"Sample prices: {prices}")
    
    # Calculate indicators
    rsi_result = TechnicalIndicators.calculate_rsi(prices, period=10)
    ema_short = TechnicalIndicators.calculate_ema(prices, period=5)
    ema_long = TechnicalIndicators.calculate_ema(prices, period=10)
    macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(prices)
    
    print(f"RSI: {rsi_result.value:.2f} ({rsi_result.signal})")
    print(f"EMA Short: {ema_short:.2f}")
    print(f"EMA Long: {ema_long:.2f}")
    print(f"MACD Line: {macd_line:.4f}")
    print(f"MACD Signal: {signal_line:.4f}")
    print(f"MACD Histogram: {histogram:.4f}")
    
    # Generate trading signal
    indicators = {
        "rsi": rsi_result,
        "ema_short": ema_short,
        "ema_long": ema_long,
        "macd": (macd_line, signal_line, histogram)
    }
    
    signal, confidence = TechnicalIndicators.generate_trading_signal(indicators)
    print(f"Trading Signal: {signal} (confidence: {confidence:.2f})")


async def demo_risk_management():
    """Demonstrate risk management features."""
    print("\n=== Risk Management Demo ===")
    
    # Create settings and risk manager
    settings = Settings(
        solana_private_key="demo",
        base_private_key="demo",
        solana_rpc_url="https://test.com",
        base_rpc_url="https://test.com",
        min_arbitrage_profit=0.001,
        max_position_size=0.3,
        min_trade_size=500,
        max_daily_loss=0.05,
        jupiter_api_url="https://test.com",
        uniswap_v3_api_url="https://test.com",
        solana_pairs=["SOL/USDC"],
        base_pairs=["ETH/USDC"],
        stop_loss_percentage=0.03,
        take_profit_percentage=0.05,
        max_slippage=0.005
    )
    
    risk_manager = RiskManager(settings)
    risk_manager.set_initial_portfolio_value(10000)
    
    print(f"Initial portfolio value: ${risk_manager.portfolio_value:,.2f}")
    
    # Calculate position sizes
    sol_position = risk_manager.calculate_position_size("SOL/USDC", 100.0, 0.8)
    eth_position = risk_manager.calculate_position_size("ETH/USDC", 2000.0, 0.6)
    
    print(f"SOL position size: {sol_position:.4f} SOL")
    print(f"ETH position size: {eth_position:.4f} ETH")
    
    # Check position limits
    can_open_sol = risk_manager.can_open_position("SOL/USDC", "long", sol_position, 100.0)
    can_open_eth = risk_manager.can_open_position("ETH/USDC", "long", eth_position, 2000.0)
    
    print(f"Can open SOL position: {can_open_sol}")
    print(f"Can open ETH position: {can_open_eth}")
    
    # Get risk metrics
    metrics = risk_manager.get_risk_metrics()
    print(f"Current positions: {metrics.current_positions}")
    print(f"Total PnL: ${metrics.total_pnl:.2f}")
    print(f"Win rate: {metrics.win_rate:.2%}")


async def demo_strategies():
    """Demonstrate trading strategies."""
    print("\n=== Trading Strategies Demo ===")
    
    # Create settings and components
    settings = Settings(
        solana_private_key="demo",
        base_private_key="demo",
        solana_rpc_url="https://test.com",
        base_rpc_url="https://test.com",
        min_arbitrage_profit=0.001,
        max_position_size=0.3,
        min_trade_size=500,
        max_daily_loss=0.05,
        jupiter_api_url="https://test.com",
        uniswap_v3_api_url="https://test.com",
        solana_pairs=["SOL/USDC"],
        base_pairs=["ETH/USDC"],
        stop_loss_percentage=0.03,
        take_profit_percentage=0.05,
        max_slippage=0.005
    )
    
    risk_manager = RiskManager(settings)
    risk_manager.set_initial_portfolio_value(10000)
    
    # Initialize strategies
    arbitrage_strategy = ArbitrageStrategy(settings, risk_manager)
    swing_strategy = SwingTradingStrategy(settings, risk_manager)
    
    # Get performance metrics
    arbitrage_metrics = arbitrage_strategy.get_performance_metrics()
    swing_metrics = swing_strategy.get_performance_metrics()
    
    print("Arbitrage Strategy Metrics:")
    print(f"  Total opportunities: {arbitrage_metrics['total_opportunities']}")
    print(f"  Total trades: {arbitrage_metrics['total_trades']}")
    print(f"  Win rate: {arbitrage_metrics['win_rate']:.2%}")
    print(f"  Total PnL: ${arbitrage_metrics['total_pnl']:.2f}")
    
    print("\nSwing Trading Strategy Metrics:")
    print(f"  Total signals: {swing_metrics['total_signals']}")
    print(f"  Total trades: {swing_metrics['total_trades']}")
    print(f"  Win rate: {swing_metrics['win_rate']:.2%}")
    print(f"  Total PnL: ${swing_metrics['total_pnl']:.2f}")


async def main():
    """Run the demo."""
    print("🚀 Crypto Trading Bot Demo")
    print("=" * 50)
    
    # Setup logging
    setup_logging("INFO")
    
    try:
        await demo_price_fetching()
        await demo_technical_analysis()
        await demo_risk_management()
        await demo_strategies()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nNext steps:")
        print("1. Generate wallets: python generate_wallets.py")
        print("2. Configure .env file with your settings")
        print("3. Start paper trading: python src/main.py --mode=paper")
        print("4. Monitor performance and adjust parameters")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logging.error(f"Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 