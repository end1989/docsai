import { useAppContext } from '../context/AppContext';

export function useProfiles() {
  const { profiles, refreshProfiles, activeProfile, setActiveProfile } = useAppContext();
  return { profiles, refreshProfiles, activeProfile, setActiveProfile };
}
