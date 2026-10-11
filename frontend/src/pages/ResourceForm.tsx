import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Check, LoaderCircle } from 'lucide-react';
import type { Row } from '../api/types';
import { api, ApiError } from '../api/client';
import { resources, canWrite } from '../features/resources';
import type { Resource } from '../features/resources';
import { toPayload, validateForm } from '../features/validation';
import { useAuth } from '../state/Auth';
import { useQuery } from '../state/useQuery';
import { Back, ErrorState, Loading, Modal, PageHeader, useToast } from '../components/UI';
import ReferenceSelect from '../components/ReferenceSelect';
export default function ResourceForm({ resource }: { resource: Resource }) {
  const { id } = useParams();
  const editing = Boolean(id);
  const def = resources[resource];
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const [values, setValues] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const query = useQuery(`${resource}-form-${id || 'new'}`, (signal) =>
    editing
      ? api.get(resource, id!, signal)
      : Promise.resolve({ success: true, message: '', data: { id: 0 } as Row })
  );
  useEffect(() => {
    if (query.data) {
      const record: Record<string, unknown> = query.data.data;
      setValues(
        Object.fromEntries(
          def.fields.map((f) => [
            f.key,
            String((editing ? record[f.key] : (searchParams.get(f.key) ?? f.default)) ?? ''),
          ])
        )
      );
    }
  }, [query.data, def, editing, searchParams]);
  if (!canWrite(resource, user!.role))
    return <ErrorState error={new ApiError(403, 'Your account cannot change these records.')} />;
  if (query.loading) return <Loading label="Preparing the form…" />;
  if (query.error) return <ErrorState error={query.error} retry={query.retry} />;
  const persist = async () => {
    setBusy(true);
    setMessage('');
    try {
      const payload = toPayload(def.fields, values, editing);
      const result = editing
        ? await api.update(resource, Number(id), payload)
        : await api.create(resource, payload);
      toast(
        `${def.singular.charAt(0).toUpperCase() + def.singular.slice(1)} ${editing ? 'updated' : 'created'} successfully.`
      );
      navigate(`/${resource}/${result.data.id}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(error.fields);
        setMessage(error.message);
      } else setMessage('Unable to save. Please try again.');
      setConfirm(false);
      requestAnimationFrame(() =>
        formRef.current
          ?.querySelector<HTMLElement>('[aria-invalid="true"], [role="alert"]')
          ?.focus()
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Back to={`/${resource}`}>Back to {def.title.toLowerCase()}</Back>
      <PageHeader
        eyebrow="ACADEMIC WORKSPACE"
        title={`${editing ? 'Edit' : 'Add'} ${def.singular}`}
        description={
          editing
            ? 'Update the details below. Changes are saved to the academic record.'
            : 'Enter the details below to create a new record.'
        }
      />
      <form
        className="panel form-panel"
        ref={formRef}
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          const invalid = validateForm(def.fields, values, editing);
          setErrors(invalid);
          setMessage('');
          if (Object.keys(invalid).length) {
            setMessage('Please review the highlighted fields.');
            requestAnimationFrame(() =>
              formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
            );
            return;
          }
          if (
            editing &&
            ['INACTIVE', 'DROPPED'].includes(values.status) &&
            values.status !== query.data?.data.status
          )
            setConfirm(true);
          else void persist();
        }}
      >
        {message && (
          <div className="form-error" tabIndex={-1} role="alert">
            {message}
          </div>
        )}
        <div className="form-grid">
          {def.fields.map((field) => {
            const error = errors[field.key];
            const controlId = `field-${field.key}`;
            const descriptionId = `help-${field.key}`;
            const update = (value: string) => {
              setValues((old) => ({ ...old, [field.key]: value }));
              setErrors((old) => ({ ...old, [field.key]: [] }));
            };
            return (
              <div
                key={field.key}
                className={`form-field ${field.type === 'textarea' ? 'wide' : ''}`}
              >
                <label htmlFor={controlId}>
                  {field.label}
                  {field.required && !(editing && field.type === 'password') && (
                    <span className="required" aria-label="required">
                      *
                    </span>
                  )}
                </label>
                {field.ref ? (
                  <ReferenceSelect
                    id={controlId}
                    label={field.label}
                    resource={field.ref}
                    value={values[field.key] || ''}
                    onChange={update}
                    required={field.required}
                    disabled={busy || (editing && field.immutable)}
                    invalid={Boolean(error?.length)}
                    describedBy={descriptionId}
                  />
                ) : field.options ? (
                  <select
                    id={controlId}
                    value={values[field.key] || ''}
                    onChange={(e) => update(e.target.value)}
                    disabled={busy}
                    aria-required={field.required && !(editing && field.type === 'password')}
                    aria-invalid={Boolean(error?.length)}
                    aria-describedby={descriptionId}
                  >
                    <option value="">Select {field.label.toLowerCase()}</option>
                    {field.options.map((v) => (
                      <option key={v} value={v}>
                        {v.toLowerCase().replaceAll('_', ' ')}
                      </option>
                    ))}
                  </select>
                ) : field.type === 'textarea' ? (
                  <textarea
                    id={controlId}
                    value={values[field.key] || ''}
                    maxLength={field.maxLength}
                    onChange={(e) => update(e.target.value)}
                    disabled={busy}
                    aria-required={field.required}
                    aria-invalid={Boolean(error?.length)}
                    aria-describedby={descriptionId}
                  />
                ) : (
                  <input
                    id={controlId}
                    type={field.type || 'text'}
                    value={values[field.key] || ''}
                    onChange={(e) => update(e.target.value)}
                    min={field.min}
                    max={field.max}
                    maxLength={field.maxLength}
                    step={field.step ?? 1}
                    disabled={busy}
                    autoComplete={field.type === 'password' ? 'new-password' : 'off'}
                    aria-required={field.required && !(editing && field.type === 'password')}
                    aria-invalid={Boolean(error?.length)}
                    aria-describedby={descriptionId}
                  />
                )}
                <div id={descriptionId}>
                  {field.help && <p className="field-help">{field.help}</p>}
                  {editing && field.immutable && (
                    <p className="field-help">This reference cannot be changed after creation.</p>
                  )}
                  {error?.map((text) => (
                    <span key={text} className="field-error">
                      {text}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        <div className="form-actions">
          <button
            type="button"
            className="secondary"
            onClick={() => navigate(`/${resource}`)}
            disabled={busy}
          >
            Cancel
          </button>
          <button disabled={busy}>
            {busy ? <LoaderCircle size={17} className="spin" /> : <Check size={17} />}{' '}
            {busy ? 'Saving…' : editing ? 'Save changes' : `Create ${def.singular}`}
          </button>
        </div>
      </form>
      {confirm && (
        <Modal
          title={values.status === 'DROPPED' ? 'Drop this enrollment?' : 'Deactivate this record?'}
          busy={busy}
          onClose={() => setConfirm(false)}
        >
          <p>
            This will change the record status to {values.status.toLowerCase()}. Its existing
            academic history will be preserved.
          </p>
          <div className="actions">
            <button className="secondary" disabled={busy} onClick={() => setConfirm(false)}>
              Cancel
            </button>
            <button disabled={busy} onClick={() => void persist()}>
              {busy ? 'Saving…' : 'Confirm change'}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
