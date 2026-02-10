import { useIngestion } from '../../hooks/useIngestion';
import Card from '../common/Card';
import IngestionProgress from './IngestionProgress';

export default function IngestionControl({ profile }: { profile: string }) {
  const { status, isRunning, start, cancel, error } = useIngestion(profile);

  return (
    <Card>
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Ingestion</h3>

      {status && status.status !== 'idle' ? (
        <>
          <IngestionProgress status={status} />
          {isRunning && (
            <button
              onClick={cancel}
              className="mt-3 px-4 py-1.5 text-sm rounded-md border border-red-700 text-red-400 hover:bg-red-900/30 transition-colors"
            >
              Cancel
            </button>
          )}
          {status.status === 'completed' && (
            <p className="mt-3 text-sm text-emerald-400">Ingestion complete.</p>
          )}
          {status.status === 'failed' && (
            <button
              onClick={start}
              className="mt-3 px-4 py-1.5 text-sm rounded-md bg-accent text-slate-900 font-semibold hover:brightness-110 transition-all"
            >
              Retry
            </button>
          )}
        </>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-slate-400">Crawl, chunk, and index this profile's sources.</p>
          <button
            onClick={start}
            className="px-5 py-2 text-sm rounded-md bg-accent text-slate-900 font-semibold hover:brightness-110 transition-all"
          >
            Start Ingestion
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </Card>
  );
}
