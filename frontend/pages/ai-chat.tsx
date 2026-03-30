'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Copy,
  Volume2,
  RefreshCw,
  MessageSquare
} from 'lucide-react';
import { aiApi, ttsApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  timestamp: Date;
}

const models = [
  { id: 'claude', name: 'Claude 3', color: 'bg-orange-500', desc: 'Anthropic' },
  { id: 'gemini', name: 'Gemini', color: 'bg-blue-500', desc: 'Google' },
  { id: 'perplexity', name: 'Perplexity', color: 'bg-teal-500', desc: 'Sonar' },
  { id: 'kimi', name: 'Kimi', color: 'bg-purple-500', desc: 'Moonshot' },
  { id: 'compare', name: 'Compare All', color: 'bg-gomale-gold', desc: 'All Models' },
];

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome to GOMALE OS AI Command Center. I can help you with:\n\n• Market analysis and trading insights\n• Technical analysis of crypto pairs\n• Business strategy and planning\n• Multi-language translation\n• General questions\n\nSelect an AI model below and start chatting!',
      model: 'system',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('claude');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      if (selectedModel === 'compare') {
        // Compare all models
        const response = await aiApi.compare(userMessage.content);
        
        const compareContent = Object.entries(response.responses)
          .map(([model, data]: [string, any]) => {
            if (data.error) return `**${model}**: Error - ${data.error}`;
            return `**${model}**:\n${data.content?.substring(0, 300)}...`;
          })
          .join('\n\n---\n\n');

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: compareContent,
          model: 'compare',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // Single model
        const response = await aiApi.chat(userMessage.content, selectedModel);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.content,
          model: selectedModel,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to get response');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success('Copied to clipboard');
  };

  const speakText = async (text: string) => {
    try {
      const cleanText = text.replace(/\*\*/g, '').substring(0, 500);
      const response = await fetch('http://localhost:8000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: cleanText }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.audio_base64) {
          const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
          audio.play();
        }
      }
    } catch (error) {
      toast.error('TTS failed');
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Chat cleared. How can I help you today?',
        model: 'system',
        timestamp: new Date(),
      },
    ]);
  };

  const getModelInfo = (modelId: string) => {
    return models.find(m => m.id === modelId) || models[0];
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Chat</h1>
          <p className="text-gray-400 mt-1">Multi-model AI intelligence center</p>
        </div>
        
        <button
          onClick={clearChat}
          className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Clear Chat
        </button>
      </div>

      {/* Model Selector */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        {models.map((model) => (
          <button
            key={model.id}
            onClick={() => setSelectedModel(model.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
              selectedModel === model.id
                ? 'bg-gomale-gold text-gomale-navy font-medium'
                : 'bg-gomale-dark text-gray-400 hover:bg-gray-800'
            }`}
          >
            <div className={`w-2 h-2 rounded-full ${model.color}`} />
            <span>{model.name}</span>
            <span className="text-xs opacity-70">{model.desc}</span>
          </button>
        ))}
      </div>

      {/* Chat Area */}
      <div className="flex-1 card-glass flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user'
                    ? 'bg-gomale-gold text-gomale-navy'
                    : 'bg-gray-700 text-white'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>

              {/* Content */}
              <div
                className={`max-w-[80%] ${
                  message.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-gomale-gold text-gomale-navy'
                      : 'bg-gomale-dark text-gray-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>

                {/* Actions */}
                {message.role === 'assistant' && message.model !== 'system' && (
                  <div className="flex items-center gap-2 mt-1">
                    <button
                      onClick={() => copyToClipboard(message.content)}
                      className="text-gray-500 hover:text-gray-300"
                      title="Copy"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => speakText(message.content)}
                      className="text-gray-500 hover:text-gray-300"
                      title="Speak"
                    >
                      <Volume2 className="w-3 h-3" />
                    </button>
                    <span className="text-xs text-gray-500">
                      {getModelInfo(message.model || '').name}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-gomale-dark rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-gomale-gold" />
                  <span className="text-gray-400">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask ${getModelInfo(selectedModel).name} something...`}
              className="flex-1 bg-gomale-dark border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-gomale-gold focus:outline-none resize-none"
              rows={2}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-gomale-gold text-gomale-navy rounded-lg font-semibold hover:bg-gomale-gold/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
