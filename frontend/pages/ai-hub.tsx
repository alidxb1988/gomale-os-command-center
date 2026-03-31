import React, { useState, useRef, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Copy,
  Volume2,
  RefreshCw,
  Image as ImageIcon,
  Code,
  Search,
  Globe,
  FileText,
  TrendingUp,
  Mic,
  MicOff,
  X,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  Check,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAIOrchestrator, AI_MODELS, AIModel } from '@/hooks/useAIOrchestrator';
import { useVoiceCommand } from '@/contexts/VoiceCommandContext';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model?: AIModel;
  taskType?: string;
  timestamp: Date;
  sources?: { title: string; url: string }[];
  images?: string[];
  isGenerating?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

const TASK_ICONS: Record<string, React.ElementType> = {
  code: Code,
  search: Search,
  image: ImageIcon,
  analysis: TrendingUp,
  translation: Globe,
  documents: FileText,
  trading: TrendingUp,
  general: Sparkles,
};

export default function AIHubPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedModel, setSelectedModel] = useState<AIModel | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const { orchestrate, isAnalyzing } = useAIOrchestrator();
  const { isListening, transcript, startListening, stopListening, speak, supported: voiceSupported } = useVoiceCommand();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle voice transcript
  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  // Voice action listener
  useEffect(() => {
    const handleVoiceAction = (e: CustomEvent) => {
      const action = e.detail;
      switch (action) {
        case 'CLEAR_CHAT':
          clearChat();
          break;
        case 'NEW_CHAT':
          startNewChat();
          break;
      }
    };

    window.addEventListener('voice-action', handleVoiceAction as EventListener);
    return () => window.removeEventListener('voice-action', handleVoiceAction as EventListener);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Use orchestrator to select best model
      const orchestration = orchestrate(userMessage.content);
      const modelToUse = selectedModel || orchestration.model;

      // Create assistant message placeholder
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        model: modelToUse,
        taskType: orchestration.taskType,
        timestamp: new Date(),
        isGenerating: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Call API based on model type
      let response;
      if (modelToUse.id === 'dall-e-3') {
        response = await generateImage(userMessage.content);
      } else {
        response = await callAIAPI(userMessage.content, modelToUse.id);
      }

      // Update assistant message with response
      setMessages((prev) =>
        prev.map((msg) =
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content: response.content,
                sources: response.sources,
                images: response.images,
                isGenerating: false,
              }
            : msg
        )
      );

      // Auto-speak if voice is enabled
      if (voiceSupported && !isListening) {
        speak(response.content.substring(0, 200));
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to get response');
      setMessages((prev) => prev.filter((msg) => msg.role !== 'assistant' || !msg.isGenerating)
      );
    } finally {
      setLoading(false);
    }
  };

  const callAIAPI = async (message: string, modelId: string) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Map model IDs to API endpoints
    const modelMapping: Record<string, string> = {
      'claude-3-5-sonnet': 'claude',
      'claude-3-opus': 'claude',
      'gemini-pro': 'gemini',
      'perplexity': 'perplexity',
      'kimi': 'kimi',
    };

    const apiModel = modelMapping[modelId] || 'claude';

    const response = await fetch(`${API_URL}/api/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        model: apiModel,
        stream: false,
      }),
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const data = await response.json();
    
    return {
      content: data.content,
      sources: data.sources || [],
      images: [],
    };
  };

  const generateImage = async (prompt: string) => {
    // This would call DALL-E API
    // For now, return placeholder
    return {
      content: `Generated image for: "${prompt}"`,
      sources: [],
      images: ['/api/placeholder/512/512'],
    };
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    toast.success('Chat cleared');
  };

  const startNewChat = () => {
    if (messages.length > 0) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: messages[0]?.content.slice(0, 50) + '...' || 'New Chat',
        messages: [...messages],
        createdAt: new Date(),
      };
      setConversations((prev) => [newConversation, ...prev]);
    }
    setMessages([]);
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success('Copied to clipboard');
  };

  return (
    <>
      <Head>
        <title>AI Hub | GOMALE OS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className={`min-h-screen bg-[#0a0a0a] flex ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
        {/* Sidebar */}
        <AnimatePresence>
          {showSidebar && (
            <motion.aside
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              className="w-80 bg-[#111111] border-r border-gray-800 flex flex-col"
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-800">
                <Link href="/" className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-gomale-gold to-yellow-600 rounded-lg flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-black" />
                  </div>
                  <div>
                    <h1 className="font-bold text-white">AI Hub</h1>
                    <p className="text-xs text-gray-500">Powered by GOMALE OS</p>
                  </div>
                </Link>
              </div>

              {/* New Chat Button */}
              <div className="p-4">
                <button
                  onClick={startNewChat}
                  className="w-full flex items-center gap-2 px-4 py-3 bg-gomale-gold/10 hover:bg-gomale-gold/20 text-gomale-gold rounded-lg border border-gomale-gold/30 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  New Chat
                </button>
              </div>

              {/* Model Selector */}
              <div className="px-4 pb-4">
                <button
                  onClick={() => setShowModelSelector(!showModelSelector)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/50 hover:bg-gray-800 text-white rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-gomale-gold" />
                    <span>{selectedModel?.name || 'Auto-Select'}</span>
                  </div>
                  {showModelSelector ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>

                <AnimatePresence>
                  {showModelSelector && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-2 space-y-1 overflow-hidden"
                    >
                      <button
                        onClick={() => {
                          setSelectedModel(null);
                          setShowModelSelector(false);
                        }}
                        className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                          !selectedModel ? 'bg-gomale-gold/20 text-gomale-gold' : 'text-gray-400 hover:bg-gray-800'
                        }`}
                      >
                        <Sparkles className="w-4 h-4" />
                        Auto-Select (Recommended)
                        {!selectedModel && <Check className="w-4 h-4 ml-auto" />}
                      </button>
                      {AI_MODELS.filter(m => m.enabled).map((model) => (
                        <button
                          key={model.id}
                          onClick={() => {
                            setSelectedModel(model);
                            setShowModelSelector(false);
                          }}
                          className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                            selectedModel?.id === model.id
                              ? 'bg-gomale-gold/20 text-gomale-gold'
                              : 'text-gray-400 hover:bg-gray-800'
                          }`}
                        >
                          <div
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: model.color }}
                          />
                          {model.name}
                          {selectedModel?.id === model.id && <Check className="w-4 h-4 ml-auto" />}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Conversation History */}
              <div className="flex-1 overflow-y-auto px-4">
                <p className="text-xs text-gray-500 mb-2">Recent Conversations</p>
                <div className="space-y-1">
                  {conversations.map((conv) => (
                    <button
                      key={conv.id}
                      className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 transition-colors truncate"
                    >
                      {conv.title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-gray-800">
                <Link
                  href="/"
                  className="flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  Back to Dashboard
                </Link>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Top Bar */}
          <header className="h-14 border-b border-gray-800 flex items-center justify-between px-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 text-gray-400 hover:text-white"
              >
                {showSidebar ? <X className="w-5 h-5" /> : <RefreshCw className="w-5 h-5" />}
              </button>
              <span className="text-sm text-gray-400">
                {isAnalyzing ? 'Analyzing task...' : selectedModel?.name || 'Auto-Select Mode'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 text-gray-400 hover:text-white"
              >
                <ExternalLink className="w-5 h-5" />
              </button>
              <button
                onClick={clearChat}
                className="p-2 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center px-4">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center"
                >
                  <div className="w-16 h-16 bg-gradient-to-br from-gomale-gold to-yellow-600 rounded-2xl flex items-center justify-center mx-auto mb-6"
                  >
                    <Sparkles className="w-8 h-8 text-black" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">GOMALE AI Hub</h2>
                  <p className="text-gray-400 max-w-md mb-8">
                    Your intelligent assistant with 10+ AI models. Ask anything about trading, 
                    coding, analysis, or get creative with images and content.
                  </p>

                  {/* Quick Suggestions */}
                  <div className="grid grid-cols-2 gap-3 max-w-lg">
                    {[
                      'Analyze BTC technicals',
                      'Generate trading strategy',
                      'Explain DeFi protocols',
                      'Create Python script',
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => {
                          setInput(suggestion);
                          inputRef.current?.focus();
                        }}
                        className="px-4 py-3 bg-gray-800/50 hover:bg-gray-800 rounded-lg text-sm text-gray-300 transition-colors text-left"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </motion.div>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto py-6 space-y-6">
                {messages.map((message) => {
                  const TaskIcon = message.taskType ? TASK_ICONS[message.taskType] || Sparkles : Sparkles;
                  
                  return (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-4 px-4 ${
                        message.role === 'user' ? 'flex-row-reverse' : ''
                      }`}
                    >
                      {/* Avatar */}
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.role === 'user'
                            ? 'bg-gomale-gold text-black'
                            : 'bg-gray-800'
                        }`}
                      >
                        {message.role === 'user' ? (
                          <User className="w-4 h-4" />
                        ) : (
                          <TaskIcon className="w-4 h-4 text-gomale-gold" />
                        )}
                      </div>

                      {/* Content */}
                      <div className={`flex-1 ${message.role === 'user' ? 'text-right' : ''}`}>
                        {message.role === 'assistant' && message.model && (
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className="text-xs px-2 py-1 rounded-full"
                              style={{
                                backgroundColor: `${message.model.color}20`,
                                color: message.model.color,
                              }}
                            >
                              {message.model.name}
                            </span>
                            {message.taskType && (
                              <span className="text-xs text-gray-500 capitalize">
                                {message.taskType}
                              </span>
                            )}
                          </div>
                        )}

                        <div
                          className={`inline-block max-w-full rounded-2xl px-4 py-3 text-left ${
                            message.role === 'user'
                              ? 'bg-gomale-gold text-black'
                              : 'bg-gray-800 text-gray-200'
                          }`}
                        >
                          {message.isGenerating ? (
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin text-gomale-gold" />
                              <span className="text-gray-400">Generating...</span>
                            </div>
                          ) : (
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          )}
                        </div>

                        {/* Actions */}
                        {message.role === 'assistant' && !message.isGenerating && (
                          <div className="flex items-center gap-2 mt-2">
                            <button
                              onClick={() => copyToClipboard(message.content)}
                              className="p-1.5 text-gray-500 hover:text-white rounded"
                              title="Copy"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => speak(message.content.substring(0, 500))}
                              className="p-1.5 text-gray-500 hover:text-white rounded"
                              title="Speak"
                            >
                              <Volume2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}

                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-3 space-y-1">
                            <p className="text-xs text-gray-500">Sources:</p>
                            {message.sources.map((source, idx) => (
                              <a
                                key={idx}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block text-xs text-blue-400 hover:underline"
                              >
                                {source.title}
                              </a>
                            ))}
                          </div>
                        )}

                        {/* Images */}
                        {message.images && message.images.length > 0 && (
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            {message.images.map((img, idx) => (
                              <img
                                key={idx}
                                src={img}
                                alt="Generated"
                                className="rounded-lg"
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-800 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask anything... (AI will auto-select the best model)"
                  rows={1}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-4 pr-24 text-white placeholder-gray-500 focus:border-gomale-gold focus:outline-none resize-none"
                  style={{ minHeight: '56px', maxHeight: '200px' }}
                />

                {/* Input Actions */}
                <div className="absolute right-2 bottom-2 flex items-center gap-1">
                  {voiceSupported && (
                    <button
                      onClick={isListening ? stopListening : startListening}
                      className={`p-2 rounded-lg transition-colors ${
                        isListening
                          ? 'bg-red-500/20 text-red-500'
                          : 'text-gray-400 hover:text-white'
                      }`}
                      title={isListening ? 'Stop listening' : 'Start listening'}
                    >
                      {isListening ? (
                        <MicOff className="w-5 h-5" />
                      ) : (
                        <Mic className="w-5 h-5" />
                      )}
                    </button>
                  )}
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    className="p-2 bg-gomale-gold text-black rounded-lg hover:bg-gomale-gold/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                㳍iv>
              </div>

              <p className="text-xs text-gray-500 mt-2 text-center">
                Press Enter to send, Shift+Enter for new line
                {isListening && <span className="text-red-400 ml-2">Listening...{transcript}</span>}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
