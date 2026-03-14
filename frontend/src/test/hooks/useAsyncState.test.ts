import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAsyncState } from '../../hooks/useAsyncState';

describe('useAsyncState', () => {
  it('starts with default state', () => {
    const { result } = renderHook(() => useAsyncState<string>());
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('accepts an initial value', () => {
    const { result } = renderHook(() => useAsyncState<string>('hello'));
    expect(result.current.data).toBe('hello');
  });

  it('returns data on success and clears isLoading', async () => {
    const { result } = renderHook(() => useAsyncState<number>());

    await act(async () => {
      await result.current.execute(async () => 42);
    });

    expect(result.current.data).toBe(42);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets error on failure and clears isLoading', async () => {
    const { result } = renderHook(() => useAsyncState<number>());

    await act(async () => {
      await result.current.execute(async () => {
        throw new Error('fetch failed');
      });
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('fetch failed');
    expect(result.current.isLoading).toBe(false);
  });

  it('clears previous error on new execute', async () => {
    const { result } = renderHook(() => useAsyncState<number>());

    await act(async () => {
      await result.current.execute(async () => { throw new Error('oops'); });
    });
    expect(result.current.error).toBe('oops');

    await act(async () => {
      await result.current.execute(async () => 99);
    });
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBe(99);
  });

  it('reset restores initial state', async () => {
    const { result } = renderHook(() => useAsyncState<number>(0));

    await act(async () => {
      await result.current.execute(async () => 10);
    });
    expect(result.current.data).toBe(10);

    act(() => result.current.reset());
    expect(result.current.data).toBe(0);
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('setError and setData allow direct mutation', () => {
    const { result } = renderHook(() => useAsyncState<string>());

    act(() => result.current.setError('manual error'));
    expect(result.current.error).toBe('manual error');

    act(() => result.current.setData('manual data'));
    expect(result.current.data).toBe('manual data');
  });

  it('returns null and uses fallback message for non-Error throws', async () => {
    const { result } = renderHook(() => useAsyncState<number>());

    await act(async () => {
      const returned = await result.current.execute(async () => {
        // eslint-disable-next-line @typescript-eslint/no-throw-literal
        throw 'string error';
      });
      expect(returned).toBeNull();
    });

    expect(result.current.error).toBe('An unexpected error occurred');
  });
});
