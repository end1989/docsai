import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { Profile } from '../api/types';
import { listProfiles, switchProfile } from '../api/profiles';

interface AppContextValue {
  activeProfile: string;
  setActiveProfile: (name: string) => Promise<void>;
  profiles: Profile[];
  refreshProfiles: () => Promise<void>;
  isConnected: boolean;
  setIsConnected: (v: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [activeProfile, setActiveProfileState] = useState('');
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const refreshProfiles = useCallback(async () => {
    try {
      const res = await listProfiles();
      setProfiles(res.profiles);
      if (res.profiles.length > 0 && !activeProfile) {
        setActiveProfileState(res.profiles[0].name);
      }
    } catch {
      setProfiles([]);
    }
  }, [activeProfile]);

  const handleSetActiveProfile = useCallback(async (name: string) => {
    try {
      await switchProfile(name);
      setActiveProfileState(name);
    } catch (err) {
      console.error('Failed to switch profile:', err);
    }
  }, []);

  useEffect(() => {
    refreshProfiles();
  }, [refreshProfiles]);

  return (
    <AppContext.Provider value={{
      activeProfile,
      setActiveProfile: handleSetActiveProfile,
      profiles,
      refreshProfiles,
      isConnected,
      setIsConnected,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be inside AppProvider');
  return ctx;
}
