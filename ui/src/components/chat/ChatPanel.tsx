import { useRef, useEffect } from 'react';
import { useAsk } from '../../hooks/useAsk';
import { useAppContext } from '../../context/AppContext';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

export default function ChatPanel() {
  const { activeProfile } = useAppContext();
  const { history, ask } = useAsk();
  const scrollRef = useRef<HTMLDivElement>(null);

  const isLoading = history.some(e => e.loading);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-auto space-y-4 pb-4">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <p className="text-lg font-medium mb-2">Ask anything about {activeProfile}</p>
            <p className="text-sm">Your answers will appear here with citations from the docs.</p>
          </div>
        ) : (
          history.map(entry => <ChatMessage key={entry.id} entry={entry} />)
        )}
      </div>

      {/* Input */}
      <div className="pt-2 border-t border-panel-border">
        <ChatInput
          onSubmit={ask}
          disabled={isLoading}
          profileName={activeProfile}
        />
      </div>
    </div>
  );
}
