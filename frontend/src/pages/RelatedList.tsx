import { Link, useParams, useSearchParams } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { Back, Empty, ErrorState, Loading, PageHeader, Pagination } from '../components/UI';
import { Cell } from './ResourceList';
import { columnLabel, labelFor } from '../features/resources';
export default function RelatedList({ kind }: { kind: 'enrollments' | 'grades' | 'roster' }) {
  const { id } = useParams();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get('page')) || 1);
  const roster = kind === 'roster';
  const resource = roster ? `course-offerings/${id}/students` : `students/${id}/${kind}`;
  const query = useQuery(`${resource}-${page}`, (signal) =>
    api.list(resource, { page, per_page: 20 }, signal)
  );
  const parent = useQuery(`${resource}-parent`, (signal) =>
    api.get(roster ? 'course-offerings' : 'students', id!, signal)
  );
  const owner = parent.data?.data;
  const cols = roster
    ? ['student_number', 'first_name', 'last_name', 'enrollment_status']
    : kind === 'grades'
      ? ['course_code', 'course_title', 'term_name', 'midterm_grade', 'final_grade', 'remarks']
      : ['course_code', 'course_title', 'term_name', 'section', 'enrollment_date', 'status'];
  if (
    (kind === 'enrollments' && !['ADMIN', 'REGISTRAR'].includes(user!.role)) ||
    (kind === 'grades' && user!.role === 'STUDENT')
  )
    return <ErrorState error={new ApiError(403, 'Your account cannot access this module.')} />;
  return (
    <>
      <Back to={`/${roster ? 'course-offerings' : 'students'}/${id}`}>
        Back to {roster ? 'offering' : 'student'}
      </Back>
      <PageHeader
        eyebrow={roster ? 'SUBJECT OFFERING' : 'STUDENT RECORD'}
        title={
          roster
            ? `Class roster${owner ? ' · ' + labelFor('course-offerings', owner) : ''}`
            : `${kind === 'grades' ? 'Grades' : 'Enrollments'}${owner ? ` · ${owner.first_name} ${owner.last_name}` : ''}`
        }
        description="Records available to your account."
      />
      <section className="panel">
        {query.loading ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={query.retry} />
        ) : !query.data?.data.length ? (
          <Empty />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {cols.map((key) => (
                    <th key={key}>{columnLabel(key)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {query.data.data.map((row) => (
                  <tr key={row.id}>
                    {cols.map((key) => (
                      <td key={key}>
                        <Cell row={row} field={key} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination meta={query.data?.meta} onPage={(page) => setParams({ page: String(page) })} />
      </section>
    </>
  );
}
