# Activity 3 — Campus frontend

Campus is a React + TypeScript frontend for the existing Student Information Management FastAPI application in the parent directory. The two applications are logically separate. All authoritative student, subject, enrollment and grade data comes from the existing REST API over HTTP. The frontend has no database connection, replacement API, or mock application data.

## Requirements

- Node.js 20.19+ and npm (tested with Node 26).
- The existing Activity 2 backend with Python 3.12+, its dependencies, migrations and seed data.
- Chrome for the configured Playwright browser tests. On a machine without Chrome, install Playwright Chromium and remove `channel: 'chrome'` from `playwright.config.ts`.

## Run both applications

From the backend project root:

```bash
source .venv/bin/activate
# First-time setup only, if needed:
# python -m pip install -r requirements.lock.txt
# cp .env.example .env
# Set your own SEED_PASSWORD in .env, then:
# alembic upgrade head
# python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open **http://127.0.0.1:5173**. Log in with `admin@example.com` and the password from the backend's local `SEED_PASSWORD` used during seeding. No demo password is built into the frontend. Other demo accounts are `registrar@example.com`, `instructor@example.com`, `instructor2@example.com`, and the five linked students `student@example.com`, `student2@example.com`, `student3@example.com`, `student4@example.com` and `student5@example.com`.

If the backend is already listening on port 8000, use that process rather than starting a second one. Restart it after changing environment configuration.

### API and CORS configuration

`frontend/.env.example` provides:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

`VITE_` values are public and embedded at build time. Never put passwords, database credentials, signing keys or private service tokens there. The frontend `.env` is separate from the backend `.env`.

The backend's `.env.example` now allows these specific local browser origins:

```dotenv
CORS_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173","http://127.0.0.1:4173","http://localhost:4173"]
```

Copy that CORS setting into an existing backend `.env` when installing elsewhere. Use an exact origin including the port, not a wildcard. The server accepts `Authorization` and `Content-Type` headers for the existing GET/POST/PATCH/DELETE operations. A tiny read-only `/api/v1/instructors` endpoint allows registrars to choose active instructors without exposing user administration or account secrets. The authoritative backend and database remain the same.

## Available screens

- Login, session expiration, logout and protected application shell.
- Overview populated from API totals and recent records.
- Student search, program/year/status filters, sort, pagination, detail, create, edit, delete and confirmed deactivation.
- Programs, subjects and academic terms with authorized maintenance.
- Subject offerings with paginated subject, term and instructor selectors; class rosters.
- Enrollments with student/offering selectors, duplicate feedback and status changes.
- Grades with enrollment selectors and 0–100 validation; the assigned instructor or an administrator encodes each subject grade.
- Academic records grouped by term using the aggregate endpoint, showing each subject grade plus the automatically computed GWA.
- Account profile and administrator-only user management.

| Role | UI scope |
|---|---|
| Administrator | All modules and user management; may also encode grades |
| Registrar | Academic management and read-only transcripts; no Grades module, no grade API, no user administration |
| Instructor | Assigned subjects/terms/offerings, rosters, enrollments and grades for their own offerings |
| Student | Own enrollments, grades, academic record, computed GWA and linked student profile |

Role-aware UI improves usability. The backend still independently rejects unauthorized operations. Foreign-key IDs shown in tables identify the corresponding backend records; forms provide labeled selectors for relationships.

## Build and serve the distributable

```bash
npm run build
npm run preview
```

The production build is generated in **`dist/`**, with its `index.html` and bundled assets. Preview it at **http://127.0.0.1:4173** while the backend remains running. The submitted code can reproduce this output with `npm ci && npm run build`.

For future hosting, configure a reachable HTTPS API base URL before building and add the frontend's exact HTTPS origin to backend CORS. Configure the static host to serve `index.html` for unknown application paths (SPA fallback), so refreshing `/students/1` works. Upload only `dist/`. Hosting the frontend alone will not make your localhost API available online. No online deployment is required for this local lab deliverable.

## Tests and code quality

```bash
npm test                 # API-client, authentication component and validation tests
npm run test:e2e         # Chrome integration tests against the actual FastAPI app
npm run typecheck
npm run format:check
npm run build
```

Run backend regression tests from the project root with `python -m pytest`.

Browser tests start the real backend on port 8001 with a freshly migrated and seeded **temporary database**, plus a frontend on port 5174. They do not alter your development database. They run positive and negative login, student CRUD, reference-data creation, enrollment/grade workflows, role restrictions, routing and mobile-layout checks. Slow, offline and 500 responses are deliberately injected by Playwright to exercise controlled failure states; core operations use the actual API.

The test password in `tests/start_backend.py` is only for throwaway synthetic accounts. It is not a real credential and is never bundled into the app. Test traces can contain session tokens; `test-results/` and `playwright-report/` are ignored by Git and should not be submitted publicly.

Screenshots are saved in `docs/evidence/`. Test results are recorded in `docs/unit-test-results.txt` and `docs/e2e-results.txt`; backend results are in `../docs/test-results.txt`.

## Source structure

```text
src/
  api/             HTTP client, normalized errors, API contracts
  state/           Auth context and cancellable server-query hook
  components/      Shell, controls, dialogs, pagination and notifications
  features/        Resource definitions, permission helpers and validation
  pages/           Login, dashboard, CRUD pages, academic record and profile
  styles/          Shared responsive design system
```

Start with `src/api/client.ts`, then `src/state/Auth.tsx`, then `src/pages/ResourceList.tsx` and `src/pages/ResourceForm.tsx`. Resource metadata in `src/features/resources.ts` drives shared pages; this keeps the same validation and interaction patterns across the eight resources.

## Required supporting documents

- `docs/api-integration-map.md` — pages, endpoints, HTTP methods and permissions.
- `docs/architecture.md` — routing, authentication, API layer and state choices.
- `docs/ai-development-log.md` — AI contributions and explicit human-review status.
- `docs/demo-guide.md` — all 20 live demonstration cases.
- `docs/evidence/README.md` — screenshot index and verification scope.

Human review and the live technical defense remain your responsibility. Practice explaining how a token reaches the backend, why a hidden button is not authorization, and how pagination and server validation work.
