import { useState, useEffect, useCallback } from 'react';
import type { ProfileStats } from '../api/types';
import { getProfileStats } from '../api/profiles';

export function useProfileStats(profileName: string) {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!profileName) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getProfileStats(profileName);
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, [profileName]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { stats, loading, error, refresh };
}
