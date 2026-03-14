import { apiGet, apiPost, apiDelete } from '../utils/apiClient';
import { ENDPOINTS } from '../config';
import type {
  VisualsListResponse,
  VisualDetail,
  ImageGenerationResponse,
} from '../types';

export interface SaveVisualInput {
  word: string;
  language: string;
  images: string; // JSON string
  prompt: string;
  explanation?: string | null;
}

export interface GenerateVisualInput {
  word: string;
  language: string;
}

const visualService = {
  /** Fetch all saved visuals for the current user. */
  async getAll(): Promise<VisualsListResponse> {
    return apiGet<VisualsListResponse>(ENDPOINTS.visuals.list);
  },

  /** Fetch a single visual entry by ID. */
  async getById(id: string): Promise<VisualDetail> {
    return apiGet<VisualDetail>(ENDPOINTS.visuals.detail(id));
  },

  /** Save a visual memory entry. */
  async save(data: SaveVisualInput): Promise<VisualDetail> {
    return apiPost<VisualDetail>(ENDPOINTS.visuals.list, data);
  },

  /** Delete a visual entry by ID. */
  async delete(id: string): Promise<void> {
    await apiDelete(ENDPOINTS.visuals.detail(id));
  },

  /** Generate images for a word using AI. */
  async generate(data: GenerateVisualInput): Promise<ImageGenerationResponse> {
    return apiPost<ImageGenerationResponse>(ENDPOINTS.visuals.generate, data);
  },
};

export default visualService;
