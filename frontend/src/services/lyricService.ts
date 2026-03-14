import { apiGet, apiPost, apiDelete } from '../utils/apiClient';
import { ENDPOINTS } from '../config';
import type { LyricsListResponse, LyricDetail, TranscriptSegment } from '../types';

export interface SaveLyricInput {
  title: string;
  video_id: string;
  language: string;
  transcript: string; // JSON string
}

export interface SaveLyricResponse {
  id: string;
  title: string;
  video_id: string;
  language: string;
  transcript: TranscriptSegment[];
  created_at: string;
  updated_at: string;
}

const lyricService = {
  /** Fetch all saved lyrics for the current user. */
  async getAll(): Promise<LyricsListResponse> {
    return apiGet<LyricsListResponse>(ENDPOINTS.lyrics.list);
  },

  /** Fetch a single lyric entry by ID. */
  async getById(id: string): Promise<LyricDetail> {
    return apiGet<LyricDetail>(ENDPOINTS.lyrics.detail(id));
  },

  /** Save a lyric/transcript entry. */
  async save(data: SaveLyricInput): Promise<SaveLyricResponse> {
    return apiPost<SaveLyricResponse>(ENDPOINTS.lyrics.list, data);
  },

  /** Delete a lyric entry by ID. */
  async delete(id: string): Promise<void> {
    await apiDelete(ENDPOINTS.lyrics.detail(id));
  },
};

export default lyricService;
