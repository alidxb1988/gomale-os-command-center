import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, 
  X, 
  Mic, 
  Send,
  Sparkles,
  TrendingUp,
  Image as ImageIcon,
  Code,
  MessageSquare,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { useVoiceCommand } from '@/contexts/VoiceCommandContext';
import { useAIOrchestrator } from '@/hooks/useAIOrchestrator';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface FloatingAIAgentProps {
  className?: string;
}

const QUICK_ACTIONS = [
  { icon: TrendingUp, label: 'Trading', href: '/trading', color: 'text-green-400' },
  { icon: MessageSquare, label: 'AI Chat', href: '/ai-hub', color: 'text-blue-400' },
  { icon: ImageIcon, label: 'Create Image', action: 'generate_image', color: 'text-purple-400' },
  { icon: Code, label: 'Code Help', action: 'code_help', color: 'text-yellow-400' },
];

export default function FloatingAIAgent({ className = '' }: FloatingAIAgentProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{role: 'user' | 'agent', content: string}[]>([
    { role: 'agent', content: 'Hi! I\'m your AI assistant. I can help with trading, coding, analysis, and more. What would you like to do?' }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);

  const { isListening, transcript, startListening, stopListening, speak, supported: voiceSupported } = useVoiceCommand();
  const { orchestrate } = useAIOrchestrator();

  // Handle voice transcript
  useEffect(() => {
    if (transcript && isOpen) {
      setInput(transcript);
    }
  }, [transcript, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsProcessing(true);
    setShowQuickActions(false);

    try {
      // Orchestrate to find best model
      const result = orchestrate(userMessage);
      
      // Simulate AI response (would call actual API)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const response = `I'll help you with that using ${result.model.name}. This appears to be a ${result.taskType} task. Let me process your request...`;
      
      setMessages(prev => [...prev, { role: 'agent', content: response }]);
      
      // Speak response if voice is enabled
      if (voiceSupported) {
        speak(response);
      }
    } catch (error) {
      toast.error('Failed to process request');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (action: typeof QUICK_ACTIONS[0]) => {
    if (action.href) {
      window.location.href = action.href;
    } else if (action.action === 'generate_image') {
      setInput('Generate an image of ');
      setShowQuickActions(false);
    } else if (action.action === 'code_help') {
      setInput('Help me write code for ');
      setShowQuickActions(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 shadow-lg shadow-purple-500/30 flex items-center justify-center ${className}`}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <div className="relative">
            <Bot className="w-7 h-7 text-white" />
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full"
            />
          </div>
        )}
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] bg-[#1a1a2e] border border-gray-800 rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-gray-800 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center"
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">AI Assistant</h3>
                  <p className="text-xs text-gray-400">Powered by GOMALE OS</p>
                </div>
              </div>
              
              <Link 
                href="/ai-hub"
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Open Full Hub →
              </Link>
            </div>

            {/* Messages */}
            <div className="h-80 overflow-y-auto p-4 space-y-3">
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-200'
                    }`}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}
              
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-gray-800 rounded-2xl px-4 py-3 flex items-center gap-2"
                  >
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 0.5 }}
                      className="w-2 h-2 bg-blue-400 rounded-full"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 0.5, delay: 0.1 }}
                      className="w-2 h-2 bg-blue-400 rounded-full"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 0.5, delay: 0.2 }}
                      className="w-2 h-2 bg-blue-400 rounded-full"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            {showQuickActions && messages.length <= 2 && (
              <div className="px-4 pb-2"
              >
                <div className="grid grid-cols-2 gap-2"
                >
                  {QUICK_ACTIONS.map((action) => (
                    <button
                      key={action.label}
                      onClick={() => handleQuickAction(action)}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-800/50 hover:bg-gray-800 rounded-lg text-sm text-gray-300 transition-colors"
                    >
                      <action.icon className={`w-4 h-4 ${action.color}`} />
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="p-4 border-t border-gray-800"
            >
              <div className="flex items-center gap-2"
              >
                {voiceSupported && (
                  <button
                    onClick={isListening ? stopListening : startListening}
                    className={`p-2.5 rounded-xl transition-colors ${
                      isListening
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-gray-800 text-gray-400 hover:text-white'
                    }`}
                  >
                    {isListening ? (
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ repeat: Infinity, duration: 0.5 }}
                      >
                        <Mic className="w-5 h-5" />
                      </motion.div>
                    ) : (
                      <Mic className="w-5 h-5" />
                    )}
                  </button>
                )}
                
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask anything..."
                  className="flex-1 bg-gray-800 border-0 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isProcessing}
                  className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              
              {isListening && (
                <p className="text-xs text-red-400 mt-2 text-center"
                >
                  Listening: {transcript}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
