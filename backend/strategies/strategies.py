"""
GOMALE OS Trading Strategies - Complete Implementation
18 institutional-grade strategies with risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradeSignal:
    symbol: str
    signal: SignalType
    strategy: str
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    reason: str = ""
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "strategy": self.strategy,
            "confidence": round(self.confidence, 4),
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size": self.position_size,
            "reason": self.reason,
            "timestamp": self.timestamp
        }

class TechnicalIndicators:
    """Technical analysis indicators library"""
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        sma = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        atr = TechnicalIndicators.atr(high, low, close, period)
        hl2 = (high + low) / 2
        
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)
        
        for i in range(len(close)):
            if i == 0:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = 1
            else:
                if close.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
                    direction.iloc[i] = -1
        
        return supertrend, direction
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=d_period).mean()
        return k, d
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, af: float = 0.02, max_af: float = 0.2) -> pd.Series:
        psar = pd.Series(index=high.index, dtype=float)
        trend = pd.Series(index=high.index, dtype=int)
        
        psar.iloc[0] = low.iloc[0]
        trend.iloc[0] = 1
        ep = high.iloc[0]
        af_current = af
        
        for i in range(1, len(high)):
            if trend.iloc[i-1] == 1:  # Uptrend
                psar.iloc[i] = psar.iloc[i-1] + af_current * (ep - psar.iloc[i-1])
                if low.iloc[i] < psar.iloc[i]:
                    trend.iloc[i] = -1
                    psar.iloc[i] = ep
                    ep = low.iloc[i]
                    af_current = af
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af_current = min(af_current + af, max_af)
            else:  # Downtrend
                psar.iloc[i] = psar.iloc[i-1] - af_current * (psar.iloc[i-1] - ep)
                if high.iloc[i] > psar.iloc[i]:
                    trend.iloc[i] = 1
                    psar.iloc[i] = ep
                    ep = high.iloc[i]
                    af_current = af
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af_current = min(af_current + af, max_af)
        
        return psar

# ============================================================================
# STRATEGY 1: EMA CROSSOVER
# ============================================================================

class EMAStrategy:
    """EMA Crossover Strategy - Classic trend following"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"ema_crossover_{fast_period}_{slow_period}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            ema_fast = TechnicalIndicators.ema(close, self.fast_period)
            ema_slow = TechnicalIndicators.ema(close, self.slow_period)
            
            # Current and previous values
            curr_fast = ema_fast.iloc[-1]
            curr_slow = ema_slow.iloc[-1]
            prev_fast = ema_fast.iloc[-2]
            prev_slow = ema_slow.iloc[-2]
            
            current_price = close.iloc[-1]
            
            # Crossover detection
            bullish_cross = prev_fast < prev_slow and curr_fast > curr_slow
            bearish_cross = prev_fast > prev_slow and curr_fast < curr_slow
            
            if bullish_cross:
                confidence = min(abs(curr_fast - curr_slow) / curr_slow * 100, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"EMA{self.fast_period} crossed above EMA{self.slow_period}"
                )
            elif bearish_cross:
                confidence = min(abs(curr_fast - curr_slow) / curr_slow * 100, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"EMA{self.fast_period} crossed below EMA{self.slow_period}"
                )
            
            trend_strength = abs(curr_fast - curr_slow) / curr_slow
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=trend_strength,
                entry_price=current_price,
                reason=f"No crossover. EMA{self.fast_period}: {curr_fast:.2f}, EMA{self.slow_period}: {curr_slow:.2f}"
            )
            
        except Exception as e:
            logger.error(f"EMA Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 2: MACD STRATEGY
# ============================================================================

class MACDStrategy:
    """MACD Strategy - Momentum-based trend following"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.name = f"macd_{fast}_{slow}_{signal}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            macd_line, signal_line, histogram = TechnicalIndicators.macd(close, self.fast, self.slow, self.signal)
            
            curr_macd = macd_line.iloc[-1]
            curr_signal = signal_line.iloc[-1]
            curr_hist = histogram.iloc[-1]
            prev_hist = histogram.iloc[-2]
            
            current_price = close.iloc[-1]
            
            # Bullish: MACD crosses above signal AND histogram turning positive
            bullish = curr_macd > curr_signal and curr_hist > 0 and prev_hist <= 0
            # Bearish: MACD crosses below signal AND histogram turning negative
            bearish = curr_macd < curr_signal and curr_hist < 0 and prev_hist >= 0
            
            if bullish:
                confidence = min(abs(curr_hist) / abs(close.mean()) * 100, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"MACD bullish crossover. Histogram: {curr_hist:.4f}"
                )
            elif bearish:
                confidence = min(abs(curr_hist) / abs(close.mean()) * 100, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"MACD bearish crossover. Histogram: {curr_hist:.4f}"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(curr_hist) / abs(close.mean()) if close.mean() != 0 else 0,
                entry_price=current_price,
                reason=f"MACD: {curr_macd:.4f}, Signal: {curr_signal:.4f}"
            )
            
        except Exception as e:
            logger.error(f"MACD Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 3: SUPERTREND
# ============================================================================

class SupertrendStrategy:
    """Supertrend Strategy - ATR-based trend following"""
    
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        self.period = period
        self.multiplier = multiplier
        self.name = f"supertrend_{period}_{multiplier}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            supertrend, direction = TechnicalIndicators.supertrend(high, low, close, self.period, self.multiplier)
            
            curr_dir = direction.iloc[-1]
            prev_dir = direction.iloc[-2]
            current_price = close.iloc[-1]
            
            # Direction change
            bullish_flip = curr_dir == 1 and prev_dir == -1
            bearish_flip = curr_dir == -1 and prev_dir == 1
            
            if bullish_flip:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=0.8,
                    entry_price=current_price,
                    stop_loss=supertrend.iloc[-1],
                    reason=f"Supertrend flipped bullish at {supertrend.iloc[-1]:.2f}"
                )
            elif bearish_flip:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=0.8,
                    entry_price=current_price,
                    stop_loss=supertrend.iloc[-1],
                    reason=f"Supertrend flipped bearish at {supertrend.iloc[-1]:.2f}"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.5,
                entry_price=current_price,
                reason=f"Supertrend: {'Bullish' if curr_dir == 1 else 'Bearish'} at {supertrend.iloc[-1]:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Supertrend Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 4: RSI STRATEGY
# ============================================================================

class RSIStrategy:
    """RSI Mean Reversion Strategy"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"rsi_{period}_{oversold}_{overbought}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            rsi = TechnicalIndicators.rsi(close, self.period)
            
            curr_rsi = rsi.iloc[-1]
            prev_rsi = rsi.iloc[-2]
            current_price = close.iloc[-1]
            
            # Bullish: RSI crosses above oversold
            bullish = prev_rsi < self.oversold and curr_rsi > self.oversold
            # Bearish: RSI crosses below overbought
            bearish = prev_rsi > self.overbought and curr_rsi < self.overbought
            
            if bullish:
                confidence = (self.oversold - curr_rsi) / self.oversold if curr_rsi < self.oversold else 0.5
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=min(confidence, 1.0),
                    entry_price=current_price,
                    reason=f"RSI ({curr_rsi:.2f}) crossed above oversold ({self.oversold})"
                )
            elif bearish:
                confidence = (curr_rsi - self.overbought) / (100 - self.overbought) if curr_rsi > self.overbought else 0.5
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=min(confidence, 1.0),
                    entry_price=current_price,
                    reason=f"RSI ({curr_rsi:.2f}) crossed below overbought ({self.overbought})"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(50 - curr_rsi) / 50,
                entry_price=current_price,
                reason=f"RSI: {curr_rsi:.2f} (neutral zone)"
            )
            
        except Exception as e:
            logger.error(f"RSI Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 5: BOLLINGER BANDS
# ============================================================================

class BollingerBandsStrategy:
    """Bollinger Bands Mean Reversion Strategy"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        self.name = f"bollinger_{period}_{std_dev}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            upper, middle, lower = TechnicalIndicators.bollinger_bands(close, self.period, self.std_dev)
            
            curr_price = close.iloc[-1]
            curr_upper = upper.iloc[-1]
            curr_lower = lower.iloc[-1]
            curr_middle = middle.iloc[-1]
            
            prev_price = close.iloc[-2]
            
            # Bullish: Price crosses below lower band and returns
            bullish = curr_price > curr_lower and prev_price <= lower.iloc[-2]
            # Bearish: Price crosses above upper band and returns
            bearish = curr_price < curr_upper and prev_price >= upper.iloc[-2]
            
            if bullish:
                confidence = min((curr_middle - curr_price) / (curr_middle - curr_lower), 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Price bounced off lower Bollinger Band ({curr_lower:.2f})"
                )
            elif bearish:
                confidence = min((curr_price - curr_middle) / (curr_upper - curr_middle), 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Price rejected from upper Bollinger Band ({curr_upper:.2f})"
                )
            
            # Position in bands
            position = (curr_price - curr_lower) / (curr_upper - curr_lower) if curr_upper != curr_lower else 0.5
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(0.5 - position) * 2,
                entry_price=curr_price,
                reason=f"Price at {position*100:.1f}% of Bollinger range"
            )
            
        except Exception as e:
            logger.error(f"Bollinger Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 6: VOLUME BREAKOUT
# ============================================================================

class VolumeBreakoutStrategy:
    """Volume-based Breakout Strategy"""
    
    def __init__(self, volume_period: int = 20, breakout_threshold: float = 2.0):
        self.volume_period = volume_period
        self.breakout_threshold = breakout_threshold
        self.name = f"volume_breakout_{volume_period}_{breakout_threshold}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            volume = df['volume']
            high = df['high']
            low = df['low']
            
            avg_volume = volume.rolling(window=self.volume_period).mean()
            
            curr_price = close.iloc[-1]
            curr_volume = volume.iloc[-1]
            curr_avg = avg_volume.iloc[-1]
            
            # Volume spike
            volume_spike = curr_volume > curr_avg * self.breakout_threshold
            
            # Price range expansion
            price_range = high.iloc[-1] - low.iloc[-1]
            avg_range = (high - low).rolling(window=self.volume_period).mean().iloc[-1]
            range_expansion = price_range > avg_range * 1.5
            
            # Breakout direction
            prev_high = high.iloc[-self.volume_period:-1].max()
            prev_low = low.iloc[-self.volume_period:-1].min()
            
            bullish_breakout = curr_price > prev_high and volume_spike and range_expansion
            bearish_breakout = curr_price < prev_low and volume_spike and range_expansion
            
            if bullish_breakout:
                confidence = min((curr_volume / curr_avg - 1) / 2, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Bullish volume breakout. Volume: {curr_volume/curr_avg:.2f}x average"
                )
            elif bearish_breakout:
                confidence = min((curr_volume / curr_avg - 1) / 2, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Bearish volume breakout. Volume: {curr_volume/curr_avg:.2f}x average"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.3,
                entry_price=curr_price,
                reason=f"Volume: {curr_volume/curr_avg:.2f}x average (no breakout)"
            )
            
        except Exception as e:
            logger.error(f"Volume Breakout Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 7: STOCHASTIC OSCILLATOR
# ============================================================================

class StochasticStrategy:
    """Stochastic Oscillator Mean Reversion"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3, oversold: int = 20, overbought: int = 80):
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"stochastic_{k_period}_{d_period}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            k, d = TechnicalIndicators.stochastic(high, low, close, self.k_period, self.d_period)
            
            curr_k = k.iloc[-1]
            curr_d = d.iloc[-1]
            prev_k = k.iloc[-2]
            
            current_price = close.iloc[-1]
            
            # Bullish: %K crosses above %D in oversold zone
            bullish = prev_k < curr_d and curr_k > curr_d and curr_k < self.oversold
            # Bearish: %K crosses below %D in overbought zone
            bearish = prev_k > curr_d and curr_k < curr_d and curr_k > self.overbought
            
            if bullish:
                confidence = (self.oversold - curr_k) / self.oversold
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=min(confidence, 1.0),
                    entry_price=current_price,
                    reason=f"Stochastic bullish crossover in oversold ({curr_k:.2f})"
                )
            elif bearish:
                confidence = (curr_k - self.overbought) / (100 - self.overbought)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=min(confidence, 1.0),
                    entry_price=current_price,
                    reason=f"Stochastic bearish crossover in overbought ({curr_k:.2f})"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(50 - curr_k) / 50,
                entry_price=current_price,
                reason=f"Stochastic %K: {curr_k:.2f}, %D: {curr_d:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Stochastic Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 8: ADX TREND STRENGTH
