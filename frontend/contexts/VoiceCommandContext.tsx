import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';

interface VoiceCommandContextType {
  isListening: boolean;
  isSpeaking: boolean;
  transcript: string;
  lastCommand: string;
  confidence: number;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string) => Promise<void>;
  supported: boolean;
  error: string | null;
}

const VoiceCommandContext = createContext<VoiceCommandContextType | undefined>(undefined);

// Voice commands mapping
const VOICE_COMMANDS = {
  navigation: {
    'go to trading': '/trading',
    'open trading': '/trading',
    'trading deck': '/trading',
    'go to dashboard': '/',
    'open dashboard': '/',
    'go to chat': '/ai-chat',
    'open chat': '/ai-chat',
    'ai chat': '/ai-chat',
    'go to settings': '/settings',
    'open settings': '/settings',
    'go to analytics': '/analytics',
    'open analytics': '/analytics',
    'go to ai hub': '/ai-hub',
    'open ai hub': '/ai-hub',
    'ai hub': '/ai-hub',
  },
  actions: {
    'show balance': 'SHOW_BALANCE',
    'check balance': 'SHOW_BALANCE',
    'my balance': 'SHOW_BALANCE',
    'buy bitcoin': 'BUY_BITCOIN',
    'sell bitcoin': 'SELL_BITCOIN',
    'show chart': 'SHOW_CHART',
    'open chart': 'SHOW_CHART',
    'close position': 'CLOSE_POSITION',
    'cancel order': 'CANCEL_ORDER',
    'refresh data': 'REFRESH_DATA',
    'clear chat': 'CLEAR_CHAT',
    'new chat': 'NEW_CHAT',
    'help': 'SHOW_HELP',
    'what can you do': 'SHOW_HELP',
  },
  voiceControl: {
    'stop listening': 'STOP_LISTENING',
    'start listening': 'START_LISTENING',
    'mute': 'MUTE',
    'unmute': 'UNMUTE',
  }
};

export function VoiceCommandProvider({ children }: { children: React.ReactNode }) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [lastCommand, setLastCommand] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [supported, setSupported] = useState(true);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    // Check for Web Speech API support
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        setSupported(false);
        setError('Speech recognition not supported in this browser');
        return;
      }

      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setError(null);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            setConfidence(event.results[i][0].confidence);
          } else {
            interimTranscript += transcript;
          }
        }

        const fullTranscript = finalTranscript || interimTranscript;
        setTranscript(fullTranscript);

        if (finalTranscript) {
          processCommand(finalTranscript.toLowerCase().trim());
        }
      };

      recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        setError(event.error);
        setIsListening(false);
      };

      // Initialize speech synthesis
      synthesisRef.current = window.speechSynthesis;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  const processCommand = useCallback((command: string) => {
    setLastCommand(command);

    // Check navigation commands
    for (const [phrase, route] of Object.entries(VOICE_COMMANDS.navigation)) {
      if (command.includes(phrase)) {
        window.location.href = route;
        return;
      }
    }

    // Check action commands
    for (const [phrase, action] of Object.entries(VOICE_COMMANDS.actions)) {
      if (command.includes(phrase)) {
        // Dispatch custom event for components to handle
        window.dispatchEvent(new CustomEvent('voice-action', { detail: action }));
        return;
      }
    }

    // Check voice control commands
    for (const [phrase, action] of Object.entries(VOICE_COMMANDS.voiceControl)) {
      if (command.includes(phrase)) {
        if (action === 'STOP_LISTENING') {
          stopListening();
        } else if (action === 'START_LISTENING') {
          startListening();
        }
        return;
      }
    }

    // If no specific command matched, treat as chat input
    window.dispatchEvent(new CustomEvent('voice-chat', { detail: command }));
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
      } catch (err) {
        setError('Failed to start listening');
      }
    }
  }, [isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  }, [isListening]);

  const speak = useCallback(async (text: string): Promise<void> => {
    if (!synthesisRef.current) return;

    return new Promise((resolve) => {
      setIsSpeaking(true);
      
      // Cancel any ongoing speech
      synthesisRef.current!.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;

      // Try to use a good English voice
      const voices = synthesisRef.current!.getVoices();
      const preferredVoice = voices.find(v => v.name.includes('Google US English')) ||
                            voices.find(v => v.name.includes('Samantha')) ||
                            voices.find(v => v.lang === 'en-US');
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onend = () => {
        setIsSpeaking(false);
        resolve();
      };

      utterance.onerror = () => {
        setIsSpeaking(false);
        resolve();
      };

      synthesisRef.current!.speak(utterance);
    });
  }, []);

  return (
    <VoiceCommandContext.Provider
      value={{
        isListening,
        isSpeaking,
        transcript,
        lastCommand,
        confidence,
        startListening,
        stopListening,
        speak,
        supported,
        error,
      }}
    >
      {children}
    </VoiceCommandContext.Provider>
  );
}

export function useVoiceCommand() {
  const context = useContext(VoiceCommandContext);
  if (context === undefined) {
    throw new Error('useVoiceCommand must be used within a VoiceCommandProvider');
  }
  return context;
}

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
