/**
 * Shared TypeScript types for the Language Learner app.
 * These mirror the backend Pydantic response schemas to provide end-to-end type safety.
 */

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface UserInfo {
  id: string;
  email: string;
}

export interface UserResponse extends UserInfo {
  created_at: string;
}

// ---------------------------------------------------------------------------
// Common
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  total?: number;
  limit?: number;
  offset: number;
  items: T[];
}

// ---------------------------------------------------------------------------
// Vocabulary & Quiz
// ---------------------------------------------------------------------------

export interface VocabWord {
  word: string;
  meaning_in_target: string;
  equivalent_in_english: string;
}

export type QuestionType = 'multiple_choice' | 'fill_blank' | 'true_false';

export interface QuizQuestion {
  id: number;
  type: QuestionType;
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  word: string;
}

export interface QuizData {
  questions: QuizQuestion[];
}

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export interface SavedStory {
  id: string;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface StoryDetail extends SavedStory {
  story_content: string;
  vocabulary: VocabWord[];
  quiz?: QuizData | null;
  audio_file_path?: string | null;
}

/** Shape returned by the AI story generation endpoint (not a saved story). */
export interface GeneratedStory {
  title: string;
  story: string;
  vocabulary: VocabWord[];
}

export interface StoriesListResponse {
  stories: SavedStory[];
  total?: number;
}

// ---------------------------------------------------------------------------
// Lyrics / YouTube
// ---------------------------------------------------------------------------

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

export interface SavedLyric {
  id: string;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface LyricDetail extends SavedLyric {
  video_id: string;
  transcript: TranscriptSegment[];
}

export interface LyricsListResponse {
  lyrics: SavedLyric[];
  total?: number;
}

// ---------------------------------------------------------------------------
// Resources (audio/video uploads)
// ---------------------------------------------------------------------------

export interface SavedResource {
  id: string;
  title: string;
  file_name: string;
  language: string;
  has_media?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResourceDetail extends SavedResource {
  file_type: string;
  transcript: TranscriptSegment[];
  media_file_path?: string | null;
}

export interface ResourcesListResponse {
  resources: SavedResource[];
  total?: number;
}

export interface TranscribeResponse {
  filename: string;
  text: string;
  segments: TranscriptSegment[];
}

// ---------------------------------------------------------------------------
// Visual Memory
// ---------------------------------------------------------------------------

export interface GeneratedImage {
  id: number;
  type: string;
  url: string;
  base64: string;
}

export interface ImageGenerationResponse {
  word: string;
  language: string;
  prompt: string;
  images: GeneratedImage[];
  text_response: string;
  success: boolean;
}

export interface SavedVisual {
  id: string;
  word: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface VisualDetail extends SavedVisual {
  images: GeneratedImage[];
  prompt: string;
  explanation: string;
}

export interface VisualsListResponse {
  visuals: SavedVisual[];
  total?: number;
}

// ---------------------------------------------------------------------------
// Shadowing
// ---------------------------------------------------------------------------

export type WordDifficulty = 'easy' | 'medium' | 'hard';
export type WordMatchStatus = 'pending' | 'current' | 'matched' | 'missed';

export interface PhraseWord {
  text: string;
  difficulty?: WordDifficulty;
}

export interface Phrase {
  text: string;
  translation: string;
  words: PhraseWord[];
}

export interface WordMatch {
  index: number;
  status: WordMatchStatus;
  confidence?: number;
}

export interface ShadowingSession {
  id: string;
  theme: string;
  language: string;
  created_at: string;
  completed_at?: string | null;
}

export interface ShadowingAttempt {
  id: string;
  session_id: string;
  phrase_id: number;
  phrase_text: string;
  accuracy_score: number;
  words_matched: number;
  total_words: number;
  attempted_at: string;
}

export interface GeneratePhrasesResponse {
  phrases: Phrase[];
  session_id: string;
}

export interface RecordAttemptResponse {
  attempt_id: string;
  accuracy_score: number;
  words_matched: number;
  total_words: number;
}
