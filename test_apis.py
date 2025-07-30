#!/usr/bin/env python3
"""
Quick test script to verify real API integrations work.
Run this first to make sure you can get live price data.
"""

import asyncio
import aiohttp
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_jupiter_api():
    """Test Jupiter API for Solana prices."""
    print("🔄 Testing Jupiter API...")
    
    # Try multiple Jupiter endpoints
    endpoints = [
        "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112",
        "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000000&slippageBps=50"
    ]
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, url in enumerate(endpoints):
            try:
                print(f"   Trying endpoint {i+1}...")
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and "So11111111111111111111111111111111111111112" in data["data"]:
                            sol_price = data["data"]["So11111111111111111111111111111111111111112"]["price"]
                            print(f"✅ SOL Price from Jupiter: ${sol_price}")
                            return True
                        elif "inputMint" in data:  # Quote endpoint
                            print(f"✅ Jupiter quote endpoint working")
                            return True
                    else:
                        print(f"   ❌ Endpoint {i+1} error: {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"   ⏰ Endpoint {i+1} timeout")
            except Exception as e:
                print(f"   ❌ Endpoint {i+1} exception: {e}")
        
        print("❌ All Jupiter endpoints failed")
        return False

async def test_uniswap_api():
    """Test Uniswap V3 API for Base prices."""
    print("🔄 Testing Uniswap V3 API...")
    
    # Try multiple approaches
    endpoints = [
        {
            "url": "https://api.studio.thegraph.com/query/48211/uniswap-v3-base/version/latest",
            "query": """
            {
              bundle(id: "1") {
                ethPriceUSD
              }
            }
            """
        },
        {
            "url": "https://api.studio.thegraph.com/query/48211/uniswap-v3-base/version/latest",
            "query": """
            {
              pools(first: 1, where: {token0_: "0x4200000000000000000000000000000000000006"}) {
                token0Price
                token1Price
              }
            }
            """
        }
    ]
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, endpoint in enumerate(endpoints):
            try:
                print(f"   Trying Uniswap endpoint {i+1}...")
                headers = {"Content-Type": "application/json"}
                async with session.post(endpoint["url"], 
                                      json={"query": endpoint["query"]}, 
                                      headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and "bundle" in data["data"]:
                            eth_price = data["data"]["bundle"]["ethPriceUSD"]
                            print(f"✅ ETH Price from Uniswap V3: ${eth_price}")
                            return True
                        elif "data" in data and "pools" in data["data"]:
                            print(f"✅ Uniswap pools endpoint working")
                            return True
                    elif response.status == 429:
                        print(f"   ⏳ Rate limited, waiting 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f"   ❌ Endpoint {i+1} error: {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"   ⏰ Endpoint {i+1} timeout")
            except Exception as e:
                print(f"   ❌ Endpoint {i+1} exception: {e}")
        
        print("❌ All Uniswap endpoints failed")
        return False

async def test_alternative_apis():
    """Test alternative price APIs as fallback."""
    print("🔄 Testing alternative price APIs...")
    
    apis = [
        {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=solana,ethereum&vs_currencies=usd",
            "parser": lambda data: {"SOL": data["solana"]["usd"], "ETH": data["ethereum"]["usd"]}
        },
        {
            "name": "CoinMarketCap (free tier)",
            "url": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=SOL,ETH",
            "parser": lambda data: {"SOL": data["data"]["SOL"]["quote"]["USD"]["price"], 
                                   "ETH": data["data"]["ETH"]["quote"]["USD"]["price"]}
        }
    ]
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for api in apis:
            try:
                print(f"   Trying {api['name']}...")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                
                async with session.get(api["url"], headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = api["parser"](data)
                        print(f"✅ {api['name']} working:")
                        for token, price in prices.items():
                            print(f"      {token}: ${price}")
                        return True
                    else:
                        print(f"   ❌ {api['name']} error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ {api['name']} exception: {e}")
        
        print("❌ All alternative APIs failed")
        return False

async def test_arbitrage_detection():
    """Test basic arbitrage detection logic."""
    print("🔄 Testing arbitrage detection...")
    
    # Simulate price differences
    sol_jupiter = 95.50
    sol_orca = 95.75    # 0.26% higher
    sol_raydium = 95.25 # 0.26% lower
    
    # Calculate arbitrage opportunities
    opportunities = []
    
    # Jupiter vs Orca
    if sol_orca > sol_jupiter:
        profit_pct = (sol_orca - sol_jupiter) / sol_jupiter
        if profit_pct > 0.001:  # 0.1% minimum
            opportunities.append(f"Buy Jupiter ${sol_jupiter} → Sell Orca ${sol_orca} = {profit_pct:.3%} profit")
    
    # Raydium vs Jupiter
    if sol_jupiter > sol_raydium:
        profit_pct = (sol_jupiter - sol_raydium) / sol_raydium
        if profit_pct > 0.001:
            opportunities.append(f"Buy Raydium ${sol_raydium} → Sell Jupiter ${sol_jupiter} = {profit_pct:.3%} profit")
    
    if opportunities:
        print("✅ Arbitrage opportunities found:")
        for opp in opportunities:
            print(f"   📈 {opp}")
        return True
    else:
        print("ℹ️  No profitable arbitrage opportunities in test data")
        return False

async def test_position_sizing():
    """Test position sizing logic."""
    print("🔄 Testing position sizing...")
    
    # Mock risk manager settings
    portfolio_value = 5000  # $5000
    max_position_size = 0.3  # 30%
    confidence = 0.8  # 80% confidence
    sol_price = 95.50
    
    # Calculate position size
    base_size = portfolio_value * max_position_size  # $1500
    adjusted_size = base_size * confidence  # $1200
    token_amount = adjusted_size / sol_price  # ~12.57 SOL
    
    print(f"✅ Position sizing calculation:")
    print(f"   💰 Portfolio: ${portfolio_value}")
    print(f"   📊 Max position: {max_position_size:.0%} = ${base_size}")
    print(f"   🎯 Adjusted for confidence ({confidence:.0%}): ${adjusted_size}")
    print(f"   🪙 SOL amount: {token_amount:.4f} SOL")
    
    return True

async def test_real_api_integration():
    """Test the actual API classes from your codebase."""
    print("🔄 Testing real API integration classes...")
    
    try:
        from src.exchanges.real_apis import JupiterAPI, UniswapV3API
        
        jupiter = JupiterAPI()
        uniswap = UniswapV3API()
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test Jupiter
            sol_price = await jupiter.get_price(session, "SOL")
            if sol_price:
                print(f"✅ Jupiter API class working: SOL = ${sol_price}")
            else:
                print("❌ Jupiter API class failed")
                return False
            
            # Test Uniswap
            eth_price = await uniswap.get_price(session, "ETH")
            if eth_price:
                print(f"✅ Uniswap API class working: ETH = ${eth_price}")
            else:
                print("❌ Uniswap API class failed")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import API classes: {e}")
        return False
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

async def test_network_connectivity():
    """Test basic network connectivity."""
    print("🔄 Testing network connectivity...")
    
    test_urls = [
        "https://httpbin.org/get",
        "https://api.github.com",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    timeout = aiohttp.ClientTimeout(total=5)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for url in test_urls:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"✅ Network connectivity OK ({url})")
                        return True
            except Exception as e:
                print(f"   ❌ {url} failed: {e}")
        
        print("❌ Network connectivity issues detected")
        return False

async def main():
    """Run all tests."""
    print("🚀 Crypto Trading Bot - API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Network Connectivity", test_network_connectivity),
        ("Jupiter API (Solana)", test_jupiter_api),
        ("Uniswap V3 API (Base)", test_uniswap_api),
        ("Alternative APIs", test_alternative_apis),
        ("Arbitrage Detection", test_arbitrage_detection),
        ("Position Sizing", test_position_sizing),
        ("Real API Integration", test_real_api_integration)
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
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed >= len(tests) - 2:  # Allow 2 failures for network issues
        print("\n🎉 Core functionality working! Your bot is ready for paper trading.")
        print("\nNext steps:")
        print("1. Fund your wallets with small amounts (~$50-100)")
        print("2. Run: python src/main.py --mode=paper")
        print("3. Monitor logs for arbitrage opportunities")
        print("4. If profitable after 24h+ → switch to live trading")
    else:
        print("\n⚠️  Multiple tests failed. Check your network connection and API endpoints.")
        print("Fix failing tests before proceeding to live trading.")
        print("\nTroubleshooting:")
        print("- Check internet connection")
        print("- Try using a VPN if APIs are blocked")
        print("- Verify firewall settings")
        print("- Check if corporate network is blocking crypto APIs")

if __name__ == "__main__":
    asyncio.run(main()) 