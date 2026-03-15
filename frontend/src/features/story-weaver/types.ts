export interface VocabWord {
  word: string;
  meaning_in_target: string;
  equivalent_in_english: string;
}

export interface StoryResponse {
  title: string;
  story: string;
  vocabulary: VocabWord[];
}

export interface SavedStory {
  id: string;
  title: string;
  language: string;
  created_at: string;
}

export interface QuizQuestion {
  id: number;
  type: 'multiple_choice' | 'fill_blank' | 'true_false';
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  word: string;
}

export interface QuizData {
  questions: QuizQuestion[];
}

export const LANGUAGES = {
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'ja': 'Japanese',
  'ko': 'Korean',
  'zh-CN': 'Chinese (Simplified)',
  'zh-TW': 'Chinese (Traditional)',
  'ru': 'Russian',
  'pt': 'Portuguese',
  'ar': 'Arabic',
} as const;
