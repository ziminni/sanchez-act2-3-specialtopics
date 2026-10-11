import { expect, it } from 'vitest';
import { resources, canWrite } from '../src/features/resources';
import { toPayload, validateForm } from '../src/features/validation';
import { score } from '../src/features/format';
it('validates required fields and email before submission', () => {
  const errors = validateForm(
    resources.students.fields,
    { email: 'invalid', year_level: '8' },
    false
  );
  expect(errors.first_name).toBeDefined();
  expect(errors.email).toBeDefined();
  expect(errors.year_level).toBeDefined();
});
it('sends numeric references and excludes immutable edit fields', () => {
  expect(
    toPayload(
      resources.enrollments.fields,
      {
        student_id: '2',
        course_offering_id: '3',
        status: 'DROPPED',
        enrollment_date: '2026-09-22',
      },
      true
    )
  ).toEqual({ status: 'DROPPED', enrollment_date: '2026-09-22' });
});
it('permits an unchanged password on account edits', () => {
  const fields = resources.users.fields.filter((f) => f.key === 'password');
  expect(validateForm(fields, { password: '' }, true)).toEqual({});
  expect(toPayload(fields, { password: '' }, true)).toEqual({});
});
it('matches instructor and student write permissions', () => {
  expect(canWrite('grades', 'INSTRUCTOR')).toBe(true);
  expect(canWrite('grades', 'ADMIN')).toBe(true);
  expect(canWrite('grades', 'REGISTRAR')).toBe(false);
  expect(canWrite('students', 'INSTRUCTOR')).toBe(false);
  expect(canWrite('grades', 'STUDENT')).toBe(false);
  expect(canWrite('users', 'REGISTRAR')).toBe(false);
});
it('limits the grade module to administrators and instructors', () => {
  expect(resources.grades.roles).toEqual(['ADMIN', 'INSTRUCTOR']);
  expect(resources.grades.roles).not.toContain('REGISTRAR');
  expect(resources.grades.roles).not.toContain('STUDENT');
});
it('formats computed scores to two decimals', () => {
  expect(score(92.5)).toBe('92.50');
  expect(score(0)).toBe('0.00');
  expect(score(null)).toBe('—');
});
