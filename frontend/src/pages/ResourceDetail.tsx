import { Link, useParams } from 'react-router-dom';
import { Pencil, ArrowRight, Plus } from 'lucide-react';
import { api } from '../api/client';
import { resources, canWrite, fieldLabel, labelFor } from '../features/resources';
import type { Resource } from '../features/resources';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { ApiError } from '../api/client';
import { Back, Badge, ErrorState, Loading, PageHeader } from '../components/UI';
import { Cell } from './ResourceList';

function ProgramSubjects({ programId }: { programId: string }) {
  const query = useQuery(`program-${programId}-subjects`, (signal) =>
    api.list('courses', { program_id: programId, per_page: 100, sort: 'course_code' }, signal)
  );

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>
          Subjects {query.data?.meta && <span className="count-pill">{query.data.meta.total}</span>}
        </h2>
        <Link className="button secondary" to={`/courses/new?program_id=${programId}`}>
          <Plus size={16} />
          Add subject
        </Link>
      </div>
      {query.loading ? (
        <Loading label="Loading subjects…" />
      ) : query.error ? (
        <ErrorState error={query.error} retry={query.retry} />
      ) : query.data!.data.length === 0 ? (
        <div className="embedded-empty">
          <p>No subjects are assigned to this program yet.</p>
        </div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Subject code</th>
                <th>Subject title</th>
                <th>Units</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {query.data!.data.map((subject) => (
                <tr key={subject.id}>
                  <td>
                    <strong>{subject.course_code}</strong>
                  </td>
                  <td>{subject.course_title}</td>
                  <td>{subject.units}</td>
                  <td>
                    <Badge value={subject.status} />
                  </td>
                  <td>
                    <Link className="text-link" to={`/courses/${subject.id}`}>
                      View <ArrowRight size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function ResourceDetail({ resource }: { resource: Resource }) {
  const { id } = useParams();
  const { user } = useAuth();
  const def = resources[resource];
  const query = useQuery(`${resource}-detail-${id}`, (signal) => api.get(resource, id!, signal));
  if (!def.roles.includes(user!.role))
    return <ErrorState error={new ApiError(403, 'Your account cannot access this module.')} />;
  if (query.loading) return <Loading />;
  if (query.error) return <ErrorState error={query.error} retry={query.retry} />;
  const row = query.data!.data;
  const [name, summary] =
    resource === 'students'
      ? [`${row.first_name} ${row.last_name}`, `${row.student_number} · ${row.program_name}`]
      : resource === 'course-offerings'
        ? [
            `${row.course_code} · ${row.course_title}`,
            `${row.term_name} · Section ${row.section} · ${row.instructor_name}`,
          ]
        : resource === 'enrollments' || resource === 'grades'
          ? [
              String(row.student_name),
              `${row.course_code} · ${row.course_title} · ${row.term_name}`,
            ]
          : resource === 'academic-terms'
            ? [labelFor(resource, row), def.title]
            : [
                String(row.name || row.course_title),
                String(row.code || row.course_code || row.email || def.title),
              ];
  return (
    <>
      <Back to={`/${resource}`}>Back to {def.title.toLowerCase()}</Back>
      <PageHeader
        eyebrow={def.title.toUpperCase()}
        title={String(name)}
        description={summary}
        action={
          canWrite(resource, user!.role) && (
            <Link className="button" to={`/${resource}/${id}/edit`}>
              <Pencil size={17} />
              Edit {def.singular}
            </Link>
          )
        }
      />
      {resource === 'students' && (
        <div className="section-links">
          {user!.role !== 'STUDENT' && (
            <>
              <Link className="button secondary" to={`/students/${id}/enrollments`}>
                Enrollments
                <ArrowRight size={15} />
              </Link>
              <Link className="button secondary" to={`/students/${id}/grades`}>
                Grades
                <ArrowRight size={15} />
              </Link>
            </>
          )}
          <Link className="button secondary" to={`/academic-record?student=${id}`}>
            Academic record
            <ArrowRight size={15} />
          </Link>
        </div>
      )}
      {resource === 'course-offerings' && (
        <div className="section-links">
          <Link className="button secondary" to={`/course-offerings/${id}/students`}>
            View class roster
            <ArrowRight size={15} />
          </Link>
        </div>
      )}
      <section className="panel">
        <div className="panel-heading">
          <h2>Record details</h2>
          {row.status && <Badge value={row.status} />}
        </div>
        <dl className="detail-grid">
          {def.fields
            .filter((field) => field.type !== 'password')
            .map((field) => (
              <div className="detail-item" key={field.key}>
                <dt>{field.label}</dt>
                <dd>
                  <Cell row={row} field={field.key} />
                </dd>
              </div>
            ))}
          <div className="detail-item">
            <dt>Created</dt>
            <dd>
              {row.created_at ? new Date(String(row.created_at) + 'Z').toLocaleString() : '—'}
            </dd>
          </div>
          <div className="detail-item">
            <dt>Last updated</dt>
            <dd>
              {row.updated_at ? new Date(String(row.updated_at) + 'Z').toLocaleString() : '—'}
            </dd>
          </div>
        </dl>
      </section>
      {resource === 'programs' && <ProgramSubjects programId={id!} />}
    </>
  );
}
