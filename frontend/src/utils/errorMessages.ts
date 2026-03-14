import { ApiError } from './apiClient';

/**
 * Maps HTTP status codes and known backend error detail strings to
 * user-friendly messages shown in the UI.
 */

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input and try again.',
  401: 'Your session has expired. Please log in again.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested item was not found.',
  409: 'A conflict occurred. This item may already exist.',
  413: 'The file is too large. Please upload a smaller file.',
  422: 'The data you submitted is invalid. Please check your input.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'A server error occurred. Please try again later.',
  502: 'The server is temporarily unavailable. Please try again later.',
  503: 'The service is currently unavailable. Please try again later.',
};

/** Known backend `detail` strings mapped to friendlier copy. */
const DETAIL_MESSAGES: Record<string, string> = {
  'Not authenticated': 'Your session has expired. Please log in again.',
  'Invalid credentials': 'Incorrect email or password.',
  'Account locked': 'Your account has been temporarily locked due to too many failed login attempts. Please try again later.',
  'Email already registered': 'An account with this email already exists.',
  'Story not found': 'This story could not be found. It may have been deleted.',
  'Lyric not found': 'This lyric entry could not be found. It may have been deleted.',
  'Resource not found': 'This resource could not be found. It may have been deleted.',
  'Visual not found': 'This visual entry could not be found. It may have been deleted.',
  'File too large': 'The uploaded file exceeds the 50 MB limit.',
  'Invalid file type': 'This file type is not supported. Please upload an audio or video file.',
  'Invalid YouTube video ID': 'The YouTube URL appears to be invalid. Please check and try again.',
  'Invalid language format': 'The language code is invalid. Please select a language from the list.',
};

/**
 * Converts any error (ApiError, Error, or unknown) into a human-readable string
 * safe to display directly in the UI.
 */
export function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    // Check for a known detail message first
    const detailMatch = DETAIL_MESSAGES[err.message];
    if (detailMatch) return detailMatch;

    // Fall back to the status-based message
    const statusMatch = STATUS_MESSAGES[err.status];
    if (statusMatch) return statusMatch;

    // Last resort: use the raw message if it looks safe (no HTML)
    if (err.message && !err.message.includes('<')) {
      return err.message;
    }
  }

  if (err instanceof Error) {
    if (err.name === 'AbortError') {
      return 'The request timed out. Please check your connection and try again.';
    }
    if (err.message.toLowerCase().includes('network') || err.message.toLowerCase().includes('fetch')) {
      return 'Network error. Please check your internet connection and try again.';
    }
    if (err.message && !err.message.includes('<')) {
      return err.message;
    }
  }

  return 'An unexpected error occurred. Please try again.';
}
