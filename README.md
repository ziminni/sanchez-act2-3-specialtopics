# Student Information Management API

A backend-only FastAPI project for the AI-Assisted REST API Laboratory. It includes student and academic record management, authentication, role and object permissions, relational constraints, seed data, Swagger documentation, and automated tests.

## Start the prepared project on this machine

The virtual environment and seeded SQLite database have already been prepared in this folder.

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/api/docs**. Use `POST /api/v1/auth/login` with `admin@example.com` and the generated `SEED_PASSWORD` in your local `.env` file. Copy `data.access_token`, click **Authorize**, and paste only the token. Try `GET /api/v1/students`.

`.env` is private local configuration and is excluded from Git. These are synthetic demonstration accounts, not real student accounts.

## Set up on another machine

Requires **Python 3.12 or newer**, pip, and a terminal. SQLite comes with Python; no separate database server is needed. The tested dependency versions are in `requirements.lock.txt`; `requirements.txt` lists direct dependency ranges.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
cp .env.example .env
```

On Windows use `py -3.12 -m venv .venv` and `.venv\Scripts\Activate.ps1`. The lock marks `uvloop` as Unix-only, so Windows skips that optional accelerator.

Set `SEED_PASSWORD` in `.env` to a demonstration password of at least 12 characters. Then:

```bash
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The seeder requires an empty migrated database and refuses to change existing data. It creates exactly **5 users, 3 programs, 100 students, 20 courses, 2 terms, 20 offerings, 200 enrollments, and 100 grades** in one transaction. To use a separate fresh database without deleting anything, set a different SQLite filename in `.env`, migrate, and seed it.

This machine's development database holds a complete, self-consistent simulation: 9 accounts with real names, 5 linked students, 3 programs (BSIT, BSCS, BSIS) with 29 subjects, the 2026-2027 FIRST and SECOND terms, 13 subject offerings split between the two instructors, 17 enrollments and 16 grades — so every role has realistic data to demonstrate, including computed GWAs. Four scripts maintain it and each is safe to re-run: `scripts/clear_demo_data.py --yes` removes records (copying the SQLite file to a timestamped backup first), `scripts/seed_catalog.py` writes programs and subjects, `scripts/seed_accounts.py` writes the accounts and their student links, and `scripts/seed_simulation.py` writes terms, offerings, enrollments and grades — all through the same service layer the API uses. Because accounts already exist, `app.seed` refuses to run against this database, so the full laboratory seeder can never silently replace real records.

## Accounts and access

All accounts use the local `SEED_PASSWORD` at the time they are created or re-initialized. Editing that environment variable later does not change existing account passwords; run `python scripts/seed_accounts.py` to reset them.

| Name | Email | Role | Access |
|---|---|---|---|
| Rafael Antonio Mercado | admin@example.com | ADMIN | All resources and user administration; may also encode grades |
| Lucia Maribel Fernandez | registrar@example.com | REGISTRAR | Manage student and academic resources; no grading, no user administration |
| Miguel Angelo Villanueva | instructor@example.com | INSTRUCTOR | Read assigned offerings, subjects, terms, enrollments and rosters; encode grades for their own offerings |
| Teresa Corazon Bautista | instructor2@example.com | INSTRUCTOR | Same rules, with a separate set of offerings |
| Ana Lourdes Dela Cruz | student@example.com | STUDENT | Own profile, enrollments, grades, academic record and computed GWA; linked to student 2026-00101 |
| Juan Carlo Santos | student2@example.com | STUDENT | Same student scope; linked to 2026-00102 |
| Maria Sofia Reyes | student3@example.com | STUDENT | Same student scope; linked to 2026-00103 |
| Paolo Miguel Garcia | student4@example.com | STUDENT | Same student scope; linked to 2026-00104 |
| Beatrice Anne Lim | student5@example.com | STUDENT | Same student scope; linked to 2026-00105 |

An instructor's roster contains names and student numbers, not contact details. Instructors cannot retrieve complete student profiles or academic records. Students cannot browse other students or catalogs. Filtering and pagination happen after permission scoping.

Grading is the assigned instructor's task, so the registrar role has no grade access at all: `/grades`, `/grades/{ident}` and `/students/{ident}/grades` return 403. Registrars keep full access to `/students/{ident}/academic-record`, which shows each subject's grade together with the computed GWA. Administrators retain grade access as an oversight and support path.

`python scripts/seed_accounts.py` creates or re-initializes these nine accounts: it applies the real names above, sets each password to the local `SEED_PASSWORD`, revokes stored sessions and links the five student accounts to five sample students distributed across BSIT, BSCS and BSIS. Repeat runs are safe, so any role can be signed in and demonstrated without inventing data by hand.

## Technology and layout

