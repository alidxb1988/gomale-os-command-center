'use client';

import { useState, useEffect } from 'react';
import { 
  ArrowUpDown, 
  TrendingUp, 
  TrendingDown, 
  Wallet,
  Send,
  RefreshCw,
  Bot,
  Play,
  Square,
  Settings,
  Shield,
  Target,
  Activity,
  BarChart3,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { tradingApi, marketApi, formatPrice, formatNumber } from '@/lib/api';
import toast from 'react-hot-toast';

interface Ticker {
  symbol: string;
  lastPrice: string;
  price24hPcnt: string;
  volume24h: string;
  highPrice24h: string;
  lowPrice24h: string;
}

interface Strategy {
  name: string;
  category: string;
  description: string;
}

interface Signal {
  symbol: string;
  signal: 'buy' | 'sell' | 'hold';
  strategy: string;
  confidence: number;
  entry_price: number;
  stop_loss?: number;
  take_profit?: number;
  reason: string;
}

export default function TradingPage() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [balance, setBalance] = useState<any>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [paperPositions, setPaperPositions] = useState<any[]>([]);
  const [paperAccount, setPaperAccount] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'market' | 'paper' | 'strategies'>('market');
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [scanResults, setScanResults] = useState<any>(null);
  const [scanning, setScanning] = useState(false);
  
  // Order form state
  const [orderForm, setOrderForm] = useState({
    side: 'Buy',
    orderType: 'Market',
    qty: '',
    price: '',
    useRiskManagement: true,
    strategy: '',
  });

  useEffect(() => {
    fetchData();
    fetchStrategies();
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [tickersRes, balanceRes, ordersRes, positionsRes, paperAccRes, paperPosRes] = await Promise.all([
        tradingApi.getTickers('spot').catch(() => ({ data: { result: { list: [] } } })),
        tradingApi.getBalance().catch(() => ({ data: {} })),
        tradingApi.getOrders('spot').catch(() => ({ data: { result: { list: [] } } })),
        tradingApi.getPositions('linear').catch(() => ({ data: { result: { list: [] } } })),
        tradingApi.getPaperAccount().catch(() => ({ data: {} })),
        tradingApi.getPaperPositions().catch(() => ({ data: [] })),
      ]);
      
      setTickers(tickersRes.data?.result?.list?.slice(0, 20) || []);
      setBalance(balanceRes.data);
      setOrders(ordersRes.data?.result?.list || []);
      setPositions(positionsRes.data?.result?.list || []);
      setPaperAccount(paperAccRes.data);
      setPaperPositions(paperPosRes.data || []);
    } catch (error) {
      console.error('Failed to fetch trading data:', error);
    }
  };

  const fetchStrategies = async () => {
    try {
      const res = await tradingApi.getStrategies();
      if (res.data) {
        setStrategies(res.data);
      }
    } catch (error) {
      console.error('Failed to fetch strategies:', error);
    }
  };

  const handlePlaceOrder = async () => {
    if (!orderForm.qty) {
      toast.error('Please enter quantity');
      return;
    }
    
    setLoading(true);
    try {
      const result = await tradingApi.placeOrder({
        symbol: selectedSymbol,
        side: orderForm.side,
        order_type: orderForm.orderType,
        qty: parseFloat(orderForm.qty),
        price: orderForm.price ? parseFloat(orderForm.price) : undefined,
        category: 'spot',
      });
      
      toast.success(`Order placed successfully! Order ID: ${result.data?.result?.orderId}`);
      setOrderForm({ side: 'Buy', orderType: 'Market', qty: '', price: '', useRiskManagement: true, strategy: '' });
      fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  const handlePaperTrade = async () => {
    if (!orderForm.qty) {
      toast.error('Please enter quantity');
      return;
    }
    
    setLoading(true);
    try {
      const result = await tradingApi.placePaperOrder({
        symbol: selectedSymbol,
        side: orderForm.side,
        order_type: orderForm.orderType,
        qty: parseFloat(orderForm.qty),
        price: orderForm.price ? parseFloat(orderForm.price) : undefined,
        use_risk_management: orderForm.useRiskManagement,
        strategy: orderForm.strategy || undefined,
      });
      
      if (result.data?.success) {
        toast.success(`Paper trade executed! Order ID: ${result.data.order_id}`);
        if (result.data.stop_loss) {
          toast.info(`Stop Loss: $${formatPrice(result.data.stop_loss)}`);
        }
        if (result.data.take_profit) {
          toast.info(`Take Profit: $${formatPrice(result.data.take_profit)}`);
        }
      } else {
        toast.error(result.data?.error || 'Paper trade failed');
      }
      
      setOrderForm({ side: 'Buy', orderType: 'Market', qty: '', price: '', useRiskManagement: true, strategy: '' });
      fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to place paper trade');
    } finally {
      setLoading(false);
    }
  };

  const handleClosePaperPosition = async (positionId: string) => {
    try {
      const result = await tradingApi.closePaperPosition(positionId);
      if (result.data?.success) {
        const pnl = result.data.pnl;
        if (pnl > 0) {
          toast.success(`Position closed with profit: +$${formatPrice(pnl)}`);
        } else if (pnl < 0) {
          toast.error(`Position closed with loss: -$${formatPrice(Math.abs(pnl))}`);
        } else {
          toast.info('Position closed at breakeven');
        }
        fetchData();
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to close position');
    }
  };

  const handleScanStrategies = async () => {
    setScanning(true);
    try {
      const result = await tradingApi.scanStrategies(selectedSymbol);
      setScanResults(result.data);
      toast.success(`Scanned ${result.data?.total_strategies} strategies`);
    } catch (error: any) {
      toast.error(error.message || 'Strategy scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleResetPaperAccount = async () => {
    if (!confirm('Are you sure you want to reset your paper trading account? This cannot be undone.')) {
      return;
    }
    try {
      await tradingApi.resetPaperAccount();
      toast.success('Paper trading account reset to $10,000');
      fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to reset account');
    }
  };

  const getChangeColor = (change: string) => {
    return parseFloat(change) >= 0 ? 'text-green-500' : 'text-red-500';
  };

  const getChangeIcon = (change: string) => {
    return parseFloat(change) >= 0 ? TrendingUp : TrendingDown;
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'buy') return 'text-green-500';
    if (signal === 'sell') return 'text-red-500';
    return 'text-yellow-500';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Deck</h1>
          <p className="text-gray-400 mt-1">Execute trades on Bybit TestNet & Paper Trading</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-gomale-gold/10 text-gomale-gold rounded-lg hover:bg-gomale-gold/20 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-800">
        {[
          { id: 'market', label: 'Live Market', icon: Activity },
          { id: 'paper', label: 'Paper Trading', icon: Target },
          { id: 'strategies', label: 'Strategies', icon: BarChart3 },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-gomale-gold text-gomale-gold'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'market' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Market Table */}
          <div className="lg:col-span-2 space-y-4">
            <div className="card-glass overflow-hidden">
              <div className="p-4 border-b border-gray-800">
                <h2 className="font-semibold text-white">Market</h2>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gomale-dark">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Symbol</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">24h Change</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Volume</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {tickers.map((ticker) => {
                      const ChangeIcon = getChangeIcon(ticker.price24hPcnt);
                      return (
                        <tr 
                          key={ticker.symbol}
                          onClick={() => setSelectedSymbol(ticker.symbol)}
                          className={`hover:bg-gray-800/50 cursor-pointer transition-colors ${
                            selectedSymbol === ticker.symbol ? 'bg-gomale-gold/5' : ''
                          }`}
                        >
                          <td className="px-4 py-3">
                            <span className="font-medium text-white">
                              {ticker.symbol}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-white">
                              ${formatPrice(ticker.lastPrice)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className={`flex items-center justify-end gap-1 ${getChangeColor(ticker.price24hPcnt)}`}>
                              <ChangeIcon className="w-3 h-3" />
                              {(parseFloat(ticker.price24hPcnt) * 100).toFixed(2)}%
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-gray-400">
                            {formatNumber(ticker.volume24h)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Active Orders & Positions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card-glass p-4">
                <h3 className="font-semibold text-white mb-4">Active Orders</h3>
                {orders.length === 0 ? (
                  <p className="text-gray-400 text-sm">No active orders</p>
                ) : (
                  <div className="space-y-2">
                    {orders.slice(0, 5).map((order: any, idx) => (
                      <div key={idx} className="p-3 rounded bg-gomale-dark text-sm">
                        <div className="flex justify-between">
                          <span className={order.side === 'Buy' ? 'text-green-500' : 'text-red-500'}>
                            {order.side} {order.symbol}
                          </span>
                          <span className="text-gray-400">{order.orderType}</span>
                        </div>
                        <div className="text-gray-400 mt-1">
                          Qty: {order.qty} @ ${formatPrice(order.price || order.avgPrice)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="card-glass p-4">
                <h3 className="font-semibold text-white mb-4">Positions</h3>
                {positions.length === 0 ? (
                  <p className="text-gray-400 text-sm">No open positions</p>
                ) : (
                  <div className="space-y-2">
                    {positions.slice(0, 5).map((pos: any, idx) => (
                      <div key={idx} className="p-3 rounded bg-gomale-dark text-sm">
                        <div className="flex justify-between">
                          <span className="text-white">{pos.symbol}</span>
                          <span className={parseFloat(pos.unrealisedPnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
                            {parseFloat(pos.unrealisedPnl) >= 0 ? '+' : ''}
                            ${formatPrice(pos.unrealisedPnl)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Order Form */}
          <div className="card-glass p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Place Live Order</h2>
            
            <div className="mb-4 p-3 rounded-lg bg-gomale-dark">
              <div className="text-sm text-gray-400 mb-1">Selected Pair</div>
              <div className="text-xl font-bold text-gomale-gold">{selectedSymbol}</div>
            </div>

            <div className="space-y-4">
              {/* Side Toggle */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setOrderForm({ ...orderForm, side: 'Buy' })}
                  className={`py-2 rounded-lg font-medium transition-colors ${
                    orderForm.side === 'Buy' 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gomale-dark text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Buy
                </button>
                <button
                  onClick={() => setOrderForm({ ...orderForm, side: 'Sell' })}
                  className={`py-2 rounded-lg font-medium transition-colors ${
                    orderForm.side === 'Sell' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gomale-dark text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Sell
                </button>
              </div>

              {/* Order Type */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Order Type</label>
                <select
                  value={orderForm.orderType}
                  onChange={(e) => setOrderForm({ ...orderForm, orderType: e.target.value })}
                  className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
                >
                  <option value="Market">Market</option>
                  <option value="Limit">Limit</option>
                </select>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Quantity</label>
                <input
                  type="number"
                  value={orderForm.qty}
                  onChange={(e) => setOrderForm({ ...orderForm, qty: e.target.value })}
                  placeholder="0.00"
                  className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-gomale-gold focus:outline-none"
                />
              </div>

              {/* Price (for Limit orders) */}
              {orderForm.orderType === 'Limit' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Price</label>
                  <input
                    type="number"
                    value={orderForm.price}
                    onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
                    placeholder="0.00"
                    className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-gomale-gold focus:outline-none"
                  />
                </div>
              )}

              {/* Submit Button */}
              <button
                onClick={handlePlaceOrder}
                disabled={loading}
                className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
                  orderForm.side === 'Buy'
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-red-500 hover:bg-red-600 text-white'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    {orderForm.side} {selectedSymbol}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'paper' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Paper Account Summary */}
          <div className="lg:col-span-2 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card-glass p-4">
                <div className="text-sm text-gray-400 mb-1">Initial Balance</div>
                <div className="text-xl font-bold text-white">
                  ${formatPrice(paperAccount?.initial_balance || 10000)}
                </div>
              </div>
              <div className="card-glass p-4">
                <div className="text-sm text-gray-400 mb-1">Current Equity</div>
                <div className={`text-xl font-bold ${(paperAccount?.total_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ${formatPrice(paperAccount?.equity || 10000)}
                </div>
              </div>
              <div className="card-glass p-4">
                <div className="text-sm text-gray-400 mb-1">Total P&L</div>
                <div className={`text-xl font-bold ${(paperAccount?.total_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {(paperAccount?.total_pnl || 0) >= 0 ? '+' : ''}
                  ${formatPrice(paperAccount?.total_pnl || 0)}
                  ({(paperAccount?.total_pnl_pct || 0).toFixed(2)}%)
                </div>
              </div>
              <div className="card-glass p-4">
                <div className="text-sm text-gray-400 mb-1">Open Positions</div>
                <div className="text-xl font-bold text-white">
                  {paperPositions.length}
                </div>
              </div>
            </div>

            {/* Paper Positions */}
            <div className="card-glass overflow-hidden">
              <div className="p-4 border-b border-gray-800 flex justify-between items-center">
                <h2 className="font-semibold text-white">Paper Positions</h2>
                <button
                  onClick={handleResetPaperAccount}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  Reset Account
                </button>
              </div>
              
              {paperPositions.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No open paper positions</p>
                  <p className="text-sm mt-2">Use the order form to start paper trading</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gomale-dark">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Symbol</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Side</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Qty</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Entry</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Current</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">P&L</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-400">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {paperPositions.map((pos: any) => (
                        <tr key={pos.order_id} className="hover:bg-gray-800/50">
                          <td className="px-4 py-3 font-medium text-white">{pos.symbol}</td>
                          <td className="px-4 py-3">
                            <span className={pos.side === 'Buy' ? 'text-green-500' : 'text-red-500'}>
                              {pos.side}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-white">{pos.qty}</td>
                          <td className="px-4 py-3 text-right text-gray-400">${formatPrice(pos.entry_price)}</td>
                          <td className="px-4 py-3 text-right text-white">${formatPrice(pos.current_price)}</td>
                          <td className={`px-4 py-3 text-right ${pos.unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {pos.unrealized_pnl >= 0 ? '+' : ''}${formatPrice(pos.unrealized_pnl)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleClosePaperPosition(pos.order_id)}
                              className="px-3 py-1 bg-red-500/20 text-red-500 rounded hover:bg-red-500/30 transition-colors text-sm"
                            >
                              Close
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Paper Trading Order Form */}
          <div className="card-glass p-6">
            <div className="flex items-center gap-2 mb-6">
              <Target className="w-5 h-5 text-gomale-gold" />
              <h2 className="text-lg font-semibold text-white">Paper Trade</h2>
            </div>
            
            <div className="mb-4 p-3 rounded-lg bg-gomale-dark">
              <div className="text-sm text-gray-400 mb-1">Selected Pair</div>
              <div className="text-xl font-bold text-gomale-gold">{selectedSymbol}</div>
            </div>

            <div className="space-y-4">
              {/* Side Toggle */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setOrderForm({ ...orderForm, side: 'Buy' })}
                  className={`py-2 rounded-lg font-medium transition-colors ${
                    orderForm.side === 'Buy' 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gomale-dark text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Buy
                </button>
                <button
                  onClick={() => setOrderForm({ ...orderForm, side: 'Sell' })}
                  className={`py-2 rounded-lg font-medium transition-colors ${
                    orderForm.side === 'Sell' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gomale-dark text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Sell
                </button>
              </div>

              {/* Risk Management Toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-gomale-dark">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gomale-gold" />
                  <span className="text-sm text-gray-300">Auto Risk Management</span>
                </div>
                <button
                  onClick={() => setOrderForm({ ...orderForm, useRiskManagement: !orderForm.useRiskManagement })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    orderForm.useRiskManagement ? 'bg-green-500' : 'bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    orderForm.useRiskManagement ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Strategy Selection */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Strategy (Optional)</label>
                <select
                  value={orderForm.strategy}
                  onChange={(e) => setOrderForm({ ...orderForm, strategy: e.target.value })}
                  className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
                >
                  <option value="">No Strategy</option>
                  {strategies.map((s) => (
                    <option key={s.name} value={s.name}>{s.name} ({s.category})</option>
                  ))}
                </select>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Quantity (or $ Amount)</label>
                <input
                  type="number"
                  value={orderForm.qty}
                  onChange={(e) => setOrderForm({ ...orderForm, qty: e.target.value })}
                  placeholder="0.00"
                  className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-gomale-gold focus:outline-none"
                />
                {orderForm.useRiskManagement && (
                  <p className="text-xs text-gomale-gold mt-1">
                    Auto-calculated for 2% risk per trade
                  </p>
                )}
              </div>

              {/* Submit Button */}
              <button
                onClick={handlePaperTrade}
                disabled={loading}
                className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
                  orderForm.side === 'Buy'
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-red-500 hover:bg-red-600 text-white'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Paper {orderForm.side}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'strategies' && (
        <div className="space-y-6">
          {/* Strategy Scanner */}
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-gomale-gold" />
                  Strategy Scanner
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Scan all 18 strategies for {selectedSymbol}
                </p>
              </div>
              <button
                onClick={handleScanStrategies}
                disabled={scanning}
                className="flex items-center gap-2 px-6 py-2 bg-gomale-gold text-gomale-navy rounded-lg font-semibold hover:bg-gomale-gold/90 disabled:opacity-50 transition-colors"
              >
                {scanning ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Activity className="w-4 h-4" />
                )}
                {scanning ? 'Scanning...' : 'Scan All Strategies'}
              </button>
            </div>

            {scanResults && (
              <div className="space-y-4">
                {/* Consensus */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-gomale-dark">
                    <div className="text-sm text-gray-400 mb-1">Consensus</div>
                    <div className={`text-xl font-bold capitalize ${
                      scanResults.consensus === 'bullish' ? 'text-green-500' :
                      scanResults.consensus === 'bearish' ? 'text-red-500' :
                      'text-yellow-500'
                    }`}>
                      {scanResults.consensus}
                    </div>
                    <div className="text-xs text-gray-500">
                      {(scanResults.consensus_confidence * 100).toFixed(1)}% confidence
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-gomale-dark">
                    <div className="text-sm text-gray-400 mb-1">Buy Signals</div>
                    <div className="text-xl font-bold text-green-500">
                      {scanResults.buy_signals}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-gomale-dark">
                    <div className="text-sm text-gray-400 mb-1">Sell Signals</div>
                    <div className="text-xl font-bold text-red-500">
                      {scanResults.sell_signals}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-gomale-dark">
                    <div className="text-sm text-gray-400 mb-1">Hold/Neutral</div>
                    <div className="text-xl font-bold text-yellow-500">
                      {scanResults.hold_signals}
                    </div>
                  </div>
                </div>

                {/* Strategy Signals */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gomale-dark">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Strategy</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-400">Signal</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Confidence</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Entry</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Stop Loss</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {scanResults.signals.map((signal: Signal, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-800/50">
                          <td className="px-4 py-3 text-white font-medium">{signal.strategy}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                              signal.signal === 'buy' ? 'bg-green-500/20 text-green-500' :
                              signal.signal === 'sell' ? 'bg-red-500/20 text-red-500' :
                              'bg-yellow-500/20 text-yellow-500'
                            }`}>
                              {signal.signal === 'buy' && <TrendingUp className="w-3 h-3" />}
                              {signal.signal === 'sell' && <TrendingDown className="w-3 h-3" />}
                              {signal.signal === 'buy' && <CheckCircle2 className="w-3 h-3" />}
                              {signal.signal === 'sell' && <XCircle className="w-3 h-3" />}
                              {signal.signal === 'hold' && <AlertTriangle className="w-3 h-3" />}
                              {signal.signal.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-white">
                            {(signal.confidence * 100).toFixed(1)}%
                          </td>
                          <td className="px-4 py-3 text-right text-gray-400">
                            {signal.entry_price ? `$${formatPrice(signal.entry_price)}` : '-'}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-400">
                            {signal.stop_loss ? `$${formatPrice(signal.stop_loss)}` : '-'}
                          </td>
                          <td className="px-4 py-3 text-left text-gray-400 text-sm max-w-xs truncate">
                            {signal.reason}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Strategy List */}
          <div className="card-glass p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Available Strategies</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {strategies.map((strategy) => (
                <div key={strategy.name} className="p-4 rounded-lg bg-gomale-dark hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white">{strategy.name}</span>
                    <span className="text-xs px-2 py-1 rounded bg-gomale-gold/20 text-gomale-gold">
                      {strategy.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">{strategy.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}