import { describe, it, expect } from 'vitest';
import { ApiError } from '../../utils/apiClient';
import { getErrorMessage } from '../../utils/errorMessages';

describe('getErrorMessage', () => {
  it('maps known detail messages to friendly copy', () => {
    expect(getErrorMessage(new ApiError(401, 'Invalid credentials'))).toMatch(/incorrect email or password/i);
    expect(getErrorMessage(new ApiError(409, 'Email already registered'))).toMatch(/already exists/i);
    expect(getErrorMessage(new ApiError(404, 'Story not found'))).toMatch(/story could not be found/i);
  });

  it('maps status codes when detail is unknown', () => {
    expect(getErrorMessage(new ApiError(404, 'Some unknown detail'))).toMatch(/not found/i);
    expect(getErrorMessage(new ApiError(500, 'Internal server error'))).toMatch(/server error/i);
    expect(getErrorMessage(new ApiError(429, 'rate limited'))).toMatch(/too many requests/i);
    expect(getErrorMessage(new ApiError(403, 'forbidden'))).toMatch(/permission/i);
  });

  it('handles AbortError as a timeout message', () => {
    const err = new Error('aborted');
    err.name = 'AbortError';
    expect(getErrorMessage(err)).toMatch(/timed out/i);
  });

  it('handles generic network errors', () => {
    expect(getErrorMessage(new Error('network failure'))).toMatch(/network error/i);
    expect(getErrorMessage(new Error('Failed to fetch'))).toMatch(/network error/i);
  });

  it('returns a fallback for unknown errors', () => {
    expect(getErrorMessage(null)).toMatch(/unexpected error/i);
    expect(getErrorMessage(undefined)).toMatch(/unexpected error/i);
    expect(getErrorMessage(42)).toMatch(/unexpected error/i);
  });

  it('does not expose raw HTML in error messages', () => {
    const err = new ApiError(400, '<script>alert(1)</script>');
    const msg = getErrorMessage(err);
    expect(msg).not.toContain('<script>');
  });
});
