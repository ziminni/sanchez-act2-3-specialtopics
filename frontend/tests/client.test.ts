import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, queryString, request, session } from '../src/api/client';
afterEach(() => vi.unstubAllGlobals());
function mockResponse(status: number, body: unknown) {
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(status === 204 ? null : JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}
describe('central API client', () => {
  it('sends the token, query parameters and JSON body', async () => {
    session.save('synthetic-token');
    const fetch = mockResponse(201, { success: true, data: { id: 1 } });
    await request('/students' + queryString({ search: 'Dela Cruz', page: 2, status: '' }), {
      method: 'POST',
      body: JSON.stringify({ first_name: 'Ana' }),
    });
    expect(fetch.mock.calls[0][0]).toContain('search=Dela+Cruz&page=2');
    expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer synthetic-token');
    expect(fetch.mock.calls[0][1].headers.get('Content-Type')).toBe('application/json');
  });
  it('accepts a 204 without parsing JSON', async () => {
    mockResponse(204, null);
    await expect(request('/auth/logout', { method: 'POST' })).resolves.toMatchObject({
      success: true,
      data: undefined,
    });
  });
  it('normalizes field validation messages', async () => {
    mockResponse(422, {
      message: 'Validation failed.',
      errors: { 'body.email': ['Invalid email.'] },
    });
    await expect(request('/students')).rejects.toMatchObject({
      status: 422,
      fields: { email: ['Invalid email.'] },
    });
  });
  it('clears a rejected session and emits expiration', async () => {
    session.save('expired');
    const handler = vi.fn();
    window.addEventListener('campus:expired', handler);
    mockResponse(401, { message: 'Expired token.' });
    await expect(request('/auth/me')).rejects.toMatchObject({ status: 401 });
    expect(session.token()).toBeNull();
    expect(handler).toHaveBeenCalledOnce();
    window.removeEventListener('campus:expired', handler);
  });
  it('preserves distinct forbidden, not-found and conflict statuses', async () => {
    for (const status of [403, 404, 409]) {
      mockResponse(status, { message: 'Request rejected.' });
      await expect(request('/students')).rejects.toMatchObject({
        status,
        message: 'Request rejected.',
      });
    }
  });
  it('never displays server internals for 500 responses', async () => {
    mockResponse(500, { message: 'private database stack trace' });
    await expect(request('/students')).rejects.toMatchObject({
      status: 500,
      message: 'The server could not complete this request. Please try again.',
    });
  });
  it('reports a network failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(request('/students')).rejects.toMatchObject({
      status: 0,
      message: expect.stringContaining('Cannot reach'),
    });
  });
  it('ignores cancelled stale requests', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new DOMException('Aborted', 'AbortError')));
    const controller = new AbortController();
    controller.abort();
    await expect(request('/students', { signal: controller.signal })).rejects.toMatchObject({
      name: 'AbortError',
    });
  });
});
