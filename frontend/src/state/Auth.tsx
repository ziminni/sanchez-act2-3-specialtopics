import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError, request, session } from '../api/client';
import type { User } from '../api/types';
interface AuthState {
  user: User | null;
  loading: boolean;
  error: ApiError | null;
  expired: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  retry: () => void;
}
const Context = createContext<AuthState>(null!);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [expired, setExpired] = useState(false);
  const restore = useCallback(async () => {
    setError(null);
    setLoading(true);
    if (!session.token()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser((await request<User>('/auth/me')).data);
    } catch (e) {
      if (e instanceof ApiError && e.status !== 401) setError(e);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void restore();
    const expire = () => {
      setUser(null);
      setExpired(true);
      setError(null);
    };
    window.addEventListener('campus:expired', expire);
    return () => window.removeEventListener('campus:expired', expire);
  }, [restore]);
  async function login(email: string, password: string) {
    const result = await request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    session.save(result.data.access_token);
    try {
      setUser((await request<User>('/auth/me')).data);
      setExpired(false);
      setError(null);
    } catch (e) {
      session.clear();
      throw e;
    }
  }
  async function logout() {
    try {
      await request('/auth/logout', { method: 'POST' });
    } finally {
      session.clear();
      setUser(null);
      setExpired(false);
    }
  }
  return (
    <Context.Provider value={{ user, loading, error, expired, login, logout, retry: restore }}>
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
