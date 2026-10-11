# API Integration Map

All paths below are relative to `VITE_API_BASE_URL`, normally `http://127.0.0.1:8000/api/v1`. All protected calls send `Authorization: Bearer <token>`. There are no direct database calls.

| Frontend page/feature | REST endpoint(s) | Method | Role / scope |
|---|---|---|---|
| Login | `/auth/login` | POST | Public; credentials validated by backend |
| Restore session / account identity | `/auth/me` | GET | Any authenticated active account |
| Logout | `/auth/logout` | POST | Authenticated; revokes token and handles 204 |
| Overview cards | `/students`, `/programs`, `/courses`, `/enrollments`, `/grades`, `/course-offerings` with `per_page=1` | GET | Only resources permitted for the current role; totals from `meta.total` |
| Recent records | `/students` or `/enrollments`, `sort=-created_at&per_page=5` | GET | Staff student records; instructor/student scoped enrollments |
| Students directory | `/students?search=...&program_id=...&year_level=...&status=...&sort=...&page=...&per_page=20` | GET | Admin/registrar; backend permits a student to see only their own record |
| Student create/detail/edit/delete | `/students`, `/students/{id}` | POST / GET / PATCH / DELETE | Writes admin/registrar; detail follows backend ownership rules |
| Student deactivation | `/students/{id}` with `status=INACTIVE` | PATCH | Admin/registrar; UI confirmation before request |
| Programs | `/programs`, `/programs/{id}` | GET / POST / PATCH / DELETE | Admin/registrar |
| Subjects | `/courses`, `/courses/{id}` | GET / POST / PATCH / DELETE | Linked to programs through `program_id`; admin/registrar writes; instructor reads assigned subject data |
| Academic terms | `/academic-terms`, `/academic-terms/{id}` | GET / POST / PATCH / DELETE | Admin/registrar writes; instructor reads assigned terms |
| Subject offerings | `/course-offerings`, `/course-offerings/{id}` | GET / POST / PATCH / DELETE | Admin/registrar writes; instructor reads assigned offerings |
| Offering instructor selector | `/instructors?page=...&per_page=20` | GET | Admin/registrar; only ID/name/status of active instructors |
| Class roster | `/course-offerings/{id}/students` | GET | Admin/registrar or assigned instructor |
| Enrollments | `/enrollments`, `/enrollments/{id}` | GET / POST / PATCH / DELETE | Admin/registrar writes; instructor/student read scoped records |
| Enrollment status | `/enrollments/{id}` | PATCH | Admin/registrar; dropping requires confirmation |
| Grades | `/grades`, `/grades/{id}` | GET / POST / PATCH | Assigned instructor for their own offerings; administrators for oversight. Registrar is denied with 403; student reads own grades |
| Student-specific enrollment list | `/students/{id}/enrollments` | GET | Admin/registrar or owner student |
| Student-specific grade list | `/students/{id}/grades` | GET | Assigned instructor, administrator or owner student (registrar: 403) |
| Academic record | `/students/{id}/academic-record?page=...&per_page=20` | GET | Admin/registrar or owner student; response adds per-term and overall `gwa` computed from subject grades |
| Profile account panel | `/auth/me` | GET | Current user only |
| Student profile link | `/students?per_page=1` then `/students/{id}` | GET | Student scope comes from authenticated backend |
| User accounts | `/users`, `/users/{id}` | GET / POST / PATCH / DELETE | Administrator only |
| Relationship form selectors | `/programs`, `/students`, `/courses`, `/academic-terms`, `/course-offerings`, `/enrollments` | GET | Same backend scope; paginated, with search where supported |

## Contract handling

- List screens use backend pagination metadata. Query state lives in the URL.
- PATCH excludes immutable enrollment and grade relationship IDs. Optional blank values become null; an empty password on account edit is omitted.
- API returns 201 for creation, 200 for normal retrieval/update and 204 for deletion/logout. The client never parses an empty 204 body as JSON.
- 401 clears the session and redirects to login. Login credential errors stay on the login form.
- 403 renders access denied; 404 renders not found. 409 displays the backend conflict message without discarding form values.
- 422 field errors are normalized from backend key paths and displayed next to their form controls. Root errors appear in the form alert.
- 500-class responses show a safe retry message. Network failures and 15-second timeouts exit loading and offer retry.
- Academic records paginate enrollments before grouping into terms; the UI preserves that contract and tells the reader a term can span pages. The GWA shown on the record and account pages is computed by the API (final grade × unit weight), never entered by the client, and always covers the whole record rather than the current page.
