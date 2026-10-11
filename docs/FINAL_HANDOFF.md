# Final handoff — Activities 2 and 3

## Completed and verified

- Existing FastAPI backend and separate React frontend are connected over HTTP.
- Local frontend: http://127.0.0.1:5173
- Backend documentation: http://127.0.0.1:8000/api/docs
- All five demo accounts successfully authenticated against the running backend using the current private `.env` password. Verification sessions were revoked afterward.
- Required seed counts are present: 5 users, 3 programs, 100 students, 20 courses, 2 terms, 20 offerings, 200 enrollments, 100 grades.
- Demonstration data was cleared and replaced with a real simulation: 9 accounts (1 administrator, 1 registrar, 2 instructors, 5 students), 5 student profiles (2026-00101 to 2026-00105), 3 programs, 29 subjects, the 2026-2027 FIRST and SECOND terms, 13 offerings, 17 enrollments and 16 grades. `scripts/clear_demo_data.py --yes` wrote a timestamped SQLite backup before clearing; `seed_catalog.py`, `seed_accounts.py` and `seed_simulation.py` rebuilt the data through the service layer, and `app.seed` still refuses to run because accounts exist.
- Every account was verified to sign in. Computed GWAs match hand-calculated values for all five students (Ana 90.00 over 9 units, Juan 82.00, Maria 92.50, Paolo 88.00, Beatrice 90.00 with a dropped subject excluded), second-term in-progress subjects are excluded, registrar grade requests still return 403, and rosters expose no contact details.
- Public `.env.example` has an empty seed password; the private working `.env` is excluded from Git and packaging.
- Backend, frontend unit/component and browser integration results are recorded in the existing evidence files.
- Production frontend output is included in the submission archive.
- Source, migrations, seed scripts, API collection, ERD, API integration map, architecture, AI contribution logs and screenshot evidence are included.
- Implementation and verification work are recorded in local Git commits. No remote submission has been made.

## Login

Use `admin@example.com` and the `SEED_PASSWORD` value in the private backend `.env`. Do not edit `.env.example` to change a working account password. Existing account passwords change only through an account update or a deliberate database reseed.

## Submission package

`output/Activities-2-and-3-submission.zip` contains both applications, documentation, tests, screenshot evidence and frontend production output. It omits private environment files, the local database, installed dependencies and browser traces.

Regenerate it after changes:

```bash
npm --prefix frontend run build
python scripts/package_submission.py
```

A recipient follows the root and frontend READMEs, supplies a new private seed password, installs dependencies, migrates and seeds the database, then runs both applications. The archive includes a text record of relevant Git history; the actual Git repository remains in the parent project.

## Steps only the student can complete

1. Read the code and complete the human-review section in `frontend/docs/ai-development-log.md` with your own observations. It has not been falsely marked complete by AI.
2. Rehearse `docs/demo-guide.md` and `frontend/docs/demo-guide.md`, including a small code modification you can explain.
3. Upload the archive and/or repository through the instructor's specified submission channel. That destination has not been provided here.

All available implementation and verification work is complete; personal understanding, the live demonstration and the actual course submission cannot be performed on the student's behalf.
