import { apiGet, apiPost } from '../utils/apiClient';
import { ENDPOINTS } from '../config';
import type {
  GeneratePhrasesResponse,
  RecordAttemptResponse,
  ShadowingSession,
} from '../types';

export interface GeneratePhrasesInput {
  theme: string;
  language: string;
  num_phrases?: number;
}

export interface StartSessionInput {
  theme: string;
  language: string;
  phrases: string; // JSON string
}

export interface StartSessionResponse {
  session_id: string;
}

export interface RecordAttemptInput {
  session_id: string;
  phrase_id: number;
  phrase_text: string;
  transcript: string;
  accuracy_score: number;
  words_matched: number;
  total_words: number;
}

export interface TTSInput {
  text: string;
  language: string;
}

export interface TTSResponse {
  audio: string; // base64 PCM
}

const shadowingService = {
  /** Generate practice phrases for a given theme and language. */
  async generatePhrases(data: GeneratePhrasesInput): Promise<GeneratePhrasesResponse> {
    return apiPost<GeneratePhrasesResponse>(ENDPOINTS.shadowing.generate, data);
  },

  /** Create a new shadowing session in the database. */
  async startSession(data: StartSessionInput): Promise<StartSessionResponse> {
    return apiPost<StartSessionResponse>(ENDPOINTS.shadowing.startSession, data);
  },

  /** Record a phrase attempt for scoring. */
  async recordAttempt(data: RecordAttemptInput): Promise<RecordAttemptResponse> {
    return apiPost<RecordAttemptResponse>(ENDPOINTS.shadowing.recordAttempt, data);
  },

  /** Fetch shadowing session history for the current user. */
  async getHistory(): Promise<ShadowingSession[]> {
    return apiGet<ShadowingSession[]>(ENDPOINTS.shadowing.history);
  },

  /** Generate TTS audio for a phrase. */
  async tts(data: TTSInput): Promise<TTSResponse> {
    return apiPost<TTSResponse>(ENDPOINTS.shadowing.tts, data);
  },
};

export default shadowingService;
