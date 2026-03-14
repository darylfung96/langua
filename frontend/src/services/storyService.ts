import { apiGet, apiPost, apiDelete } from '../utils/apiClient';
import { ENDPOINTS } from '../config';
import type {
  StoriesListResponse,
  StoryDetail,
  GeneratedStory,
  QuizData,
} from '../types';

export interface SaveStoryInput {
  title: string;
  story_content: string;
  language: string;
  vocabulary: string; // JSON string
  quiz?: string | null;
  audio?: string | null;
}

export interface GenerateStoryInput {
  words: string[];
  language: string;
}

export interface GenerateQuizInput {
  story: string;
  vocabulary: string; // JSON string
  language: string;
}

export interface GenerateAudioInput {
  text: string;
  language: string;
}

export interface GenerateAudioResponse {
  audio: string; // base64 PCM
}

const storyService = {
  /** Fetch all saved stories for the current user. */
  async getAll(): Promise<StoriesListResponse> {
    return apiGet<StoriesListResponse>(ENDPOINTS.stories.list);
  },

  /** Fetch a single story by ID. */
  async getById(id: string): Promise<StoryDetail> {
    return apiGet<StoryDetail>(ENDPOINTS.stories.detail(id));
  },

  /** Save a generated story. */
  async save(data: SaveStoryInput): Promise<StoryDetail> {
    return apiPost<StoryDetail>(ENDPOINTS.stories.list, data);
  },

  /** Delete a story by ID. */
  async delete(id: string): Promise<void> {
    await apiDelete(ENDPOINTS.stories.detail(id));
  },

  /** Generate a story from vocabulary words using Gemini. */
  async generateStory(data: GenerateStoryInput): Promise<GeneratedStory> {
    return apiPost<GeneratedStory>(ENDPOINTS.storyGen.generate, data);
  },

  /** Generate a quiz for a saved story. */
  async generateQuiz(data: GenerateQuizInput): Promise<QuizData> {
    return apiPost<QuizData>(ENDPOINTS.storyGen.generateQuiz, data);
  },

  /** Generate TTS audio for story text. */
  async generateAudio(data: GenerateAudioInput): Promise<GenerateAudioResponse> {
    return apiPost<GenerateAudioResponse>(ENDPOINTS.storyGen.generateAudio, data);
  },
};

export default storyService;