# ============================================================================

class ADXStrategy:
    """ADX Trend Strength Strategy"""
    
    def __init__(self, period: int = 14, adx_threshold: int = 25):
        self.period = period
        self.adx_threshold = adx_threshold
        self.name = f"adx_{period}_{adx_threshold}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            adx, plus_di, minus_di = TechnicalIndicators.adx(high, low, close, self.period)
            
            curr_adx = adx.iloc[-1]
            curr_plus = plus_di.iloc[-1]
            curr_minus = minus_di.iloc[-1]
            prev_plus = plus_di.iloc[-2]
            prev_minus = minus_di.iloc[-2]
            
            current_price = close.iloc[-1]
            
            # Strong trend required
            strong_trend = curr_adx > self.adx_threshold
            
            # DI crossover
            bullish_cross = prev_plus < prev_minus and curr_plus > curr_minus
            bearish_cross = prev_plus > prev_minus and curr_plus < curr_minus
            
            if bullish_cross and strong_trend:
                confidence = min(curr_adx / 50, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"Strong bullish trend (ADX: {curr_adx:.2f})"
                )
            elif bearish_cross and strong_trend:
                confidence = min(curr_adx / 50, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=current_price,
                    reason=f"Strong bearish trend (ADX: {curr_adx:.2f})"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=curr_adx / 100 if not pd.isna(curr_adx) else 0,
                entry_price=current_price,
                reason=f"ADX: {curr_adx:.2f}, +DI: {curr_plus:.2f}, -DI: {curr_minus:.2f}"
            )
            
        except Exception as e:
            logger.error(f"ADX Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 9: ATR BREAKOUT
# ============================================================================

class ATRBreakoutStrategy:
    """ATR-based Volatility Breakout"""
    
    def __init__(self, atr_period: int = 14, multiplier: float = 2.0):
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.name = f"atr_breakout_{atr_period}_{multiplier}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            atr = TechnicalIndicators.atr(high, low, close, self.atr_period)
            
            curr_close = close.iloc[-1]
            curr_atr = atr.iloc[-1]
            prev_close = close.iloc[-2]
            
            # ATR bands
            upper_band = prev_close + (self.multiplier * curr_atr)
            lower_band = prev_close - (self.multiplier * curr_atr)
            
            bullish = curr_close > upper_band
            bearish = curr_close < lower_band
            
            if bullish:
                confidence = min((curr_close - upper_band) / curr_atr, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_close - (2 * curr_atr),
                    reason=f"ATR breakout above {upper_band:.2f} (ATR: {curr_atr:.2f})"
                )
            elif bearish:
                confidence = min((lower_band - curr_close) / curr_atr, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_close + (2 * curr_atr),
                    reason=f"ATR breakout below {lower_band:.2f} (ATR: {curr_atr:.2f})"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.3,
                entry_price=curr_close,
                reason=f"Within ATR bands. Upper: {upper_band:.2f}, Lower: {lower_band:.2f}"
            )
            
        except Exception as e:
            logger.error(f"ATR Breakout Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 10: DONCHIAN CHANNEL
# ============================================================================

class DonchianChannelStrategy:
    """Donchian Channel Breakout Strategy"""
    
    def __init__(self, period: int = 20):
        self.period = period
        self.name = f"donchian_{period}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            
            upper_channel = high.rolling(window=self.period).max()
            lower_channel = low.rolling(window=self.period).min()
            
            curr_price = close.iloc[-1]
            curr_upper = upper_channel.iloc[-1]
            curr_lower = lower_channel.iloc[-1]
            prev_upper = upper_channel.iloc[-2]
            prev_lower = lower_channel.iloc[-2]
            
            # Breakout
            bullish = curr_price > prev_upper
            bearish = curr_price < prev_lower
            
            if bullish:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=0.75,
                    entry_price=curr_price,
                    stop_loss=curr_lower,
                    reason=f"Donchian channel breakout above {curr_upper:.2f}"
                )
            elif bearish:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=0.75,
                    entry_price=curr_price,
                    stop_loss=curr_upper,
                    reason=f"Donchian channel breakdown below {curr_lower:.2f}"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.3,
                entry_price=curr_price,
                reason=f"Within Donchian channel: {curr_lower:.2f} - {curr_upper:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Donchian Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 11: PARABOLIC SAR
# ============================================================================

class ParabolicSARStrategy:
    """Parabolic SAR Trend Following"""
    
    def __init__(self, af: float = 0.02, max_af: float = 0.2):
        self.af = af
        self.max_af = max_af
        self.name = f"parabolic_sar_{af}_{max_af}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            psar = TechnicalIndicators.parabolic_sar(high, low, self.af, self.max_af)
            
            curr_price = close.iloc[-1]
            curr_psar = psar.iloc[-1]
            prev_psar = psar.iloc[-2]
            
            # PSAR flip
            above_prev = close.iloc[-2] > prev_psar
            above_curr = curr_price > curr_psar
            
            bullish_flip = above_curr and not above_prev
            bearish_flip = not above_curr and above_prev
            
            if bullish_flip:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=0.7,
                    entry_price=curr_price,
                    stop_loss=curr_psar,
                    reason=f"Parabolic SAR flipped bullish at {curr_psar:.2f}"
                )
            elif bearish_flip:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=0.7,
                    entry_price=curr_price,
                    stop_loss=curr_psar,
                    reason=f"Parabolic SAR flipped bearish at {curr_psar:.2f}"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.4,
                entry_price=curr_price,
                reason=f"PSAR: {curr_psar:.2f}, Price: {curr_price:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Parabolic SAR Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 12: WILLIAMS %R
