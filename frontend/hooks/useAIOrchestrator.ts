import { useState, useCallback } from 'react';

// AI Model Configuration
export interface AIModel {
  id: string;
  name: string;
  provider: string;
  color: string;
  icon: string;
  capabilities: string[];
  priority: number;
  enabled: boolean;
}

export const AI_MODELS: AIModel[] = [
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    color: '#F97316',
    icon: 'Brain',
    capabilities: ['code', 'analysis', 'writing', 'math', 'reasoning', 'documents'],
    priority: 1,
    enabled: true,
  },
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    provider: 'Anthropic',
    color: '#F97316',
    icon: 'Brain',
    capabilities: ['code', 'analysis', 'writing', 'math', 'reasoning', 'complex-tasks'],
    priority: 2,
    enabled: true,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    provider: 'Google',
    color: '#3B82F6',
    icon: 'Sparkles',
    capabilities: ['code', 'analysis', 'multimodal', 'documents'],
    priority: 3,
    enabled: true,
  },
  {
    id: 'perplexity',
    name: 'Perplexity',
    provider: 'Perplexity',
    color: '#14B8A6',
    icon: 'Search',
    capabilities: ['search', 'research', 'facts', 'news'],
    priority: 1,
    enabled: true,
  },
  {
    id: 'kimi',
    name: 'Kimi',
    provider: 'Moonshot',
    color: '#A855F7',
    icon: 'MessageCircle',
    capabilities: ['code', 'translation', 'long-context', 'chinese'],
    priority: 4,
    enabled: true,
  },
  {
    id: 'dall-e-3',
    name: 'DALL-E 3',
    provider: 'OpenAI',
    color: '#10B981',
    icon: 'Image',
    capabilities: ['image-generation'],
    priority: 1,
    enabled: true,
  },
  {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    provider: 'ElevenLabs',
    color: '#EC4899',
    icon: 'Volume2',
    capabilities: ['text-to-speech', 'voice-cloning'],
    priority: 1,
    enabled: true,
  },
];

// Task Types and their optimal models
const TASK_MODEL_MAPPING: Record<string, { primary: string[]; backup: string[] }> = {
  code: {
    primary: ['claude-3-5-sonnet', 'claude-3-opus'],
    backup: ['kimi', 'gemini-pro'],
  },
  search: {
    primary: ['perplexity'],
    backup: ['claude-3-5-sonnet'],
  },
  image: {
    primary: ['dall-e-3'],
    backup: [],
  },
  voice: {
    primary: ['elevenlabs'],
    backup: [],
  },
  analysis: {
    primary: ['claude-3-opus', 'claude-3-5-sonnet'],
    backup: ['gemini-pro', 'kimi'],
  },
  translation: {
    primary: ['kimi', 'claude-3-5-sonnet'],
    backup: ['gemini-pro'],
  },
  documents: {
    primary: ['claude-3-5-sonnet', 'gemini-pro'],
    backup: ['claude-3-opus'],
  },
  trading: {
    primary: ['claude-3-opus'],
    backup: ['perplexity', 'claude-3-5-sonnet'],
  },
  general: {
    primary: ['claude-3-5-sonnet'],
    backup: ['gemini-pro', 'kimi'],
  },
};

// Task detection keywords
const TASK_KEYWORDS: Record<string, string[]> = {
  code: ['code', 'program', 'function', 'api', 'bug', 'error', 'debug', 'python', 'javascript', 'typescript', 'react', 'nextjs', 'css', 'html', 'sql', 'database'],
  search: ['search', 'find', 'lookup', 'what is', 'who is', 'where', 'when', 'latest', 'news', 'current', 'today'],
  image: ['image', 'picture', 'photo', 'generate image', 'create image', 'draw', 'illustration', 'art'],
  voice: ['voice', 'speak', 'audio', 'sound', 'read aloud', 'narrate'],
  analysis: ['analyze', 'analysis', 'compare', 'evaluate', 'assessment', 'review', 'study'],
  translation: ['translate', 'translation', 'in french', 'in spanish', 'in chinese', 'in arabic', 'in japanese', 'en français', 'en español'],
  documents: ['document', 'pdf', 'summary', 'summarize', 'extract', 'report', 'paper'],
  trading: ['trading', 'crypto', 'bitcoin', 'btc', 'eth', 'sol', 'price', 'chart', 'technical analysis', 'signal', 'buy', 'sell', 'position'],
};

export interface OrchestratorResult {
  model: AIModel;
  taskType: string;
  confidence: number;
  reason: string;
}

export function useAIOrchestrator() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const detectTaskType = useCallback((input: string): { taskType: string; confidence: number } => {
    const lowerInput = input.toLowerCase();
    const scores: Record<string, number> = {};

    for (const [task, keywords] of Object.entries(TASK_KEYWORDS)) {
      scores[task] = 0;
      for (const keyword of keywords) {
        if (lowerInput.includes(keyword.toLowerCase())) {
          scores[task] += 1;
        }
      }
    }

    // Find the task with highest score
    let bestTask = 'general';
    let bestScore = 0;

    for (const [task, score] of Object.entries(scores)) {
      if (score > bestScore) {
        bestScore = score;
        bestTask = task;
      }
    }

    // Calculate confidence (0-1)
    const confidence = Math.min(bestScore / 3, 1);

    return { taskType: bestTask, confidence };
  }, []);

  const selectModel = useCallback((taskType: string): OrchestratorResult => {
    const mapping = TASK_MODEL_MAPPING[taskType] || TASK_MODEL_MAPPING.general;
    
    // Try primary models first
    for (const modelId of mapping.primary) {
      const model = AI_MODELS.find(m => m.id === modelId && m.enabled);
      if (model) {
        return {
          model,
          taskType,
          confidence: 0.9,
          reason: `Selected ${model.name} for ${taskType} task based on optimal capability match`,
        };
      }
    }

    // Fall back to backup models
    for (const modelId of mapping.backup) {
      const model = AI_MODELS.find(m => m.id === modelId && m.enabled);
      if (model) {
        return {
          model,
          taskType,
          confidence: 0.7,
          reason: `Using backup model ${model.name} for ${taskType} task`,
        };
      }
    }

    // Ultimate fallback to general model
    const fallback = AI_MODELS.find(m => m.id === 'claude-3-5-sonnet');
    return {
      model: fallback!,
      taskType,
      confidence: 0.5,
      reason: 'Using default model as no specific model matched',
    };
  }, []);

  const orchestrate = useCallback((input: string): OrchestratorResult => {
    setIsAnalyzing(true);
    
    try {
      const { taskType, confidence } = detectTaskType(input);
      const result = selectModel(taskType);
      
      return {
        ...result,
        confidence: Math.round((result.confidence + confidence) / 2 * 100) / 100,
      };
    } finally {
      setIsAnalyzing(false);
    }
  }, [detectTaskType, selectModel]);

  const getAllModelsForTask = useCallback((taskType: string): AIModel[] => {
    const mapping = TASK_MODEL_MAPPING[taskType] || TASK_MODEL_MAPPING.general;
    const allModelIds = [...mapping.primary, ...mapping.backup];
    return AI_MODELS.filter(m => allModelIds.includes(m.id) && m.enabled);
  }, []);

  return {
    orchestrate,
    detectTaskType,
    getAllModelsForTask,
    isAnalyzing,
    models: AI_MODELS,
  };
}

export type { AIModel };
