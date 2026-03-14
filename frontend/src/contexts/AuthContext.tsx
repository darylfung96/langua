import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch, ApiError } from '../utils/apiClient';

interface UserInfo {
  id: string;
  email: string;
}

interface AuthContextValue {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  loginWithToken: (token: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, verify whether the httpOnly cookie is still valid.
  useEffect(() => {
    apiFetch('/auth/me')
      .then((res) => res.json())
      .then((data: UserInfo) => setUser(data))
      .catch((err) => {
        // 401 = not authenticated — expected on first load when no session exists.
        // Any other error (network failure, 5xx) is unexpected; log it for visibility.
        if (!(err instanceof ApiError && err.status === 401)) {
          console.error('Auth check failed with unexpected error:', err);
        }
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    await apiFetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });
    // Cookie is set by the backend; fetch /auth/me to populate user state.
    const me = await apiFetch('/auth/me');
    setUser(await me.json());
  };

  const register = async (email: string, password: string) => {
    await apiFetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    await login(email, password);
  };

  /** Called after Google OAuth code exchange — token is already set as a cookie. */
  const loginWithToken = async (_token: string) => {
    const me = await apiFetch('/auth/me');
    setUser(await me.json());
  };

  const logout = async () => {
    await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        loginWithToken,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
