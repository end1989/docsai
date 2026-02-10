export type Tab = 'chat' | 'dashboard';

interface TabNavProps {
  active: Tab;
  onChange: (tab: Tab) => void;
}

export default function TabNav({ active, onChange }: TabNavProps) {
  const tabs: { id: Tab; label: string }[] = [
    { id: 'chat', label: 'Chat' },
    { id: 'dashboard', label: 'Dashboard' },
  ];

  return (
    <nav className="flex gap-6 px-6 pt-3 text-sm">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`pb-2 border-b-2 transition-colors ${
            active === t.id
              ? 'text-accent border-accent'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}
