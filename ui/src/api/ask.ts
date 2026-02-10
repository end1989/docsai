import { api } from './client';
import type { AskResponse, PromptMode } from './types';

export const askQuestion = (q: string, mode?: PromptMode) => {
  const params = new URLSearchParams({ q });
  if (mode) params.set('mode', mode);
  return api.get<AskResponse>(`/ask?${params}`);
};
