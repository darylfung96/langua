import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast, TOAST_TIMEOUT_MS } from '../../hooks/useToast';

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts with null success and error', () => {
    const { result } = renderHook(() => useToast());
    expect(result.current.success).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('setSuccess shows message then auto-clears after timeout', () => {
    const { result } = renderHook(() => useToast());

    act(() => result.current.setSuccess('Saved!'));
    expect(result.current.success).toBe('Saved!');

    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS));
    expect(result.current.success).toBeNull();
  });

  it('setError shows message then auto-clears after timeout', () => {
    const { result } = renderHook(() => useToast());

    act(() => result.current.setError('Something failed'));
    expect(result.current.error).toBe('Something failed');

    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS));
    expect(result.current.error).toBeNull();
  });

  it('supports a custom timeout', () => {
    const { result } = renderHook(() => useToast());

    act(() => result.current.setSuccess('Custom timeout', 5000));
    expect(result.current.success).toBe('Custom timeout');

    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS));
    expect(result.current.success).toBe('Custom timeout');

    act(() => vi.advanceTimersByTime(5000 - TOAST_TIMEOUT_MS));
    expect(result.current.success).toBeNull();
  });

  it('passing null clears immediately', () => {
    const { result } = renderHook(() => useToast());

    act(() => result.current.setSuccess('Will be cleared'));
    act(() => result.current.setSuccess(null));
    expect(result.current.success).toBeNull();
  });

  it('clearAll removes both success and error', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.setSuccess('ok');
      result.current.setError('nope');
    });
    expect(result.current.success).toBe('ok');
    expect(result.current.error).toBe('nope');

    act(() => result.current.clearAll());
    expect(result.current.success).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('setting a new message resets the timer', () => {
    const { result } = renderHook(() => useToast());

    act(() => result.current.setSuccess('first'));
    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS / 2));

    act(() => result.current.setSuccess('second'));
    expect(result.current.success).toBe('second');

    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS / 2));
    expect(result.current.success).toBe('second');

    act(() => vi.advanceTimersByTime(TOAST_TIMEOUT_MS));
    expect(result.current.success).toBeNull();
  });
});
