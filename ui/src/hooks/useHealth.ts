import { useEffect, useRef } from 'react';
import { useAppContext } from '../context/AppContext';
import type { HealthResponse } from '../api/types';

export function useHealth() {
  const { setIsConnected } = useAppContext();
  const intervalRef = useRef<ReturnType<typeof setInterval>>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/health');
        const data: HealthResponse = await res.json();
        setIsConnected(data.ok === true);
      } catch {
        setIsConnected(false);
      }
    };

    check();
    intervalRef.current = setInterval(check, 10000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [setIsConnected]);
}
