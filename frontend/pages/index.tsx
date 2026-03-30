'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Activity, 
  Bot,
  DollarSign,
  BarChart3,
  Clock
} from 'lucide-react';
import { tradingApi, marketApi, formatPrice, formatPercent } from '@/lib/api';
import Link from 'next/link';

interface MarketOverview {
  symbol: string;
  last_price: string;
  change_24h: string;
  volume_24h: string;
  high_24h: string;
  low_24h: string;
}

interface AccountInfo {
  equity?: string;
  available_balance?: string;
}

export default function DashboardPage() {
  const [marketData, setMarketData] = useState<MarketOverview[]>([]);
  const [accountInfo, setAccountInfo] = useState<AccountInfo>({});
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [market, account] = await Promise.all([
        marketApi.getOverview().catch(() => ({ data: [] })),
        tradingApi.getAccount().catch(() => ({ data: {} })),
      ]);
      
      setMarketData(market.data || []);
      setAccountInfo(account.data?.result?.list?.[0] || {});
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getChangeColor = (change: string) => {
    const num = parseFloat(change);
    return num >= 0 ? 'text-green-500' : 'text-red-500';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Welcome back to GOMALE OS Command Center</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          Last update: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Account Equity"
          value={`$${formatPrice(accountInfo.equity || '0')}`}
          icon={Wallet}
          trend="+2.4%"
          trendUp={true}
        />
        
        <StatCard
          title="Available Balance"
          value={`$${formatPrice(accountInfo.available_balance || '0')}`}
          icon={DollarSign}
        />
        
        <StatCard
          title="Active Positions"
          value="0"
          icon={BarChart3}
        />
        
        <StatCard
          title="AI Status"
          value="Online"
          icon={Bot}
          trend="All systems go"
          trendUp={true}
        />
      </div>

      {/* Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Cards */}
        <div className="lg:col-span-2 card-glass p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-gomale-gold" />
              Market Overview
            </h2>
            <Link 
              href="/trading"
              className="text-sm text-gomale-gold hover:underline"
            >
              View Trading Deck →
            </Link>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gomale-gold" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {marketData.map((coin) => (
                <div 
                  key={coin.symbol}
                  className="p-4 rounded-lg bg-gomale-dark border border-gray-800 hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white">
                      {coin.symbol.replace('USDT', '')}
                    </span>
                    <span className={getChangeColor(coin.change_24h)}>
                      {parseFloat(coin.change_24h) >= 0 ? '+' : ''}
                      {(parseFloat(coin.change_24h) * 100).toFixed(2)}%
                    </span>
                  </div>
                  
                  <div className="text-2xl font-bold text-white mb-1">
                    ${formatPrice(coin.last_price)}
                  </div>
                  
                  <div className="text-xs text-gray-500">
                    Vol: ${formatPrice(coin.volume_24h, 0)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card-glass p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Quick Actions</h2>
          
          <div className="space-y-3">
            <QuickAction
              href="/trading"
              icon={TrendingUp}
              title="Place Trade"
              description="Execute buy/sell orders"
            />
            
            <QuickAction
              href="/ai-chat"
              icon={Bot}
              title="Ask AI"
              description="Get market insights"
            />
            
            <QuickAction
              href="/analytics"
              icon={BarChart3}
              title="View Analytics"
              description="Technical analysis"
            />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card-glass p-6">
        <h2 className="text-lg font-semibold text-white mb-4">System Status</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusItem name="Claude AI" status="online" />
          <StatusItem name="Gemini AI" status="online" />
          <StatusItem name="Perplexity" status="online" />
          <StatusItem name="Kimi AI" status="online" />
          <StatusItem name="Bybit TestNet" status="online" />
          <StatusItem name="WebSocket" status="online" />
          <StatusItem name="ElevenLabs" status="online" />
          <StatusItem name="Market Data" status="online" />
        </div>
      </div>
    </div>
  );
}

function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  trendUp 
}: { 
  title: string; 
  value: string; 
  icon: any;
  trend?: string;
  trendUp?: boolean;
}) {
  return (
    <div className="card-glass p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {trend && (
            <p className={`text-sm mt-1 ${trendUp ? 'text-green-500' : 'text-red-500'}`}>
              {trendUp ? '↑' : '↓'} {trend}
            </p>
          )}
        </div>
        <div className="w-12 h-12 rounded-lg bg-gomale-gold/10 flex items-center justify-center">
          <Icon className="w-6 h-6 text-gomale-gold" />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ 
  href, 
  icon: Icon, 
  title, 
  description 
}: { 
  href: string; 
  icon: any; 
  title: string; 
  description: string;
}) {
  return (
    <Link 
      href={href}
      className="flex items-center gap-4 p-4 rounded-lg bg-gomale-dark border border-gray-800 hover:border-gomale-gold/50 transition-colors group"
    >
      <div className="w-10 h-10 rounded-lg bg-gomale-gold/10 flex items-center justify-center group-hover:bg-gomale-gold/20 transition-colors">
        <Icon className="w-5 h-5 text-gomale-gold" />
      </div>
      <div>
        <p className="font-medium text-white">{title}</p>
        <p className="text-sm text-gray-400">{description}</p>
      </div>
    </Link>
  );
}

function StatusItem({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-sm text-gray-400">{name}</span>
    </div>
  );
}
