import { Link } from 'react-router-dom';
import {
  ArrowDownRight,
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  GraduationCap,
  Layers3,
  ScrollText,
  UsersRound,
} from 'lucide-react';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { api } from '../api/client';
import { Badge, Empty, ErrorState, Loading, PageHeader } from '../components/UI';
export default function Dashboard() {
  const { user } = useAuth();
  const staff = ['ADMIN', 'REGISTRAR'].includes(user!.role);
  const student = user!.role === 'STUDENT';
  const resources = staff
    ? ['students', 'programs', 'courses', 'enrollments']
    : student
      ? ['enrollments']
      : ['courses', 'my-students', 'grades'];
  // Instructors and students have no Enrollments page; point their enrollment links elsewhere.
  const enrollmentsLink = staff ? '/enrollments' : student ? '/academic-record' : '/my-students';
  const stats = useQuery(`dashboard-${user!.id}`, async (signal) =>
    Promise.all(
      resources.map(async (name) => ({
        name,
        response: await api.list(name, { per_page: 1 }, signal),
      }))
    )
  );
  const recent = useQuery(`recent-${user!.id}`, (signal) =>
    api.list(staff ? 'students' : 'enrollments', { per_page: 5, sort: '-created_at' }, signal)
  );
  const labels: Record<string, string> = {
    students: 'Students',
    programs: 'Programs',
    courses: staff ? 'Subjects' : 'My subjects',
    'my-students': 'My students',
    enrollments: 'Enrollments',
    grades: 'Grade records',
  };
  const icons: Record<string, typeof UsersRound> = {
    students: UsersRound,
    'my-students': UsersRound,
    programs: Layers3,
    courses: BookOpen,
    enrollments: ClipboardCheck,
    grades: ScrollText,
  };
  return (
    <>
      <PageHeader
        eyebrow="YOUR WORKSPACE, AT A GLANCE"
        title={`Welcome back, ${user!.name.split(' ')[0]}.`}
        description={
          staff
            ? 'Keep student records and academic operations moving forward.'
            : 'Your academic information, together in one place.'
        }
        action={
          <span className="date-chip">
            {new Intl.DateTimeFormat('en', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            }).format(new Date())}
          </span>
        }
      />
      {stats.loading ? (
        <Loading label="Loading your overview…" />
      ) : stats.error ? (
        <ErrorState error={stats.error} retry={stats.retry} />
      ) : (
        <div className="stats-grid">
          {stats.data?.map(({ name, response }) => {
            const Icon = icons[name];
            return (
              <Link
                key={name}
                className="stat-card"
                to={name === 'enrollments' ? enrollmentsLink : `/${name}`}
              >
                <div>
                  <span>{labels[name]}</span>
                  <Icon size={20} />
                </div>
                <strong>{response.meta?.total.toLocaleString()}</strong>
                <span className="stat-caption">
                  {staff ? 'Across your institution' : 'Available to your account'}
                  <ArrowDownRight size={17} />
                </span>
              </Link>
            );
          })}
        </div>
      )}
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>{staff ? 'Recently added students' : 'Recent enrollments'}</h2>
              <p className="muted">
                {staff
                  ? 'The newest additions to your student directory.'
                  : 'Your latest registration records.'}
              </p>
            </div>
            <Link className="text-link" to={staff ? '/students' : enrollmentsLink}>
              View all
              <ArrowRight size={15} />
            </Link>
          </div>
          {recent.loading ? (
            <Loading />
          ) : recent.error ? (
            <ErrorState error={recent.error} retry={recent.retry} />
          ) : !recent.data?.data.length ? (
            <Empty />
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{staff ? 'Student' : 'Subject'}</th>
                    <th>{staff ? 'Year level' : 'Term'}</th>
                    <th>Status</th>
                    <th>
                      <span className="sr-only">Details</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recent.data.data.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <div className="person-cell">
                          <span className="avatar pale">
                            {staff ? (
                              `${String(row.first_name)[0]}${String(row.last_name)[0]}`
                            ) : (
                              <ClipboardCheck size={18} />
                            )}
                          </span>
                          <span>
                            <strong>
                              {staff
                                ? `${row.first_name} ${row.last_name}`
                                : `${row.course_code} · ${row.course_title}`}
                            </strong>
                            <small>
                              {staff
                                ? row.student_number
                                : student
                                  ? `Section ${row.section}`
                                  : row.student_name}
                            </small>
                          </span>
                        </div>
                      </td>
                      <td>{staff ? `Year ${row.year_level}` : row.term_name}</td>
                      <td>
                        <Badge value={row.status} />
                      </td>
                      <td>
                        {staff && (
                          <Link
                            className="icon-link"
                            aria-label={`View student ${row.id}`}
                            to={`/students/${row.id}`}
                          >
                            <ArrowRight size={18} />
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <section className="quick-panel">
          <span className="quick-icon">
            <GraduationCap size={28} />
          </span>
          <p className="eyebrow">THE NEXT STEP</p>
          <h2>{staff ? 'A smoother academic day.' : 'Your next chapter starts here.'}</h2>
          <p>
            {staff
              ? 'From a new student to a complete academic record. Everything you need, a little closer.'
              : 'Stay connected to your subjects, enrollments, and academic progress.'}
          </p>
          <div className="quick-links">
            {(staff
              ? [
                  ['/students/new', 'Add a student'],
                  ['/enrollments/new', 'Register an enrollment'],
                  user!.role === 'ADMIN'
                    ? ['/academic-record', 'View academic records']
                    : ['/enrollments', 'Review enrollments'],
                ]
              : student
                ? [['/academic-record', 'My academic record']]
                : [
                    ['/courses', 'My subjects'],
                    ['/my-students', 'My students'],
                    ['/grades', 'Manage grades'],
                  ]
            ).map(([to, label]) => (
              <Link key={to} to={to}>
                {label}
                <ArrowRight size={17} />
              </Link>
            ))}
          </div>
        </section>
      </div>
      <div className="overview-note">
        <span className="note-icon">
          <BookOpen size={19} />
        </span>
        <div>
          <strong>One place for the whole academic journey</strong>
          <p>Keep profiles, registrations, and grades connected through your academic workspace.</p>
        </div>
      </div>
    </>
  );
}
