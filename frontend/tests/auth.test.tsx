import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '../src/state/Auth';
import Login from '../src/pages/Login';
function UserView() {
  const { user } = useAuth();
  return user ? <div>Signed in as {user.name}</div> : <Login />;
}
it('shows invalid credentials returned by the API', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ message: 'Invalid email or password.' }), { status: 401 })
  );
  render(
    <MemoryRouter>
      <AuthProvider>
        <UserView />
      </AuthProvider>
    </MemoryRouter>
  );
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email address'), 'wrong@example.com');
  await user.type(screen.getByLabelText('Password'), 'wrong-password');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.');
});
it('logs in and obtains the current identity from the real contract', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(
    async (url) =>
      new Response(
        JSON.stringify(
          String(url).endsWith('/auth/login')
            ? { data: { access_token: 'demo-token' } }
            : {
                data: {
                  id: 1,
                  name: 'Demo Admin',
                  email: 'admin@example.com',
                  role: 'ADMIN',
                  status: 'ACTIVE',
                },
              }
        ),
        { status: 200 }
      )
  );
  render(
    <MemoryRouter>
      <AuthProvider>
        <UserView />
      </AuthProvider>
    </MemoryRouter>
  );
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email address'), 'admin@example.com');
  await user.type(screen.getByLabelText('Password'), 'demo-password');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByText('Signed in as Demo Admin')).toBeInTheDocument();
  expect(sessionStorage.getItem('campus.session')).toBe('demo-token');
});
