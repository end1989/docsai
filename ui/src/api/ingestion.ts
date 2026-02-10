import { api } from './client';
import type { IngestionStartResponse, IngestionStatus, IngestionActiveResponse } from './types';

export const startIngestion = (profile: string) =>
  api.post<IngestionStartResponse>(`/ingestion/start/${profile}`);

export const getIngestionStatus = (taskId: string) =>
  api.get<IngestionStatus>(`/ingestion/status/${taskId}`);

export const cancelIngestion = (taskId: string) =>
  api.post<{ success: boolean; message: string }>(`/ingestion/cancel/${taskId}`);

export const getActiveIngestion = () =>
  api.get<IngestionActiveResponse>('/ingestion/active');
