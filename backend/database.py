"""
GOMALE OS Paper Trading Database
SQLite-based storage for paper trading operations
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class PaperTradingDB:
    """SQLite database for paper trading"""
    
    def __init__(self, db_path: str = "paper_trading.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Paper trading accounts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    initial_balance REAL NOT NULL,
                    current_balance REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trades/Positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    status TEXT DEFAULT 'open',
                    pnl REAL DEFAULT 0,
                    pnl_pct REAL DEFAULT 0,
                    strategy TEXT,
                    signal_confidence REAL,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """)
            
            # Trade signals log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    confidence REAL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    executed BOOLEAN DEFAULT FALSE,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """)
            
            # Balance history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    unrealized_pnl REAL DEFAULT 0,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """)
            
            # Strategy performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    strategy TEXT NOT NULL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    avg_pnl REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    UNIQUE(account_id, strategy)
                )
            """)
            
            logger.info("Paper trading database initialized")
    
    def create_account(self, name: str, initial_balance: float) -> int:
        """Create new paper trading account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO accounts (name, initial_balance, current_balance) VALUES (?, ?, ?)",
                (name, initial_balance, initial_balance)
            )
            return cursor.lastrowid
    
    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get account details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM accounts WHERE id = ?",
                (account_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_account_balance(self, account_id: int, new_balance: float):
        """Update account balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE accounts 
                   SET current_balance = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (new_balance, account_id)
            )
    
    def record_trade(
        self,
        account_id: int,
        order_id: str,
        symbol: str,
        side: str,
        qty: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: Optional[str] = None,
        signal_confidence: Optional[float] = None
    ) -> int:
        """Record new trade"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO trades 
                   (account_id, order_id, symbol, side, qty, entry_price, 
                    stop_loss, take_profit, strategy, signal_confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (account_id, order_id, symbol, side, qty, entry_price,
                 stop_loss, take_profit, strategy, signal_confidence)
            )
            return cursor.lastrowid
    
    def close_trade(
        self,
        order_id: str,
        exit_price: float,
        pnl: float,
        pnl_pct: float
    ):
        """Close a trade"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE trades 
                   SET exit_price = ?, pnl = ?, pnl_pct = ?, 
                       status = 'closed', closed_at = CURRENT_TIMESTAMP
                   WHERE order_id = ?""",
                (exit_price, pnl, pnl_pct, order_id)
            )
    
    def get_open_trades(self, account_id: int) -> List[Dict]:
        """Get all open trades for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM trades 
                   WHERE account_id = ? AND status = 'open'
                   ORDER BY opened_at DESC""",
                (account_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trade_history(self, account_id: int, limit: int = 100) -> List[Dict]:
        """Get trade history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM trades 
                   WHERE account_id = ? AND status = 'closed'
                   ORDER BY closed_at DESC
                   LIMIT ?""",
                (account_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def record_signal(
        self,
        account_id: Optional[int],
        symbol: str,
        signal: str,
        strategy: str,
        confidence: float,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reason: str = ""
    ) -> int:
        """Record trading signal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO signals 
                   (account_id, symbol, signal, strategy, confidence,
                    entry_price, stop_loss, take_profit, reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (account_id, symbol, signal, strategy, confidence,
                 entry_price, stop_loss, take_profit, reason)
            )
            return cursor.lastrowid
    
    def record_balance(
        self,
        account_id: int,
        balance: float,
        equity: float,
        unrealized_pnl: float = 0
    ):
        """Record balance snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO balance_history 
                   (account_id, balance, equity, unrealized_pnl)
                   VALUES (?, ?, ?, ?)""",
                (account_id, balance, equity, unrealized_pnl)
            )
    
    def get_balance_history(
        self,
        account_id: int,
        hours: int = 24
    ) -> List[Dict]:
        """Get balance history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM balance_history 
                   WHERE account_id = ? 
                   AND recorded_at > datetime('now', '-{} hours')
                   ORDER BY recorded_at ASC""".format(hours),
                (account_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_strategy_performance(
        self,
        account_id: int,
        strategy: str,
        pnl: float,
        won: bool
    ):
        """Update strategy performance metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if entry exists
            cursor.execute(
                """SELECT * FROM strategy_performance 
                   WHERE account_id = ? AND strategy = ?""",
                (account_id, strategy)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                total_trades = existing["total_trades"] + 1
                winning_trades = existing["winning_trades"] + (1 if won else 0)
                losing_trades = existing["losing_trades"] + (0 if won else 1)
                total_pnl = existing["total_pnl"] + pnl
                win_rate = (winning_trades / total_trades) * 100
                avg_pnl = total_pnl / total_trades
                
                cursor.execute(
                    """UPDATE strategy_performance 
                       SET total_trades = ?, winning_trades = ?, 
                           losing_trades = ?, total_pnl = ?, 
                           avg_pnl = ?, win_rate = ?,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE account_id = ? AND strategy = ?""",
                    (total_trades, winning_trades, losing_trades,
                     total_pnl, avg_pnl, win_rate, account_id, strategy)
                )
            else:
                # Create new
                cursor.execute(
                    """INSERT INTO strategy_performance 
                       (account_id, strategy, total_trades, winning_trades,
                        losing_trades, total_pnl, avg_pnl, win_rate)
                       VALUES (?, ?, 1, ?, ?, ?, ?, ?)""",
                    (account_id, strategy, 1 if won else 0, 0 if won else 1,
                     pnl, pnl, 100 if won else 0)
                )
    
    def get_strategy_performance(
        self,
        account_id: int
    ) -> List[Dict]:
        """Get strategy performance summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM strategy_performance 
                   WHERE account_id = ?
                   ORDER BY total_pnl DESC""",
                (account_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trading_stats(self, account_id: int) -> Dict:
        """Get comprehensive trading statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute(
                """SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                    AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
                   FROM trades WHERE account_id = ? AND status = 'closed'""",
                (account_id,)
            )
            stats = dict(cursor.fetchone())
            
            # Calculate win rate and profit factor
            total_trades = stats.get("total_trades", 0) or 0
            winning_trades = stats.get("winning_trades", 0) or 0
            losing_trades = stats.get("losing_trades", 0) or 0
            
            stats["win_rate"] = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_wins = abs(stats.get("avg_win", 0) or 0) * winning_trades
            total_losses = abs(stats.get("avg_loss", 0) or 0) * losing_trades
            stats["profit_factor"] = total_wins / total_losses if total_losses > 0 else 0
            
            # Recent performance (last 7 days)
            cursor.execute(
                """SELECT 
                    DATE(closed_at) as date,
                    COUNT(*) as trades,
                    SUM(pnl) as daily_pnl
                   FROM trades 
                   WHERE account_id = ? 
                   AND status = 'closed'
                   AND closed_at > datetime('now', '-7 days')
                   GROUP BY DATE(closed_at)
                   ORDER BY date DESC""",
                (account_id,)
            )
            stats["daily_performance"] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old signal and balance history data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """DELETE FROM signals 
                   WHERE created_at < datetime('now', '-{} days')""".format(days)
            )
            
            cursor.execute(
                """DELETE FROM balance_history 
                   WHERE recorded_at < datetime('now', '-{} days')""".format(days)
            )
            
            logger.info(f"Cleaned up data older than {days} days")