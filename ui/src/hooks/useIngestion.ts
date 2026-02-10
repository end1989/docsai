import { useState, useEffect, useCallback, useRef } from 'react';
import type { IngestionStatus } from '../api/types';
import { startIngestion, getIngestionStatus, cancelIngestion, getActiveIngestion } from '../api/ingestion';

const TERMINAL_STATUSES = ['completed', 'failed', 'cancelled'];

export function useIngestion(profileName: string) {
  const [status, setStatus] = useState<IngestionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const taskIdRef = useRef<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    if (!taskIdRef.current) return;
    try {
      const s = await getIngestionStatus(taskIdRef.current);
      setStatus(s);
      if (TERMINAL_STATUSES.includes(s.status)) {
        stopPolling();
      }
    } catch {
      stopPolling();
    }
  }, [stopPolling]);

  const startPolling = useCallback(() => {
    stopPolling();
    intervalRef.current = setInterval(poll, 2000);
    poll();
  }, [poll, stopPolling]);

  const start = useCallback(async () => {
    if (!profileName) return;
    setError(null);
    try {
      const res = await startIngestion(profileName);
      taskIdRef.current = res.task_id;
      startPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start ingestion');
    }
  }, [profileName, startPolling]);

  const cancel = useCallback(async () => {
    if (!taskIdRef.current) return;
    try {
      await cancelIngestion(taskIdRef.current);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel');
    }
  }, []);

  // Check for active ingestion on profile change
  useEffect(() => {
    const checkActive = async () => {
      try {
        const res = await getActiveIngestion();
        if (res.active_task && res.active_task.profile_name === profileName) {
          taskIdRef.current = res.active_task.id;
          setStatus(res.active_task);
          if (!TERMINAL_STATUSES.includes(res.active_task.status)) {
            startPolling();
          }
        } else {
          setStatus(null);
          taskIdRef.current = null;
        }
      } catch {
        // Backend may not have active ingestion endpoint in some states
      }
    };
    checkActive();
    return stopPolling;
  }, [profileName, startPolling, stopPolling]);

  const isRunning = status !== null && !TERMINAL_STATUSES.includes(status.status);

  return { status, isRunning, start, cancel, error };
}
