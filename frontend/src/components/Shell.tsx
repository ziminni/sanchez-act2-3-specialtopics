import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  GraduationCap,
  LayoutDashboard,
  Layers3,
  LogOut,
  Menu,
  NotebookPen,
  PanelLeftClose,
  ScrollText,
  UserRound,
  UsersRound,
  X,
} from 'lucide-react';
import { useAuth } from '../state/Auth';
import { useToast } from './UI';
const items = [
  {
    to: '/',
    label: 'Overview',
    icon: LayoutDashboard,
    roles: ['ADMIN', 'REGISTRAR', 'INSTRUCTOR', 'STUDENT'],
  },
  { to: '/students', label: 'Students', icon: UsersRound, roles: ['ADMIN', 'REGISTRAR'] },
  { to: '/programs', label: 'Programs', icon: Layers3, roles: ['ADMIN', 'REGISTRAR'] },
  {
    to: '/courses',
    label: 'Subjects',
    instructorLabel: 'My subjects',
    icon: BookOpen,
    roles: ['ADMIN', 'REGISTRAR', 'INSTRUCTOR'],
  },
  {
    to: '/academic-terms',
    label: 'Academic terms',
    icon: CalendarDays,
    roles: ['ADMIN', 'REGISTRAR'],
  },
  {
    to: '/course-offerings',
    label: 'Subject offerings',
    icon: NotebookPen,
    roles: ['ADMIN', 'REGISTRAR'],
  },
  { to: '/my-students', label: 'My students', icon: UsersRound, roles: ['INSTRUCTOR'] },
  {
    to: '/enrollments',
    label: 'Enrollments',
    icon: ClipboardCheck,
    roles: ['ADMIN', 'REGISTRAR'],
  },
  {
    to: '/grades',
    label: 'Grades',
    icon: ScrollText,
    roles: ['ADMIN', 'INSTRUCTOR'],
  },
  {
    to: '/academic-record',
    label: 'Academic record',
    icon: GraduationCap,
    roles: ['ADMIN', 'INSTRUCTOR', 'STUDENT'],
  },
  { to: '/users', label: 'User accounts', icon: UserRound, roles: ['ADMIN'] },
];
export default function Shell() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const toast = useToast();
  const location = useLocation();
  const labelOf = (item: (typeof items)[number]) =>
    (user!.role === 'INSTRUCTOR' && item.instructorLabel) || item.label;
  const current = items.find((item) => item.to !== '/' && location.pathname.startsWith(item.to));
  const section =
    (current && labelOf(current)) || (location.pathname === '/profile' ? 'My account' : 'Overview');
  return (
    <div className="app-layout">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {open && (
        <button
          aria-label="Close navigation"
          className="nav-scrim"
          onClick={() => setOpen(false)}
        />
      )}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <NavLink className="brand" to="/" onClick={() => setOpen(false)}>
          <div className="brand-mark">
            <GraduationCap size={24} />
          </div>
          <div>
            campus<span>STUDENT INFORMATION</span>
          </div>
        </NavLink>
        <button
          className="mobile-close icon-button"
          aria-label="Close menu"
          onClick={() => setOpen(false)}
        >
          <X />
        </button>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {items
            .filter((item) => item.roles.includes(user!.role))
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setOpen(false)}
              >
                <item.icon size={19} />
                {labelOf(item)}
              </NavLink>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="workspace-note">
            <span className="status-dot" />
            Academic workspace
          </div>
          <NavLink className="account-link" to="/profile" onClick={() => setOpen(false)}>
            <span className="avatar">
              {user!.name
                .split(' ')
                .map((n) => n[0])
                .slice(0, 2)
                .join('')}
            </span>
            <span>
              <strong>{user!.name}</strong>
              <small>{user!.role.toLowerCase()}</small>
            </span>
          </NavLink>
          <button
            className="logout"
            disabled={leaving}
            onClick={async () => {
              setLeaving(true);
              try {
                await logout();
              } catch {
                toast('Signed out on this device. Server logout could not be confirmed.', 'error');
              } finally {
                setLeaving(false);
              }
            }}
          >
            <LogOut size={17} />
            {leaving ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </aside>
      <div className="app-content">
        <header className="topbar">
          <div>
            <button
              className="icon-button mobile-menu"
              aria-label="Open menu"
              onClick={() => setOpen(true)}
            >
              <Menu size={21} />
            </button>
            <PanelLeftClose className="desktop-only" size={18} />
            <span className="breadcrumb">
              Workspace<span>/</span>
              <strong>{section}</strong>
            </span>
          </div>
          <span className="topbar-label">
            <span className="status-dot" />
            {user!.role === 'STUDENT'
              ? 'Student portal'
              : user!.role === 'INSTRUCTOR'
                ? 'Faculty portal'
                : 'Academic administration'}
          </span>
        </header>
        <main id="main" className="main-content">
          <Outlet />
        </main>
        <footer className="app-footer">
          <span>Campus / Student Information System</span>
          <span>Academic records, connected.</span>
        </footer>
      </div>
    </div>
  );
}
