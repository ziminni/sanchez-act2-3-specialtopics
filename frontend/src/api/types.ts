export type Role = 'ADMIN' | 'REGISTRAR' | 'INSTRUCTOR' | 'STUDENT';
export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  status: string;
}
export interface Row {
  id: number;
  [key: string]: string | number | null | undefined;
}
export interface Meta {
  page: number;
  per_page: number;
  total: number;
  last_page: number;
}
export interface Envelope<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: Meta;
}
export interface RecordCourse {
  enrollment_id: number;
  status: string;
  course_code: string;
  course_title: string;
  units: number;
  section: string;
  midterm_grade: number | null;
  final_grade: number | null;
  remarks: string | null;
}
export interface AcademicRecord {
  student_id: number;
  student_name: string;
  student_number: string;
  /** Computed by the API from each subject's final grade, weighted by units. */
  gwa: number | null;
  units: number;
  terms: {
    academic_term_id: number;
    academic_year: string;
    semester: string;
    gwa: number | null;
    units: number;
    courses: RecordCourse[];
  }[];
}
