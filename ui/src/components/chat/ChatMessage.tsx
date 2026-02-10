import type { ChatEntry } from '../../hooks/useAsk';
import AnswerDisplay from './AnswerDisplay';
import CitationList from './CitationList';
import Spinner from '../common/Spinner';

export default function ChatMessage({ entry }: { entry: ChatEntry }) {
  return (
    <div className="bg-panel border border-panel-border rounded-lg p-5 space-y-3">
      {/* Question */}
      <div className="flex items-start gap-3">
        <span className="text-accent font-bold text-sm mt-0.5">Q</span>
        <p className="text-slate-100 font-medium">{entry.question}</p>
      </div>

      {/* Divider */}
      <div className="border-t border-panel-border" />

      {/* Answer */}
      {entry.loading ? (
        <div className="flex items-center gap-3 py-4">
          <Spinner size="sm" />
          <span className="text-sm text-slate-400">Searching and generating answer...</span>
        </div>
      ) : entry.error ? (
        <div className="text-red-400 text-sm py-2">{entry.error}</div>
      ) : (
        <>
          <AnswerDisplay answer={entry.answer} citations={entry.citations} />
          <CitationList citations={entry.citations} />
        </>
      )}
    </div>
  );
}
