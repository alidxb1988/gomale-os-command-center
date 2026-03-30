# GOMALE OS Command Center - Frontend

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

## Build

```bash
npm run build
```

## Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Features

- **Dashboard**: Account overview, market data, system status
- **Trading Deck**: Place orders, view positions, market data
- **AI Chat**: Multi-model chat (Claude, Gemini, Perplexity, Kimi)
- **Analytics**: AI-powered market analysis
- **Settings**: API configuration, preferences

## Tech Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide Icons
