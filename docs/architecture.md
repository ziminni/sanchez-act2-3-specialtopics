# Architecture and design decisions

## Request lifecycle

1. FastAPI matches a versioned resource route and Pydantic validates its parameters and body.
2. `get_db` provides one SQLAlchemy session for the request. Authentication and endpoint handlers share that session through dependency caching.
3. `current_user` hashes the supplied bearer token, checks its stored expiry, and loads an active user.
4. Services scope read queries by role and ownership or validate write permissions.
5. Services validate relationships and academic rules before committing. Database unique/check/foreign-key constraints are the final integrity boundary.
6. Response models expose documented fields. Central handlers format validation, HTTP and integrity errors.

## Components

`models.py` describes storage; `schemas.py` describes the public contract. They are deliberately separate: user input contains a password, the database contains a password hash, and user responses contain neither.

`main.py` registers a shared CRUD route factory and explicit authentication and academic-record routes. A factory creates ordinary FastAPI endpoints with typed request/response models for each resource. It is an abstraction worth reviewing after first following one student-create request. `services.py` owns permission rules, reference checks and mutations; handlers handle HTTP concerns.

No separate repository layer is included: SQLAlchemy already supplies a small, parameterized data-access layer. This API is the only authoritative data source; the Activity 3 React client in `frontend/` consumes it over HTTP and has no database of its own. SQLite keeps setup reproducible on a learner's computer; Alembic remains the only schema-management path.

## Authentication and authorization

Argon2id hashes passwords with per-password salts. Login generates 32 random bytes in a URL-safe token. SHA-256 of that token is stored, with expiry and a user reference. A database read on each request makes logout, account disablement and permission changes effective immediately. This trades stateless verification for simple revocation; no JWT signing secret is needed.

The read scope applies before search, pagination or aggregation. Students are linked to accounts by a unique nullable `students.user_id`. Instructors are linked to offerings by `instructor_id`. Grade access follows grade → enrollment → offering → instructor. This prevents changing a URL ID to read or edit someone else's data. Instructors receive a limited roster, not student contact details or a complete transcript.

Encoding a grade belongs to the instructor assigned to that offering, so grade reads and writes are limited to that instructor and, for oversight, administrators. The registrar role is denied grade endpoints entirely (`/grades`, `/grades/{ident}`, `/students/{ident}/grades` return 403) and instead uses the transcript, which reports each subject grade and the computed GWA. A hidden button is not a boundary: the service layer, not the client, enforces this.

New role/status/password changes revoke all existing account tokens. Administrators cannot demote, disable or delete themselves. Linked student/instructor roles cannot be changed until their assignments are removed. User management is admin-only; registrars manage academic data.

## Transactions and capacity

For SQLite, every write request takes `BEGIN IMMEDIATE` before authentication or academic reads. This serializes writers so two enrollments cannot both take the last seat. Sessions roll back on failure. A 30-second SQLite busy timeout is configured. This deliberately simple strategy is appropriate for a local lab; it reduces concurrent write throughput.

Enrollment validation also locks the offering row on database engines supporting `FOR UPDATE`. SQLite is the validated backend. Do not assume production concurrency behavior on a different engine has been tested merely because SQLAlchemy supports it.

Unique constraints handle duplicate student numbers, course/program codes, accounts, term pairs, offering sections, enrollments and grade records. Foreign keys restrict deletion so academic history cannot become orphaned. A dropped enrollment preserves its unique student/offering pair and its existing grade record.

## Validation and contract choices

Grades use percentages from 0 to 100. Each subject is graded on its own enrollment record; the instructor never enters an overall average. `GET /students/{ident}/academic-record` derives the GWA as Σ(final grade × subject units) ÷ Σ(subject units), rounded to two decimals, excluding `DROPPED` enrollments and subjects without a final grade, and returns it per term and across the whole record. Because `GradeCreate` forbids unknown fields, a submitted `gwa` is rejected with 422. Only active enrollments consume capacity. Student year level is 1–6; general statuses and roles are enumerated. Birth dates cannot be in the future. Terms have ordered dates and consecutive year labels.

PATCH merges the supplied fields with current values and revalidates the full create schema. This catches cross-field errors such as updating only a term's end date to precede its start date. Reference fields identifying an enrollment or a grade cannot be transferred by PATCH.

Collection sizes are bounded to 100, including rosters and transcript enrollment pages. Academic records group each page by term. The client must follow pagination to assemble a full record, and a term can appear on multiple pages. Search/sort column names are allowlisted; user-provided SQL is never constructed.

## Error handling and operational limits

Success envelopes contain data; error envelopes contain a message and field errors. Validation errors exclude the submitted input. Database integrity errors return generic conflicts. Unexpected error logs contain only exception class, method and path; raw SQL, bound parameters, request bodies, passwords and tokens are not logged by the application. Timestamps are UTC stored without offsets for SQLite compatibility.

CORS starts disabled. The app is prepared for local use, with no public deployment or external accounts configured. Gateway rate limiting, HTTPS, backups and operational monitoring remain deployment work. No email verification, password recovery, audit trail or refresh tokens are included because those are optional lab enhancements. The separate Activity 3 React client lives in `frontend/` and consumes this API over HTTP with an exact local CORS allowlist.

## AI contribution record

AI generated the initial application, schema migration, fixtures, automated tests, API collection and documentation. The implementation was exercised with automated API tests, migration/seed recreation checks and collection replay. The student should record their own subsequent review, corrections and understanding separately. A generated test suite is evidence for tested behavior, not a claim that all possible cases are correct.

Suggested first review: trace `POST /students` through its schema, `save`, `validate_business`, the foreign key constraint and the serialized response. Then explain how `scoped` changes a student's query and why both route-level authentication and object-level authorization are needed.
