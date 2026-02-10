export default function Spinner({ size = 'md' }: { size?: 'sm' | 'md' }) {
  const cls = size === 'sm' ? 'w-4 h-4 border-2' : 'w-6 h-6 border-2';
  return (
    <div className={`${cls} border-panel-border border-t-accent rounded-full animate-spin`} />
  );
}
