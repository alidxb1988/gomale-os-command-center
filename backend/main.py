"""
GOMALE OS Command Center - Production-Ready Trading Platform
Version 2.1.0 - Enhanced with Paper Trading, Risk Management & 18 Strategies
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gomale_os.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = "/root/.openclaw/workspace/.env.gomale"
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
else:
    logger.warning(f"Environment file not found: {env_path}")

# Import trading modules
try:
    from pybit.unified_trading import HTTP as BybitHTTP
    BYBIT_AVAILABLE = True
except ImportError:
    logger.warning("pybit not installed. Bybit trading will be disabled.")
    BYBIT_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic not installed. Claude AI will be disabled.")
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai not installed. Gemini will be disabled.")
    GEMINI_AVAILABLE = False

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    logger.warning("pandas/numpy not installed. Some features will be limited.")
    PANDAS_AVAILABLE = False

# Import local modules
sys.path.insert(0, os.path.dirname(__file__))
from strategies.strategies import (
    STRATEGIES, get_strategy, list_strategies, SignalType
)
from risk_management import (
    RiskManager, RiskParameters, PaperTradingAccount, PositionSizingMethod
)
from database import PaperTradingDB

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BYBIT_TESTNET_KEY = os.getenv("BYBIT_TESTNET_KEY")
BYBIT_TESTNET_SECRET = os.getenv("BYBIT_TESTNET_SECRET")

# Initialize AI clients
anthropic_client = None
if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
    try:
        anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Claude AI client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Claude: {e}")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini AI configured")
    except Exception as e:
        logger.error(f"Failed to configure Gemini: {e}")

# Bybit client
bybit_client = None
if BYBIT_AVAILABLE and BYBIT_TESTNET_KEY and BYBIT_TESTNET_SECRET:
    try:
        bybit_client = BybitHTTP(
            testnet=True,
            api_key=BYBIT_TESTNET_KEY,
            api_secret=BYBIT_TESTNET_SECRET
        )
        logger.info("Bybit TestNet client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Bybit: {e}")

# Paper Trading System
paper_db = PaperTradingDB()
paper_account = PaperTradingAccount(initial_balance=10000.0)
risk_manager = RiskManager(RiskParameters(
    account_balance=paper_account.balance,
    risk_per_trade=0.02,
    max_position_size=0.10,
    stop_loss_type="atr",
    take_profit_ratio=2.0
))

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for symbol, subscribers in self.subscriptions.items():
            if websocket in subscribers:
                subscribers.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                disconnected.append(connection)
        
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def send_to_symbol(self, symbol: str, message: dict):
        if symbol in self.subscriptions:
            disconnected = []
            for websocket in self.subscriptions[symbol]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)
            for conn in disconnected:
                if conn in self.subscriptions[symbol]:
                    self.subscriptions[symbol].remove(conn)

manager = ConnectionManager()

# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    model: str = "claude"
    system_prompt: Optional[str] = None
    stream: bool = False

class TradeRequest(BaseModel):
    symbol: str
    side: str
    order_type: str = "Market"
    qty: float
    price: Optional[float] = None
    category: str = "spot"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class PaperTradeRequest(BaseModel):
    symbol: str
    side: str
    order_type: str = "Market"
    qty: float
    price: Optional[float] = None
    strategy: Optional[str] = None
    use_risk_management: bool = True

class StrategySignalRequest(BaseModel):
    symbol: str
    strategy: str
    timeframe: str = "1h"

class RiskSettingsRequest(BaseModel):
    risk_per_trade: float = 0.02
    max_position_size: float = 0.10
    stop_loss_type: str = "atr"
    take_profit_ratio: float = 2.0
    trailing_stop: bool = False

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
    model: str = "eleven_multilingual_v2"

class AIAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    include_indicators: bool = True

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting GOMALE OS Command Center v2.1.0")
    
    # Initialize paper trading account
    account = paper_db.get_account(1)
    if not account:
        paper_db.create_account("default", 10000.0)
        logger.info("Created default paper trading account with $10,000")
    
    # Start background tasks
    price_task = asyncio.create_task(price_stream_task())
    paper_task = asyncio.create_task(paper_trading_monitor())
    
    yield
    
    # Cleanup
    price_task.cancel()
    paper_task.cancel()
    logger.info("Shutting down GOMALE OS Command Center")

app = FastAPI(
    title="GOMALE OS Command Center",
    version="2.1.0",
    description="Production-ready trading platform with 18 strategies, paper trading, and AI",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "name": "GOMALE OS Command Center",
        "version": "2.1.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "ai_chat": {
                "claude": ANTHROPIC_AVAILABLE and anthropic_client is not None,
                "gemini": GEMINI_AVAILABLE,
                "perplexity": PERPLEXITY_API_KEY is not None,
                "kimi": KIMI_API_KEY is not None
            },
            "trading": {
                "bybit_testnet": BYBIT_AVAILABLE and bybit_client is not None,
                "paper_trading": True,
                "strategies": len(STRATEGIES)
            },
            "websocket": True,
            "tts": ELEVENLABS_API_KEY is not None
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "online",
            "bybit": "online" if bybit_client else "offline",
            "database": "online",
            "websocket": len(manager.active_connections)
        }
    }

# ============================================================================
# AI CHAT ENDPOINTS
# ============================================================================

@app.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    """Chat with any AI model"""
    try:
        if request.model == "claude":
            return await chat_claude(request)
        elif request.model == "gemini":
            return await chat_gemini(request)
        elif request.model == "perplexity":
            return await chat_perplexity(request)
        elif request.model == "kimi":
            return await chat_kimi(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model: {request.model}")
    except Exception as e:
        logger.error(f"AI chat error ({request.model}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def chat_claude(request: ChatRequest):
    """Chat with Claude"""
    if not anthropic_client:
        raise HTTPException(status_code=503, detail="Claude AI not available")
    
    system = request.system_prompt or """You are GOMALE OS, an advanced AI trading and business assistant for GOMALE GROUP. 
    You provide expert analysis on crypto trading, market analysis, and business strategy."""
    
    response = await anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": request.message}]
    )
    
    return {
        "model": "claude",
        "content": response.content[0].text,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }
    }

async def chat_gemini(request: ChatRequest):
    """Chat with Gemini"""
    if not GEMINI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Gemini AI not available")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await asyncio.to_thread(
        model.generate_content,
        request.message
    )
    
    return {
        "model": "gemini",
        "content": response.text,
        "usage": {}
    }

async def chat_perplexity(request: ChatRequest):
    """Chat with Perplexity"""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=503, detail="Perplexity not available")
    
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": request.message}]
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return {
            "model": "perplexity",
            "content": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {})
        }

async def chat_kimi(request: ChatRequest):
    """Chat with Kimi"""
    if not KIMI_API_KEY:
        raise HTTPException(status_code=503, detail="Kimi AI not available")
    
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": request.message}]
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return {
            "model": "kimi",
            "content": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {})
        }

@app.post("/api/ai/compare")
async def compare_all_models(request: ChatRequest):
    """Get responses from all AI models simultaneously"""
    models = ["claude", "gemini", "perplexity", "kimi"]
    tasks = []
    
    for model in models:
        req = ChatRequest(
            message=request.message,
            model=model,
            system_prompt=request.system_prompt
        )
        tasks.append(ai_chat_safe(req))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    responses = {}
    for model, result in zip(models, results):
        if isinstance(result, Exception):
            responses[model] = {"error": str(result)}
        else:
            responses[model] = result
    
    return {"query": request.message, "responses": responses}

async def ai_chat_safe(request: ChatRequest):
    """Safe wrapper for AI chat"""
    try:
        return await ai_chat(request)
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# TTS ENDPOINTS
# ============================================================================

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using ElevenLabs"""
    try:
        if not ELEVENLABS_API_KEY:
            raise HTTPException(status_code=503, detail="TTS not available")
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": request.text,
                    "model_id": request.model,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                import base64
                audio_base64 = base64.b64encode(response.content).decode()
                return {
                    "success": True,
                    "audio_base64": audio_base64,
                    "format": "mp3"
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BYBIT TRADING ENDPOINTS
# ============================================================================

@app.get("/api/bybit/account")
async def get_account_info():
    """Get Bybit account information"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        wallet = bybit_client.get_wallet_balance(accountType="UNIFIED")
        return {"status": "success", "data": wallet}
    except Exception as e:
        logger.error(f"Bybit account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bybit/balance")
async def get_wallet_balance(coin: Optional[str] = None):
    """Get wallet balance"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        params = {"accountType": "UNIFIED"}
        if coin:
            params["coin"] = coin
        
        balance = bybit_client.get_wallet_balance(**params)
        return {"status": "success", "data": balance}
    except Exception as e:
        logger.error(f"Bybit balance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bybit/tickers")
async def get_tickers(category: str = "spot", symbol: Optional[str] = None):
    """Get market tickers"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        
        tickers = bybit_client.get_tickers(**params)
        return {"status": "success", "data": tickers}
    except Exception as e:
        logger.error(f"Bybit tickers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bybit/kline")
async def get_kline(
    symbol: str,
    interval: str = "60",
    limit: int = 200,
    category: str = "spot"
):
    """Get candlestick data"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        klines = bybit_client.get_kline(
            category=category,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return {"status": "success", "data": klines}
    except Exception as e:
        logger.error(f"Bybit kline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bybit/order")
async def place_order(request: TradeRequest):
    """Place a trading order on Bybit TestNet"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        order_params = {
            "category": request.category,
            "symbol": request.symbol,
            "side": request.side,
            "orderType": request.order_type,
            "qty": str(request.qty),
        }
        
        if request.order_type == "Limit" and request.price:
            order_params["price"] = str(request.price)
        
        result = bybit_client.place_order(**order_params)
        
        logger.info(f"Bybit order placed: {request.symbol} {request.side} {request.qty}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Bybit order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bybit/orders")
async def get_orders(category: str = "spot", symbol: Optional[str] = None):
    """Get active orders"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        params = {"category": category, "openOnly": 0, "limit": 50}
        if symbol:
            params["symbol"] = symbol
        
        orders = bybit_client.get_open_orders(**params)
        return {"status": "success", "data": orders}
    except Exception as e:
        logger.error(f"Bybit orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bybit/positions")
async def get_positions(category: str = "linear", symbol: Optional[str] = None):
    """Get open positions"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        
        positions = bybit_client.get_positions(**params)
        return {"status": "success", "data": positions}
    except Exception as e:
        logger.error(f"Bybit positions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bybit/order/{order_id}")
async def cancel_order(order_id: str, category: str = "spot", symbol: str = None):
    """Cancel an order"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        result = bybit_client.cancel_order(
            category=category,
            symbol=symbol,
            orderId=order_id
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Bybit cancel order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PAPER TRADING ENDPOINTS
# ============================================================================

@app.get("/api/paper/account")
async def get_paper_account():
    """Get paper trading account summary"""
    try:
        summary = paper_account.get_account_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"Paper account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/paper/order")
