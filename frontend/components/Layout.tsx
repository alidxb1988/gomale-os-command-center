'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  LayoutDashboard, 
  TrendingUp, 
  MessageSquare, 
  Settings,
  Menu,
  X,
  Activity,
  Zap,
  Sparkles,
  Globe
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import LanguageSwitcher from './LanguageSwitcher';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [isRTL, setIsRTL] = useState(false);

  // Check for RTL languages
  useEffect(() => {
    setIsRTL(i18n.language === 'ar');
    document.documentElement.dir = i18n.language === 'ar' ? 'rtl' : 'ltr';
  }, [i18n.language]);

  const navItems = [
    { href: '/', label: t('nav.dashboard'), icon: LayoutDashboard },
    { href: '/trading', label: t('nav.trading'), icon: TrendingUp },
    { href: '/ai-hub', label: 'AI Hub', icon: Sparkles },
    { href: '/ai-chat', label: t('nav.aiChat'), icon: MessageSquare },
    { href: '/analytics', label: t('nav.analytics'), icon: Activity },
    { href: '/settings', label: t('nav.settings'), icon: Settings },
  ];

  // WebSocket connection
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/prices`);
    
    ws.onopen = () => {
      setWsStatus('connected');
      ws.send(JSON.stringify({ action: 'subscribe', symbol: 'BTCUSDT' }));
    };
    
    ws.onclose = () => setWsStatus('disconnected');
    ws.onerror = () => setWsStatus('disconnected');
    
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, []);

  return (
    <div className={`min-h-screen bg-gomale-darker flex ${isRTL ? 'flex-row-reverse' : ''}`}>
      {/* Sidebar */}
      <aside 
        className={clsx(
          'fixed lg:static inset-y-0 z-50 w-64 bg-gomale-navy border-r border-gray-800 transition-transform duration-300',
          isRTL ? 'right-0 border-l border-r-0' : 'left-0',
          sidebarOpen ? 'translate-x-0' : `${isRTL ? 'translate-x-full' : '-translate-x-full'} lg:translate-x-0 lg:w-20`
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gomale-gold rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-gomale-navy" />
            </div>
            <span className={clsx(
              'font-bold text-lg text-white transition-opacity',
              sidebarOpen ? 'opacity-100' : 'opacity-0 lg:hidden'
            )}>
              {t('app.name')}
            </span>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  isActive 
                    ? 'bg-gomale-gold/20 text-gomale-gold border border-gomale-gold/30' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className={clsx(
                  'transition-opacity',
                  sidebarOpen ? 'opacity-100' : 'opacity-0 lg:hidden'
                )}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
        
        {/* WebSocket Status */}
        <div className={clsx(
          'absolute bottom-4 p-3 rounded-lg bg-gomale-dark border border-gray-800',
          sidebarOpen ? 'block left-4 right-4' : 'hidden lg:hidden'
        )}>
          <div className="flex items-center gap-2">
            <div className={clsx(
              'w-2 h-2 rounded-full animate-pulse',
              wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
            )} />
            <span className="text-xs text-gray-400">
              {wsStatus === 'connected' ? 'Live Data' : 'Disconnected'}
            </span>
          </div>
        </div>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-gomale-navy/50 backdrop-blur border-b border-gray-800 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hidden lg:block"
            >
              <Menu className="w-5 h-5" />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 lg:hidden"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <span className="text-sm text-gray-400">TestNet</span>
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
          </div>
        </header>
        
        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
      
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
    </div>
  );
}