| File | What to learn from it |
|---|---|
| `app/main.py` | HTTP routes, dependency injection, response handling and OpenAPI |
| `app/models.py` | SQLAlchemy tables, keys, indexes and constraints |
| `app/schemas.py` | Pydantic request validation and response contracts |
| `app/services.py` | Permissions, CRUD operations and academic business rules |
| `app/security.py` | Argon2 password hashing and bearer token verification |
| `app/database.py` | Database connections and request transactions |
| `app/config.py` | Environment configuration |
| `app/seed.py` | Repeatable synthetic data generation |
| `migrations/` | Versioned Alembic schema changes |
| `tests/` | Positive, negative, security and reproducibility tests |
| `docs/` | ERD, architecture notes, demo guide, OpenAPI and Postman collection |

The flow is **HTTP request → Pydantic validation → authentication → service permission/business checks → SQLAlchemy/database → response**. Shared CRUD endpoints use one route factory to avoid duplicating HTTP plumbing. Resource-specific behavior stays in the service layer.

## API usage

Interactive Swagger UI: `/api/docs`. ReDoc: `/api/redoc`. OpenAPI JSON: `/openapi.json`. The exported specification is `docs/openapi.json`.

Base URL: `http://127.0.0.1:8000/api/v1`.

| Resource | Operations |
|---|---|
| `/auth/login`, `/auth/logout`, `/auth/me` | POST login, POST logout, GET current user |
| `/users` | Admin list/create; GET/PATCH/DELETE `/{ident}` |
| `/programs`, `/students`, `/courses`, `/academic-terms`, `/course-offerings` | GET list, POST create; GET/PATCH/DELETE `/{ident}` |
| `/enrollments` | GET list, POST create; GET/PATCH/DELETE `/{ident}` |
| `/grades` | GET list, POST create; GET/PATCH `/{ident}` |
| `/students/{ident}/enrollments` | GET own/authorized enrollments |
| `/students/{ident}/grades` | GET own/authorized grades (registrar: 403) |
| `/students/{ident}/academic-record` | GET records grouped by term, with each subject grade and the computed GWA |
| `/course-offerings/{ident}/students` | GET authorized roster |
| `/instructors` | GET minimal active-instructor directory for admin/registrar offering forms |
| `/health` | GET database connectivity check |

`PATCH` is the supported update method; `PUT` is not implemented. Omitted fields keep their current values. Explicit null is accepted only for nullable fields. Request bodies reject unknown fields.

Success responses have `success`, `message`, and `data`; lists also have `meta` with `page`, `per_page`, `total`, `last_page`. Errors have `success: false`, `message`, and `errors`. Creation returns 201, normal reads/updates 200, deletes/logout 204, missing authentication 401, forbidden access 403, missing records 404, conflicts 409 and invalid input 422. Malformed JSON follows FastAPI validation semantics (422). Unexpected errors return a safe 500.

Example student request:

```json
{
  "student_number": "2026-00101",
  "first_name": "Maria",
  "last_name": "Reyes",
  "email": "maria@example.com",
  "program_id": 1,
  "year_level": 1
}
```

Example collection query:

```text
GET /api/v1/students?search=Student&program_id=1&year_level=1&status=ACTIVE&sort=-last_name&page=1&per_page=10
```

Search is a case-insensitive literal substring; `%` and `_` are escaped. Sort uses a column name, with `-` for descending; allowed columns are `id`, timestamps, and that resource's search/filter columns. Ties use `id`. All lists default to 20 records and cap `per_page` at 100. Unknown or unsupported filters/sort columns return 422.

| Resource | Search fields | Filters |
|---|---|---|
| users | name, email | role, status |
| programs | code, name | status |
| students | student_number, first_name, last_name | program_id, year_level, status |
| courses | course_code, course_title | program_id, status |
| academic-terms | academic_year, semester | status |
| course-offerings | section, schedule, room | course_id, academic_term_id, instructor_id, status |
| enrollments | none | student_id, course_offering_id, status |
| grades | remarks | enrollment_id |

Nested endpoints accept `page` and `per_page`. Academic records paginate enrollments before grouping by term, so one term may span pages; retrieve all pages for the full record.

## Domain rules

