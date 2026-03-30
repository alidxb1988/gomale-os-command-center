# GOMALE OS Command Center v2.1.0

**Production-ready trading platform with 18 strategies, paper trading, and AI analysis**

## Features

### 🤖 AI Integration
- **Claude** (Anthropic) - Primary trading analysis AI
- **Gemini** (Google) - Alternative AI model
- **Perplexity** - Real-time market research
- **Kimi** (Moonshot) - Chinese market insights
- **ElevenLabs TTS** - Voice synthesis for alerts

### 📈 Trading (18 Strategies)

#### Trend Following
1. **EMA Crossover** - EMA12/26 crossover signals
2. **MACD** - MACD line/signal with histogram
3. **Supertrend** - ATR-based trend direction
4. **ADX** - Trend strength analysis
5. **Parabolic SAR** - Trailing stop-based following
6. **Ichimoku Cloud** - Multi-factor trend analysis

#### Mean Reversion
7. **RSI** - Oversold/overbought extremes
8. **Bollinger Bands** - Price deviation trading
9. **Stochastic Oscillator** - Momentum reversals
10. **Williams %R** - Extreme capture

#### Breakout/Momentum
11. **Volume Breakout** - High volume breakouts
12. **ATR Breakout** - Volatility expansion
13. **Donchian Channel** - Highest high/lowest low breaks
14. **Momentum Burst** - Short-term acceleration

#### Pattern/Advanced
15. **Engulfing Pattern** - Candlestick patterns
16. **Stop Hunt** - Smart money detection
17. **Support/Resistance Flip** - Key level trading
18. **MTF Confluence** - Multi-timeframe confirmation

### 💰 Paper Trading
- Virtual balance tracking ($10,000 default)
- Real-time position management
- Auto stop-loss/take-profit execution
- Trade history and P&L tracking
- SQLite database for persistence

### 🛡️ Risk Management
- Position sizing (2% risk per trade default)
- ATR-based stop losses
- Configurable R:R ratios (default 2:1)
- Trailing stop support
- Portfolio exposure limits

### 📊 Live Trading (Bybit TestNet)
- Real market data
- Paper and live trading modes
- Position tracking
- Order management

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs on http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

### Environment Variables

Create `.env.gomale` in workspace root:

```env
# AI APIs
ANTHROPIC_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key
PERPLEXITY_API_KEY=your_perplexity_key
KIMI_API_KEY=your_kimi_key

# Trading (Bybit TestNet)
BYBIT_TESTNET_KEY=your_bybit_key
BYBIT_TESTNET_SECRET=your_bybit_secret

# TTS
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## API Endpoints

### Health
- `GET /` - System status
- `GET /health` - Health check

### AI
- `POST /api/ai/chat` - Chat with AI
- `POST /api/ai/compare` - Compare all models
- `POST /api/tts` - Text-to-speech

### Trading (Bybit)
- `GET /api/bybit/account` - Account info
- `GET /api/bybit/balance` - Wallet balance
- `GET /api/bybit/tickers` - Market tickers
- `POST /api/bybit/order` - Place order
- `GET /api/bybit/positions` - Open positions

### Paper Trading
- `GET /api/paper/account` - Paper account summary
- `POST /api/paper/order` - Place paper trade
- `POST /api/paper/close/{id}` - Close position
- `GET /api/paper/positions` - Open positions
- `POST /api/paper/reset` - Reset account

### Strategies
- `GET /api/strategies` - List strategies
- `POST /api/strategies/signal` - Get signal
- `POST /api/strategies/scan` - Scan all strategies
- `GET /api/strategies/performance` - Performance metrics

### Risk Management
- `GET /api/risk/settings` - Get settings
- `POST /api/risk/settings` - Update settings
- `GET /api/risk/portfolio` - Portfolio risk

### Market Data
- `GET /api/market/overview` - Market overview
- `POST /api/analysis/market` - AI analysis

## Deployment

### Backend
Run on any VPS or cloud provider:

```bash
# Using systemd
sudo systemctl enable gomale-os
sudo systemctl start gomale-os

# Using Docker (optional)
docker build -t gomale-os .
docker run -p 8000:8000 gomale-os
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

## Version History

### v2.1.0 (Current)
- Added 18 trading strategies
- Complete paper trading system
- Risk management with position sizing
- Strategy scanner with consensus
- SQLite database integration
- Enhanced error handling and logging

### v1.0.0
- Initial release
- Basic Bybit integration
- AI chat endpoints
- Dashboard UI

## License

MIT - GOMALE GROUP 2025