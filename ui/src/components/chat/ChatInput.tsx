import { useState, useRef, useCallback } from 'react';
import type { PromptMode } from '../../api/types';
import ModeSelector from './ModeSelector';

interface ChatInputProps {
  onSubmit: (question: string, mode?: PromptMode) => void;
  disabled: boolean;
  profileName: string;
}

export default function ChatInput({ onSubmit, disabled, profileName }: ChatInputProps) {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState<PromptMode | undefined>(undefined);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const q = question.trim();
    if (!q || disabled) return;
    onSubmit(q, mode);
    setQuestion('');
    textareaRef.current?.focus();
  }, [question, mode, disabled, onSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Ask the ${profileName} docs...`}
          rows={3}
          className="w-full p-3 pr-24 bg-panel border border-panel-border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent resize-none"
        />
        <div className="absolute right-3 top-3">
          <ModeSelector value={mode} onChange={setMode} />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">Enter to send, Shift+Enter for newline</span>
        <button
          onClick={handleSubmit}
          disabled={disabled || !question.trim()}
          className="bg-accent text-slate-900 font-semibold px-5 py-1.5 rounded-md text-sm hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {disabled ? 'Searching...' : 'Ask'}
        </button>
      </div>
    </div>
  );
}
