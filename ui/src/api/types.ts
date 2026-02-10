export interface Profile {
  name: string;
  description: string;
  source_type: string;
  path: string;
}

export interface ProfileListResponse {
  profiles: Profile[];
}

export interface ProfileSwitchResponse {
  success: boolean;
  profile: string;
  message: string;
}

export interface ProfileStats {
  profile: string;
  totalDocuments: number;
  totalChunks: number;
  lastIngestion: string | null;
  categories: Record<string, number>;
  cacheSize: number;
  dataSize: number;
}

export interface AskResponse {
  answer: string;
  citations: string[];
  error?: string;
}

export interface IngestionStartResponse {
  success: boolean;
  task_id: string;
  message: string;
}

export interface IngestionStatus {
  id: string;
  profile_name: string;
  status: 'idle' | 'preparing' | 'scanning' | 'processing' | 'indexing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_file: string;
  total_files: number;
  processed_files: number;
  total_chunks: number;
  indexed_chunks: number;
  errors: string[];
  warnings: string[];
  start_time: string | null;
  end_time: string | null;
  duration: number | null;
  stats: Record<string, unknown>;
}

export interface IngestionActiveResponse {
  active_task: IngestionStatus | null;
}

export interface HealthResponse {
  ok: boolean;
}

export type PromptMode = 'comprehensive' | 'integration' | 'debugging' | 'learning';

export interface ProfileCreateRequest {
  name: string;
  sourceType: string;
  webDomains?: string[];
  localPaths?: string[];
  fileTypes?: string[];
  crawlDepth?: number;
  description?: string;
}

export interface ProfileCreateResponse {
  success: boolean;
  profile: string;
  path: string;
  message: string;
}
