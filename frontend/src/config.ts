/**
 * Centralised app configuration.
 * All magic numbers, API endpoint paths, and feature limits live here.
 */

// ---------------------------------------------------------------------------
// API Endpoints
// ---------------------------------------------------------------------------

export const ENDPOINTS = {
  // Auth
  auth: {
    me: '/auth/me',
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    googleCallback: '/auth/google/callback',
  },

  // Stories
  stories: {
    list: '/stories',
    detail: (id: string) => `/stories/${id}`,
  },

  // Story generation (Gemini)
  storyGen: {
    generate: '/gemini/generate-story',
    generateQuiz: '/gemini/generate-quiz',
    generateAudio: '/gemini/generate-audio',
  },

  // Lyrics / YouTube
  lyrics: {
    list: '/lyrics',
    detail: (id: string) => `/lyrics/${id}`,
  },

  // Resources
  resources: {
    list: '/resources',
    detail: (id: string) => `/resources/${id}`,
    media: (id: string) => `/resources/media/${id}`,
  },

  // Transcription
  transcribe: '/transcribe',

  // Visuals
  visuals: {
    list: '/visuals',
    detail: (id: string) => `/visuals/${id}`,
    generate: '/image/generate',
  },

  // Shadowing
  shadowing: {
    generate: '/shadowing/generate',
    startSession: '/shadowing/start-session',
    recordAttempt: '/shadowing/record-attempt',
    history: '/shadowing/history',
    tts: '/shadowing/tts',
  },
} as const;

// ---------------------------------------------------------------------------
// Upload limits (mirror backend constants)
// ---------------------------------------------------------------------------

export const UPLOAD_LIMITS = {
  maxFileSizeBytes: 50 * 1024 * 1024, // 50 MB
  maxFileSizeMb: 50,
  allowedMimeTypes: new Set([
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'audio/wave',
    'audio/ogg',
    'audio/flac',
    'video/mp4',
    'video/webm',
    'video/ogg',
  ]),
} as const;

// ---------------------------------------------------------------------------
// Content length limits (mirror backend constants)
// ---------------------------------------------------------------------------

export const CONTENT_LIMITS = {
  maxTitleLength: 500,
  maxStoryContentLength: 100_000,
  maxWordLength: 200,
  maxPromptLength: 5_000,
  maxExplanationLength: 10_000,
  maxVideoIdLength: 50,
} as const;

// ---------------------------------------------------------------------------
// UI / UX config
// ---------------------------------------------------------------------------

export const UI_CONFIG = {
  toastDurationMs: 2_000,
  requestTimeoutMs: 15_000,
  audioSampleRate: 24_000,
  defaultShadowingPhraseCount: 5,
  maxShadowingPhraseCount: 20,
} as const;
