import ProfileSelector from '../profile/ProfileSelector';
import { useAppContext } from '../../context/AppContext';

interface HeaderProps {
  onCreateProfile: () => void;
}

export default function Header({ onCreateProfile }: HeaderProps) {
  const { isConnected } = useAppContext();

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-panel-border bg-panel">
      <h1 className="text-xl font-bold text-accent tracking-wide">DocsAI</h1>
      <div className="flex items-center gap-3">
        <ProfileSelector />
        <button
          onClick={onCreateProfile}
          title="Create new profile"
          className="w-7 h-7 flex items-center justify-center rounded-md border border-panel-border text-slate-400 hover:text-accent hover:border-accent transition-colors text-lg leading-none"
        >
          +
        </button>
        <div
          className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-red-400'}`}
          title={isConnected ? 'Backend connected' : 'Backend disconnected'}
        />
      </div>
    </header>
  );
}
