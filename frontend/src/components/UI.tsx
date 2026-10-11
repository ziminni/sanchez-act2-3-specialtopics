import { createContext, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  LoaderCircle,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ApiError } from '../api/client';
import type { Meta } from '../api/types';
export function Badge({ value }: { value: unknown }) {
  const text = String(value || 'Not set');
  return (
    <span
      className={`badge ${['ACTIVE', 'ENROLLED', 'COMPLETED'].includes(text) ? 'positive' : 'neutral'}`}
    >
      <span className="status-dot" />
      {text.replaceAll('_', ' ').toLowerCase()}
    </span>
  );
}
export function Loading({ label = 'Loading records…' }: { label?: string }) {
  return (
    <div className="state-panel" role="status">
      <LoaderCircle className="spin" size={24} />
      <p>{label}</p>
    </div>
  );
}
export function ErrorState({ error, retry }: { error: ApiError; retry?: () => void }) {
  const title =
    error.status === 403
      ? 'Access denied'
      : error.status === 404
        ? 'Record not found'
        : error.status === 0
          ? 'Connection unavailable'
          : 'Something went wrong';
  return (
    <div className="state-panel error-state" role="alert">
      <AlertCircle size={28} />
      <h2>{title}</h2>
      <p>{error.message}</p>
      <div className="actions">
        {retry && <button onClick={retry}>Try again</button>}
        <Link className="button secondary" to="/">
          Back to overview
        </Link>
      </div>
    </div>
  );
}
export function Empty({
  title = 'No records found',
  detail = 'Try changing your search or filters.',
  action,
}: {
  title?: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div className="state-panel">
      <FolderOpen size={30} />
      <h2>{title}</h2>
      <p>{detail}</p>
      {action}
    </div>
  );
}
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function Pagination({ meta, onPage }: { meta?: Meta; onPage: (page: number) => void }) {
  if (!meta) return null;
  const first = meta.total ? (meta.page - 1) * meta.per_page + 1 : 0;
  return (
    <div className="pagination">
      <span>
        {first}–{Math.min(meta.page * meta.per_page, meta.total)} of {meta.total} records
      </span>
      <div>
        <button
          className="icon-button"
          aria-label="Previous page"
          disabled={meta.page <= 1}
          onClick={() => onPage(meta.page - 1)}
        >
          <ChevronLeft size={18} />
        </button>
        <span>
          Page {meta.page} of {meta.last_page}
        </span>
        <button
          className="icon-button"
          aria-label="Next page"
          disabled={meta.page >= meta.last_page}
          onClick={() => onPage(meta.page + 1)}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
  busy = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
      aria-label={title}
    >
      <div className="dialog-heading">
        <h2>{title}</h2>
        <button className="icon-button" aria-label="Close dialog" disabled={busy} onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
const ToastContext = createContext<(message: string, kind?: 'success' | 'error') => void>(() => {});
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; kind: string } | null>(null);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 6500);
    return () => clearTimeout(id);
  }, [toast]);
  return (
    <ToastContext.Provider value={(message, kind = 'success') => setToast({ message, kind })}>
      {children}
      <div className="toast-region" aria-live="polite">
        {toast && (
          <div className={`toast ${toast.kind}`}>
            {toast.kind === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            <span>{toast.message}</span>
            <button
              className="icon-button"
              aria-label="Dismiss notification"
              onClick={() => setToast(null)}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </ToastContext.Provider>
  );
}
export const useToast = () => useContext(ToastContext);
export function Back({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link className="back-link" to={to}>
      <ArrowLeft size={16} />
      {children}
    </Link>
  );
}
