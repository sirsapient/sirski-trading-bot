"""
Basic tests to verify the project setup.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.config.settings import Settings
        from src.utils.wallet import WalletManager
        from src.risk.manager import RiskManager
        from src.exchanges.solana_dex import SolanaDEX
        from src.exchanges.base_dex import BaseDEX
        from src.strategies.arbitrage import ArbitrageStrategy
        from src.strategies.swing_trading import SwingTradingStrategy
        from src.indicators.technical import TechnicalIndicators
        from src.utils.logger import setup_logging
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_settings_creation():
    """Test settings creation."""
    from src.config.settings import Settings
    
    # Test with default values
    settings = Settings(
        solana_private_key="test",
        base_private_key="test",
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
    
    assert settings.min_arbitrage_profit == 0.001
    assert settings.max_position_size == 0.3
    assert len(settings.get_solana_pairs()) == 1
    assert len(settings.get_base_pairs()) == 1


def test_technical_indicators():
    """Test technical indicators calculations."""
    from src.indicators.technical import TechnicalIndicators
    import numpy as np
    
    # Test data
    prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
    
    # Test RSI
    rsi_result = TechnicalIndicators.calculate_rsi(prices, period=5)
    assert isinstance(rsi_result.value, float)
    assert 0 <= rsi_result.value <= 100
    
    # Test EMA
    ema = TechnicalIndicators.calculate_ema(prices, period=5)
    assert isinstance(ema, float)
    assert ema > 0
    
    # Test SMA
    sma = TechnicalIndicators.calculate_sma(prices, period=5)
    assert isinstance(sma, float)
    assert sma > 0
    
    # Test MACD
    macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(prices)
    assert isinstance(macd_line, float)
    assert isinstance(signal_line, float)
    assert isinstance(histogram, float)


def test_risk_manager():
    """Test risk manager functionality."""
    from src.risk.manager import RiskManager
    from src.config.settings import Settings
    
    # Create test settings
    settings = Settings(
        solana_private_key="test",
        base_private_key="test",
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
    
    # Test portfolio value setting
    risk_manager.set_initial_portfolio_value(10000)
    assert risk_manager.portfolio_value == 10000
    
    # Test position size calculation
    position_size = risk_manager.calculate_position_size("SOL/USDC", 100.0, 0.8)
    assert position_size > 0
    
    # Test position opening
    can_open = risk_manager.can_open_position("SOL/USDC", "long", 10.0, 100.0)
    assert isinstance(can_open, bool)


if __name__ == "__main__":
    pytest.main([__file__]) 