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

## Feature request from PM

The PM has requested three features. This section documents the AS-IS backend API surface, the TO-BE requirements, and every mismatch found before writing specs. Findings below were resolved at the spec level.

### Feature 1 — Date range filter on the home dashboard

**PM requirement:**
- Two date inputs (start date, end date) at the top of the dashboard.
- Dates sent to API in `YYYY-MM-DD` format.
- Both inputs optional; when empty, show all data.
- Show available date range (min/max from facets) near the inputs.

**AS-IS API — `GET /api/metrics/facets`**
- Query params: none.
- Response shape:
  ```json
  {
    "operation_types": ["income", "outcome"],
    "business_types": ["B2B", "B2C"],
    "categories": ["administrative", "operational", "others", "sales", "suppliers"],
    "min_date": "2025-11-03",
    "max_date": "2026-10-28"
  }
  ```

**AS-IS API — `GET /api/metrics`**
- Query params: `start_date`, `end_date` (both optional, `YYYY-MM-DD` format), `category`, `operation_type`.
- Response shape: `FinancialMovement[]` (list of `{ create_date, amount, operation_type, category, business_type }`).
- The frontend currently calls this endpoint without any params and computes KPIs + monthly charts client-side.

**Frontend AS-IS fetch pattern:**
- `App.tsx` calls `fetchFinancialData()` which hits `${API_BASE_URL}/api/metrics` with no query params.
- No date state, no facets fetch, no date inputs exist in the UI.
- No router exists (`react-router-dom` is not in `package.json`).

**Mismatches found (resolved in spec):**
1. **PM wording says "filter all data currently displayed on the page"** — the dashboard currently computes everything client-side from raw movements. The spec must clarify that date filtering will be done by passing `start_date`/`end_date` to the API, not by filtering in the browser, so the backend does the work.
2. **PM wording says "available date range must be shown near the inputs"** — facets endpoint returns `min_date` and `max_date`. The spec must call out that the frontend needs a separate `GET /api/metrics/facets` call to populate these hints. The current `facets` endpoint has no date filter itself (it always returns the full range), which is correct.
3. **PM does not mention category/operation_type filters** — the API supports them, but the spec should ignore them for this feature.

### Feature 2 — Anomaly alerts table on the home dashboard

**PM requirement:**
- Table below existing charts with columns: period, recorded outcome, rolling average of previous 3 periods, percentage increase.
- Configurable threshold via numeric input (0.01 to 1.0, default 0.3).
- Explicit empty state message when no anomalies detected.
- Must respect date range from Feature 1 if active.

**AS-IS API — `GET /api/metrics/alerts`**
- Query params: `threshold` (default=0.3, ge=0), `group_by` (default="month"), `start_date`, `end_date`, `business_type`.
- Response shape:
  ```json
  [
    {
      "period": "2026-01",
      "outcome_total": 45231.12,
      "baseline_average": 32145.50,
      "increase_ratio": 0.4065
    }
  ]
  ```
- Returns an empty list `[]` when no spikes exceed the threshold — the API **already handles the empty case** by returning `[]`.
- The alert detection uses the aggregate outcome of ALL previous periods (not just the previous 3), then compares each period's outcome against that ALL-periods average.

**Frontend AS-IS fetch pattern:**
- Not fetched. No alerts table component exists.

**Mismatches found (resolved in spec):**
1. **⚠️ CRITICAL — PM says "rolling average of the previous 3 periods"** but the backend `detect_outcome_alerts()` computes the average of ALL historical outcomes since the beginning, not a sliding window of 3 periods. This is a **backend logic gap**: the API needs a new query parameter (e.g. `window_size=3`) or the backend logic must be changed. The spec must call this out as a backend change needed.
2. **PM says threshold range 0.01–1.0** but the backend only enforces `ge=0` (no upper bound). The spec should tighten this to `ge=0.01, le=1.0`.
3. **PM says "recorded outcome"** but the API field is `outcome_total`. Acceptable field name mismatch — spec will use `outcome_total`.
4. **PM says "rolling average of the previous 3 periods"** and API field is `baseline_average` — the semantics differ. Spec to note: rename to `rolling_average` after backend fix, or accept `baseline_average` with a comment.
5. **PM says "percentage increase"** but the API returns `increase_ratio` (a decimal like 0.4065). The spec should clarify that the frontend formats `increase_ratio` as a percentage (e.g. 40.7%).

### Feature 3 — B2B vs B2C comparison view

**PM requirement:**
- New page in the dashboard for comparing B2B vs B2C.
- Two side-by-side sections, each with a table of top 5 income categories: category name, total income, percentage of group total.
- Below both sections, a chart comparing total income of B2B vs B2C visually.
- User can filter by date range (`YYYY-MM-DD`).
- Available categories must come from the facets endpoint.

