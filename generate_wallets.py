#!/usr/bin/env python3
"""
Wallet generation script for Solana and Base chains.
This script generates new wallets for testing purposes.
"""

import json
import base58
from solders.keypair import Keypair
from eth_account import Account
from pathlib import Path


def generate_solana_wallet():
    """Generate a new Solana wallet."""
    keypair = Keypair()
    
    return {
        "public_key": str(keypair.pubkey()),
        "private_key": base58.b58encode(bytes(keypair.secret())).decode('utf-8'),
        "private_key_array": list(bytes(keypair.secret()))
    }


def generate_base_wallet():
    """Generate a new Base wallet."""
    account = Account.create()
    
    return {
        "address": account.address,
        "private_key": account.key.hex(),
        "private_key_with_0x": "0x" + account.key.hex()
    }


def main():
    """Generate wallets and save to file."""
    print("Generating new wallets for testing...")
    
    # Generate wallets
    solana_wallet = generate_solana_wallet()
    base_wallet = generate_base_wallet()
    
    # Create wallets object
    wallets = {
        "solana": solana_wallet,
        "base": base_wallet,
        "generated_at": "2024-01-01T00:00:00Z"
    }
    
    # Save to file
    output_file = Path("generated_wallets.json")
    with open(output_file, 'w') as f:
        json.dump(wallets, f, indent=2)
    
    print(f"Wallets generated and saved to {output_file}")
    print("\n=== WALLET INFORMATION ===")
    print(f"Solana Public Key: {solana_wallet['public_key']}")
    print(f"Base Address: {base_wallet['address']}")
    print("\n⚠️  IMPORTANT: Keep these private keys secure!")
    print("⚠️  These are for testing only - don't use with real funds!")
    
    # Create .env template
    env_content = f"""# Wallet Configuration
SOLANA_PRIVATE_KEY={solana_wallet['private_key_array']}
BASE_PRIVATE_KEY={base_wallet['private_key_with_0x']}

# RPC Endpoints (use free tiers to start)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BASE_RPC_URL=https://mainnet.base.org

# Trading Parameters
MIN_ARBITRAGE_PROFIT=0.001    # 0.1%
MAX_POSITION_SIZE=0.3         # 30% of portfolio
MIN_TRADE_SIZE=500           # $500 minimum
MAX_DAILY_LOSS=0.05          # 5% daily loss limit

# Monitoring
DISCORD_WEBHOOK_URL=your_discord_webhook_for_alerts

# Jupiter API (for Solana price data)
JUPITER_API_URL=https://price.jup.ag/v4

# Uniswap V3 API (for Base price data)
UNISWAP_V3_API_URL=https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3

# Trading pairs to monitor
SOLANA_PAIRS=SOL/USDC,ETH/USDC,RAY/USDC
BASE_PAIRS=ETH/USDC,WETH/USDC

# Risk management
STOP_LOSS_PERCENTAGE=0.03    # 3% stop loss
TAKE_PROFIT_PERCENTAGE=0.05  # 5% take profit
MAX_SLIPPAGE=0.005          # 0.5% max slippage
"""
    
    env_file = Path(".env")
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"\nEnvironment file created: {env_file}")
    print("\nNext steps:")
    print("1. Fund your wallets with small amounts for testing")
    print("2. Run: python src/main.py --mode=paper")
    print("3. Monitor the bot's performance")
    print("4. Only switch to live trading after successful paper trading")


if __name__ == "__main__":
    main() 