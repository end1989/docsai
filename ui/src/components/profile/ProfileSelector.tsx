import { useProfiles } from '../../hooks/useProfiles';

export default function ProfileSelector() {
  const { profiles, activeProfile, setActiveProfile } = useProfiles();

  if (profiles.length === 0) {
    return <span className="text-sm text-slate-500">No profiles</span>;
  }

  return (
    <select
      value={activeProfile}
      onChange={e => setActiveProfile(e.target.value)}
      className="bg-panel border border-panel-border rounded-md px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-accent cursor-pointer"
    >
      {profiles.map(p => (
        <option key={p.name} value={p.name}>{p.name}</option>
      ))}
    </select>
  );
}