**AS-IS API — `GET /api/metrics/categories/top`**
- Query params: `operation_type` (default="outcome"), `limit` (default=5, ge=1, le=20), `start_date`, `end_date`, `business_type`.
- Response shape:
  ```json
  [
    {
      "category": "sales",
      "operation_type": "income",
      "total_amount": 452312.50
    }
  ]
  ```

**AS-IS API — `GET /api/metrics/facets`** (for available categories)
- Returns `categories: ["administrative", "operational", "others", "sales", "suppliers"]` and `business_types: ["B2B", "B2C"]`.

**Frontend AS-IS fetch pattern:**
- Neither endpoint is currently called.
- No routing exists (`react-router-dom` is not a dependency).
- No B2B/B2C page or components exist.

**Mismatches found (resolved in spec):**

1. **PM says "percentage of the group total"** — the API returns raw `total_amount` but not the percentage. The frontend must compute the percentage from the sum of all returned categories' `total_amount`, or the backend needs a new field. **Decision**: spec will have the frontend compute the percentage from the API response since the sum of top 5 is available client-side. The spec should note this is approximate if the 5 categories don't sum to the full group income.

2. **PM says "facets endpoint provides available categories for each group"** — the facets endpoint returns ALL categories, not categories filtered by business type. The frontend can get the full category list but cannot pre-filter by B2B vs B2C from facets alone. The spec should accept this.

3. **PM does not specify a total income comparison chart shape** — the spec should define it as a simple bar chart (B2B bar vs B2C bar) or a single-value comparison.

4. **No dedicated B2B-income-summary endpoint exists** — the spec should use `GET /api/metrics/summary` with `business_type=B2B` + `operation_type=income` for the B2B total, and same for B2C. Alternatively use the categories/top endpoint with `business_type` filter and aggregate from there. The spec will define which approach to use.

5. **Routing needed** — `react-router-dom` must be added to `package.json` to create a new page separate from the home dashboard.

### Summary of all API→PM mismatches

| # | Feature | PM wording | Actual API behavior | Resolution |
|---|---------|-----------|-------------------|-----------|
| 1 | F2 — Alerts | "rolling average of the previous 3 periods" | Average of ALL historical periods, not a sliding window | **Backend change needed**: add `window_size` param to `detect_outcome_alerts` |
| 2 | F2 — Alerts | "threshold between 0.01 and 1.0" | Backend accepts `ge=0` (no upper bound) | **Backend change needed**: tighten to `ge=0.01, le=1.0` |
| 3 | F2 — Alerts | "percentage increase" column | API returns `increase_ratio` (decimal) | Frontend formats as percentage |
| 4 | F2 — Alerts | "recorded outcome" column | API field is `outcome_total` | Acceptable name difference |
| 5 | F3 — B2B/B2C | "percentage of the group total" | API returns `total_amount` only | Frontend computes percentage client-side |
| 6 | F3 — B2B/B2C | "single chart compares total income" | No dedicated endpoint for B2B vs B2C total income side by side | Spec will define using summary endpoint with business_type filter |

## Integration work still needed

1. **Choose one API connection strategy.** Either keep direct browser requests and set `VITE_API_BASE_URL` to the host-reachable API origin (`http://localhost:8001` in this Compose setup), or use relative paths such as `/api/metrics` so Vite proxies them to `backend:8000`. Do not put the internal Compose hostname in browser configuration.
2. **Make the API contract explicit in the frontend.** Add TypeScript interfaces for facets, summary, top-category, comparison, and alert payloads. Put fetch/query-string construction in a small API client module rather than expanding `App.tsx`.
3. **Connect date and facet filters.** Fetch `/api/metrics/facets`, provide date/category/operation selectors, send selected values to API calls, and derive the header label from the selected range.
4. **Connect analytical endpoints to UI.** Decide which dashboard panels consume server-side summary, category ranking, comparison, and alerts. Avoid duplicating equivalent aggregation in the browser and backend without a reason.
5. **Unify B2B/B2C filtering.** Add a business-type selector and ensure all cards/charts use the same selection. The summary/top/comparison/alerts endpoints accept `business_type`; `/api/metrics` does not, while dedicated B2B and B2C movement endpoints exist.
6. **Decide how real financial data enters the system.** Before replacing the mock generator, define source, schema, validation, access control, persistence, and migration strategy. The current API is not a live financial data integration.
7. **Review runtime/security requirements before deployment.** Restrict CORS to intended origins, decide on health/readiness checks, and replace development servers/reload/debug exposure with an appropriate production setup if deployment is in scope.
8. **Align documentation and configuration.** Correct the README's API port and proxy description, and reconcile the proxy comments in `frontend/.env.example` with the actual default in `App.tsx`. Note that `frontend/src/lib/mock-data.ts` exists but is not imported by the current `App.tsx` path.