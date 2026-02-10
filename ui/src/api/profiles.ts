import { api } from './client';
import type { ProfileListResponse, ProfileSwitchResponse, ProfileStats, ProfileCreateRequest, ProfileCreateResponse } from './types';

export const listProfiles = () => api.get<ProfileListResponse>('/profiles/list');
export const switchProfile = (name: string) => api.post<ProfileSwitchResponse>(`/profile/switch/${name}`);
export const getProfileStats = (name: string) => api.get<ProfileStats>(`/profile/${name}/stats`);
export const createProfile = (req: ProfileCreateRequest) => api.post<ProfileCreateResponse>('/profiles/create', req);
export const deleteProfile = (name: string) => api.delete(`/profiles/${name}`);