# ============================================================================

class WilliamsRStrategy:
    """Williams %R Mean Reversion"""
    
    def __init__(self, period: int = 14, oversold: int = -80, overbought: int = -20):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"williams_r_{period}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            high, low, close = df['high'], df['low'], df['close']
            williams_r = TechnicalIndicators.williams_r(high, low, close, self.period)
            
            curr_wr = williams_r.iloc[-1]
            prev_wr = williams_r.iloc[-2]
            curr_price = close.iloc[-1]
            
            # Bullish: crosses above oversold
            bullish = prev_wr < self.oversold and curr_wr > self.oversold
            # Bearish: crosses below overbought
            bearish = prev_wr > self.overbought and curr_wr < self.overbought
            
            if bullish:
                confidence = min(abs(curr_wr - self.oversold) / 20, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Williams %R ({curr_wr:.2f}) crossed above oversold"
                )
            elif bearish:
                confidence = min(abs(curr_wr - self.overbought) / 20, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Williams %R ({curr_wr:.2f}) crossed below overbought"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(-50 - curr_wr) / 50,
                entry_price=curr_price,
                reason=f"Williams %R: {curr_wr:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Williams %R Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 13: ENGULFING PATTERN
# ============================================================================

class EngulfingStrategy:
    """Candlestick Engulfing Pattern Strategy"""
    
    def __init__(self):
        self.name = "engulfing_pattern"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            open_price = df['open']
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Current and previous candles
            curr_open = open_price.iloc[-1]
            curr_close = close.iloc[-1]
            curr_high = high.iloc[-1]
            curr_low = low.iloc[-1]
            
            prev_open = open_price.iloc[-2]
            prev_close = close.iloc[-2]
            prev_high = high.iloc[-2]
            prev_low = low.iloc[-2]
            
            # Bullish engulfing
            prev_bearish = prev_close < prev_open
            curr_bullish = curr_close > curr_open
            bullish_engulfing = (prev_bearish and curr_bullish and 
                                curr_open < prev_close and curr_close > prev_open)
            
            # Bearish engulfing
            prev_bullish = prev_close > prev_open
            curr_bearish = curr_close < curr_open
            bearish_engulfing = (prev_bullish and curr_bearish and 
                                curr_open > prev_close and curr_close < prev_open)
            
            if bullish_engulfing:
                body_size = abs(curr_close - curr_open)
                prev_body = abs(prev_close - prev_open)
                confidence = min(body_size / prev_body if prev_body > 0 else 0.5, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_low,
                    reason=f"Bullish engulfing pattern detected"
                )
            elif bearish_engulfing:
                body_size = abs(curr_close - curr_open)
                prev_body = abs(prev_close - prev_open)
                confidence = min(body_size / prev_body if prev_body > 0 else 0.5, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_high,
                    reason=f"Bearish engulfing pattern detected"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.2,
                entry_price=curr_close,
                reason="No engulfing pattern"
            )
            
        except Exception as e:
            logger.error(f"Engulfing Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 14: STOP HUNT REVERSAL
# ============================================================================

class StopHuntStrategy:
    """Stop Hunt Reversal - Detects smart money manipulation"""
    
    def __init__(self, lookback: int = 5, wick_threshold: float = 0.6):
        self.lookback = lookback
        self.wick_threshold = wick_threshold
        self.name = f"stop_hunt_{lookback}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            open_price = df['open']
            high = df['high']
            low = df['low']
            close = df['close']
            
            curr_open = open_price.iloc[-1]
            curr_close = close.iloc[-1]
            curr_high = high.iloc[-1]
            curr_low = low.iloc[-1]
            
            # Calculate wicks
            upper_wick = curr_high - max(curr_open, curr_close)
            lower_wick = min(curr_open, curr_close) - curr_low
            body = abs(curr_close - curr_open)
            
            # Recent range
            recent_high = high.iloc[-self.lookback:].max()
            recent_low = low.iloc[-self.lookback:].min()
            
            # Stop hunt conditions
            upper_hunt = (curr_high >= recent_high and 
                         upper_wick > body * self.wick_threshold and
                         curr_close < curr_high - upper_wick * 0.5)
            
            lower_hunt = (curr_low <= recent_low and 
                         lower_wick > body * self.wick_threshold and
                         curr_close > curr_low + lower_wick * 0.5)
            
            if upper_hunt:
                confidence = min(upper_wick / body if body > 0 else 0.7, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_high,
                    reason=f"Upper stop hunt detected (wick: {upper_wick:.2f})"
                )
            elif lower_hunt:
                confidence = min(lower_wick / body if body > 0 else 0.7, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_close,
                    stop_loss=curr_low,
                    reason=f"Lower stop hunt detected (wick: {lower_wick:.2f})"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.2,
                entry_price=curr_close,
                reason="No stop hunt pattern"
            )
            
        except Exception as e:
            logger.error(f"Stop Hunt Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 15: SUPPORT/RESISTANCE FLIP
# ============================================================================

class SupportResistanceStrategy:
    """Support and Resistance Level Strategy"""
    
    def __init__(self, lookback: int = 20, touch_threshold: float = 0.005):
        self.lookback = lookback
        self.touch_threshold = touch_threshold
        self.name = f"sr_flip_{lookback}"
    
    def find_levels(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Find support and resistance levels"""
        highs = df['high'].iloc[-self.lookback:]
        lows = df['low'].iloc[-self.lookback:]
        
        # Simple pivot detection
        resistance = []
        support = []
        
        for i in range(2, len(highs) - 2):
            if highs.iloc[i] == highs.iloc[i-2:i+3].max():
                resistance.append(highs.iloc[i])
            if lows.iloc[i] == lows.iloc[i-2:i+3].min():
                support.append(lows.iloc[i])
        
        # Get strongest levels
        resistance = sorted(list(set([round(r, 2) for r in resistance])), reverse=True)[:3]
        support = sorted(list(set([round(s, 2) for s in support])))[:3]
        
        return resistance, support
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            
            curr_price = close.iloc[-1]
            curr_high = high.iloc[-1]
            curr_low = low.iloc[-1]
            prev_close = close.iloc[-2]
            
            resistance, support = self.find_levels(df)
            
            # Check for level interactions
            for level in resistance:
                # Bearish rejection from resistance
                if (abs(curr_high - level) / level < self.touch_threshold and
                    curr_close < prev_close):
                    return TradeSignal(
                        symbol=symbol,
                        signal=SignalType.SELL,
                        strategy=self.name,
                        confidence=0.7,
                        entry_price=curr_price,
                        stop_loss=curr_high,
                        reason=f"Rejected from resistance at {level:.2f}"
                    )
                
                # Bullish breakout (resistance becomes support)
                if (prev_close < level and curr_close > level * (1 + self.touch_threshold)):
                    return TradeSignal(
                        symbol=symbol,
                        signal=SignalType.BUY,
                        strategy=self.name,
                        confidence=0.75,
                        entry_price=curr_price,
                        stop_loss=level,
                        reason=f"Resistance breakout at {level:.2f}"
                    )
            
            for level in support:
                # Bullish bounce from support
                if (abs(curr_low - level) / level < self.touch_threshold and
                    curr_close > prev_close):
                    return TradeSignal(
                        symbol=symbol,
                        signal=SignalType.BUY,
                        strategy=self.name,
                        confidence=0.7,
                        entry_price=curr_price,
                        stop_loss=curr_low,
                        reason=f"Bounce from support at {level:.2f}"
                    )
                
                # Bearish breakdown (support becomes resistance)
                if (prev_close > level and curr_close < level * (1 - self.touch_threshold)):
                    return TradeSignal(
                        symbol=symbol,
                        signal=SignalType.SELL,
                        strategy=self.name,
                        confidence=0.75,
                        entry_price=curr_price,
                        stop_loss=level,
                        reason=f"Support breakdown at {level:.2f}"
                    )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.3,
                entry_price=curr_price,
                reason=f"Nearest S: {support[0] if support else 'N/A'}, R: {resistance[0] if resistance else 'N/A'}"
            )
            
        except Exception as e:
            logger.error(f"S/R Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 16: MOMENTUM BURST
# ============================================================================

class MomentumBurstStrategy:
    """Short-term Momentum Acceleration Strategy"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20, momentum_threshold: float = 0.02):
        self.short_period = short_period
        self.long_period = long_period
        self.momentum_threshold = momentum_threshold
        self.name = f"momentum_burst_{short_period}_{long_period}"
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            volume = df['volume']
            
            # Price momentum
            short_ma = TechnicalIndicators.sma(close, self.short_period)
            long_ma = TechnicalIndicators.sma(close, self.long_period)
            
            # Rate of change
            roc = (close - close.shift(self.short_period)) / close.shift(self.short_period)
            
            curr_price = close.iloc[-1]
            curr_short = short_ma.iloc[-1]
            curr_long = long_ma.iloc[-1]
            curr_roc = roc.iloc[-1]
            
            # Volume confirmation
            avg_volume = volume.rolling(window=self.long_period).mean().iloc[-1]
            volume_spike = volume.iloc[-1] > avg_volume * 1.5
            
            # Momentum burst conditions
            bullish_burst = (curr_short > curr_long and curr_roc > self.momentum_threshold and 
                           volume_spike and roc.iloc[-2] < curr_roc)
            bearish_burst = (curr_short < curr_long and curr_roc < -self.momentum_threshold and 
                           volume_spike and roc.iloc[-2] > curr_roc)
            
            if bullish_burst:
                confidence = min(abs(curr_roc) / 0.05, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Bullish momentum burst: {curr_roc*100:.2f}% with volume"
                )
            elif bearish_burst:
                confidence = min(abs(curr_roc) / 0.05, 1.0)
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"Bearish momentum burst: {curr_roc*100:.2f}% with volume"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(curr_roc) / 0.05 if curr_roc else 0,
                entry_price=curr_price,
                reason=f"Momentum: {curr_roc*100:.2f}%, Vol ratio: {volume.iloc[-1]/avg_volume:.2f}x"
            )
            
        except Exception as e:
            logger.error(f"Momentum Burst Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 17: ICHIMOKU CLOUD
# ============================================================================

class IchimokuStrategy:
    """Ichimoku Cloud Strategy"""
    
    def __init__(self):
        self.name = "ichimoku_cloud"
    
    def calculate_ichimoku(self, df: pd.DataFrame) -> Dict:
        """Calculate Ichimoku Cloud components"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        period9_high = high.rolling(window=9).max()
        period9_low = low.rolling(window=9).min()
        tenkan_sen = (period9_high + period9_low) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = high.rolling(window=26).max()
        period26_low = low.rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = high.rolling(window=52).max()
        period52_low = low.rolling(window=52).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close shifted back 26 periods
        chikou_span = close.shift(-26)
        
        return {
            'tenkan': tenkan_sen,
            'kijun': kijun_sen,
            'senkou_a': senkou_span_a,
            'senkou_b': senkou_span_b,
            'chikou': chikou_span
        }
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        try:
            close = df['close']
            ichimoku = self.calculate_ichimoku(df)
            
            curr_price = close.iloc[-1]
            curr_tenkan = ichimoku['tenkan'].iloc[-1]
            curr_kijun = ichimoku['kijun'].iloc[-1]
            curr_senkou_a = ichimoku['senkou_a'].iloc[-1]
            curr_senkou_b = ichimoku['senkou_b'].iloc[-1]
            
            # Cloud
            cloud_top = max(curr_senkou_a, curr_senkou_b)
            cloud_bottom = min(curr_senkou_a, curr_senkou_b)
            
            # TK Cross
            prev_tenkan = ichimoku['tenkan'].iloc[-2]
            prev_kijun = ichimoku['kijun'].iloc[-2]
            
            tk_bullish = prev_tenkan < prev_kijun and curr_tenkan > curr_kijun
            tk_bearish = prev_tenkan > prev_kijun and curr_tenkan < curr_kijun
            
            # Price vs Cloud
            above_cloud = curr_price > cloud_top
            below_cloud = curr_price < cloud_bottom
            
            if tk_bullish and above_cloud:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=0.8,
                    entry_price=curr_price,
                    stop_loss=cloud_bottom,
                    reason=f"Bullish TK cross above cloud"
                )
            elif tk_bearish and below_cloud:
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=0.8,
                    entry_price=curr_price,
                    stop_loss=cloud_top,
                    reason=f"Bearish TK cross below cloud"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=0.4,
                entry_price=curr_price,
                reason=f"Cloud: {cloud_bottom:.2f}-{cloud_top:.2f}, TK: {curr_tenkan:.2f}/{curr_kijun:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Ichimoku Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY 18: MULTI-TIMEFRAME CONFLUENCE
# ============================================================================

class MTFConfluenceStrategy:
    """Multi-Timeframe Confluence Strategy"""
    
    def __init__(self):
        self.name = "mtf_confluence"
        self.strategies = {
            'ema': EMAStrategy(),
            'rsi': RSIStrategy(),
            'macd': MACDStrategy()
        }
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        """
        For true MTF, this would need data from multiple timeframes.
        Here we simulate by using different indicator periods as "timeframes".
        """
        try:
            close = df['close']
            curr_price = close.iloc[-1]
            
            # Simulate multiple "timeframes" with different EMA periods
            ema_short = TechnicalIndicators.ema(close, 9)
            ema_med = TechnicalIndicators.ema(close, 21)
            ema_long = TechnicalIndicators.ema(close, 50)
            
            # RSI on different lookbacks
            rsi_fast = TechnicalIndicators.rsi(close, 7)
            rsi_slow = TechnicalIndicators.rsi(close, 21)
            
            # Confluence scoring
            buy_signals = 0
            sell_signals = 0
            
            # EMA alignment
            if ema_short.iloc[-1] > ema_med.iloc[-1] > ema_long.iloc[-1]:
                buy_signals += 1
            elif ema_short.iloc[-1] < ema_med.iloc[-1] < ema_long.iloc[-1]:
                sell_signals += 1
            
            # RSI confluence
            if 40 < rsi_fast.iloc[-1] < 70 and rsi_slow.iloc[-1] > 50:
                buy_signals += 1
            elif 30 < rsi_slow.iloc[-1] < 60 and rsi_fast.iloc[-1] < 50:
                sell_signals += 1
            
            # Price vs EMAs
            if curr_price > ema_short.iloc[-1]:
                buy_signals += 1
            elif curr_price < ema_short.iloc[-1]:
                sell_signals += 1
            
            # Generate signal based on confluence
            if buy_signals >= 2 and buy_signals > sell_signals:
                confidence = buy_signals / 3
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"MTF confluence: {buy_signals}/3 bullish signals"
                )
            elif sell_signals >= 2 and sell_signals > buy_signals:
                confidence = sell_signals / 3
                return TradeSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    strategy=self.name,
                    confidence=confidence,
                    entry_price=curr_price,
                    reason=f"MTF confluence: {sell_signals}/3 bearish signals"
                )
            
            return TradeSignal(
                symbol=symbol,
                signal=SignalType.HOLD,
                strategy=self.name,
                confidence=abs(buy_signals - sell_signals) / 3,
                entry_price=curr_price,
                reason=f"MTF: {buy_signals} buy, {sell_signals} sell signals"
            )
            
        except Exception as e:
            logger.error(f"MTF Confluence Strategy error: {e}")
            return TradeSignal(symbol=symbol, signal=SignalType.HOLD, strategy=self.name, confidence=0, reason=str(e))

# ============================================================================
# STRATEGY REGISTRY
# ============================================================================

STRATEGIES = {
    # Trend Following
    'ema_crossover': EMAStrategy,
    'macd': MACDStrategy,
    'supertrend': SupertrendStrategy,
    'adx': ADXStrategy,
    'parabolic_sar': ParabolicSARStrategy,
    'ichimoku': IchimokuStrategy,
    
    # Mean Reversion
    'rsi': RSIStrategy,
    'bollinger': BollingerBandsStrategy,
    'stochastic': StochasticStrategy,
    'williams_r': WilliamsRStrategy,
    
    # Breakout/Momentum
    'volume_breakout': VolumeBreakoutStrategy,
    'atr_breakout': ATRBreakoutStrategy,
    'donchian': DonchianChannelStrategy,
    'momentum_burst': MomentumBurstStrategy,
    
    # Pattern/Advanced
    'engulfing': EngulfingStrategy,
    'stop_hunt': StopHuntStrategy,
    'support_resistance': SupportResistanceStrategy,
    'mtf_confluence': MTFConfluenceStrategy,
}

def get_strategy(name: str, **kwargs):
    """Get strategy instance by name"""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name](**kwargs)

def list_strategies() -> List[Dict]:
    """List all available strategies with categories"""
    return [
        {"name": "ema_crossover", "category": "Trend Following", "description": "EMA12/26 crossover"},
        {"name": "macd", "category": "Trend Following", "description": "MACD line/signal crossover"},
        {"name": "supertrend", "category": "Trend Following", "description": "ATR-based trend direction"},
        {"name": "adx", "category": "Trend Following", "description": "Trend strength based entries"},
        {"name": "parabolic_sar", "category": "Trend Following", "description": "Trailing stop trend following"},
        {"name": "ichimoku", "category": "Trend Following", "description": "Multi-factor trend analysis"},
        {"name": "rsi", "category": "Mean Reversion", "description": "RSI oversold/overbought"},
        {"name": "bollinger", "category": "Mean Reversion", "description": "Bollinger Bands mean reversion"},
        {"name": "stochastic", "category": "Mean Reversion", "description": "Stochastic oscillator"},
        {"name": "williams_r", "category": "Mean Reversion", "description": "Williams %R extremes"},
        {"name": "volume_breakout", "category": "Breakout", "description": "High volume price breakouts"},
        {"name": "atr_breakout", "category": "Breakout", "description": "Volatility expansion breakouts"},
        {"name": "donchian", "category": "Breakout", "description": "Highest high/lowest low breaks"},
        {"name": "momentum_burst", "category": "Breakout", "description": "Short-term momentum acceleration"},
        {"name": "engulfing", "category": "Pattern", "description": "Candlestick engulfing patterns"},
        {"name": "stop_hunt", "category": "Pattern", "description": "Smart money manipulation detection"},
        {"name": "support_resistance", "category": "Pattern", "description": "Key level rejection/acceptance"},
        {"name": "mtf_confluence", "category": "Advanced", "description": "Multi-timeframe confirmation"},
    ]