async def place_paper_order(request: PaperTradeRequest):
    """Place a paper trading order"""
    try:
        # Get current price if market order
        if request.order_type == "Market" and not request.price:
            if bybit_client:
                ticker = bybit_client.get_tickers(category="spot", symbol=request.symbol)
                if ticker.get("result") and ticker["result"].get("list"):
                    request.price = float(ticker["result"]["list"][0]["lastPrice"])
        
        if not request.price:
            raise HTTPException(status_code=400, detail="Price required for paper trade")
        
        # Calculate stop loss and take profit if using risk management
        stop_loss = None
        take_profit = None
        
        if request.use_risk_management:
            # Get klines for ATR calculation
            if bybit_client:
                try:
                    klines = bybit_client.get_kline(
                        category="spot",
                        symbol=request.symbol,
                        interval="60",
                        limit=50
                    )
                    if klines.get("result") and klines["result"].get("list"):
                        import pandas as pd
                        data = klines["result"]["list"]
                        df = pd.DataFrame(data, columns=[
                            "timestamp", "open", "high", "low", "close", "volume", "turnover"
                        ])
                        for col in ["open", "high", "low", "close", "volume"]:
                            df[col] = pd.to_numeric(df[col])
                        
                        from strategies.strategies import TechnicalIndicators
                        atr = TechnicalIndicators.atr(df["high"], df["low"], df["close"], 14).iloc[-1]
                        
                        side = "buy" if request.side == "Buy" else "sell"
                        stop_loss = risk_manager.calculate_stop_loss(
                            entry_price=request.price,
                            side=side,
                            atr=atr
                        )
                        
                        # Calculate take profit based on R:R
                        risk = abs(request.price - stop_loss)
                        if request.side == "Buy":
                            take_profit = request.price + (risk * risk_manager.params.take_profit_ratio)
                        else:
                            take_profit = request.price - (risk * risk_manager.params.take_profit_ratio)
                        
                        # Calculate position size based on risk
                        position = risk_manager.calculate_position_size(
                            symbol=request.symbol,
                            entry_price=request.price,
                            stop_loss=stop_loss,
                            atr=atr
                        )
                        request.qty = position.position_size
                        
                except Exception as calc_error:
                    logger.warning(f"Could not calculate risk parameters: {calc_error}")
        
        result = paper_account.place_order(
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            qty=request.qty,
            price=request.price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if result["success"]:
            # Record in database
            paper_db.record_trade(
                account_id=1,
                order_id=result["order_id"],
                symbol=request.symbol,
                side=request.side,
                qty=request.qty,
                entry_price=result["price"],
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=request.strategy
            )
            
            logger.info(f"Paper order placed: {result['order_id']} {request.symbol} {request.side}")
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Paper order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/paper/close/{position_id}")
async def close_paper_position(position_id: str):
    """Close a paper trading position"""
    try:
        # Get current price
        position = paper_account.positions.get(position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        
        current_price = position["current_price"]
        if bybit_client:
            try:
                ticker = bybit_client.get_tickers(category="spot", symbol=position["symbol"])
                if ticker.get("result") and ticker["result"].get("list"):
                    current_price = float(ticker["result"]["list"][0]["lastPrice"])
            except Exception as e:
                logger.warning(f"Could not get current price: {e}")
        
        result = paper_account.close_position(position_id, current_price)
        
        if result["success"]:
            # Update database
            paper_db.close_trade(
                order_id=position_id,
                exit_price=current_price,
                pnl=result["pnl"],
                pnl_pct=(result["pnl"] / (position["entry_price"] * position["qty"])) * 100
            )
            
            # Update strategy performance if applicable
            if position.get("strategy"):
                paper_db.update_strategy_performance(
                    account_id=1,
                    strategy=position["strategy"],
                    pnl=result["pnl"],
                    won=result["pnl"] > 0
                )
            
            logger.info(f"Paper position closed: {position_id} PnL: {result['pnl']:.2f}")
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Close paper position error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/paper/positions")
async def get_paper_positions():
    """Get paper trading positions"""
    try:
        positions = paper_account.get_positions()
        return {"status": "success", "data": positions}
    except Exception as e:
        logger.error(f"Paper positions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/paper/history")
async def get_paper_history(limit: int = 100):
    """Get paper trading history"""
    try:
        history = paper_db.get_trade_history(account_id=1, limit=limit)
        return {"status": "success", "data": history}
    except Exception as e:
        logger.error(f"Paper history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/paper/reset")
async def reset_paper_account():
    """Reset paper trading account"""
    try:
        paper_account.reset_account()
        risk_manager.params.account_balance = paper_account.balance
        logger.info("Paper trading account reset")
        return {"status": "success", "message": "Paper trading account reset to $10,000"}
    except Exception as e:
        logger.error(f"Reset paper account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RISK MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/risk/settings")
async def get_risk_settings():
    """Get current risk management settings"""
    try:
        return {
            "status": "success",
            "data": {
                "risk_per_trade": risk_manager.params.risk_per_trade,
                "max_position_size": risk_manager.params.max_position_size,
                "max_daily_loss": risk_manager.params.max_daily_loss,
                "max_open_positions": risk_manager.params.max_open_positions,
                "stop_loss_type": risk_manager.params.stop_loss_type,
                "take_profit_ratio": risk_manager.params.take_profit_ratio,
                "trailing_stop": risk_manager.params.trailing_stop,
                "trailing_stop_pct": risk_manager.params.trailing_stop_pct
            }
        }
    except Exception as e:
        logger.error(f"Risk settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/risk/settings")
async def update_risk_settings(request: RiskSettingsRequest):
    """Update risk management settings"""
    try:
        risk_manager.params.risk_per_trade = request.risk_per_trade
        risk_manager.params.max_position_size = request.max_position_size
        risk_manager.params.stop_loss_type = request.stop_loss_type
        risk_manager.params.take_profit_ratio = request.take_profit_ratio
        risk_manager.params.trailing_stop = request.trailing_stop
        
        logger.info("Risk settings updated")
        return {"status": "success", "message": "Risk settings updated"}
    except Exception as e:
        logger.error(f"Update risk settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk/portfolio")
async def get_portfolio_risk():
    """Get portfolio risk metrics"""
    try:
        metrics = risk_manager.get_portfolio_risk()
        return {"status": "success", "data": metrics}
    except Exception as e:
        logger.error(f"Portfolio risk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@app.get("/api/strategies")
async def get_strategies():
    """Get list of all available strategies"""
    try:
        strategies = list_strategies()
        return {"status": "success", "data": strategies}
    except Exception as e:
        logger.error(f"Strategies list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/signal")
async def get_strategy_signal(request: StrategySignalRequest):
    """Get trading signal from a specific strategy"""
    try:
        if not PANDAS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Pandas required for strategy analysis")
        
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit client required for market data")
        
        # Get klines
        klines = bybit_client.get_kline(
            category="spot",
            symbol=request.symbol,
            interval=request.timeframe,
            limit=100
        )
        
        if not klines.get("result") or not klines["result"].get("list"):
            raise HTTPException(status_code=400, detail="No data available")
        
        # Convert to DataFrame
        data = klines["result"]["list"]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        
        # Get strategy
        strategy = get_strategy(request.strategy)
        
        # Generate signal
        signal = strategy.generate_signal(df, request.symbol)
        
        # Record signal in database
        paper_db.record_signal(
            account_id=1,
            symbol=request.symbol,
            signal=signal.signal.value,
            strategy=request.strategy,
            confidence=signal.confidence,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            reason=signal.reason
        )
        
        return {"status": "success", "data": signal.to_dict()}
    except Exception as e:
        logger.error(f"Strategy signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/scan")
async def scan_all_strategies(symbol: str, timeframe: str = "1h"):
    """Scan all strategies for a symbol"""
    try:
        if not PANDAS_AVAILABLE or not bybit_client:
            raise HTTPException(status_code=503, detail="Required dependencies not available")
        
        # Get klines
        klines = bybit_client.get_kline(
            category="spot",
            symbol=symbol,
            interval=timeframe,
            limit=100
        )
        
        if not klines.get("result") or not klines["result"].get("list"):
            raise HTTPException(status_code=400, detail="No data available")
        
        # Convert to DataFrame
        data = klines["result"]["list"]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        
        # Scan all strategies
        signals = []
        buy_signals = 0
        sell_signals = 0
        
        for strategy_name in STRATEGIES.keys():
            try:
                strategy = get_strategy(strategy_name)
                signal = strategy.generate_signal(df, symbol)
                
                signals.append(signal.to_dict())
                
                if signal.signal == SignalType.BUY:
                    buy_signals += 1
                elif signal.signal == SignalType.SELL:
                    sell_signals += 1
                
            except Exception as strategy_error:
                logger.warning(f"Strategy {strategy_name} error: {strategy_error}")
                continue
        
        # Determine consensus
        consensus = "neutral"
        consensus_confidence = 0.0
        
        total_signals = buy_signals + sell_signals
        if total_signals > 0:
            if buy_signals > sell_signals * 1.5:
                consensus = "bullish"
                consensus_confidence = buy_signals / len(signals)
            elif sell_signals > buy_signals * 1.5:
                consensus = "bearish"
                consensus_confidence = sell_signals / len(signals)
        
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "timeframe": timeframe,
                "total_strategies": len(signals),
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "hold_signals": len(signals) - buy_signals - sell_signals,
                "consensus": consensus,
                "consensus_confidence": round(consensus_confidence, 4),
                "signals": signals
            }
        }
    except Exception as e:
        logger.error(f"Strategy scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/performance")
async def get_strategy_performance():
    """Get strategy performance metrics"""
    try:
        performance = paper_db.get_strategy_performance(account_id=1)
        return {"status": "success", "data": performance}
    except Exception as e:
        logger.error(f"Strategy performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MARKET DATA & ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/market/overview")
async def get_market_overview():
    """Get market overview with major pairs"""
    try:
        if not bybit_client:
            raise HTTPException(status_code=503, detail="Bybit not available")
        
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        overview = []
        
        for symbol in symbols:
            try:
                ticker = bybit_client.get_tickers(category="spot", symbol=symbol)
                if ticker.get("result") and ticker["result"].get("list"):
                    data = ticker["result"]["list"][0]
                    overview.append({
                        "symbol": symbol,
                        "last_price": data.get("lastPrice"),
                        "change_24h": data.get("price24hPcnt"),
                        "volume_24h": data.get("volume24h"),
                        "high_24h": data.get("highPrice24h"),
                        "low_24h": data.get("lowPrice24h")
                    })
            except Exception as e:
                logger.warning(f"Error fetching {symbol}: {e}")
                continue
        
        return {"status": "success", "data": overview}
    except Exception as e:
        logger.error(f"Market overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/market")
async def ai_market_analysis(request: AIAnalysisRequest):
    """Get AI-powered market analysis"""
    try:
        if not bybit_client or not PANDAS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Required services not available")
        
        # Get market data
        klines = bybit_client.get_kline(
            category="spot",
            symbol=request.symbol,
            interval=request.timeframe,
            limit=100
        )
        
        if not klines.get("result") or not klines["result"].get("list"):
            raise HTTPException(status_code=400, detail="No data available")
        
        # Convert to DataFrame
        data = klines["result"]["list"]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        df["close"] = pd.to_numeric(df["close"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["volume"] = pd.to_numeric(df["volume"])
        
        prices = df["close"].tolist()
        current_price = prices[-1]
        
        # Calculate indicators
        from strategies.strategies import TechnicalIndicators
        
        rsi = TechnicalIndicators.rsi(df["close"], 14).iloc[-1]
        ema_20 = TechnicalIndicators.ema(df["close"], 20).iloc[-1]
        ema_50 = TechnicalIndicators.ema(df["close"], 50).iloc[-1]
        atr = TechnicalIndicators.atr(df["high"], df["low"], df["close"], 14).iloc[-1]
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df["close"])
        
        # Get AI analysis
        if anthropic_client:
            prompt = f"""Analyze {request.symbol} market data as an expert trader:

Current Price: ${current_price:,.2f}
Technical Indicators:
- RSI (14): {rsi:.2f}
- EMA 20: ${ema_20:.2f}
- EMA 50: ${ema_50:.2f}
- ATR (14): ${atr:.2f}
- MACD Histogram: {histogram.iloc[-1]:.4f}

Price Action (last 10 candles): {prices[-10:]}

Provide a concise technical analysis with:
1. Trend direction (Bullish/Bearish/Neutral)
2. Key support and resistance levels
3. Trading recommendation (Buy/Sell/Hold) with reasoning
4. Risk level (Low/Medium/High)
5. Suggested stop loss and take profit levels

Keep it under 200 words and actionable."""
            
            chat_request = ChatRequest(message=prompt, model="claude")
            analysis = await chat_claude(chat_request)
            ai_content = analysis["content"]
        else:
            ai_content = "AI analysis not available. Please check technical indicators above."
        
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "current_price": current_price,
            "indicators": {
                "rsi": round(rsi, 2) if not pd.isna(rsi) else None,
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "atr": round(atr, 2) if not pd.isna(atr) else None,
                "macd_histogram": round(histogram.iloc[-1], 4) if not pd.isna(histogram.iloc[-1]) else None
            },
            "ai_analysis": ai_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/performance")
async def get_trading_analytics():
    """Get comprehensive trading analytics"""
    try:
        stats = paper_db.get_trading_stats(account_id=1)
        balance_history = paper_db.get_balance_history(account_id=1, hours=168)  # 1 week
        
        return {
            "status": "success",
            "data": {
                "stats": stats,
                "balance_history": balance_history,
                "current_equity": paper_account.equity
            }
        }
    except Exception as e:
        logger.error(f"Trading analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket for live price updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                symbol = message.get("symbol", "BTCUSDT")
                if symbol not in manager.subscriptions:
                    manager.subscriptions[symbol] = []
                if websocket not in manager.subscriptions[symbol]:
                    manager.subscriptions[symbol].append(websocket)
                
                await websocket.send_json({
                    "type": "subscribed",
                    "symbol": symbol,
                    "message": f"Subscribed to {symbol} updates"
                })
            
            elif message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def price_stream_task():
    """Background task to stream prices to connected clients"""
    while True:
        try:
            if manager.active_connections and bybit_client:
                symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
                updates = {}
                
                for symbol in symbols:
                    try:
                        ticker = bybit_client.get_tickers(category="spot", symbol=symbol)
                        if ticker.get("result") and ticker["result"].get("list"):
                            data = ticker["result"]["list"][0]
                            updates[symbol] = {
                                "price": data.get("lastPrice"),
                                "change": data.get("price24hPcnt"),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                    except Exception as e:
                        logger.warning(f"Price fetch error for {symbol}: {e}")
                        continue
                
                if updates:
                    await manager.broadcast({
                        "type": "price_update",
                        "data": updates
                    })
        except Exception as e:
            logger.error(f"Price stream error: {e}")
        
        await asyncio.sleep(5)  # Update every 5 seconds

async def paper_trading_monitor():
    """Background task to monitor paper trading positions"""
    while True:
        try:
            # Update prices
            if bybit_client:
                prices = {}
                for position in paper_account.get_positions():
                    symbol = position["symbol"]
                    if symbol not in prices:
                        try:
                            ticker = bybit_client.get_tickers(category="spot", symbol=symbol)
                            if ticker.get("result") and ticker["result"].get("list"):
                                prices[symbol] = float(ticker["result"]["list"][0]["lastPrice"])
                        except:
                            continue
                
                paper_account.update_prices(prices)
                
                # Check for triggered stop losses and take profits
                triggered = paper_account.check_stop_loss_take_profit(prices)
                for trigger in triggered:
                    logger.info(f"Triggered {trigger['type']} for {trigger['position_id']}")
                    # Auto-close position
                    result = paper_account.close_position(
                        trigger["position_id"],
                        trigger["trigger_price"]
                    )
                    if result["success"]:
                        paper_db.close_trade(
                            order_id=trigger["position_id"],
                            exit_price=trigger["trigger_price"],
                            pnl=result["pnl"],
                            pnl_pct=0  # Will be calculated in DB
                        )
                
                # Record balance snapshot every 5 minutes
                paper_db.record_balance(
                    account_id=1,
                    balance=paper_account.balance,
                    equity=paper_account.equity
                )
        except Exception as e:
            logger.error(f"Paper trading monitor error: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )