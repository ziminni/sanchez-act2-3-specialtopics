import type { Role, Row } from '../api/types';
export type Resource =
  | 'students'
  | 'programs'
  | 'courses'
  | 'academic-terms'
  | 'course-offerings'
  | 'enrollments'
  | 'grades'
  | 'users';
export interface Field {
  key: string;
  label: string;
  type?: 'text' | 'email' | 'number' | 'date' | 'textarea' | 'password';
  required?: boolean;
  options?: string[];
  ref?: string;
  min?: number;
  max?: number;
  step?: number;
  maxLength?: number;
  help?: string;
  immutable?: boolean;
  default?: string | number;
}
interface Definition {
  title: string;
  singular: string;
  description: string;
  fields: Field[];
  columns: string[];
  roles: Role[];
  filters: string[];
  sort: string[];
  search: boolean;
}
const staff: Role[] = ['ADMIN', 'REGISTRAR'];
const status: Field = {
  key: 'status',
  label: 'Status',
  options: ['ACTIVE', 'INACTIVE'],
  required: true,
  default: 'ACTIVE',
};
const description: Field = {
  key: 'description',
  label: 'Description',
  type: 'textarea',
  maxLength: 5000,
};
export const resources: Record<Resource, Definition> = {
  students: {
    title: 'Students',
    singular: 'student',
    description: 'Manage student profiles and their academic information.',
    roles: [...staff, 'STUDENT'],
    search: true,
    filters: ['program_id', 'year_level', 'status'],
    sort: ['last_name', 'student_number', 'created_at', 'year_level'],
    columns: ['student_number', 'name', 'program_id', 'year_level', 'status'],
    fields: [
      { key: 'student_number', label: 'Student number', required: true, maxLength: 30 },
      { key: 'program_id', label: 'Program', ref: 'programs', required: true },
      { key: 'first_name', label: 'First name', required: true, maxLength: 100 },
      { key: 'last_name', label: 'Last name', required: true, maxLength: 100 },
      { key: 'middle_name', label: 'Middle name', maxLength: 100 },
      { key: 'suffix', label: 'Suffix', maxLength: 20 },
      { key: 'email', label: 'Email address', type: 'email' },
      { key: 'birth_date', label: 'Birth date', type: 'date' },
      { key: 'contact_number', label: 'Contact number', maxLength: 30 },
      {
        key: 'year_level',
        label: 'Year level',
        type: 'number',
        min: 1,
        max: 6,
        required: true,
        default: 1,
      },
      status,
      {
        key: 'user_id',
        label: 'Linked student account ID',
        type: 'number',
        min: 1,
        help: 'Optional. Link an existing account with the Student role.',
      },
      { key: 'address', label: 'Address', type: 'textarea', maxLength: 2000 },
    ],
  },
  programs: {
    title: 'Programs',
    singular: 'program',
    description: 'Academic pathways offered by your institution.',
    roles: staff,
    search: true,
    filters: ['status'],
    sort: ['code', 'name', 'created_at'],
    columns: ['code', 'name', 'description', 'status'],
    fields: [
      { key: 'code', label: 'Program code', required: true, maxLength: 30 },
      { key: 'name', label: 'Program name', required: true, maxLength: 150 },
      description,
      status,
    ],
  },
  courses: {
    title: 'Subjects',
    singular: 'subject',
    description: 'Maintain the subject catalog and unit information.',
    roles: [...staff, 'INSTRUCTOR'],
    search: true,
    filters: ['program_id', 'status'],
    sort: ['course_code', 'course_title', 'created_at'],
    columns: ['course_code', 'course_title', 'program_id', 'units', 'status'],
    fields: [
      { key: 'program_id', label: 'Program', ref: 'programs', required: true },
      { key: 'course_code', label: 'Subject code', required: true, maxLength: 30 },
      { key: 'course_title', label: 'Subject title', required: true, maxLength: 150 },
      {
        key: 'units',
        label: 'Units',
        type: 'number',
        min: 0.5,
        max: 12,
        step: 0.5,
        required: true,
        default: 3,
      },
      description,
      status,
    ],
  },
  'academic-terms': {
    title: 'Academic terms',
    singular: 'academic term',
    description: 'Organize academic years, semesters, and their dates.',
    roles: staff,
    search: true,
    filters: ['status'],
    sort: ['academic_year', 'semester', 'created_at'],
    columns: ['academic_year', 'semester', 'start_date', 'end_date', 'status'],
    fields: [
      {
        key: 'academic_year',
        label: 'Academic year',
        required: true,
        help: 'Consecutive years, for example 2026-2027.',
      },
      {
        key: 'semester',
        label: 'Semester',
        options: ['FIRST', 'SECOND', 'SUMMER'],
        required: true,
      },
      { key: 'start_date', label: 'Start date', type: 'date', required: true },
      { key: 'end_date', label: 'End date', type: 'date', required: true },
      status,
    ],
  },
  'course-offerings': {
    title: 'Subject offerings',
    singular: 'subject offering',
    description: 'Connect subjects, faculty, and students for each term.',
    roles: staff,
    search: true,
    filters: ['academic_term_id', 'status'],
    sort: ['section', 'created_at'],
    columns: ['course_id', 'section', 'academic_term_id', 'instructor_id', 'capacity', 'status'],
    fields: [
      { key: 'course_id', label: 'Subject', ref: 'courses', required: true },
      { key: 'academic_term_id', label: 'Academic term', ref: 'academic-terms', required: true },
      { key: 'instructor_id', label: 'Instructor', ref: 'instructors', required: true },
      { key: 'section', label: 'Section', required: true, maxLength: 30 },
      {
        key: 'schedule',
        label: 'Schedule',
        maxLength: 200,
        help: 'For example Monday 09:00–10:30.',
      },
      { key: 'room', label: 'Room', maxLength: 50 },
      {
        key: 'capacity',
        label: 'Capacity',
        type: 'number',
        required: true,
        min: 1,
        max: 1000,
        default: 30,
      },
      status,
    ],
  },
  enrollments: {
    title: 'Enrollments',
    singular: 'enrollment',
    description: 'Track subject registrations and enrollment status.',
    roles: staff,
    search: false,
    filters: ['status'],
    sort: ['created_at', 'enrollment_date', 'student_id'],
    columns: ['student_id', 'course_offering_id', 'enrollment_date', 'status'],
    fields: [
      { key: 'student_id', label: 'Student', ref: 'students', required: true, immutable: true },
      {
        key: 'course_offering_id',
        label: 'Subject offering',
        ref: 'course-offerings',
        required: true,
        immutable: true,
      },
      {
        key: 'enrollment_date',
        label: 'Enrollment date',
        type: 'date',
        required: true,
        default: new Date().toISOString().slice(0, 10),
      },
      {
        key: 'status',
        label: 'Status',
        options: ['ENROLLED', 'DROPPED', 'COMPLETED'],
        required: true,
        default: 'ENROLLED',
      },
    ],
  },
  grades: {
    title: 'Grades',
    singular: 'grade',
    description: 'View academic performance and record authorized grades.',
    // Grading is the assigned instructor's task; the registrar has no grade access.
    roles: ['ADMIN', 'INSTRUCTOR'],
    search: true,
    filters: [],
    sort: ['created_at', 'enrollment_id'],
    columns: ['enrollment_id', 'midterm_grade', 'final_grade', 'remarks'],
    fields: [
      {
        key: 'enrollment_id',
        label: 'Enrollment',
        ref: 'enrollments',
        required: true,
        immutable: true,
      },
      {
        key: 'midterm_grade',
        label: 'Midterm grade',
        type: 'number',
        min: 0,
        max: 100,
        step: 0.01,
        help: 'Percentage from 0 to 100. Leave blank if not yet encoded.',
      },
      {
        key: 'final_grade',
        label: 'Final grade',
        type: 'number',
        min: 0,
        max: 100,
        step: 0.01,
        help: 'Percentage from 0 to 100.',
      },
      { key: 'remarks', label: 'Remarks', type: 'textarea', maxLength: 250 },
    ],
  },
  users: {
    title: 'User accounts',
    singular: 'user account',
    description: 'Manage access to the academic workspace.',
    roles: ['ADMIN'],
    search: true,
    filters: ['role', 'status'],
    sort: ['name', 'email', 'created_at'],
    columns: ['name', 'email', 'role', 'status'],
    fields: [
      { key: 'name', label: 'Full name', required: true, maxLength: 120 },
      { key: 'email', label: 'Email address', type: 'email', required: true },
      {
        key: 'password',
        label: 'Password',
        type: 'password',
        required: true,
        maxLength: 128,
        help: 'At least 12 characters. Leave blank when editing to keep the current password.',
      },
      {
        key: 'role',
        label: 'Role',
        required: true,
        options: ['ADMIN', 'REGISTRAR', 'INSTRUCTOR', 'STUDENT'],
      },
      status,
    ],
  },
};
// Enrollment dates are not a backend sort key: use the supported creation timestamp.
resources.enrollments.sort = ['created_at', 'student_id', 'status'];
// Instructors only see the subjects they teach, so their list reads as their own.
export function titleFor(resource: Resource, role: Role) {
  return resource === 'courses' && role === 'INSTRUCTOR'
    ? 'My subjects'
    : resources[resource].title;
}
export function canWrite(resource: Resource, role: Role) {
  if (resource === 'users') return role === 'ADMIN';
  // The assigned instructor encodes each subject grade; administrators keep oversight.
  if (resource === 'grades') return role === 'ADMIN' || role === 'INSTRUCTOR';
  return staff.includes(role);
}
export function canDelete(resource: Resource, role: Role) {
  return resource !== 'grades' && canWrite(resource, role) && role !== 'INSTRUCTOR';
}
export function labelFor(resource: string, row: Row): string {
  if (resource === 'students') return `${row.student_number} · ${row.first_name} ${row.last_name}`;
  if (resource === 'programs') return `${row.code} · ${row.name}`;
  if (resource === 'courses') return `${row.course_code} · ${row.course_title}`;
  if (resource === 'academic-terms')
    return `${row.academic_year} · ${String(row.semester).toLowerCase()} semester`;
  if (resource === 'course-offerings')
    return `${row.course_code} · ${row.course_title} · ${row.term_name} · Section ${row.section}`;
  if (resource === 'enrollments' || resource === 'grades')
    return `${row.student_name} · ${row.course_code} ${row.course_title} · ${row.term_name}`;
  return String(row.name || row.email || 'this record');
}
// Readable names the API adds for referenced records, plus related-list columns.
const columnLabels: Record<string, string> = {
  student_name: 'Student',
  student_number: 'Student number',
  course_code: 'Subject code',
  course_title: 'Subject',
  term_name: 'Term',
  section: 'Section',
  instructor_name: 'Instructor',
  program_name: 'Program',
  first_name: 'First name',
  last_name: 'Last name',
  enrollment_date: 'Enrollment date',
  enrollment_status: 'Status',
  midterm_grade: 'Midterm grade',
  final_grade: 'Final grade',
  remarks: 'Remarks',
  status: 'Status',
};
export function columnLabel(key: string) {
  return columnLabels[key] || key.replaceAll('_', ' ');
}
export function fieldLabel(resource: Resource, key: string) {
  return key === 'id'
    ? 'ID'
    : key === 'name'
      ? 'Name'
      : resources[resource].fields.find((field) => field.key === key)?.label || columnLabel(key);
}
