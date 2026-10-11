import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { api } from '../api/client';
import { labelFor } from '../features/resources';
import { useQuery } from '../state/useQuery';
import type { Row } from '../api/types';
export default function ReferenceSelect({
  resource,
  value,
  onChange,
  id,
  label,
  required = false,
  disabled = false,
  invalid = false,
  describedBy,
}: {
  resource: string;
  value: string;
  onChange: (value: string) => void;
  id: string;
  label: string;
  required?: boolean;
  disabled?: boolean;
  invalid?: boolean;
  describedBy?: string;
}) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState('');
  const [selected, setSelected] = useState<Row>();
  const searchable = !['enrollments', 'instructors'].includes(resource);
  const query = useQuery(`${resource}-${page}-${search}`, (signal) =>
    api.list(resource, { page, per_page: 20, ...(search ? { search } : {}) }, signal)
  );
  useEffect(() => {
    if (!value || resource === 'instructors') {
      setSelected(undefined);
      return;
    }
    const controller = new AbortController();
    api
      .get(resource, value, controller.signal)
      .then((r) => setSelected(r.data))
      .catch(() => {});
    return () => controller.abort();
  }, [value, resource]);
  const rows = query.data?.data || [];
  return (
    <div className="reference-control">
      {!disabled && searchable && (
        <div className="reference-search">
          <input
            aria-label={`Search ${label.toLowerCase()} options`}
            placeholder={`Find ${label.toLowerCase()}…`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                setSearch(draft);
                setPage(1);
              }
            }}
          />
          <button
            type="button"
            className="secondary"
            aria-label={`Search ${label.toLowerCase()}`}
            onClick={() => {
              setSearch(draft);
              setPage(1);
            }}
          >
            <Search size={16} />
          </button>
        </div>
      )}
      <select
        id={id}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setSelected(rows.find((r) => r.id === Number(e.target.value)));
        }}
        required={required}
        disabled={disabled}
        aria-invalid={invalid}
        aria-describedby={describedBy}
      >
        <option value="">
          {query.loading ? 'Loading options…' : `Select ${label.toLowerCase()}`}
        </option>
        {value && !rows.some((row) => row.id === Number(value)) && (
          <option value={value}>
            {selected ? labelFor(resource, selected) : `Selected record #${value}`}
          </option>
        )}
        {rows.map((row) => (
          <option key={row.id} value={row.id}>
            {labelFor(resource, row)}
          </option>
        ))}
      </select>
      {query.error && (
        <div className="inline-error" role="alert">
          {query.error.message}
          <button type="button" className="secondary" onClick={query.retry}>
            Retry options
          </button>
        </div>
      )}
      {!disabled && query.data?.meta && query.data.meta.last_page > 1 && (
        <div className="reference-pagination">
          <button
            type="button"
            className="icon-button"
            aria-label={`Previous ${label.toLowerCase()} options`}
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft size={14} />
          </button>
          <span>
            Options page {page} of {query.data.meta.last_page}
          </span>
          <button
            type="button"
            className="icon-button"
            aria-label={`Next ${label.toLowerCase()} options`}
            disabled={page >= query.data.meta.last_page}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
