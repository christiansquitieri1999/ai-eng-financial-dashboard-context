# Project Memory Bank

**Status checked:** 2026-11-03
**Purpose:** evidence-backed working context for contributors and coding agents. This is a snapshot of the repository, not a product specification or an approved roadmap. Update it when source, configuration, or verified test results change.

## Product Overview

The repository describes a **Financial Metrics Dashboard** with a React + TypeScript single-page frontend and a FastAPI backend. The current page requests financial movements, computes KPIs and monthly aggregates in the browser, and renders KPI cards and two charts. The backend returns deterministic mock movements generated in memory; no database, persistence layer, or external financial-data integration is present in the checked application path.

Evidence: [README](../README.md), [frontend App](../frontend/src/App.tsx), [frontend calculations](../frontend/src/lib/financial-utils.ts), [backend routes and generator](../backend/app/routes.py).

### What is implemented

- The browser requests `GET /api/metrics`; it computes income, outcome, profit, profit percentage, and monthly chart data client-side.
- The backend provides `/health` and eight metrics routes: movements, facets, summary, top categories, comparison, alerts, B2B movements, and B2C movements.
- Backend mock generation is seeded with `42` at the route call sites and returns 360 movements. Generated dates are relative to the current date; the dashboard header is currently hard-coded to `2024 - Full Year`.
- Docker Compose defines frontend and backend development services. Host ports are `5173` for the frontend, `8001` for the backend (container port `8000`), and `5678` for debugpy.

Evidence: [App](../frontend/src/App.tsx), [financial utilities](../frontend/src/lib/financial-utils.ts), [backend routes](../backend/app/routes.py), [Compose configuration](../docker-compose.yml), [frontend Vite configuration](../frontend/vite.config.ts).

## Technology Stack

| Area | Current repository evidence |
| --- | --- |
| Frontend language and UI | TypeScript; React and React DOM `^19.2.4` |
| Frontend build and tests | Vite `^8.0.4`; Vitest `^4.1.4`; TypeScript `~6.0.2`; ESLint 9 |
| Frontend charts and styling | Recharts `^3.8.1`; Tailwind CSS `^4.2.2`; `lucide-react`; `clsx`, `tailwind-merge`, and `class-variance-authority` |
| Backend language and API | Python; FastAPI; Pydantic models; Uvicorn |
| Backend test/debug tooling | pytest, pytest-cov, httpx, debugpy |
| Containers and local orchestration | Dockerfiles use `python:3.13-slim` and `node:24-alpine`; Docker Compose runs both development services |
| Dependency declarations | Frontend dependencies are declared in `frontend/package.json` with `frontend/package-lock.json` present. Backend dependencies are listed without version pins in `backend/requirements.txt`. |

Evidence: [frontend package manifest](../frontend/package.json), [frontend lockfile](../frontend/package-lock.json), [backend requirements](../backend/requirements.txt), [backend Dockerfile](../backend/Dockerfile), [frontend Dockerfile](../frontend/Dockerfile), [Compose configuration](../docker-compose.yml).

The local backend tests in this environment ran under Python 3.11; the backend container image is Python 3.13. These are distinct environments, not a claim that the project has a formally tested Python support range.

## Current Status

### Verified working

The following checks were run against this checkout while preparing this snapshot:

- `python -m pytest backend/tests/test_routes.py -q`: **15 passed**.
- `python -m pytest .agents/rules/_validation/test_rules_validation.py -q`: **6 passed, 6 xfailed**. The expected failures are strict defect probes, not ordinary passing product tests.
- Frontend product suite: **1 file, 5 tests** with `npx vitest run` from `frontend/`.
- Relocated frontend evidence probes: **2 files, 7 tests** with `npx vitest run --dir ../.agents/rules/_validation` from `frontend/`.
- `npx tsc --noEmit -p tsconfig.app.json`, `npx tsc -b`, and `npx eslint .` passed in the last recorded frontend verification.
- The validation scripts report 25 R-rules and 8 C-conventions, with no missing rule IDs in their index.

The two evidence tests are outside Vitest's `frontend/` root. A plain `npx vitest run` does **not** discover them; the explicit `--dir` command is required. Bare `npx tsc --noEmit` is not a valid project type-check here; use the app project or build command above.

### Known gaps and constraints

These are observed implementation gaps, not assertions that a fix has been approved:

- **Mock data only:** the current request path has no database, persistence, or external transaction source. The UI must not be described as a live financial-data product.
- **Analytics not fully connected:** backend analytical routes exist, but `App.tsx` currently calls only `/api/metrics`; KPI and chart aggregation runs in the frontend.
- **API origin and proxy differ:** Vite proxies `/api` to `http://backend:8000`, but `App.tsx` defaults to the absolute `http://localhost:8001` origin. The current absolute request bypasses the Vite proxy and may not suit forwarded development environments such as Codespaces.
- **Period label can mislead:** the UI says `2024 - Full Year`, while generated data is relative to the current date.
- **Documentation is stale:** the READMEs describe backend host port `8000` and claim the Vite proxy is the default; Compose publishes host port `8001`, and the current `App.tsx` default is absolute. See the [verification and gap analysis](../verification.md).
- **Development configuration only:** the backend container starts Uvicorn with reload and debugpy, and CORS allows all origins. Production deployment, access control, and security requirements are not established by this repository snapshot.
- **Validation date/count inconsistency:** the rules draft currently says 24 of 25 rules have `Validated` evidence, while the executable [`coverage audit`](../.agents/rules/_validation/val_rule_coverage.py) and [`validation report`](../.agents/rules/_validation/validation.md) report 25 of 25. Prefer the executable audit result; the draft's summary is stale. Some audit documents also carry a date later than this snapshot date, so their embedded dates are not used here as the current status date.

Evidence: [App](../frontend/src/App.tsx), [Vite config](../frontend/vite.config.ts), [Compose config](../docker-compose.yml), [backend app/CORS](../backend/app/main.py), [verification analysis](../verification.md), [rules draft](../.agents/rules/project-rules.draft.md), [validation index](../.agents/rules/_validation/README.md), [validation report](../.agents/rules/_validation/validation.md).

## Candidate Priorities (Not Approved)

No approved product roadmap or sequencing is recorded in the checked repository. The items below are evidence-backed decisions that may need an owner; they are **not authorization to implement them**:

1. Choose the browser-to-API strategy: keep the absolute host origin and define environment configuration, or use same-origin `/api` requests through Vite's proxy.
2. Decide whether this remains a mock-data dashboard or needs a real data source; only then define persistence, schema, validation, and access requirements.
3. Decide which existing analytical endpoints should appear in the UI and which filters/date range the dashboard should expose.
4. Reconcile the fixed 2024 label with the generated date range and correct the README port/proxy instructions.
5. Define deployment requirements before changing wildcard CORS, debugpy, reload, or development-server configuration.

These priorities are derived from [verification.md](../verification.md) and current source/configuration. Their order is not a committed roadmap.

## Working Rules for This Memory

- Treat source and executable checks as stronger evidence than stale prose; link the evidence beside important claims.
- Distinguish implemented behavior, measured validation, known gaps, and open product decisions.
- Do not infer persistence, live data, authentication, deployment readiness, or planned features from the product name or from endpoints that the UI does not call.
- Keep this file concise and refresh its status when a relevant implementation or verification result changes.
