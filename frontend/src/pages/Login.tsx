import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, GraduationCap, LoaderCircle, ShieldCheck } from 'lucide-react';
import { useAuth } from '../state/Auth';
import { ApiError } from '../api/client';
export default function Login() {
  const { user, login, expired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const from = location.state?.from;
  const destination =
    typeof from === 'string' && from.startsWith('/') && !from.startsWith('//') && from !== '/login'
      ? from
      : '/';
  if (user) return <Navigate to={destination} replace />;
  return (
    <div className="login-page">
      <section className="login-story">
        <div className="brand">
          <div className="brand-mark">
            <GraduationCap size={25} />
          </div>
          <div>
            campus<span>STUDENT INFORMATION</span>
          </div>
        </div>
        <div className="login-editorial">
          <p className="eyebrow">THE ACADEMIC WORKSPACE</p>
          <h1>
            Every student.
            <br />
            Every next chapter.
          </h1>
          <p>A shared home for student information, subject registration, and academic progress.</p>
          <div className="login-rule" />
          <div className="story-detail">
            <BookOpen size={23} />
            <span>
              Connected records.
              <br />
              <strong>A clearer view of learning.</strong>
            </span>
          </div>
        </div>
        <p className="login-foot">Student Information Management System</p>
      </section>
      <main className="login-form-side">
        <div className="login-form-wrap">
          <span className="small-label">WELCOME TO CAMPUS</span>
          <h2>Sign in to your workspace</h2>
          <p className="muted">Use your account to continue.</p>
          {expired && (
            <div className="notice" role="status">
              Your session has expired. Please sign in again.
            </div>
          )}
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError('');
              try {
                await login(email, password);
                navigate(destination, { replace: true });
              } catch (error) {
                setError(
                  error instanceof ApiError ? error.message : 'Sign in failed. Please try again.'
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <div className="form-error" role="alert">
                {error}
              </div>
            )}
            <button className="primary login-submit" disabled={busy}>
              {busy ? (
                <>
                  <LoaderCircle size={18} className="spin" />
                  Signing in…
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
          <p className="secure-note">
            <ShieldCheck size={17} />
            Your access is based on your account role.
          </p>
        </div>
        <p className="login-bottom">Students · Faculty · Academic administration</p>
      </main>
    </div>
  );
}
