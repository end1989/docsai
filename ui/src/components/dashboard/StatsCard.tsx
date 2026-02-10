interface StatsCardProps {
  label: string;
  value: string;
  sub?: string;
}

export default function StatsCard({ label, value, sub }: StatsCardProps) {
  return (
    <div className="bg-panel border border-panel-border rounded-lg p-4 text-center">
      <p className="text-2xl font-bold text-slate-100">{value}</p>
      <p className="text-xs text-slate-400 uppercase tracking-wider mt-1">{label}</p>
      {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}
