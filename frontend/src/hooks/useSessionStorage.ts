import { useState, useEffect, useCallback } from 'react';

/**
 * Drop-in replacement for useState that persists the value in sessionStorage.
 * Serialises values as JSON so any serialisable type is supported.
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = sessionStorage.getItem(key);
      return item !== null ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(key, JSON.stringify(storedValue));
    } catch {
      // Quota exceeded or private-browsing restriction — degrade silently
    }
  }, [key, storedValue]);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue(prev =>
        typeof value === 'function' ? (value as (prev: T) => T)(prev) : value,
      );
    },
    [],
  );

  return [storedValue, setValue];
}
