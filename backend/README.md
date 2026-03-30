# GOMALE OS Backend

## Setup

```bash
pip install -r requirements.txt
```

## Run Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Run Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### AI Chat
- `POST /api/ai/chat` - Chat with AI models
- `POST /api/ai/compare` - Compare all AI models

### TTS
- `POST /api/tts` - Text to speech

### Bybit Trading
- `GET /api/bybit/account` - Account info
- `GET /api/bybit/balance` - Wallet balance
- `GET /api/bybit/tickers` - Market tickers
- `GET /api/bybit/kline` - Candlestick data
- `GET /api/bybit/orders` - Active orders
- `GET /api/bybit/positions` - Open positions
- `POST /api/bybit/order` - Place order

### Market Data
- `GET /api/market/overview` - Market overview
- `WS /ws/prices` - WebSocket price stream

### AI Analysis
- `POST /api/analysis/market` - AI market analysis

## WebSocket Usage

Connect to `ws://localhost:8000/ws/prices`

Send JSON:
```json
{"action": "subscribe", "symbol": "BTCUSDT"}
```

## Environment Variables

See `.env.gomale` for required API keys.
