import type { IngestionStatus } from '../../api/types';
import Badge from '../common/Badge';
import { formatDuration } from '../../lib/format';

const STATUS_COLORS: Record<string, string> = {
  preparing: 'yellow',
  scanning: 'blue',
  processing: 'teal',
  indexing: 'teal',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
  idle: 'gray',
};

export default function IngestionProgress({ status }: { status: IngestionStatus }) {
  const pct = Math.round(status.progress * 100);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Badge color={STATUS_COLORS[status.status] || 'gray'}>{status.status}</Badge>
        {status.duration !== null && (
          <span className="text-xs text-slate-500">{formatDuration(status.duration)}</span>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-base rounded-full h-2">
        <div
          className="bg-accent h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>{pct}%</span>
        {status.status === 'scanning' ? (
          <span>Pages found: {status.processed_files}</span>
        ) : (
          <span>Files: {status.processed_files}/{status.total_files}</span>
        )}
        <span>Chunks: {status.indexed_chunks}</span>
      </div>

      {status.current_file && (
        <p className="text-xs text-slate-500 truncate">Current: {status.current_file}</p>
      )}

      {status.errors.length > 0 && (
        <div className="mt-2 text-xs text-red-400">
          <p className="font-semibold">{status.errors.length} error(s):</p>
          <ul className="list-disc list-inside mt-1">
            {status.errors.slice(0, 3).map((err, i) => (
              <li key={i}>{err}</li>
            ))}
            {status.errors.length > 3 && <li>...and {status.errors.length - 3} more</li>}
          </ul>
        </div>
      )}
    </div>
  );
}
