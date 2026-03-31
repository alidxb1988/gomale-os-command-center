// API URL - will be set after backend deployment
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// AI APIs
export const aiApi = {
  chat: (message: string, model: string) => 
    fetchApi('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, model }),
    }),
  
  compare: (message: string) =>
    fetchApi('/api/ai/compare', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  
  tts: (text: string, voiceId?: string) =>
    fetchApi('/api/tts', {
      method: 'POST',
      body: JSON.stringify({ text, voice_id: voiceId }),
    }),
};

// Bybit Trading APIs
export const tradingApi = {
  // Live Trading
  getAccount: () => fetchApi('/api/bybit/account'),
  getBalance: () => fetchApi('/api/bybit/balance'),
  getTickers: (category = 'spot') => fetchApi(`/api/bybit/tickers?category=${category}`),
  getOrders: (category = 'spot') => fetchApi(`/api/bybit/orders?category=${category}`),
  getPositions: (category = 'linear') => fetchApi(`/api/bybit/positions?category=${category}`),
  getKline: (symbol: string, interval = '60') => 
    fetchApi(`/api/bybit/kline?symbol=${symbol}&interval=${interval}`),
  
  placeOrder: (order: {
    symbol: string;
    side: string;
    order_type: string;
    qty: number;
    price?: number;
    category?: string;
  }) => fetchApi('/api/bybit/order', {
    method: 'POST',
    body: JSON.stringify(order),
  }),

  cancelOrder: (orderId: string, category: string, symbol: string) =>
    fetchApi(`/api/bybit/order/${orderId}?category=${category}&symbol=${symbol}`, {
      method: 'DELETE',
    }),

  // Paper Trading
  getPaperAccount: () => fetchApi('/api/paper/account'),
  getPaperPositions: () => fetchApi('/api/paper/positions'),
  getPaperHistory: (limit = 100) => fetchApi(`/api/paper/history?limit=${limit}`),
  
  placePaperOrder: (order: {
    symbol: string;
    side: string;
    order_type: string;
    qty: number;
    price?: number;
    use_risk_management?: boolean;
    strategy?: string;
  }) => fetchApi('/api/paper/order', {
    method: 'POST',
    body: JSON.stringify(order),
  }),

  closePaperPosition: (positionId: string) =>
    fetchApi(`/api/paper/close/${positionId}`, {
      method: 'POST',
    }),

  resetPaperAccount: () =>
    fetchApi('/api/paper/reset', {
      method: 'POST',
    }),

  // Risk Management
  getRiskSettings: () => fetchApi('/api/risk/settings'),
  updateRiskSettings: (settings: {
    risk_per_trade: number;
    max_position_size: number;
    stop_loss_type: string;
    take_profit_ratio: number;
    trailing_stop: boolean;
  }) => fetchApi('/api/risk/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  }),
  getPortfolioRisk: () => fetchApi('/api/risk/portfolio'),

  // Strategies
  getStrategies: () => fetchApi('/api/strategies'),
  getStrategySignal: (symbol: string, strategy: string, timeframe = '1h') =>
    fetchApi('/api/strategies/signal', {
      method: 'POST',
      body: JSON.stringify({ symbol, strategy, timeframe }),
    }),
  scanStrategies: (symbol: string, timeframe = '1h') =>
    fetchApi(`/api/strategies/scan?symbol=${symbol}&timeframe=${timeframe}`, {
      method: 'POST',
    }),
  getStrategyPerformance: () => fetchApi('/api/strategies/performance'),
};

// Market Data APIs
export const marketApi = {
  getOverview: () => fetchApi('/api/market/overview'),
  analyze: (symbol: string, timeframe = '1h') =>
    fetchApi('/api/analysis/market', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframe }),
    }),
  getAnalytics: () => fetchApi('/api/analytics/performance'),
};

// TTS API (alias for aiApi.tts)
export const ttsApi = {
  generate: (text: string, voiceId?: string) =>
    fetchApi('/api/tts', {
      method: 'POST',
      body: JSON.stringify({ text, voice_id: voiceId }),
    }),
};

// Format utilities
export const formatPrice = (price: number | string, decimals = 2) => {
  const num = typeof price === 'string' ? parseFloat(price) : price;
  if (num === undefined || num === null || isNaN(num)) return '0.00';
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatPercent = (value: number | string) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num === undefined || num === null || isNaN(num)) return '0.00%';
  const formatted = (num * 100).toFixed(2);
  return `${num >= 0 ? '+' : ''}${formatted}%`;
};

export const formatNumber = (value: number | string) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num === undefined || num === null || isNaN(num)) return '0';
  return num.toLocaleString('en-US', { maximumFractionDigits: 0 });
};