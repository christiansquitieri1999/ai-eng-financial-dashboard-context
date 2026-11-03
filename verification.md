# Project Verification

This document compares the intended project summary with the repository as it exists now. Statuses below refer to a check against the current source and configuration; they do not imply that containers or test suites were run.

## Status key

- **APPROVED** — confirmed by the checked code/configuration.
- **REJECT** — contradicted by the checked code/configuration, or stated as complete when it is not implemented.
- **TO DEEP DIVE** — cannot be fully verified from static inspection, or needs a product/architecture decision before implementation.

## Project at a glance

Financial Metrics Dashboard is a React + TypeScript single-page application backed by a FastAPI service. It currently displays financial KPIs and monthly charts using deterministic mock movements generated in the backend. There is no database or persistent data layer in the checked repository.

## Repository map and entry points

```text
.
├── docker-compose.yml              # Frontend and backend development services
├── backend/
│   ├── Dockerfile                   # Python image; Uvicorn reload and debugpy
│   ├── requirements.txt             # API and test dependencies
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS middleware, router registration
│   │   └── routes.py                # Pydantic models, mock data, calculations, API routes
│   └── tests/
│       ├── conftest.py              # Adds backend root to the test import path
│       └── test_routes.py            # Backend route and calculation tests
└── frontend/
    ├── Dockerfile                   # Node/Vite development server
    ├── package.json                 # npm scripts and dependencies
    ├── vite.config.ts               # Vite plugins, @ alias, /api proxy
    └── src/
        ├── main.tsx                 # React DOM entry point and global CSS
        ├── App.tsx                  # Fetches movements and composes dashboard
        ├── components/dashboard/    # Header, KPI cards/row, charts
        ├── components/ui/           # Shared card and skeleton components
        └── lib/                     # Types, client-side calculations, formatting, tests
```

### Services and entry points

| Service | Entry point / command | Host -> container ports | Responsibility |
| --- | --- | --- | --- |
| `frontend` | `frontend/src/main.tsx` -> `App.tsx`; `npm run dev` | `5173 -> 5173` | Vite-served React dashboard. Source is bind-mounted for development. |
| `backend` | `backend/app/main.py`; Uvicorn runs `app.main:app` | `8001 -> 8000`; debugpy `5678 -> 5678` | FastAPI API with reload. Backend source is bind-mounted. |

Compose uses `depends_on` for frontend/backend startup ordering; it does not configure an API readiness health condition. The Vite proxy target `http://backend:8000` is reachable on the Compose network, not as a hostname from the user's host browser.

## How to run and test

### Docker Compose

Prerequisite: Docker with Docker Compose.

```bash
docker compose up --build
```

- Dashboard: http://localhost:5173
- Backend API: http://localhost:8001
- OpenAPI docs: http://localhost:8001/docs
- Health check: http://localhost:8001/health
- Python debugger: port `5678`

Stop the services with `docker compose down`.

### Tests and local checks

Backend, from `backend/`:

```bash
pytest
```

Frontend, from `frontend/` (install dependencies first with `npm install` if needed):

```bash
npm test
npm run lint
npm run build
```

These are the repository's documented/available commands; they have not been run as part of this verification.

## Current data flow

1. `frontend/src/App.tsx` requests `GET /api/metrics` when the page loads. Its API base URL defaults to `http://localhost:8001` and can be overridden by `VITE_API_BASE_URL`.
2. `backend/app/routes.py` generates 360 mock movements using seed `42`, filters and sorts them, then returns them. The data is regenerated in memory on each request; there is no persistence.
3. `frontend/src/lib/financial-utils.ts` computes totals, profit, margin, and monthly aggregates in the browser.
4. `KPIRow` renders the four KPI cards. `IncomeOutcomeChart` and `ProfitPercentChart` render monthly values using Recharts.

The dashboard header is passed the fixed label `2024 - Full Year`, while the backend's mock dates are generated relative to the current date. Therefore the displayed label can disagree with the date range in the returned data.

## Backend API surface

The following routes are defined in `backend/app/routes.py`:

| Method and path | Current purpose |
| --- | --- |
| `GET /health` | Returns `{"status":"ok"}`. |
| `GET /api/metrics` | Returns movements; supports `start_date`, `end_date`, `category`, and `operation_type`. |
| `GET /api/metrics/facets` | Returns available operation/business types, categories, and min/max dates. |
| `GET /api/metrics/summary` | Aggregates income/outcome/net by day, week, or month; accepts date/category/operation/business filters. |
| `GET /api/metrics/categories/top` | Returns ranked categories for an operation type; accepts limit, dates, and business type. |
| `GET /api/metrics/comparison` | Compares net value over a required date range with the preceding equal-length range. |
| `GET /api/metrics/alerts` | Finds periods whose outcomes exceed the average of earlier periods by a threshold. |
| `GET /api/metrics/b2b` and `GET /api/metrics/b2c` | Return movements restricted to a business type, with date/category/operation filters. |

