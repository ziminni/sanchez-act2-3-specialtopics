import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Pencil, Plus, Search, SlidersHorizontal, Trash2 } from 'lucide-react';
import { api, ApiError } from '../api/client';
import type { Row } from '../api/types';
import {
  resources,
  canWrite,
  canDelete,
  fieldLabel,
  labelFor,
  titleFor,
} from '../features/resources';
import type { Resource } from '../features/resources';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import {
  Badge,
  Empty,
  ErrorState,
  Loading,
  Modal,
  PageHeader,
  Pagination,
  useToast,
} from '../components/UI';
// Show the referenced record's name, never its database ID.
const referenceNames: Record<string, (row: Row) => string | false> = {
  program_id: (row) => !!row.program_name && String(row.program_name),
  user_id: (row) => !!row.account_email && String(row.account_email),
  course_id: (row) => !!row.course_code && `${row.course_code} · ${row.course_title}`,
  academic_term_id: (row) => !!row.term_name && String(row.term_name),
  instructor_id: (row) => !!row.instructor_name && String(row.instructor_name),
  student_id: (row) => !!row.student_name && `${row.student_name} · ${row.student_number}`,
  course_offering_id: (row) =>
    !!row.course_code &&
    `${row.course_code} · ${row.course_title} · ${row.term_name} · Section ${row.section}`,
  enrollment_id: (row) =>
    !!row.student_name && `${row.student_name} · ${row.course_code} · ${row.term_name}`,
};
export function Cell({ row, field }: { row: Row; field: string }) {
  const value =
    field in referenceNames && row[field] !== null
      ? referenceNames[field](row) || 'Linked record'
      : row[field];
  if (field === 'status' || field === 'role') return <Badge value={value} />;
  if (field === 'name' && row.first_name)
    return (
      <div className="person-cell">
        <span className="avatar pale">
          {String(row.first_name)[0]}
          {String(row.last_name)[0]}
        </span>
        <strong>
          {row.first_name} {row.last_name}
        </strong>
      </div>
    );
  if (field === 'year_level') return <>Year {value}</>;
  return (
    <span title={String(value || '')}>
      {value === null || value === undefined || value === ''
        ? '—'
        : String(value).length > 65
          ? String(value).slice(0, 65) + '…'
          : String(value)}
    </span>
  );
}
export default function ResourceList({ resource }: { resource: Resource }) {
  const def = resources[resource];
  const { user } = useAuth();
  const navigate = useNavigate();
  const title = titleFor(resource, user!.role);
  const [params, setParams] = useSearchParams();
  const [draft, setDraft] = useState(params.get('search') || '');
  const currentSearch = params.get('search') || '';
  useEffect(() => setDraft(currentSearch), [currentSearch, resource]);
  const [deleting, setDeleting] = useState<Row | null>(null);
  const [busy, setBusy] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const toast = useToast();
  const page = Math.max(1, Number(params.get('page')) || 1);
  const filters: Record<string, string | number> = {
    page,
    per_page: 20,
    sort: params.get('sort') || 'id',
  };
  if (def.search && params.get('search')) filters.search = params.get('search')!;
  def.filters.forEach((f) => {
    if (params.get(f)) filters[f] = params.get(f)!;
  });
  const query = useQuery(`${resource}-${JSON.stringify(filters)}`, (signal) =>
    api.list(resource, filters, signal)
  );
  const update = (key: string, value: string) => {
    // History updates before React's navigation transition commits. Read the
    // current URL so quick filter changes cannot restore a cleared search.
    const next = new URLSearchParams(window.location.search);
    value ? next.set(key, value) : next.delete(key);
    if (key !== 'page') next.delete('page');
    setParams(next);
  };
  if (!def.roles.includes(user!.role))
    return <ErrorState error={new ApiError(403, 'Your account cannot access this module.')} />;
  return (
    <>
      <PageHeader
        eyebrow="ACADEMIC WORKSPACE"
        title={title}
        description={
          title === def.title ? def.description : 'Subjects you teach and their enrolled students.'
        }
        action={
          canWrite(resource, user!.role) && (
            <Link className="button" to={`/${resource}/new`}>
              <Plus size={17} />
              Add {def.singular}
            </Link>
          )
        }
      />
      <section className="panel">
        <div className="panel-heading">
          <h2 className="list-info">
            {user!.role === 'STUDENT'
              ? 'My records'
              : title === def.title
                ? 'All ' + title.toLowerCase()
                : title}
            {query.data?.meta && <span className="count-pill">{query.data.meta.total}</span>}
          </h2>
          <SlidersHorizontal size={17} color="#819781" />
        </div>
        <div className="toolbar">
          {def.search && (
            <form
              className="search-form"
              onSubmit={(e) => {
                e.preventDefault();
                update('search', draft);
              }}
            >
              <div className="search-wrap">
                <Search size={18} />
                <input
                  aria-label={`Search ${title.toLowerCase()}`}
                  placeholder={`Search ${title.toLowerCase()}…`}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                />
              </div>
              <button className="secondary" type="submit">
                Search
              </button>
            </form>
          )}
          {def.filters.map((key) => {
            const field = def.fields.find((f) => f.key === key)!;
            // Skip reference filters whose options this role cannot load (e.g. programs for instructors).
            const ref = field.ref as Resource | undefined;
            if (ref && ref in resources && !resources[ref].roles.includes(user!.role)) return null;
            return (
              <div className="filter-field" key={key}>
                <label htmlFor={`filter-${key}`}>{field.label}</label>
                {field.options ? (
                  <select
                    id={`filter-${key}`}
                    value={params.get(key) || ''}
                    onChange={(e) => update(key, e.target.value)}
                  >
                    <option value="">All {field.label.toLowerCase()}</option>
                    {field.options.map((v) => (
                      <option key={v} value={v}>
                        {v.toLowerCase()}
                      </option>
                    ))}
                  </select>
                ) : key === 'year_level' ? (
                  <select
                    id={`filter-${key}`}
                    value={params.get(key) || ''}
                    onChange={(e) => update(key, e.target.value)}
                  >
                    <option value="">All years</option>
                    {[1, 2, 3, 4, 5, 6].map((v) => (
                      <option key={v} value={v}>
                        Year {v}
                      </option>
                    ))}
                  </select>
                ) : (
                  <FilterReference
                    resource={field.ref!}
                    id={`filter-${key}`}
                    value={params.get(key) || ''}
                    onChange={(v) => update(key, v)}
                    label={field.label}
                  />
                )}
              </div>
            );
          })}
          <div className="filter-field">
            <label htmlFor="sort">Sort by</label>
            <select
              id="sort"
              value={params.get('sort') || 'id'}
              onChange={(e) => update('sort', e.target.value)}
            >
              <option value="id">Default order</option>
              {def.sort.flatMap((key) => [
                <option key={key} value={key}>
                  {fieldLabel(resource, key)} · ascending
                </option>,
                <option key={'-' + key} value={'-' + key}>
                  {fieldLabel(resource, key)} · descending
                </option>,
              ])}
            </select>
          </div>
          {params.size > 0 && (
            <button
              className="secondary"
              onClick={() => {
                setParams({});
                setDraft('');
              }}
            >
              Reset
            </button>
          )}
        </div>
        {query.loading ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={query.retry} />
        ) : !query.data?.data.length ? (
          <Empty
            title={`No ${title.toLowerCase()} found`}
            detail="Try changing the filters or add a record if you have permission."
          />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {def.columns.map((key) => (
                    <th key={key}>{fieldLabel(resource, key)}</th>
                  ))}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {query.data.data.map((row) => (
                  <tr
                    key={row.id}
                    className="clickable-row"
                    onClick={(e) => {
                      // Row actions keep their own behavior; anywhere else opens the record.
                      if ((e.target as HTMLElement).closest('a, button')) return;
                      navigate(`/${resource}/${row.id}`);
                    }}
                  >
                    {def.columns.map((key) => (
                      <td key={key}>
                        <Cell row={row} field={key} />
                      </td>
                    ))}
                    <td>
                      <div className="row-actions">
                        <Link
                          className="icon-link"
                          aria-label={`View ${def.singular} ${row.id}`}
                          to={`/${resource}/${row.id}`}
                        >
                          <ArrowRight size={17} />
                        </Link>
                        {canWrite(resource, user!.role) && (
                          <Link
                            className="icon-link"
                            aria-label={`Edit ${def.singular} ${row.id}`}
                            to={`/${resource}/${row.id}/edit`}
                          >
                            <Pencil size={16} />
                          </Link>
                        )}
                        {canDelete(resource, user!.role) && (
                          <button
                            className="icon-button"
                            aria-label={`Delete ${def.singular} ${row.id}`}
                            onClick={() => {
                              setDeleting(row);
                              setDeleteError('');
                            }}
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination meta={query.data?.meta} onPage={(page) => update('page', String(page))} />
      </section>
      {deleting && (
        <Modal title={`Delete ${def.singular}?`} onClose={() => setDeleting(null)} busy={busy}>
          <p>
            {labelFor(resource, deleting)} will be permanently removed. Records linked to academic
            history cannot be deleted. You can change their status instead.
          </p>
          {deleteError && (
            <div className="form-error" role="alert">
              {deleteError}
            </div>
          )}
          <div className="actions">
            <button className="secondary" disabled={busy} onClick={() => setDeleting(null)}>
              Cancel
            </button>
            <button
              className="danger"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                setDeleteError('');
                try {
                  await api.remove(resource, deleting.id);
                  setDeleting(null);
                  toast(`${def.singular} deleted.`);
                  query.retry();
                } catch (e) {
                  setDeleteError(e instanceof Error ? e.message : 'Unable to delete.');
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy ? 'Deleting…' : 'Delete record'}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
function FilterReference({
  resource,
  id,
  value,
  onChange,
  label,
}: {
  resource: string;
  id: string;
  value: string;
  onChange: (v: string) => void;
  label: string;
}) {
  const q = useQuery(`filter-${resource}`, async (signal) => {
    let page = 1;
    let rows: Row[] = [];
    while (true) {
      const r = await api.list(resource, { page, per_page: 100 }, signal);
      rows = [...rows, ...r.data];
      if (!r.meta || page >= r.meta.last_page) break;
      page++;
    }
    return rows;
  });
  return (
    <>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)} aria-label={label}>
        <option value="">All {label.toLowerCase()}s</option>
        {q.data?.map((row) => (
          <option key={row.id} value={row.id}>
            {row.code || row.academic_year || row.name} {row.semester ? `· ${row.semester}` : ''}
          </option>
        ))}
      </select>
      {q.error && (
        <button className="secondary" onClick={q.retry}>
          Retry filters
        </button>
      )}
    </>
  );
}
