import type { PromptMode } from '../../api/types';

interface ModeSelectorProps {
  value: PromptMode | undefined;
  onChange: (mode: PromptMode | undefined) => void;
}

const MODES: { value: PromptMode | undefined; label: string }[] = [
  { value: undefined, label: 'Auto' },
  { value: 'comprehensive', label: 'Comprehensive' },
  { value: 'integration', label: 'Integration' },
  { value: 'debugging', label: 'Debugging' },
  { value: 'learning', label: 'Learning' },
];

export default function ModeSelector({ value, onChange }: ModeSelectorProps) {
  return (
    <select
      value={value || ''}
      onChange={e => onChange((e.target.value || undefined) as PromptMode | undefined)}
      className="bg-base border border-panel-border rounded px-2 py-1 text-xs text-slate-400 focus:outline-none focus:border-accent"
    >
      {MODES.map(m => (
        <option key={m.label} value={m.value || ''}>{m.label}</option>
      ))}
    </select>
  );
}
