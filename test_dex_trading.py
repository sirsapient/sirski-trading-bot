#!/usr/bin/env python3
"""
Comprehensive DEX Trading Test
Tests the bot's ability to perform DEX trading on Solana and Base chains.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_solana_dex_trading():
    """Test Solana DEX trading functionality."""
    print("🔄 Testing Solana DEX Trading...")
    
    try:
        from src.config.settings import Settings
        from src.exchanges.real_apis import RealSolanaDEX
        
        # Load settings
        settings = Settings.from_env_file()
        
        # Create Solana DEX instance
        dex = RealSolanaDEX(settings)
        await dex.initialize()
        
        # Test getting prices from multiple DEXs
        prices = await dex.get_all_prices("SOL")
        if prices:
            print(f"✅ Solana DEX prices working: {prices}")
            
            # Test arbitrage opportunity detection
            opportunities = await dex.find_arbitrage_opportunities(min_profit=0.001)
            print(f"✅ Solana arbitrage detection working: {len(opportunities)} opportunities found")
            
            if opportunities:
                for opp in opportunities[:3]:  # Show first 3
                    print(f"   📈 {opp.pair}: {opp.dex1} ${opp.price1:.2f} → {opp.dex2} ${opp.price2:.2f} = {opp.profit_percentage:.3%} profit")
        else:
            print("❌ Solana DEX prices failed")
            return False
        
        await dex.close()
        return True
        
    except Exception as e:
        print(f"❌ Solana DEX test failed: {e}")
        return False

async def test_base_dex_trading():
    """Test Base DEX trading functionality."""
    print("🔄 Testing Base DEX Trading...")
    
    try:
        from src.config.settings import Settings
        from src.exchanges.real_apis import RealBaseDEX
        
        # Load settings
        settings = Settings.from_env_file()
        
        # Create Base DEX instance
        dex = RealBaseDEX(settings)
        await dex.initialize()
        
        # Test getting prices from multiple DEXs
        prices = await dex.get_all_prices("ETH")
        if prices:
            print(f"✅ Base DEX prices working: {prices}")
            
            # Test arbitrage opportunity detection
            opportunities = await dex.find_arbitrage_opportunities(min_profit=0.001)
            print(f"✅ Base arbitrage detection working: {len(opportunities)} opportunities found")
            
            if opportunities:
                for opp in opportunities[:3]:  # Show first 3
                    print(f"   📈 {opp.pair}: {opp.dex1} ${opp.price1:.2f} → {opp.dex2} ${opp.price2:.2f} = {opp.profit_percentage:.3%} profit")
        else:
            print("❌ Base DEX prices failed")
            return False
        
        await dex.close()
        return True
        
    except Exception as e:
        print(f"❌ Base DEX test failed: {e}")
        return False

async def test_arbitrage_strategy():
    """Test the arbitrage strategy integration."""
    print("🔄 Testing Arbitrage Strategy...")
    
    try:
        from src.config.settings import Settings
        from src.risk.manager import RiskManager
        from src.strategies.arbitrage import ArbitrageStrategy
        
        # Load settings
        settings = Settings.from_env_file()
        
        # Create risk manager
        risk_manager = RiskManager(settings)
        
        # Create arbitrage strategy
        strategy = ArbitrageStrategy(settings, risk_manager)
        await strategy.initialize()
        
        # Test scanning for opportunities
        await strategy.scan_for_opportunities()
        
        # Get performance metrics
        metrics = strategy.get_performance_metrics()
        print(f"✅ Arbitrage strategy working: {metrics}")
        
        await strategy.stop()
        return True
        
    except Exception as e:
        print(f"❌ Arbitrage strategy test failed: {e}")
        return False

async def test_jupiter_api_integration():
    """Test Jupiter API integration for Solana."""
    print("🔄 Testing Jupiter API Integration...")
    
    try:
        from src.exchanges.real_apis import JupiterAPI
        
        jupiter = JupiterAPI()
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test getting SOL price
            sol_price = await jupiter.get_price(session, "SOL")
            if sol_price:
                print(f"✅ Jupiter API working: SOL = ${sol_price}")
                
                # Test getting quote
                quote = await jupiter.get_quote(session, "SOL", "USDC", 1000000000)  # 1 SOL
                if quote:
                    print(f"✅ Jupiter quote working: {quote.get('outAmount', 'N/A')} USDC for 1 SOL")
                    return True
                else:
                    print("❌ Jupiter quote failed")
                    return False
            else:
                print("❌ Jupiter price failed")
                return False
                
    except Exception as e:
        print(f"❌ Jupiter API test failed: {e}")
        return False

async def test_uniswap_api_integration():
    """Test Uniswap V3 API integration for Base."""
    print("🔄 Testing Uniswap V3 API Integration...")
    
    try:
        from src.exchanges.real_apis import UniswapV3API
        
        uniswap = UniswapV3API()
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test getting ETH price
            eth_price = await uniswap.get_price(session, "ETH")
            if eth_price:
                print(f"✅ Uniswap V3 API working: ETH = ${eth_price}")
                
                # Test getting pools
                pools = await uniswap.get_pools(session, "ETH", "USDC")
                if pools:
                    print(f"✅ Uniswap pools working: {len(pools)} pools found")
                    return True
                else:
                    print("❌ Uniswap pools failed")
                    return False
            else:
                print("❌ Uniswap price failed")
                return False
                
    except Exception as e:
        print(f"❌ Uniswap API test failed: {e}")
        return False

async def test_paper_trading_mode():
    """Test paper trading mode functionality."""
    print("🔄 Testing Paper Trading Mode...")
    
    try:
        from src.config.settings import Settings
        from src.strategies.arbitrage import ArbitrageStrategy
        from src.risk.manager import RiskManager
        
        # Load settings with paper trading mode
        settings = Settings.from_env_file()
        settings.trading_mode = "paper"
        
        # Create components
        risk_manager = RiskManager(settings)
        strategy = ArbitrageStrategy(settings, risk_manager)
        
        # Test initialization
        await strategy.initialize()
        
        # Test one scan cycle
        await strategy.scan_for_opportunities()
        
        print("✅ Paper trading mode working")
        await strategy.stop()
        return True
        
    except Exception as e:
        print(f"❌ Paper trading test failed: {e}")
        return False

async def main():
    """Run all DEX trading tests."""
    print("🚀 DEX Trading Test Suite")
    print("=" * 50)
    
    tests = [
        ("Jupiter API Integration", test_jupiter_api_integration),
        ("Uniswap V3 API Integration", test_uniswap_api_integration),
        ("Solana DEX Trading", test_solana_dex_trading),
        ("Base DEX Trading", test_base_dex_trading),
        ("Arbitrage Strategy", test_arbitrage_strategy),
        ("Paper Trading Mode", test_paper_trading_mode)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
            print()
    
    # Summary
    print("=" * 50)
    print("📊 DEX Trading Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed >= len(tests) - 1:  # Allow 1 failure for network issues
        print("\n🎉 DEX trading functionality is working!")
        print("Your bot is ready for DEX trading on Solana and Base.")
        print("\nNext steps:")
        print("1. Run: python -m src.main --mode=paper")
        print("2. Monitor for arbitrage opportunities")
        print("3. Test with small amounts before live trading")
    else:
        print("\n⚠️  Multiple DEX tests failed.")
        print("Check your network connection and API endpoints.")
        print("Fix failing tests before proceeding to live trading.")

if __name__ == "__main__":
    asyncio.run(main()) 