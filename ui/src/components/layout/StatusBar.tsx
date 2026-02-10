import { useAppContext } from '../../context/AppContext';

export default function StatusBar() {
  const { activeProfile, isConnected } = useAppContext();

  return (
    <footer className="px-6 py-1.5 border-t border-panel-border bg-panel text-xs text-slate-500 flex items-center gap-4">
      <span>Profile: <span className="text-slate-300">{activeProfile || 'none'}</span></span>
      <span className="text-panel-border">|</span>
      <span>Backend: <span className={isConnected ? 'text-emerald-400' : 'text-red-400'}>{isConnected ? 'connected' : 'disconnected'}</span></span>
      <span className="text-panel-border">|</span>
      <span>Port: 8080</span>
    </footer>
  );
}
