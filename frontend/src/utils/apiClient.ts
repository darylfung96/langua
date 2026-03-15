// Validate and normalize BASE_URL
const rawBaseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

let BASE_URL: string;
try {
  const url = new URL(rawBaseUrl);
  if (!url.protocol.startsWith('http')) {
    throw new Error('VITE_BACKEND_URL must use http or https protocol');
  }
  BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;
} catch (e) {
  console.error('Invalid VITE_BACKEND_URL:', rawBaseUrl, e);
  BASE_URL = 'http://localhost:8000';
}

const DEFAULT_TIMEOUT_MS = 15_000;
const MAX_RETRIES = 2; // Total attempts = 1 + MAX_RETRIES

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

/**
 * Determines if a request is safe to retry based on method and status code
 */
function isRetryable(method: string, status: number): boolean {
  // Don't retry non-idempotent methods
  if (!['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())) {
    return false;
  }
  // Retry on network errors (status 0), 5xx server errors, or 429 too many requests
  return status === 0 || status >= 500 || status === 429;
}

/**
 * Calculate delay with exponential backoff and jitter
 */
function getRetryDelay(attempt: number): number {
  const baseDelay = 500; // 500ms base
  const maxDelay = 5000; // 5s max
  const exponential = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  const jitter = exponential * 0.1 * Math.random(); // ±10% jitter
  return exponential + jitter;
}

/**
 * Get CSRF token from cookie
 */
function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Fetch wrapper that:
 *  - prepends the configured backend base URL
 *  - always sends cookies (credentials: 'include') for httpOnly cookie auth
 *  - enforces a request timeout (default 15 s)
 *  - retries on failure with exponential backoff for idempotent methods
 *  - automatically includes CSRF token for state-changing requests
 *  - throws ApiError with the server's `detail` message on non-2xx responses
 */
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const method = (options.method || 'GET').toUpperCase();
  const isSafeMethod = ['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method);

  // Get CSRF token for non-safe methods
  const csrfToken = isSafeMethod ? null : getCsrfToken();

  const headers: HeadersInit = {
    ...options.headers,
    ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
  };

  const mergedOptions: RequestInit = {
    ...options,
    signal: controller.signal,
    credentials: 'include',
    headers,
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    if (attempt > 0) {
      const delay = getRetryDelay(attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, mergedOptions);

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const error = new ApiError(response.status, body.detail || response.statusText);

        if (isRetryable(method, response.status) && attempt < MAX_RETRIES) {
          lastError = error;
          continue; // Retry
        }

        throw error;
      }

      clearTimeout(timeoutId); // Prevent abort from firing after a successful response
      return response;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        lastError = err;
        continue; // Timeout - retry if attempts remain
      }
      if (attempt >= MAX_RETRIES) {
        throw err;
      }
      lastError = err;
      // Network errors - retry
    }
  }

  throw lastError || new Error('Request failed after retries');
}

/** Convenience: fetch JSON response */
export async function apiGet<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await apiFetch(endpoint, { ...options, method: 'GET' });
  return res.json();
}

/** Convenience: POST JSON body, receive JSON response */
export async function apiPost<T>(endpoint: string, body: unknown, options?: RequestInit): Promise<T> {
  const res = await apiFetch(endpoint, {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    body: JSON.stringify(body),
  });
  return res.json();
}

/** Convenience: DELETE request */
export async function apiDelete<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await apiFetch(endpoint, { ...options, method: 'DELETE' });
  return res.json();
}

/** Expose base URL for cases where it's needed directly (e.g., file URL construction) */
export { BASE_URL };
