import type { Field, Resource } from './resources';
export function validateForm(fields: Field[], values: Record<string, string>, editing: boolean) {
  const errors: Record<string, string[]> = {};
  for (const field of fields) {
    const value = values[field.key] ?? '';
    if (field.required && !value.trim() && !(editing && field.type === 'password'))
      errors[field.key] = ['This field is required.'];
    if (value && field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
      errors[field.key] = ['Enter a valid email address.'];
    if (value && field.type === 'password' && value.length < 12)
      errors[field.key] = ['Use at least 12 characters.'];
    if (
      value &&
      (field.type === 'number' || field.ref) &&
      (!Number.isFinite(Number(value)) ||
        (field.min !== undefined && Number(value) < field.min) ||
        (field.max !== undefined && Number(value) > field.max))
    )
      errors[field.key] = [
        `Enter a number${field.min !== undefined ? ` from ${field.min}` : ''}${field.max !== undefined ? ` to ${field.max}` : ''}.`,
      ];
  }
  return errors;
}
export function toPayload(
  fields: Field[],
  values: Record<string, string>,
  editing: boolean
): Record<string, unknown> {
  return Object.fromEntries(
    fields
      .filter(
        (f) => !(editing && f.immutable) && !(editing && f.type === 'password' && !values[f.key])
      )
      .map((f) => {
        const value = values[f.key] ?? '';
        return [f.key, value === '' ? null : f.type === 'number' || f.ref ? Number(value) : value];
      })
  );
}
