import { useState } from 'react';

interface AsyncState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
}

interface UseAsyncStateReturn<T> extends AsyncState<T> {
  execute: (fn: () => Promise<T>) => Promise<T | null>;
  setError: (msg: string | null) => void;
  setData: (data: T | null) => void;
  reset: () => void;
}

/**
 * Consolidates the common [isLoading, error, data] pattern used across pages.
 *
 * Usage:
 *   const { data, error, isLoading, execute } = useAsyncState<Story[]>();
 *   const load = () => execute(async () => apiGet<Story[]>('/stories'));
 */
export function useAsyncState<T>(initial: T | null = null): UseAsyncStateReturn<T> {
  const [data, setData] = useState<T | null>(initial);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const execute = async (fn: () => Promise<T>): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setData(initial);
    setError(null);
    setIsLoading(false);
  };

  return { data, error, isLoading, execute, setError, setData, reset };
}
