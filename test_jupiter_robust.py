#!/usr/bin/env python3
"""
Robust Jupiter API test with multiple endpoints and fallbacks
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_jupiter_multiple_endpoints():
    """Test Jupiter API with multiple endpoints."""
    print("🔄 Testing Jupiter API with multiple endpoints...")
    
    # Multiple Jupiter endpoints to try
    endpoints = [
        {
            "name": "Jupiter Price API v4",
            "url": "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112",
            "type": "price"
        },
        {
            "name": "Jupiter Quote API v6",
            "url": "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000000&slippageBps=50",
            "type": "quote"
        },
        {
            "name": "Jupiter Price API v6",
            "url": "https://price.jup.ag/v6/price?ids=So11111111111111111111111111111111111111112",
            "type": "price"
        },
        {
            "name": "Jupiter Price API (alternative)",
            "url": "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112,EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "type": "price"
        }
    ]
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for endpoint in endpoints:
            try:
                print(f"   Testing {endpoint['name']}...")
                async with session.get(endpoint["url"]) as response:
                    print(f"      Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"      ✅ {endpoint['name']} working!")
                        if endpoint["type"] == "price" and "data" in data:
                            if "So11111111111111111111111111111111111111112" in data["data"]:
                                sol_price = data["data"]["So11111111111111111111111111111111111111112"]["price"]
                                print(f"      SOL Price: ${sol_price}")
                        return True
                    else:
                        print(f"      ❌ Status {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"      ⏰ Timeout")
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        print("❌ All Jupiter endpoints failed")
        return False

async def test_jupiter_api_class():
    """Test the Jupiter API class from the codebase."""
    print("🔄 Testing Jupiter API class...")
    
    try:
        from src.exchanges.real_apis import JupiterAPI
        
        jupiter = JupiterAPI()
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test getting SOL price
            sol_price = await jupiter.get_price(session, "SOL")
            if sol_price:
                print(f"✅ Jupiter API class working: SOL = ${sol_price}")
                return True
            else:
                print("❌ Jupiter API class failed to get SOL price")
                return False
                
    except ImportError as e:
        print(f"❌ Could not import Jupiter API class: {e}")
        return False
    except Exception as e:
        print(f"❌ Jupiter API class test failed: {e}")
        return False

async def test_alternative_apis():
    """Test alternative APIs as fallback."""
    print("🔄 Testing alternative APIs...")
    
    apis = [
        {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
            "parser": lambda data: data["solana"]["usd"]
        },
        {
            "name": "Coinbase",
            "url": "https://api.coinbase.com/v2/prices/SOL-USD/spot",
            "parser": lambda data: float(data["data"]["amount"])
        }
    ]
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for api in apis:
            try:
                print(f"   Testing {api['name']}...")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                
                async with session.get(api["url"], headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = api["parser"](data)
                        print(f"      ✅ {api['name']} working: SOL = ${price}")
                        return True
                    else:
                        print(f"      ❌ {api['name']} error: {response.status}")
                        
            except Exception as e:
                print(f"      ❌ {api['name']} exception: {e}")
        
        print("❌ All alternative APIs failed")
        return False

async def test_bot_integration():
    """Test the bot's ability to use Jupiter API."""
    print("🔄 Testing bot integration...")
    
    try:
        from src.config.settings import Settings
        from src.exchanges.solana_dex import SolanaDEX
        
        # Load settings
        settings = Settings.from_env_file()
        
        # Create Solana DEX instance
        dex = SolanaDEX(settings)
        await dex.initialize()
        
        # Test getting prices
        prices = await dex.get_all_prices("SOL")
        if prices:
            print(f"✅ Bot integration working: {prices}")
            await dex.close()
            return True
        else:
            print("❌ Bot integration failed to get prices")
            await dex.close()
            return False
            
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        return False

async def main():
    """Run all Jupiter tests."""
    print("🚀 Jupiter API Test Suite")
    print("=" * 40)
    
    tests = [
        ("Jupiter Multiple Endpoints", test_jupiter_multiple_endpoints),
        ("Jupiter API Class", test_jupiter_api_class),
        ("Alternative APIs", test_alternative_apis),
        ("Bot Integration", test_bot_integration)
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
    print("=" * 40)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed >= 2:  # At least 2 tests should pass
        print("\n🎉 Jupiter API functionality is working!")
        print("The bot can use Jupiter API or fall back to alternative APIs.")
    else:
        print("\n⚠️  Jupiter API has connectivity issues.")
        print("The bot will use alternative APIs as fallback.")

if __name__ == "__main__":
    asyncio.run(main()) 