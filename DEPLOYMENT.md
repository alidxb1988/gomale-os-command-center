# GOMALE OS Trading Platform - Deployment Guide

## 🚀 Backend Deployment to Railway

### Prerequisites
1. Railway CLI installed: `npm install -g @railway/cli`
2. Railway account and project created
3. Environment variables configured

### Deployment Steps

1. **Login to Railway:**
```bash
railway login
```

2. **Link to your project:**
```bash
cd /root/.openclaw/workspace/gomale-os-command-center/backend
railway link
```

3. **Set environment variables:**
```bash
railway variables set ANTHROPIC_API_KEY="your_key"
railway variables set GEMINI_API_KEY="your_key"
railway variables set PERPLEXITY_API_KEY="your_key"
railway variables set KIMI_API_KEY="your_key"
railway variables set ELEVENLABS_API_KEY="your_key"
railway variables set BYBIT_TESTNET_KEY="your_key"
railway variables set BYBIT_TESTNET_SECRET="your_secret"
```

4. **Deploy:**
```bash
railway up
```

5. **Get the public URL:**
```bash
railway domain
```

## 🌐 Frontend Deployment to Vercel

### Prerequisites
1. Vercel CLI installed: `npm install -g vercel`
2. Vercel account

### Deployment Steps

1. **Login to Vercel:**
```bash
vercel login
```

2. **Update API URL in frontend:**
Edit `/frontend/lib/api.ts` and set the backend URL:
```typescript
export const API_URL = 'https://your-backend-url.railway.app';
```

3. **Deploy:**
```bash
cd /root/.openclaw/workspace/gomale-os-command-center/frontend
vercel --prod
```

## 📋 Features Implemented

### 1. AI Hub (/ai-hub)
- Perplexity-style minimal interface
- Multi-model AI orchestration (Claude, Gemini, Perplexity, Kimi)
- Intelligent task routing
- Sidebar with conversation history
- Model selector with auto-select mode
- Voice input support
- Fullscreen mode

### 2. Internationalization (i18n)
- 10 languages: EN, FR, AR, ES, PT, DE, IT, RU, ZH, JA
- RTL support for Arabic
- Language switcher in header
- Full translation coverage

### 3. Voice Assistant
- Web Speech API integration
- VoiceCommandContext for state management
- Voice commands for navigation
- Voice feedback using ElevenLabs
- Floating AI agent with voice input

### 4. Floating AI Agent
- Gemini logo floating button
- Quick actions (Trading, AI Chat, Create Image, Code Help)
- Expandable chat interface
- Quick access to full AI Hub

### 5. Backend API Endpoints
- `/api/ai/chat` - Chat with any AI model
- `/api/ai/compare` - Compare all models
- `/api/orchestrate` - Intelligent AI routing
- `/api/models` - List available models
- `/api/tts` - Text-to-speech
- Trading endpoints for Bybit
- Paper trading system

## 🔑 Environment Variables Required

### Backend (.env)
```
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
PERPLEXITY_API_KEY=your_perplexity_key
KIMI_API_KEY=your_kimi_key
ELEVENLABS_API_KEY=your_elevenlabs_key
BYBIT_TESTNET_KEY=your_bybit_key
BYBIT_TESTNET_SECRET=your_bybit_secret
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

## 🌟 Access Control

### Routes
- `/` - Landing page
- `/dashboard` - Trading dashboard (admin)
- `/ai-hub` - Full AI Hub (admin + team)
- `/ai-chat` - Basic AI chat
- `/trading` - Trading deck
- `/analytics` - Analytics
- `/settings` - Settings

### User Levels
- **Admin**: Full access to all features
- **Team**: AI Hub with all models and tools
- **Public**: Limited access to basic models only

## 🔗 GitHub Repository
https://github.com/alidxb1988/gomale-os-command-center

## 📝 API Documentation

### Orchestration Endpoint
```
POST /api/orchestrate
{
  "message": "Your question here",
  "preferred_model": "optional_model_id"
}
```

Response:
```json
{
  "model": "claude",
  "model_name": "Claude 3.5 Sonnet",
  "task_type": "code",
  "confidence": 0.85,
  "content": "AI response...",
  "sources": []
}
```

### Models Endpoint
```
GET /api/models
```

Returns list of available AI models with capabilities.

## 🎯 Next Steps

1. Deploy backend to Railway
2. Copy backend public URL
3. Update frontend API_URL
4. Deploy frontend to Vercel
5. Test all API connections
6. Configure custom domains (optional)

## 📞 Support

For issues or questions, check:
- Backend logs: `railway logs`
- Frontend build: `vercel --debug`
- GitHub Issues: https://github.com/alidxb1988/gomale-os-command-center/issues
