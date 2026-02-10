import { useState } from 'react';
import type { Profile } from '../../api/types';
import { deleteProfile } from '../../api/profiles';
import { useProfiles } from '../../hooks/useProfiles';
import Badge from '../common/Badge';
import Card from '../common/Card';

interface ProfileInfoProps {
  profile: Profile;
}

const TYPE_COLORS: Record<string, string> = {
  web: 'blue',
  local: 'green',
  mixed: 'teal',
};

export default function ProfileInfo({ profile }: ProfileInfoProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const { refreshProfiles, setActiveProfile, profiles } = useProfiles();

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteProfile(profile.name);
      await refreshProfiles();
      const remaining = profiles.filter(p => p.name !== profile.name);
      if (remaining.length > 0) {
        setActiveProfile(remaining[0].name);
      }
    } catch (e) {
      console.error('Failed to delete profile:', e);
    } finally {
      setDeleting(false);
      setConfirming(false);
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Profile Info</h3>
          <p className="text-lg font-medium text-slate-100 mb-1">{profile.description || profile.name}</p>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Badge color={TYPE_COLORS[profile.source_type] || 'gray'}>{profile.source_type}</Badge>
            <span>{profile.path}</span>
          </div>
        </div>
        <div className="flex-shrink-0 ml-4">
          {!confirming ? (
            <button
              onClick={() => setConfirming(true)}
              className="text-xs text-slate-500 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-red-400/10"
            >
              Delete
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-xs text-red-400 hover:text-red-300 transition-colors px-2 py-1 rounded bg-red-400/10 hover:bg-red-400/20 disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Confirm'}
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-2 py-1"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
