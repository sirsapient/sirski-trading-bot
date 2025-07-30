"""
Wallet management for Solana and Base chains.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from web3 import Web3
from web3.eth import AsyncEth
from eth_account import Account

from src.config.settings import Settings


@dataclass
class WalletInfo:
    """Wallet information for a specific chain."""
    address: str
    balance: float
    chain: str


class WalletManager:
    """Manages wallet connections and operations for both chains."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Solana wallet
        self.solana_client: Optional[AsyncClient] = None
        self.solana_keypair: Optional[Keypair] = None
        
        # Base wallet
        self.base_client: Optional[Web3] = None
        self.base_account: Optional[Account] = None
        
        # Wallet info cache
        self._wallet_cache: Dict[str, WalletInfo] = {}
    
    async def initialize(self):
        """Initialize wallet connections."""
        self.logger.info("Initializing wallet connections...")
        
        # Initialize Solana wallet
        await self._init_solana_wallet()
        
        # Initialize Base wallet
        await self._init_base_wallet()
        
        # Get initial balances
        await self._update_balances()
        
        self.logger.info("Wallet initialization complete")
    
    async def _init_solana_wallet(self):
        """Initialize Solana wallet connection."""
        try:
            # Create Solana client
            self.solana_client = AsyncClient(self.settings.solana_rpc_url)
            
            # Create keypair from private key
            if self.settings.solana_private_key:
                # Convert private key to bytes
                if self.settings.solana_private_key.startswith('['):
                    # Array format
                    import json
                    private_key_bytes = bytes(json.loads(self.settings.solana_private_key))
                else:
                    # Base58 format
                    import base58
                    private_key_bytes = base58.b58decode(self.settings.solana_private_key)
                
                self.solana_keypair = Keypair.from_bytes(private_key_bytes)
                self.logger.info(f"Solana wallet initialized: {self.solana_keypair.pubkey()}")
            else:
                self.logger.warning("No Solana private key provided")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Solana wallet: {e}")
    
    async def _init_base_wallet(self):
        """Initialize Base wallet connection."""
        try:
            # Create Web3 client for Base
            self.base_client = Web3(
                Web3.AsyncHTTPProvider(self.settings.base_rpc_url),
                modules={'eth': (AsyncEth,)},
                middlewares=[]
            )
            
            # Create account from private key
            if self.settings.base_private_key:
                self.base_account = Account.from_key(self.settings.base_private_key)
                self.logger.info(f"Base wallet initialized: {self.base_account.address}")
            else:
                self.logger.warning("No Base private key provided")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Base wallet: {e}")
    
    async def _update_balances(self):
        """Update wallet balances."""
        try:
            # Update Solana balance
            if self.solana_client and self.solana_keypair:
                response = await self.solana_client.get_balance(self.solana_keypair.pubkey())
                if response.value:
                    sol_balance = response.value / 1e9  # Convert lamports to SOL
                    self._wallet_cache["solana"] = WalletInfo(
                        address=str(self.solana_keypair.pubkey()),
                        balance=sol_balance,
                        chain="solana"
                    )
            
            # Update Base balance
            if self.base_client and self.base_account:
                balance = await self.base_client.eth.get_balance(self.base_account.address)
                eth_balance = self.base_client.from_wei(balance, 'ether')
                self._wallet_cache["base"] = WalletInfo(
                    address=self.base_account.address,
                    balance=float(eth_balance),
                    chain="base"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update balances: {e}")
    
    async def get_balance(self, chain: str) -> Optional[float]:
        """Get wallet balance for specified chain."""
        if chain not in self._wallet_cache:
            await self._update_balances()
        
        wallet_info = self._wallet_cache.get(chain)
        return wallet_info.balance if wallet_info else None
    
    async def get_wallet_info(self, chain: str) -> Optional[WalletInfo]:
        """Get wallet information for specified chain."""
        if chain not in self._wallet_cache:
            await self._update_balances()
        
        return self._wallet_cache.get(chain)
    
    def get_solana_keypair(self) -> Optional[Keypair]:
        """Get Solana keypair."""
        return self.solana_keypair
    
    def get_base_account(self) -> Optional[Account]:
        """Get Base account."""
        return self.base_account
    
    async def close(self):
        """Close wallet connections."""
        if self.solana_client:
            await self.solana_client.close()
        
        self.logger.info("Wallet connections closed")
    
    async def generate_wallets(self) -> Dict[str, str]:
        """Generate new wallets for both chains (for testing)."""
        wallets = {}
        
        # Generate Solana wallet
        solana_keypair = Keypair()
        wallets["solana"] = {
            "public_key": str(solana_keypair.pubkey()),
            "private_key": str(bytes(solana_keypair.secret()))
        }
        
        # Generate Base wallet
        base_account = Account.create()
        wallets["base"] = {
            "address": base_account.address,
            "private_key": base_account.key.hex()
        }
        
        return wallets 