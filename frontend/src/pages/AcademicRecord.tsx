import { useSearchParams } from 'react-router-dom';
import { GraduationCap } from 'lucide-react';
import { api, ApiError, queryString, request } from '../api/client';
import type { AcademicRecord as RecordType } from '../api/types';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { Badge, Empty, ErrorState, Loading, PageHeader, Pagination } from '../components/UI';
import ReferenceSelect from '../components/ReferenceSelect';
import { score } from '../features/format';
export default function AcademicRecord() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const student = user!.role === 'STUDENT';
  const instructor = user!.role === 'INSTRUCTOR';
  const permitted = student || instructor || user!.role === 'ADMIN';
  // Instructors choose among the students enrolled in their own classes.
  const taught = useQuery(`record-taught-${user!.id}`, (signal) =>
    instructor ? api.list('my-students', { per_page: 100 }, signal) : Promise.resolve(null)
  );
  const own = useQuery(`my-student-${user!.id}`, (signal) =>
    student ? api.list('students', { per_page: 1 }, signal) : Promise.resolve(null)
  );
  const selected = student ? String(own.data?.data[0]?.id || '') : params.get('student') || '';
  const page = Math.max(1, Number(params.get('page')) || 1);
  const query = useQuery(`record-${selected}-${page}`, (signal) =>
    selected
      ? request<RecordType>(
          `/students/${selected}/academic-record${queryString({ page, per_page: 20 })}`,
          { signal }
        )
      : Promise.resolve(null)
  );
  if (!permitted)
    return <ErrorState error={new ApiError(403, 'Your account cannot view academic records.')} />;
  return (
    <>
      <PageHeader
        eyebrow="ACADEMIC PROGRESS"
        title={student ? 'My academic record' : 'Academic record'}
        description="Enrollments and grades, organized by academic term."
      />
      {!student && (
        <section className="record-controls">
          <label htmlFor="record-student">Student</label>
          {instructor ? (
            <select
              id="record-student"
              value={selected}
              onChange={(e) => setParams(e.target.value ? { student: e.target.value } : {})}
            >
              <option value="">
                {taught.loading ? 'Loading your students…' : 'Select student'}
              </option>
              {taught.data?.data.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.student_number} · {row.first_name} {row.last_name}
                </option>
              ))}
            </select>
          ) : (
            <ReferenceSelect
              id="record-student"
              label="Student"
              resource="students"
              value={selected}
              onChange={(value) => setParams(value ? { student: value } : {})}
            />
          )}
        </section>
      )}
      {own.error ? (
        <ErrorState error={own.error} retry={own.retry} />
      ) : own.loading || query.loading ? (
        <Loading />
      ) : !selected ? (
        <Empty
          title={student ? 'No student profile linked' : 'Choose a student'}
          detail={
            student
              ? 'Contact your registrar to link your account to a student profile.'
              : 'Select a student to view their academic record.'
          }
        />
      ) : query.error ? (
        <ErrorState error={query.error} retry={query.retry} />
      ) : !query.data?.data.terms.length ? (
        <Empty
          title="No academic records yet"
          detail="Academic records will appear after enrollment."
        />
      ) : (
        <>
          <div className="panel-heading">
            <h2>
              <GraduationCap size={19} /> {query.data.data.student_name} ·{' '}
              {query.data.data.student_number}
            </h2>
            <span className="muted">Grades use a 0–100 scale</span>
          </div>
          <section className="panel gwa-banner">
            <div>
              <p className="eyebrow">AUTOMATICALLY COMPUTED</p>
              <h2>General weighted average</h2>
              <p className="muted">
                Calculated by the API from each subject's final grade, weighted by units. Dropped
                and ungraded subjects are excluded, and no GWA is ever entered by hand.
              </p>
            </div>
            <div className="gwa-figure">
              <strong data-testid="gwa-value">{score(query.data.data.gwa)}</strong>
              <span>{query.data.data.units} counted units</span>
            </div>
          </section>
          {query.data.data.terms.map((term) => (
            <section className="panel record-term" key={term.academic_term_id}>
              <div className="term-heading">
                <div>
                  <h2>{term.academic_year}</h2>
                  <p>{term.semester.toLowerCase()} semester</p>
                </div>
                <div className="term-pills">
                  <span className="count-pill">
                    {term.courses.length} subject{term.courses.length !== 1 ? 's' : ''} on this page
                  </span>
                  <span className="count-pill">Term GWA {score(term.gwa)}</span>
                </div>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Subject</th>
                      <th>Section</th>
                      <th>Units</th>
                      <th>Midterm</th>
                      <th>Final grade</th>
                      <th>Status</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {term.courses.map((course) => (
                      <tr key={course.enrollment_id}>
                        <td>
                          <div className="person-cell">
                            <span>
                              <strong>{course.course_code}</strong>
                              <small>{course.course_title}</small>
                            </span>
                          </div>
                        </td>
                        <td>{course.section}</td>
                        <td>{course.units}</td>
                        <td>{course.midterm_grade ?? 'Not encoded'}</td>
                        <td>
                          <strong>{course.final_grade ?? 'Not encoded'}</strong>
                        </td>
                        <td>
                          <Badge value={course.status} />
                        </td>
                        <td>{course.remarks || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
          <Pagination
            meta={query.data.meta}
            onPage={(value) => {
              const next = new URLSearchParams(params);
              next.set('page', String(value));
              setParams(next);
            }}
          />
          <p className="warning-note">
            Records are paginated by enrollment, but the GWA always covers the full record. A term
            may continue on the next page.
          </p>
        </>
      )}
    </>
  );
}
