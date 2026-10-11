# Laboratory demonstration guide

Start the server using the README, open `/api/docs`, and log in as `admin@example.com` with your local seed password. Authorize with the returned token. Use new codes/numbers each time you create data. Keep track of IDs returned by create requests.

This machine's database holds a complete simulation — 9 accounts, 5 student profiles, 3 programs, 29 subjects, both 2026-2027 terms, 13 offerings, 17 enrollments and 16 grades — so most cases below can be demonstrated immediately (duplicate enrollment, grading, GWA and role denials all work on the existing records). Create additional records only where a case asks for a new code, section or ID. The Postman collection expects a freshly seeded database instead; run it against a separate seeded database file if you want its seeded-ID assertions to hold.

The Postman collection automates most of the requests below and checks expected success and failure statuses. Set its `password` variable first. It contains synthetic records and can be run locally without external services.

| Lab case | Demonstration |
|---|---|
| 1. Start API and database | `uvicorn app.main:app --reload`, then `GET /api/v1/health` |
| 2. Authenticate | `POST /api/v1/auth/login`, show access token |
| 3. Reject unauthenticated access | Remove Authorization and `GET /api/v1/students` → 401 |
| 4. Create program | `POST /api/v1/programs` with unique code and name → 201 |
| 5. Create student | `POST /api/v1/students` with required fields and program ID → 201 |
| 6. Reject invalid/duplicate student | Invalid email → 422; repeat student number → 409 |
| 7. Retrieve/update student | GET by ID, then PATCH `{"year_level":2}` |
| 8. Search/filter | `GET /api/v1/students?search=Student&program_id=1` |
| 9. Pagination/sorting | `GET /api/v1/students?sort=-last_name&page=2&per_page=10` |
| 10. Create subject and term | POST courses (a subject needs `program_id`) and academic-terms with unique code/year+semester |
| 11. Create offering | POST course-offerings with subject, term, instructor 3, section, capacity |
| 12. Enroll | POST enrollments with student and offering IDs |
| 13. Reject duplicate enrollment | Repeat that request → 409 |
| 14. Encode a subject grade | As the assigned instructor (`instructor@example.com`), POST grades for that offering's enrollment, then PATCH it. Show that the same request as `registrar@example.com` returns 403, and that sending a `gwa` field is rejected with 422. |
| 15. Academic record and GWA | GET students/{ID}/academic-record; show grouping by term plus the automatically computed unit-weighted GWA. Confirm the GWA changes when a subject grade changes and that nobody types it. |
| 16. Forbidden access | Login as student; GET students/2/academic-record → 403 |
| 17. Not found | Login as admin; GET students/99999999 → 404 |
| 18. Documentation | Show `/api/docs`, examples, error schemas and bearer security |
| 19. Tests | Run `python -m pytest` and open `docs/test-results.txt` |
| 20. Explain AI contribution | Trace student creation or instructor grade authorization; make and test a small change yourself |

## Suggested learning order

1. Read the health endpoint. Identify the decorator, URL, method, database dependency and returned dictionary.
2. Read `StudentCreate` in `schemas.py`. Change a request's year level to 0 and explain why it fails before SQL.
3. Read `Student` in `models.py` and find the unique student number and program foreign key.
4. Follow `services.save` for student creation and `validate_business` for the referenced program check.
5. Follow `current_user`, then `scoped`, and explain authentication versus authorization.
6. Read `test_student_object_level_access_and_scoped_lists` and predict its outcomes before running it.
7. Explain why a duplicate enrollment needs both a useful API error and a database unique constraint.
8. Create your own small improvement, test it, and commit that genuine development step.

## Example requests

Program:

```json
{"code":"DEMO-PROGRAM","name":"Demonstration Program"}
```

Subject (a subject belongs to a program):

```json
{"program_id":1,"course_code":"DEMO101","course_title":"REST API Development","units":3}
```

Term:

```json
{"academic_year":"2027-2028","semester":"FIRST","start_date":"2027-08-01","end_date":"2027-12-20"}
```

Offering (replace subject/term IDs with your created IDs):

```json
{"course_id":1,"academic_term_id":1,"instructor_id":3,"section":"DEMO","capacity":30}
```

Enrollment and one subject grade (replace IDs; log in as that offering's instructor to post the grade):

```json
{"student_id":1,"course_offering_id":1}
```

```json
{"enrollment_id":1,"midterm_grade":85,"final_grade":90,"remarks":"Demo grade"}
```

Never send a `gwa` field: it is rejected with 422 because the average is computed by the API from each subject's final grade, weighted by units, and returned by `GET /students/{ID}/academic-record` (per term and overall).

Always use the actual IDs returned by your server; example IDs are illustrative.
