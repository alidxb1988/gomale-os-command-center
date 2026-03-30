# GOMALE OS Command Center

Complete full-stack trading and AI intelligence platform for GOMALE GROUP.

## Architecture

```
gomale-os-command-center/
├── backend/          # FastAPI Backend
│   ├── main.py       # Main API with all endpoints
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/         # Next.js Frontend
    ├── pages/        # React pages
    ├── components/   # Shared components
    ├── lib/          # API utilities
    └── styles/       # Tailwind CSS
```

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Access

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Features

### Backend (FastAPI)
- **AI APIs**: Claude, Gemini, Perplexity, Kimi
- **TTS**: ElevenLabs text-to-speech
- **Trading**: Bybit TestNet integration
- **WebSocket**: Real-time price streaming
- **REST API**: Full CRUD operations
- **CORS**: Configured for Vercel deployment

### Frontend (Next.js)
- **Dashboard**: Live market data, account info
- **Trading Deck**: Order execution, positions
- **AI Chat**: All 4 models + compare mode
- **Analytics**: AI-powered market analysis
- **Settings**: API configuration

## API Keys (from .env.gomale)

All API keys are loaded from `/root/.openclaw/workspace/.env.gomale`

## Deployment

### Backend
```bash
cd backend
docker build -t gomale-backend .
docker run -p 8000:8000 gomale-backend
```

### Frontend
```bash
cd frontend
vercel --prod
```

## Environment Variables

Backend automatically loads from `.env.gomale`.

Frontend needs:
```
NEXT_PUBLIC_API_URL=https://your-backend-url
NEXT_PUBLIC_WS_URL=wss://your-backend-url
```

## License
Private - GOMALE GROUP
