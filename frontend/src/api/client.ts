import type { Envelope, Row } from './types';
export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
).replace(/\/$/, '');
const TOKEN_KEY = 'campus.session';
export const session = {
  token: () => {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  save: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};
export class ApiError extends Error {
  status: number;
  fields: Record<string, string[]>;
  constructor(status: number, message: string, fields: Record<string, string[]> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}
export async function request<T>(path: string, options: RequestInit = {}): Promise<Envelope<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort('timeout'), 15000);
  const cancel = () => controller.abort('cancelled');
  options.signal?.addEventListener('abort', cancel, { once: true });
  if (options.signal?.aborted) controller.abort('cancelled');
  try {
    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    if (options.body) headers.set('Content-Type', 'application/json');
    const token = session.token();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (response.status === 204)
      return { success: true, message: 'Completed.', data: undefined as T };
    const json = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401 && path !== '/auth/login') {
        session.clear();
        window.dispatchEvent(new Event('campus:expired'));
      }
      const fields: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(json?.errors || {}))
        fields[key.split('.').pop()!] = Array.isArray(value) ? value.map(String) : [String(value)];
      throw new ApiError(
        response.status,
        response.status >= 500
          ? 'The server could not complete this request. Please try again.'
          : json?.message || 'The request could not be completed.',
        fields
      );
    }
    if (!json || !('data' in json))
      throw new ApiError(502, 'The server returned an unexpected response. Please try again.');
    return json;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (options.signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
    throw new ApiError(
      0,
      controller.signal.aborted
        ? 'The request took too long. Please try again.'
        : 'Cannot reach the server. Check your connection and try again.'
    );
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', cancel);
  }
}
export function queryString(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return query.size ? `?${query}` : '';
}
export const api = {
  list: (
    resource: string,
    params: Record<string, string | number | undefined> = {},
    signal?: AbortSignal
  ) => request<Row[]>(`/${resource}${queryString(params)}`, { signal }),
  get: (resource: string, id: string | number, signal?: AbortSignal) =>
    request<Row>(`/${resource}/${id}`, { signal }),
  create: (resource: string, data: Record<string, unknown>) =>
    request<Row>(`/${resource}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (resource: string, id: number, data: Record<string, unknown>) =>
    request<Row>(`/${resource}/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  remove: (resource: string, id: number) =>
    request<void>(`/${resource}/${id}`, { method: 'DELETE' }),
};
