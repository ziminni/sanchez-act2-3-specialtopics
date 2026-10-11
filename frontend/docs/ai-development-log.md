# AI Development Log — Activity 3

Tool: OpenAI Codex. This log describes engineering contributions, not private reasoning. The initial request was to implement the attached frontend laboratory as a continuation of the existing FastAPI activity.

| Task | Prompt summary | Result | Human review status | Evidence |
|---|---|---|---|---|
| Requirements and API inspection | Build Activity 3 using the supplied PDF and existing API | Mapped required modules to the current OpenAPI and roles | Pending student review | `api-integration-map.md`, backend `docs/openapi.json` |
| Framework and layout | Create a separate frontend that consumes the existing backend | React/TypeScript/Vite app; desktop shell, mobile navigation, login and overview | Pending student review | `src/main.tsx`, `src/components/Shell.tsx`, screenshots |
| API and authentication | Use real login/current-user/logout and predictable error handling | Central bearer client, session restoration, protected navigation, 401/403/error states | Pending student review; automated checks executed | `src/api/client.ts`, `src/state/Auth.tsx`, unit/E2E results |
| Resource workflows | Implement student and academic management through HTTP | Shared CRUD pages, relationship selectors, enrollment, grading and academic records | Pending student review; real API workflows exercised | `src/features/resources.ts`, `src/pages/`, E2E suite |
| Backend integration support | Enable local cross-origin requests and a safe staff instructor selector | Exact CORS allowlist and minimal read-only instructor endpoint | Pending student review; regression checks executed | `../app/main.py`, `../tests/test_api.py` |
| Validation and failures | Exercise positive, negative and restricted interactions | Inline 422 feedback, conflict preservation, confirmed destructive actions, offline/server failures | Pending student review; automated checks executed | `tests/client.test.ts`, `tests/e2e/activity3.spec.ts`, error-state screenshots |
| Debugging | Fix a failure discovered in browser testing | Corrected a race where login redirected to overview instead of the originally requested route | Pending student review; regression scenario included | `src/pages/Login.tsx`, authentication E2E test |
| Grading policy revision | Remove grading from the registrar and derive the GWA from per-subject grades, then show it in the student's account | Registrar grade endpoints return 403 while the transcript stays readable; instructors and administrators encode per-subject grades; academic records return computed per-term and overall GWA, displayed on the student's record and account pages | Implemented and verified with backend, unit and browser tests; pending student review | `../app/services.py`, `../app/main.py`, `src/pages/AcademicRecord.tsx`, `src/pages/Profile.tsx`, `docs/test-results.txt` |
| Documentation and evidence | Prepare required final outputs and a demo guide | README, architecture, integration map, this log, screenshots, production build and test output | Pending student review | `README.md`, `docs/`, `dist/` after build |

## Recorded implementation history

- `de85ade`: integrated the React client and existing FastAPI source, including the instructor directory and local CORS configuration.
- The subsequent verification/documentation commit contains the tests, screenshot evidence, setup instructions and this log. Use `git log --oneline -- Act2` from the parent repository to inspect both commits.

These are actual implementation and verification milestones from this session, not a reconstructed earlier development history. Human review remains pending.

## Student review record — complete this yourself

- Reviewer and date:
- Files reviewed:
- Explanation of the API client and token storage:
- Explanation of backend versus frontend authorization:
- Tests personally rerun and their results:
- Changes accepted, modified or rejected:
- A change you made and can demonstrate:
- Relevant commit(s):

No entry above claims that the student has already read, understood or manually verified the generated work. Record that evidence only after doing it.
