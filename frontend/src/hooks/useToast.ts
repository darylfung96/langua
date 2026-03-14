import { useState, useCallback, useRef, useEffect } from 'react';

export const TOAST_TIMEOUT_MS = 2000;

interface ToastState {
  success: string | null;
  error: string | null;
  setSuccess: (msg: string | null, timeoutMs?: number) => void;
  setError: (msg: string | null, timeoutMs?: number) => void;
  clearAll: () => void;
}

/**
 * Manages auto-dismissing success/error toast messages.
 * Passing null clears immediately; passing a string shows it for `timeoutMs` ms.
 */
export function useToast(defaultTimeoutMs = TOAST_TIMEOUT_MS): ToastState {
  const [success, setSuccessRaw] = useState<string | null>(null);
  const [error, setErrorRaw] = useState<string | null>(null);
  const successTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const errorTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (successTimer.current) clearTimeout(successTimer.current);
      if (errorTimer.current) clearTimeout(errorTimer.current);
    };
  }, []);

  const setSuccess = useCallback(
    (msg: string | null, timeoutMs = defaultTimeoutMs) => {
      if (successTimer.current) clearTimeout(successTimer.current);
      setSuccessRaw(msg);
      if (msg !== null) {
        successTimer.current = setTimeout(() => setSuccessRaw(null), timeoutMs);
      }
    },
    [defaultTimeoutMs],
  );

  const setError = useCallback(
    (msg: string | null, timeoutMs = defaultTimeoutMs) => {
      if (errorTimer.current) clearTimeout(errorTimer.current);
      setErrorRaw(msg);
      if (msg !== null) {
        errorTimer.current = setTimeout(() => setErrorRaw(null), timeoutMs);
      }
    },
    [defaultTimeoutMs],
  );

  const clearAll = useCallback(() => {
    if (successTimer.current) clearTimeout(successTimer.current);
    if (errorTimer.current) clearTimeout(errorTimer.current);
    setSuccessRaw(null);
    setErrorRaw(null);
  }, []);

  return { success, error, setSuccess, setError, clearAll };
}
