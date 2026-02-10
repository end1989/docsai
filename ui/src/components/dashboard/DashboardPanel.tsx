import { useAppContext } from '../../context/AppContext';
import { useProfileStats } from '../../hooks/useProfileStats';
import ProfileInfo from './ProfileInfo';
import StatsCard from './StatsCard';
import IngestionControl from './IngestionControl';
import Spinner from '../common/Spinner';
import { humanSize } from '../../lib/format';

export default function DashboardPanel() {
  const { activeProfile, profiles } = useAppContext();
  const { stats, loading, error } = useProfileStats(activeProfile);

  const profile = profiles.find(p => p.name === activeProfile);

  if (!activeProfile) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <p>No profile selected.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top row: profile info + ingestion */}
      <div className="grid md:grid-cols-2 gap-4">
        {profile && <ProfileInfo profile={profile} />}
        <IngestionControl profile={activeProfile} />
      </div>

      {/* Stats cards */}
      {error ? (
        <p className="text-red-400 text-sm">{error}</p>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatsCard label="Chunks" value={stats.totalChunks.toLocaleString()} />
          <StatsCard label="Documents" value={stats.totalDocuments.toLocaleString()} />
          <StatsCard label="Cache" value={humanSize(stats.cacheSize)} />
          <StatsCard label="Vector Store" value={humanSize(stats.dataSize)} />
        </div>
      ) : null}

      {stats && stats.totalChunks === 0 && (
        <div className="text-center py-4 text-slate-500 text-sm">
          No data indexed yet. Use the ingestion controls above to crawl and index this profile's sources.
        </div>
      )}
    </div>
  );
}
