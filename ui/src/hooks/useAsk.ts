import { useState, useCallback } from 'react';
import type { PromptMode } from '../api/types';
import { askQuestion } from '../api/ask';

export interface ChatEntry {
  id: string;
  question: string;
  answer: string;
  citations: string[];
  mode: PromptMode | 'auto';
  timestamp: Date;
  loading: boolean;
  error?: string;
}

export function useAsk() {
  const [history, setHistory] = useState<ChatEntry[]>([]);

  const ask = useCallback(async (question: string, mode?: PromptMode) => {
    const entry: ChatEntry = {
      id: crypto.randomUUID(),
      question,
      answer: '',
      citations: [],
      mode: mode || 'auto',
      timestamp: new Date(),
      loading: true,
    };

    setHistory(prev => [...prev, entry]);

    try {
      const res = await askQuestion(question, mode);
      setHistory(prev =>
        prev.map(e =>
          e.id === entry.id
            ? { ...e, answer: res.answer, citations: res.citations, loading: false, error: res.error }
            : e
        )
      );
    } catch (err) {
      setHistory(prev =>
        prev.map(e =>
          e.id === entry.id
            ? { ...e, loading: false, error: err instanceof Error ? err.message : 'Request failed' }
            : e
        )
      );
    }
  }, []);

  const clearHistory = useCallback(() => setHistory([]), []);

  return { history, ask, clearHistory };
}
