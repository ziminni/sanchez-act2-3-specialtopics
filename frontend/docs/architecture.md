# Frontend architecture

## Application boundary

React and TypeScript render a Vite single-page application. React Router supplies browser-history routes. FastAPI remains the existing independent backend process, with all persistence, business rules and authoritative permissions. The frontend has no API server, server actions, ORM, database library or database credentials.

The only backend integration changes are an exact local CORS allowlist and a paginated minimal instructor directory for staff. The instructor directory avoids giving registrars the administrator-only `/users` endpoint. It returns no password hashes, email addresses or tokens.

## Routes and permissions

A protected route wrapper restores the session from `/auth/me` before displaying the application shell. It distinguishes missing authentication from a network failure during restoration: an unreachable API shows retry, rather than pretending the user is authenticated or silently clearing a valid token. A requested protected path is retained and restored after login.

Resource metadata describes labels, fields, columns, supported sort/filter parameters and allowed roles. Shared list, form and detail pages consume those definitions. Reference selectors load paginated records over HTTP. Specific pages handle academic records, rosters, dashboard and profile because their shapes differ from basic CRUD.

Navigation and edit controls reflect backend roles. Deep links also display access-denied states. All real reads and mutations still reach FastAPI, whose object-level authorization prevents ID substitution attacks. No claim is made that client route guards provide a security boundary.

## Authentication

The existing backend issues opaque bearer tokens. The frontend stores only the token in `sessionStorage`, so it survives a refresh within the current tab but is not stored permanently in localStorage. The current identity comes from `/auth/me`; the browser does not invent a role or decode trusted identity from unverified data.

The centralized client attaches the token. A 401 from a protected request clears it and emits an expiration event, causing the Auth context to redirect to login. An invalid login is an inline error instead. Logout calls the revocation endpoint and clears client state even if the server is unreachable, with a warning that server revocation could not be confirmed. Account role/status/password changes are checked by the backend.

`sessionStorage` is readable by JavaScript and therefore vulnerable to XSS. React escapes text; no arbitrary HTML rendering is used. For public production use, add deployment-appropriate CSP/HTTPS and evaluate an HttpOnly-cookie strategy with the backend. Tokens are not passed in URLs or logged by the frontend.

## API layer and state

`api/client.ts` owns the base URL, fetch options, authorization, JSON parsing, 204 handling, timeouts and errors. Components call `api.list/get/create/update/remove` instead of duplicating request boilerplate. Domain aggregate endpoints use the same `request` wrapper.

`useQuery` owns request data, loading, error and retry. Every query has an AbortController and changing its key cancels the previous load; aborted stale results are not applied to state. Queries are tied to resources, filters, page numbers and record IDs. This is deliberately a small hook rather than a second cache/store system.

Forms keep temporary edits locally. Lists keep search/filter/sort/page state in URL parameters. Successful creates and edits navigate to a freshly fetched detail screen; successful deletes reload the list. Data never treats browser storage as an authoritative student database.

## Validation and feedback

Client rules catch required fields, email formatting, password length and numeric ranges. The backend remains responsible for uniqueness, references, permissions, dates and academic business rules. Inputs are preserved after backend rejection. Field error paths are normalized to field names; errors are associated with controls using `aria-describedby`.

Native modal dialogs confirm hard deletion, student/reference deactivation and enrollment dropping. Dialogs support Escape and focus containment; controls disable while saving. Notifications acknowledge success without blocking navigation. Lists distinguish loading, empty, denied, not found, server failure and network failure.

## Layout and accessibility

A persistent desktop sidebar becomes a dismissible menu below 850px. Forms use two columns on wide screens and one column on narrow screens. Data tables scroll inside their panel, rather than widening the document. Semantic labels, headings, button names, a skip link, visible focus states and text status badges support keyboard and assistive use. Reduced-motion preferences are respected.

The theme uses deep green, white work surfaces and a clear typographic hierarchy. CSS uses system fallbacks if the optional Google-hosted fonts are unavailable. No imagery or animation is required to understand the data.

## Verification scope

Vitest tests request normalization, token handling, React login, validation and permission helpers. Playwright drives actual Chrome against the real FastAPI implementation on a throwaway seeded database. Browser evidence covers major modules, success/failure states, deep-link refresh and desktop/mobile layouts. Backend regression tests verify the instructor-directory and CORS changes as well as the original API behavior.

The AI-generated code and tests still require the student's human review and technical defense. Automated evidence cannot demonstrate personal understanding.
