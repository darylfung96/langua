import { apiFetch, apiGet, apiDelete } from '../utils/apiClient';
import { ENDPOINTS } from '../config';
import type { ResourcesListResponse, ResourceDetail, TranscribeResponse } from '../types';

export interface SaveResourceInput {
  title: string;
  file_name: string;
  file_type: string;
  language: string;
  transcript: string; // JSON string
  media_file_path?: string | null;
}

const resourceService = {
  /** Fetch all saved resources for the current user. */
  async getAll(): Promise<ResourcesListResponse> {
    return apiGet<ResourcesListResponse>(ENDPOINTS.resources.list);
  },

  /** Fetch a single resource by ID. */
  async getById(id: string): Promise<ResourceDetail> {
    return apiGet<ResourceDetail>(ENDPOINTS.resources.detail(id));
  },

  /** Save a resource entry (metadata + transcript). */
  async save(data: SaveResourceInput): Promise<ResourceDetail> {
    const res = await apiFetch(ENDPOINTS.resources.list, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  /** Delete a resource by ID. */
  async delete(id: string): Promise<void> {
    await apiDelete(ENDPOINTS.resources.detail(id));
  },

  /** Upload a media file and get a transcript back. */
  async transcribe(file: File, language: string): Promise<TranscribeResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);
    const res = await apiFetch(ENDPOINTS.transcribe, {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },

  /** Get a streaming URL for a saved resource's media file. */
  getMediaUrl(id: string): string {
    return ENDPOINTS.resources.media(id);
  },
};

export default resourceService;
