const COLORS: Record<string, string> = {
  green: 'bg-emerald-900/50 text-emerald-400 border-emerald-700',
  yellow: 'bg-amber-900/50 text-amber-400 border-amber-700',
  red: 'bg-red-900/50 text-red-400 border-red-700',
  blue: 'bg-blue-900/50 text-blue-400 border-blue-700',
  gray: 'bg-slate-700/50 text-slate-400 border-slate-600',
  teal: 'bg-teal-900/50 text-teal-400 border-teal-700',
};

export default function Badge({ children, color = 'gray' }: { children: React.ReactNode; color?: string }) {
  return (
    <span className={`inline-block text-xs px-2 py-0.5 rounded border ${COLORS[color] || COLORS.gray}`}>
      {children}
    </span>
  );
}
