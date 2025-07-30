#!/usr/bin/env python3
"""
Simple Jupiter API test
"""

import asyncio
import aiohttp

async def test_jupiter():
    """Test Jupiter API connectivity."""
    print("Testing Jupiter API...")
    
    urls = [
        "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112",
        "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000000&slippageBps=50"
    ]
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, url in enumerate(urls):
            try:
                print(f"Testing URL {i+1}: {url}")
                async with session.get(url) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"Data: {data}")
                        return True
                    else:
                        print(f"Error: {response.status}")
                        
            except Exception as e:
                print(f"Exception: {e}")
        
        return False

if __name__ == "__main__":
    result = asyncio.run(test_jupiter())
    print(f"Test result: {result}") 