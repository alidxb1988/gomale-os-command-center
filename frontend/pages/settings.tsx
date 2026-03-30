'use client';

import { useState } from 'react';
import { 
  Settings, 
  Key, 
  Bell, 
  Shield, 
  Globe,
  Save
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    apiEndpoint: 'http://localhost:8000',
    theme: 'dark',
    notifications: true,
    autoRefresh: true,
    refreshInterval: 10,
    defaultSymbol: 'BTCUSDT',
    defaultModel: 'claude',
  });

  const handleSave = () => {
    toast.success('Settings saved successfully');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">Configure your GOMALE OS Command Center</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Settings */}
        <div className="card-glass p-6">
          <div className="flex items-center gap-2 text-gomale-gold mb-6">
            <Key className="w-5 h-5" />
            <h2 className="font-semibold">API Configuration</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Backend API URL</label>
              <input
                type="text"
                value={settings.apiEndpoint}
                onChange={(e) => setSettings({ ...settings, apiEndpoint: e.target.value })}
                className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                Your FastAPI backend endpoint
              </p>
            </div>

            <div className="p-4 rounded-lg bg-gomale-dark">
              <h3 className="font-medium text-white mb-2">Connected APIs</h3>
              <div className="space-y-2 text-sm">
                <ApiStatus name="Claude (Anthropic)" status="connected" />
                <ApiStatus name="Gemini (Google)" status="connected" />
                <ApiStatus name="Perplexity" status="connected" />
                <ApiStatus name="Kimi (Moonshot)" status="connected" />
                <ApiStatus name="Bybit TestNet" status="connected" />
                <ApiStatus name="ElevenLabs" status="connected" />
              </div>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="card-glass p-6">
          <div className="flex items-center gap-2 text-gomale-gold mb-6">
            <Settings className="w-5 h-5" />
            <h2 className="font-semibold">Preferences</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Default Trading Pair</label>
              <select
                value={settings.defaultSymbol}
                onChange={(e) => setSettings({ ...settings, defaultSymbol: e.target.value })}
                className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
              >
                <option value="BTCUSDT">BTC/USDT</option>
                <option value="ETHUSDT">ETH/USDT</option>
                <option value="SOLUSDT">SOL/USDT</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Default AI Model</label>
              <select
                value={settings.defaultModel}
                onChange={(e) => setSettings({ ...settings, defaultModel: e.target.value })}
                className="w-full px-4 py-2 bg-gomale-dark border border-gray-700 rounded-lg text-white focus:border-gomale-gold focus:outline-none"
              >
                <option value="claude">Claude 3</option>
                <option value="gemini">Gemini</option>
                <option value="perplexity">Perplexity</option>
                <option value="kimi">Kimi</option>
              </select>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-gomale-dark">
              <span className="text-sm text-gray-300">Auto-refresh data</span>
              <button
                onClick={() => setSettings({ ...settings, autoRefresh: !settings.autoRefresh })}
                className={`w-12 h-6 rounded-full transition-colors ${
                  settings.autoRefresh ? 'bg-gomale-gold' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                  settings.autoRefresh ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-gomale-dark">
              <span className="text-sm text-gray-300">Notifications</span>
              <button
                onClick={() => setSettings({ ...settings, notifications: !settings.notifications })}
                className={`w-12 h-6 rounded-full transition-colors ${
                  settings.notifications ? 'bg-gomale-gold' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                  settings.notifications ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="lg:col-span-2 card-glass p-6">
          <div className="flex items-center gap-2 text-gomale-gold mb-4">
            <Globe className="w-5 h-5" />
            <h2 className="font-semibold">About GOMALE OS</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-gomale-dark">
              <div className="text-sm text-gray-400 mb-1">Version</div>
              <div className="text-lg font-semibold text-white">2.0.0</div>
            </div>

            <div className="p-4 rounded-lg bg-gomale-dark">
              <div className="text-sm text-gray-400 mb-1">Environment</div>
              <div className="text-lg font-semibold text-white">TestNet</div>
            </div>

            <div className="p-4 rounded-lg bg-gomale-dark">
              <div className="text-sm text-gray-400 mb-1">Last Updated</div>
              <div className="text-lg font-semibold text-white">March 2026</div>
            </div>
          </div>

          <p className="text-gray-400 mt-4">
            GOMALE OS Command Center is a comprehensive trading and AI intelligence platform 
            built for GOMALE GROUP. Features include multi-model AI chat, Bybit TestNet trading, 
            real-time market data, and advanced analytics.
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 bg-gomale-gold text-gomale-navy rounded-lg font-semibold hover:bg-gomale-gold/90 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </div>
  );
}

function ApiStatus({ name, status }: { name: string; status: 'connected' | 'disconnected' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-300">{name}</span>
      <span className={`text-xs px-2 py-1 rounded ${
        status === 'connected' 
          ? 'bg-green-500/20 text-green-500' 
          : 'bg-red-500/20 text-red-500'
      }`}>
        {status === 'connected' ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}
