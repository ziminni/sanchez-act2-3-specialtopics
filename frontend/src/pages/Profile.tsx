import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { api, queryString, request } from '../api/client';
import type { AcademicRecord as RecordType } from '../api/types';
import { Badge, PageHeader } from '../components/UI';
import { score } from '../features/format';
export default function Profile() {
  const { user } = useAuth();
  const own = useQuery(`profile-${user!.id}`, (signal) =>
    user!.role === 'STUDENT' ? api.list('students', { per_page: 1 }, signal) : Promise.resolve(null)
  );
  const studentId = own.data?.data[0]?.id;
  // The GWA is computed by the API from per-subject grades, so the profile only displays it.
  const record = useQuery(`profile-gwa-${studentId ?? 'none'}`, (signal) =>
    studentId
      ? request<RecordType>(
          `/students/${studentId}/academic-record${queryString({ per_page: 1 })}`,
          { signal }
        )
      : Promise.resolve(null)
  );
  return (
    <>
      <PageHeader
        eyebrow="YOUR WORKSPACE"
        title="My account"
        description="Your identity and access in Campus."
      />
      <section className="panel">
        <div className="profile-banner">
          <span className="avatar">
            {user!.name
              .split(' ')
              .map((n) => n[0])
              .slice(0, 2)
              .join('')}
          </span>
          <div>
            <h2>{user!.name}</h2>
            <p>{user!.email}</p>
          </div>
        </div>
        <dl className="detail-grid">
          <div className="detail-item">
            <dt>Role</dt>
            <dd>
              <Badge value={user!.role} />
            </dd>
          </div>
          <div className="detail-item">
            <dt>Status</dt>
            <dd>
              <Badge value={user!.status} />
            </dd>
          </div>
        </dl>
        {record.data && (
          <div className="gwa-banner">
            <div>
              <p className="eyebrow">AUTOMATICALLY COMPUTED</p>
              <h2>General weighted average</h2>
              <p className="muted">
                Calculated from your graded subjects. Open your academic record for the per-term
                breakdown; no GWA is entered by hand.
              </p>
            </div>
            <div className="gwa-figure">
              <strong data-testid="profile-gwa">{score(record.data.data.gwa)}</strong>
              <span>{record.data.data.units} counted units</span>
            </div>
          </div>
        )}
        {own.data?.data[0] && (
          <div className="panel-heading">
            <Link className="button secondary" to={`/students/${own.data.data[0].id}`}>
              View my student profile
              <ArrowRight size={16} />
            </Link>
          </div>
        )}
      </section>
    </>
  );
}
