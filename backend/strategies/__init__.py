"""
GOMALE OS Trading Strategies

This module implements 18 institutional-grade trading strategies with risk management.

Strategy Categories:
- Trend Following: EMA Crossover, MACD, Supertrend, ADX, Parabolic SAR, Ichimoku
- Mean Reversion: RSI, Bollinger Bands, Stochastic, Williams %R
- Breakout: Volume Breakout, ATR Breakout, Donchian Channel, Momentum Burst
- Pattern/Advanced: Engulfing, Stop Hunt, Support/Resistance, MTF Confluence
"""

from .strategies import (
    STRATEGIES,
    get_strategy,
    list_strategies,
    SignalType,
    TradeSignal,
    TechnicalIndicators,
    # Strategy classes
    EMAStrategy,
    MACDStrategy,
    SupertrendStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    VolumeBreakoutStrategy,
    StochasticStrategy,
    ADXStrategy,
    ATRBreakoutStrategy,
    DonchianChannelStrategy,
    ParabolicSARStrategy,
    WilliamsRStrategy,
    EngulfingStrategy,
    StopHuntStrategy,
    SupportResistanceStrategy,
    MomentumBurstStrategy,
    IchimokuStrategy,
    MTFConfluenceStrategy,
)

__all__ = [
    'STRATEGIES',
    'get_strategy',
    'list_strategies',
    'SignalType',
    'TradeSignal',
    'TechnicalIndicators',
]