The frontend types in `frontend/src/lib/financial-types.ts` describe movement records and client-computed dashboard data, but do not yet model all payloads from the analytical endpoints.

## Gap analysis: summary claims vs. checked implementation

| Area / claim | Status | Evidence and implications |
| --- | --- | --- |
| React + TypeScript frontend and FastAPI backend | **APPROVED** | Frontend entry is `src/main.tsx`; backend app is `app.main:app`. |
| Docker Compose provides frontend and backend services | **APPROVED** | `docker-compose.yml` defines both services and their published ports. |
| Host backend URL is `http://localhost:8001` | **APPROVED** | Compose maps host `8001` to container `8000`; `App.tsx` uses host port `8001` as its default API origin. |
| README's backend URL `http://localhost:8000` matches Compose | **REJECT** | README says `8000`, but Compose exposes host port `8001`. Use `8001` for the current Compose setup or update the mapping/docs deliberately. |
| Vite `/api` proxy is used by the page by default | **REJECT** | `vite.config.ts` defines the proxy, but `App.tsx` defaults to an absolute `http://localhost:8001` URL. Absolute-origin fetches bypass the Vite proxy. |
| The browser can use proxy target `http://backend:8000` directly | **REJECT** | `backend` is the Compose service hostname; it is not the host-browser address. Browser requests should use host-accessible `localhost:8001` or a same-origin relative `/api` request through Vite. |
| The page currently fetches `/api/metrics` and renders KPI and monthly charts | **APPROVED** | Confirmed in `App.tsx`, `financial-utils.ts`, `kpi-row.tsx`, and the chart components. |
| API data is persistent/live financial data | **REJECT** | Routes generate seeded mock movements in memory. No persistence layer or database configuration is present. |
| Backend already exposes facets, summaries, ranking, comparison, alerts, and B2B/B2C routes | **APPROVED** | Routes and parameters are implemented in `backend/app/routes.py`, with several covered by backend tests. This does not mean the UI consumes them. |
| All backend analytics are already connected to the dashboard | **REJECT** | `App.tsx` calls only `/api/metrics`; KPI and chart aggregation is client-side. The other analytical routes are not wired into the page. |
| Header accurately labels the data's date period | **REJECT** | Header receives a fixed `2024 - Full Year`; mock date generation is relative to the current date. |
| `frontend/.env.example` exists as referenced by README | **APPROVED** | The file exists and documents `VITE_API_BASE_URL` as an optional backend-origin override. Its comments say the Vite proxy is used by default, but `App.tsx` currently defaults to the absolute `http://localhost:8001` origin, so the example's proxy guidance and runtime behavior are inconsistent; see the proxy row above. |
| Backend test suite passes | **TO DEEP DIVE** | Test files and pytest dependencies exist, but tests were not run in this check. Run `pytest` from `backend/`. |
| Frontend tests, lint, and production build pass | **TO DEEP DIVE** | Scripts exist in `frontend/package.json`, but were not run. Run `npm test`, `npm run lint`, and `npm run build` from `frontend/`. |
| Development startup has readiness handling and production hardening | **TO DEEP DIVE** | Compose only declares `depends_on`; CORS allows all origins and the containers run dev servers/reload. Production deployment requirements and security posture need separate decisions. |

## Integration work still needed

1. **Choose one API connection strategy.** Either keep direct browser requests and set `VITE_API_BASE_URL` to the host-reachable API origin (`http://localhost:8001` in this Compose setup), or use relative paths such as `/api/metrics` so Vite proxies them to `backend:8000`. Do not put the internal Compose hostname in browser configuration.
2. **Make the API contract explicit in the frontend.** Add TypeScript interfaces for facets, summary, top-category, comparison, and alert payloads. Put fetch/query-string construction in a small API client module rather than expanding `App.tsx`.
3. **Connect date and facet filters.** Fetch `/api/metrics/facets`, provide date/category/operation selectors, send selected values to API calls, and derive the header label from the selected range.
4. **Connect analytical endpoints to UI.** Decide which dashboard panels consume server-side summary, category ranking, comparison, and alerts. Avoid duplicating equivalent aggregation in the browser and backend without a reason.
5. **Unify B2B/B2C filtering.** Add a business-type selector and ensure all cards/charts use the same selection. The summary/top/comparison/alerts endpoints accept `business_type`; `/api/metrics` does not, while dedicated B2B and B2C movement endpoints exist.
6. **Decide how real financial data enters the system.** Before replacing the mock generator, define source, schema, validation, access control, persistence, and migration strategy. The current API is not a live financial data integration.
7. **Review runtime/security requirements before deployment.** Restrict CORS to intended origins, decide on health/readiness checks, and replace development servers/reload/debug exposure with an appropriate production setup if deployment is in scope.
8. **Align documentation and configuration.** Correct the README's API port and proxy description, and reconcile the proxy comments in `frontend/.env.example` with the actual default in `App.tsx`. Note that `frontend/src/lib/mock-data.ts` exists but is not imported by the current `App.tsx` path.