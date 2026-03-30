'use client';

import { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Activity,
  Brain,
  Target,
  AlertTriangle
} from 'lucide-react';
import { marketApi, formatPrice } from '@/lib/api';
import toast from 'react-hot-toast';

const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT'];
const timeframes = [
  { value: '15', label: '15m' },
  { value: '60', label: '1h' },
  { value: '240', label: '4h' },
  { value: 'D', label: '1d' },
];

export default function AnalyticsPage() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('60');
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const result = await marketApi.analyze(symbol, timeframe);
      setAnalysis(result);
    } catch (error: any) {
      toast.error(error.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (rec: string) => {
    if (rec?.toLowerCase().includes('buy')) return 'text-green-500';
    if (rec?.toLowerCase().includes('sell')) return 'text-red-500';
    return 'text-yellow-500';
  };

  const getRiskColor = (risk: string) => {
    if (risk?.toLowerCase().includes('low')) return 'text-green-500';
    if (risk?.toLowerCase().includes('high')) return 'text-red-500';
    return 'text-yellow-500';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-gray-400 mt-1">AI-powered market analysis</p>
        </div>
      </div>

      {/* Controls */}
      <div className="card-glass p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Symbol</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
            >
              {symbols.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>{tf.label}</option>
              ))}
            </select>
          </div>

          <button
            onClick={runAnalysis}
            disabled={loading}
            className="px-6 py-2 bg-gomale-gold text-gomale-navy rounded-lg font-semibold hover:bg-gomale-gold/90 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <Brain className="w-4 h-4" />
            {loading ? 'Analyzing...' : 'Run AI Analysis'}
          </button>
        </div>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Price Info */}
          <div className="card-glass p-6">
            <div className="flex items-center gap-2 text-gomale-gold mb-4">
              <Activity className="w-5 h-5" />
              <h2 className="font-semibold">Price Info</h2>
            </div>

            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-400">Current Price</div>
                <div className="text-3xl font-bold text-white">
                  ${formatPrice(analysis.current_price)}
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-400">24h Change</div>
                <div className={`text-xl font-semibold ${
                  analysis.price_change_24h >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {analysis.price_change_24h >= 0 ? '+' : ''}
                  {analysis.price_change_24h?.toFixed(2)}%
                </div>
              </div>

              <div className="pt-4 border-t border-gray-800">
                <div className="text-sm text-gray-400">Last Updated</div>
                <div className="text-sm text-gray-300">
                  {new Date(analysis.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="lg:col-span-2 card-glass p-6">
            <div className="flex items-center gap-2 text-gomale-gold mb-4">
              <Brain className="w-5 h-5" />
              <h2 className="font-semibold">AI Analysis</h2>
            </div>

            <div className="prose prose-invert max-w-none">
              <div className="whitespace-pre-wrap text-gray-300 leading-relaxed">
                {analysis.ai_analysis}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={BarChart3}
          title="Total Analysis"
          value="0"
        />
        <StatCard
          icon={TrendingUp}
          title="Bullish Signals"
          value="0"
        />
        <StatCard
          icon={Target}
          title="Accuracy"
          value="--"
        />
        <StatCard
          icon={AlertTriangle}
          title="Risk Alerts"
          value="0"
        />
      </div>
    </div>
  );
}

function StatCard({ 
  icon: Icon, 
  title, 
  value 
}: { 
  icon: any; 
  title: string; 
  value: string;
}) {
  return (
    <div className="card-glass p-4">
      <div className="flex items-center gap-2 text-gray-400 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-sm">{title}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
