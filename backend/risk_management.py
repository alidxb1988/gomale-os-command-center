"""
GOMALE OS Risk Management Module
Position sizing, stop losses, and portfolio risk controls
"""

import numpy as np
from typing import Dict, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PositionSizingMethod(Enum):
    FIXED_RISK = "fixed_risk"
    KELLY = "kelly_criterion"
    VOLATILITY = "volatility_adjusted"
    FIXED_AMOUNT = "fixed_amount"

@dataclass
class RiskParameters:
    """Risk management parameters"""
    account_balance: float = 10000.0
    risk_per_trade: float = 0.02  # 2% per trade
    max_position_size: float = 0.10  # 10% max per position
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_open_positions: int = 5
    stop_loss_type: Literal["fixed", "atr", "technical"] = "atr"
    take_profit_ratio: float = 2.0  # 2:1 R:R
    trailing_stop: bool = False
    trailing_stop_pct: float = 0.02  # 2% trailing

@dataclass
class PositionSize:
    """Calculated position size result"""
    symbol: str
    position_size: float  # in base currency
    position_value: float  # in quote currency
    risk_amount: float
    stop_loss: float
    take_profit: float
    leverage: float = 1.0

class RiskManager:
    """Risk Management Engine"""
    
    def __init__(self, params: RiskParameters):
        self.params = params
        self.daily_pnl = 0.0
        self.open_positions = {}
        self.trade_history = []
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        atr: Optional[float] = None,
        volatility: Optional[float] = None,
        win_rate: Optional[float] = None,
        method: PositionSizingMethod = PositionSizingMethod.FIXED_RISK
    ) -> PositionSize:
        """
        Calculate optimal position size based on risk parameters
        """
        try:
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            if risk_distance == 0:
                logger.warning("Risk distance is zero, using default")
                risk_distance = entry_price * 0.01  # 1% default
            
            # Risk amount in account currency
            risk_amount = self.params.account_balance * self.params.risk_per_trade
            
            # Apply position sizing method
            if method == PositionSizingMethod.FIXED_RISK:
                position_value = risk_amount / (risk_distance / entry_price)
                
            elif method == PositionSizingMethod.KELLY and win_rate is not None:
                # Kelly Criterion: f* = (p*b - q) / b
                # where p = win rate, q = loss rate, b = avg win/avg loss
                avg_win_loss_ratio = self.params.take_profit_ratio
                p = win_rate
                q = 1 - win_rate
                kelly_pct = (p * avg_win_loss_ratio - q) / avg_win_loss_ratio
                kelly_pct = max(0, min(kelly_pct * 0.5, self.params.max_position_size))  # Half Kelly, capped
                position_value = self.params.account_balance * kelly_pct
                
            elif method == PositionSizingMethod.VOLATILITY and volatility is not None:
                # Reduce size in high volatility
                vol_factor = max(0.2, 1 - (volatility - 0.2) * 2)  # Scale 0.2-1.0
                position_value = (risk_amount / (risk_distance / entry_price)) * vol_factor
                
            elif method == PositionSizingMethod.FIXED_AMOUNT:
                position_value = self.params.account_balance * self.params.max_position_size
                
            else:
                position_value = risk_amount / (risk_distance / entry_price)
            
            # Cap at max position size
            max_position_value = self.params.account_balance * self.params.max_position_size
            position_value = min(position_value, max_position_value)
            
            # Calculate position size in base currency
            position_size = position_value / entry_price
            
            # Calculate take profit
            if entry_price > stop_loss:  # Long position
                take_profit = entry_price + (risk_distance * self.params.take_profit_ratio)
            else:  # Short position
                take_profit = entry_price - (risk_distance * self.params.take_profit_ratio)
            
            return PositionSize(
                symbol=symbol,
                position_size=position_size,
                position_value=position_value,
                risk_amount=risk_amount,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            # Return minimal position as fallback
            return PositionSize(
                symbol=symbol,
                position_size=0,
                position_value=0,
                risk_amount=0,
                stop_loss=stop_loss,
                take_profit=entry_price
            )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: Literal["buy", "sell"],
        atr: Optional[float] = None,
        support_level: Optional[float] = None,
        resistance_level: Optional[float] = None,
        fixed_pct: float = 0.02
    ) -> float:
        """
        Calculate stop loss based on method
        """
        try:
            if self.params.stop_loss_type == "atr" and atr is not None:
                # ATR-based stop (2x ATR)
                stop_distance = atr * 2
                if side == "buy":
                    return entry_price - stop_distance
                else:
                    return entry_price + stop_distance
                    
            elif self.params.stop_loss_type == "technical":
                # Use support/resistance levels
                if side == "buy" and support_level is not None:
                    return support_level * 0.99  # Just below support
                elif side == "sell" and resistance_level is not None:
                    return resistance_level * 1.01  # Just above resistance
                    
            # Default fixed percentage
            if side == "buy":
                return entry_price * (1 - fixed_pct)
            else:
                return entry_price * (1 + fixed_pct)
                
        except Exception as e:
            logger.error(f"Stop loss calculation error: {e}")
            # Fallback to fixed percentage
            if side == "buy":
                return entry_price * 0.98
            else:
                return entry_price * 1.02
    
    def check_risk_limits(self, new_position_value: float = 0) -> Dict[str, bool]:
        """
        Check if new trade violates risk limits
        """
        checks = {
            "daily_loss_limit": abs(self.daily_pnl) < self.params.account_balance * self.params.max_daily_loss,
            "max_positions": len(self.open_positions) < self.params.max_open_positions,
            "position_size": new_position_value <= self.params.account_balance * self.params.max_position_size,
            "sufficient_balance": self.params.account_balance > 0
        }
        
        checks["can_trade"] = all(checks.values())
        return checks
    
    def update_trailing_stop(
        self,
        position_id: str,
        current_price: float,
        current_stop: float,
        side: Literal["buy", "sell"]
    ) -> float:
        """
        Update trailing stop if price moves favorably
        """
        if not self.params.trailing_stop:
            return current_stop
        
        try:
            if side == "buy":
                # For long positions, trail below price
                new_stop = current_price * (1 - self.params.trailing_stop_pct)
                return max(current_stop, new_stop)
            else:
                # For short positions, trail above price
                new_stop = current_price * (1 + self.params.trailing_stop_pct)
                return min(current_stop, new_stop)
                
        except Exception as e:
            logger.error(f"Trailing stop error: {e}")
            return current_stop
    
    def add_position(self, position_id: str, position: PositionSize):
        """Add new position to tracking"""
        self.open_positions[position_id] = position
        logger.info(f"Added position {position_id}: {position.symbol} size={position.position_size}")
    
    def remove_position(self, position_id: str, pnl: float = 0):
        """Remove position and update P&L"""
        if position_id in self.open_positions:
            del self.open_positions[position_id]
            self.daily_pnl += pnl
            self.trade_history.append({
                "position_id": position_id,
                "pnl": pnl,
                "daily_pnl": self.daily_pnl
            })
            logger.info(f"Removed position {position_id}, P&L: {pnl}")
    
    def get_portfolio_risk(self) -> Dict:
        """Get current portfolio risk metrics"""
        total_exposure = sum(pos.position_value for pos in self.open_positions.values())
        total_risk = sum(pos.risk_amount for pos in self.open_positions.values())
        
        return {
            "total_exposure": total_exposure,
            "exposure_pct": total_exposure / self.params.account_balance if self.params.account_balance > 0 else 0,
            "total_risk": total_risk,
            "risk_pct": total_risk / self.params.account_balance if self.params.account_balance > 0 else 0,
            "open_positions": len(self.open_positions),
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": self.daily_pnl / self.params.account_balance if self.params.account_balance > 0 else 0,
            "available_risk": self.params.account_balance * self.params.max_daily_loss - abs(self.daily_pnl)
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of trading day)"""
        self.daily_pnl = 0.0
        logger.info("Daily stats reset")

# ============================================================================
# PAPER TRADING ACCOUNT MANAGER
# ============================================================================

class PaperTradingAccount:
    """Virtual trading account for paper trading"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions = {}
        self.orders = []
        self.trade_history = []
        self.position_counter = 0
    
    def get_next_position_id(self) -> str:
        """Generate unique position ID"""
        self.position_counter += 1
        return f"PAPER_{self.position_counter:04d}"
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """Place a virtual order"""
        try:
            order_id = self.get_next_position_id()
            
            # For market orders, use provided price or estimate
            if order_type == "Market":
                if price is None:
                    return {"success": False, "error": "Market order requires current price"}
                fill_price = price
            else:
                fill_price = price
            
            order_value = qty * fill_price
            
            # Check balance for buy orders
            if side == "Buy" and order_value > self.balance:
                return {
                    "success": False,
                    "error": f"Insufficient balance. Required: {order_value:.2f}, Available: {self.balance:.2f}"
                }
            
            # Create position
            position = {
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "entry_price": fill_price,
                "current_price": fill_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "value": order_value,
                "unrealized_pnl": 0.0,
                "open_time": None  # Will be set when tracked
            }
            
            # Update balance
            if side == "Buy":
                self.balance -= order_value
            
            self.positions[order_id] = position
            
            self.orders.append({
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "qty": qty,
                "price": fill_price,
                "status": "filled"
            })
            
            return {
                "success": True,
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": fill_price,
                "value": order_value
            }
            
        except Exception as e:
            logger.error(f"Paper order error: {e}")
            return {"success": False, "error": str(e)}
    
    def close_position(self, position_id: str, exit_price: float) -> Dict:
        """Close a virtual position"""
        try:
            if position_id not in self.positions:
                return {"success": False, "error": "Position not found"}
            
            position = self.positions[position_id]
            
            # Calculate P&L
            if position["side"] == "Buy":
                pnl = (exit_price - position["entry_price"]) * position["qty"]
            else:
                pnl = (position["entry_price"] - exit_price) * position["qty"]
            
            # Update balance
            exit_value = position["qty"] * exit_price
            if position["side"] == "Buy":
                self.balance += exit_value
            else:
                self.balance += exit_value + pnl  # Short: return margin + pnl
            
            # Record trade
            trade = {
                "position_id": position_id,
                "symbol": position["symbol"],
                "side": position["side"],
                "entry_price": position["entry_price"],
                "exit_price": exit_price,
                "qty": position["qty"],
                "pnl": pnl,
                "pnl_pct": (pnl / (position["entry_price"] * position["qty"])) * 100
            }
            self.trade_history.append(trade)
            
            # Remove position
            del self.positions[position_id]
            
            return {
                "success": True,
                "position_id": position_id,
                "exit_price": exit_price,
                "pnl": pnl,
                "balance": self.balance
            }
            
        except Exception as e:
            logger.error(f"Close position error: {e}")
            return {"success": False, "error": str(e)}
    
    def update_prices(self, prices: Dict[str, float]):
        """Update position prices and calculate unrealized P&L"""
        total_unrealized = 0.0
        
        for position_id, position in self.positions.items():
            symbol = position["symbol"]
            if symbol in prices:
                current_price = prices[symbol]
                position["current_price"] = current_price
                
                # Calculate unrealized P&L
                if position["side"] == "Buy":
                    unrealized = (current_price - position["entry_price"]) * position["qty"]
                else:
                    unrealized = (position["entry_price"] - current_price) * position["qty"]
                
                position["unrealized_pnl"] = unrealized
                total_unrealized += unrealized
        
        self.equity = self.balance + total_unrealized
    
    def check_stop_loss_take_profit(self, prices: Dict[str, float]) -> list:
        """Check for triggered stop losses and take profits"""
        triggered = []
        
        for position_id, position in self.positions.items():
            symbol = position["symbol"]
            if symbol not in prices:
                continue
            
            current_price = prices[symbol]
            
            # Check stop loss
            if position["stop_loss"]:
                if position["side"] == "Buy" and current_price <= position["stop_loss"]:
                    triggered.append({
                        "position_id": position_id,
                        "type": "stop_loss",
                        "trigger_price": current_price
                    })
                elif position["side"] == "Sell" and current_price >= position["stop_loss"]:
                    triggered.append({
                        "position_id": position_id,
                        "type": "stop_loss",
                        "trigger_price": current_price
                    })
            
            # Check take profit
            if position["take_profit"]:
                if position["side"] == "Buy" and current_price >= position["take_profit"]:
                    triggered.append({
                        "position_id": position_id,
                        "type": "take_profit",
                        "trigger_price": current_price
                    })
                elif position["side"] == "Sell" and current_price <= position["take_profit"]:
                    triggered.append({
                        "position_id": position_id,
                        "type": "take_profit",
                        "trigger_price": current_price
                    })
        
        return triggered
    
    def get_account_summary(self) -> Dict:
        """Get paper trading account summary"""
        total_unrealized = sum(pos["unrealized_pnl"] for pos in self.positions.values())
        
        return {
            "initial_balance": self.initial_balance,
            "balance": self.balance,
            "equity": self.equity,
            "unrealized_pnl": total_unrealized,
            "total_pnl": self.equity - self.initial_balance,
            "total_pnl_pct": ((self.equity - self.initial_balance) / self.initial_balance) * 100,
            "open_positions": len(self.positions),
            "total_trades": len(self.trade_history),
            "winning_trades": len([t for t in self.trade_history if t["pnl"] > 0]),
            "losing_trades": len([t for t in self.trade_history if t["pnl"] < 0])
        }
    
    def get_positions(self) -> list:
        """Get list of open positions"""
        return list(self.positions.values())
    
    def get_trade_history(self) -> list:
        """Get trade history"""
        return self.trade_history
    
    def reset_account(self):
        """Reset account to initial state"""
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.positions = {}
        self.orders = []
        self.trade_history = []
        self.position_counter = 0
        logger.info("Paper trading account reset")