- Roles: `ADMIN`, `REGISTRAR`, `INSTRUCTOR`, `STUDENT`.
- General status: `ACTIVE`, `INACTIVE`. Enrollment status: `ENROLLED`, `DROPPED`, `COMPLETED`.
- Year levels: 1–6. Course units: greater than 0 and at most 12.
- Terms: `FIRST`, `SECOND`, `SUMMER`; academic year uses consecutive years such as `2026-2027`. End date cannot precede start date.
- Grade scale: **0–100 inclusive**. Midterm and final grades are optional until encoded. Instructors and administrators enter a grade for each subject separately; a GWA is never submitted by a client.
- **GWA is derived, not encoded.** `GET /students/{ident}/academic-record` returns `gwa` and `units` per term and across the whole record, computed as Σ(final grade × subject units) ÷ Σ(subject units) and rounded to two decimals. `DROPPED` enrollments and subjects without a final grade are excluded, so the value always matches the stored subject grades. Student responses reject an unknown `gwa` field with 422.
- A student's optional `user_id` must refer to a STUDENT account and is unique. Student numbers, program codes, course codes, user emails, term year/semester pairs, and offering course/term/section combinations are unique.
- One enrollment per student/offering, including dropped enrollments. Reactivate an existing enrollment rather than creating a duplicate. Each enrollment has at most one grade record.
- Active enrollment requires an active student and offering with space. Only `ENROLLED` records consume capacity. Capacity cannot be lowered below the current count.
- Enrollment student/offering and grade enrollment links cannot be changed. An offering with enrollments cannot change its course or term. Reassigning its instructor transfers grade access to the new instructor.
- Grades cannot be edited for dropped enrollments. Existing grades remain for history.
- DELETE physically removes an unreferenced record. Foreign keys reject deletion of referenced academic records with 409. Use status changes for deactivation or dropping an enrollment. Grades have no delete endpoint.

## Tests, collection and migrations

```bash
python -m pytest
python -m app.export_docs
alembic check
python scripts/seed_catalog.py          # add the program/subject catalog, skipping existing codes
python scripts/seed_accounts.py         # create or re-initialize the nine accounts and their student links
python scripts/seed_simulation.py       # add terms, offerings, enrollments and instructor-encoded grades
python scripts/clear_demo_data.py --yes # remove records, keeping the accounts
```

Tests use isolated databases and do not alter the development database. They cover authentication/logout/expiry, CRUD, validation, duplicate constraints, scoped permissions, capacity, per-subject grade encoding, registrar grade denial, computed GWA arithmetic (unit weighting, dropped and ungraded exclusion), query behavior, safe errors, migrations, seed counts and the Postman request sequence. `docs/test-results.txt` records the verified run.

Import `docs/postman_collection.json` into Postman. Set the collection variable `password` to the local seed password and run folders in order. Tokens and created IDs are captured automatically. Negative requests intentionally assert 401/403/404/409/422. The collection creates additional synthetic records; repeat runs use unique identifiers. It expects a **freshly seeded** database because it asserts seeded records (for example academic term 1 and the second instructor's offering), so point `DATABASE_URL` at a separate seeded database file before running it against this machine, whose database now contains accounts only.

For a schema change: edit the models, run `alembic revision --autogenerate -m "Describe change"`, review the migration, then run `alembic upgrade head` and the tests. Migrations are explicit snapshots; the server does not silently create tables.

## Security and operational scope

Passwords use Argon2id through pwdlib. Login returns a cryptographically random opaque bearer token; only its SHA-256 digest is stored in the database. Tokens expire after `TOKEN_TTL_MINUTES` (default 120). Logout deletes the token. Password, status or role updates revoke that account's existing tokens. Every authenticated request checks the current account status and role.

This is a local laboratory application. The supplied `.env.example` lists explicit localhost frontend origins; configure deployment origins in `.env` if needed. Before public hosting, add HTTPS, login rate limits at a trusted gateway, a database backup policy, and deployment-specific configuration. SQLite is the tested database; other database engines would require their driver and integration testing. Database errors, input bodies, passwords and tokens are not included in error logs.

## Learning and AI assistance

Read `docs/architecture.md`, `docs/erd.md`, and `docs/demo-guide.md`. AI assisted with implementation, migrations, seed generation, tests and documentation. Automated tests verify the listed flows; you still need to review the code and practice explaining and modifying it. Do not claim manual review or demonstration steps until you have done them yourself.

This folder belongs to the existing parent Git repository. Activity 3 records the implementation and its verification/documentation in separate local commits on `codex/activity3-frontend`. Continue that history with your actual human review, fixes and improvements; no earlier development timeline or human review has been fabricated.

References: [FastAPI security documentation](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) and [SQLAlchemy ORM guide](https://docs.sqlalchemy.org/en/20/orm/quickstart.html).

## Activity 3 frontend

A separate React + TypeScript frontend is now available in `frontend/`. See [frontend/README.md](frontend/README.md) for installation, API/CORS configuration, tests and production builds.

Start this FastAPI server on port 8000, then run `npm run dev` from `frontend/` and open http://127.0.0.1:5173. The frontend uses the same seeded accounts and actual API. The backend's local CORS allowlist and a restricted instructor directory support this integration.

The frontend includes its own API integration map, architecture note, AI development log, 20-step demo guide, automated browser tests and screenshot evidence. No frontend database or replacement backend was introduced.
