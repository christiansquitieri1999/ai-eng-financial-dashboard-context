# Proposed Rules

Status: **proposal, not yet active.** This document records de-risking findings, risky patterns, and conventions already in force in this repository, expressed as rules so that future contributors and coding agents can apply them without repeating the analysis.

Evidence basis: static inspection of the files named in each entry. Snapshot date: **2026-11-03**. No tests, linters, or containers were executed for this analysis, and no corrective change has been applied to the source. Every rule is anchored to at least one verifiable repository fact — a file, a line of configuration, a measured size, or a test body. The [Rule-to-fact map](#rule-to-fact-map) at the end lists every anchor so it can be checked without re-reading the evidence column; entries without an anchor were deliberately excluded.

Intended location: `AGENTS.md` requires agent guidance under `./.agents/rules/`. This file is the proposal source for that directory and is intentionally kept outside it until the rules are accepted.

## Status key

- **PROPOSED** — observed behavior that future work should avoid, preserve, or consciously decide on. Not a defect report and not a request to change the current snapshot.
- **CONFIRMED** — convention already followed in the code; recorded so it survives refactors.
- **DEPLOYMENT** — only binding once the API is exposed outside local development or serves non-public data.

Severity expresses the impact if the described code path or deployment context applies. It is not a claim that an incident occurred.

## Index

IDs are stable identifiers carried over from the audit, not sequence numbers. Rules are grouped by category; every row cites at least one verified repository fact.

| Category | Rules | Count |
| --- | --- | --- |
| 1. Architecture & module boundaries | R17, R6, R11, R16 | 4 |
| 2. Data correctness & time handling | R1, R2 | 2 |
| 3. API contract & typing | R3, R14 | 2 |
| 4. Naming & domain language | R18, R19 | 2 |
| 5. Testing & verification | R21, R22, R12 | 3 |
| 6. Database & persistence | R20 | 1 |
| 7. UX, errors & accessibility | R24, R25, R13, R5, R7 | 5 |
| 8. Documentation & agent guidance | R23, R15 | 2 |
| 9. Build, deployment & security | R4, R8, R9, R10 | 4 |
| 10. Conventions already in force | C1–C8 | 8 |

## How to read a rule

- **Scope** — file globs where the rule applies.
- **Rule** — the constraint to apply when writing or reviewing code.
- **Evidence** — the repository fact that justifies it. A rule without a verifiable fact does not belong in this document.

---

## 1. Architecture & module boundaries

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R17** | PROPOSED | Medium | `backend/app/*.py` | One module must not host the domain models, the data source, the aggregations, and the HTTP handlers together. Split by responsibility before adding routes. | `backend/app/routes.py` is a single 391-line module containing 35 top-level declarations: 6 Pydantic models, the `Literal` aliases, `_year_for_month`, `_build_movement`, `generate_mock_movements`, 8 calculation helpers, and 9 route handlers. Every new endpoint grows the same file. |
| **R6** | PROPOSED | Low | `backend/app/routes.py` | Never reseed a process-global random generator from request-handling code; use a locally seeded instance. | `generate_mock_movements` calls `random.seed(seed)` on every request, reseeding Python's module-global generator. Output stays deterministic, but any other code relying on `random` in the same process inherits a sequence reset by an HTTP call. |
| **R11** | PROPOSED | Low | `frontend/src/lib/mock-data.ts` | A repository must have one source of truth for sample financial data. Additional datasets must be declared as fixtures and kept aligned. | The file hardcodes a separate 2024 dataset (`mockMovements`) that no module imports. It duplicates the concept of the backend generator with no test asserting agreement, so fixtures and documentation can drift from the data the app actually renders. |
| **R16** | PROPOSED | Low | `frontend/vite.config.ts`, `frontend/src/App.tsx` | A proxy target that only resolves inside Compose must be environment-driven, not hardcoded, so host-based development keeps working when the client switches to relative URLs. | The proxy forwards `/api` to `http://backend:8000`, a hostname available only on the Compose network. The mismatch is masked because `App.tsx` calls the absolute `http://localhost:8001` origin and bypasses the proxy, so adopting relative paths for host runs would break without making the target configurable. |

## 2. Data correctness & time handling

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R1** | PROPOSED | Medium | `backend/app/routes.py`, `frontend/src/App.tsx` | A displayed period must be derived from the data actually rendered, never hardcoded independently of the payload's date range. | `_year_for_month` maps months before the current month to the current year and the remaining months to the previous year, so the 360 generated movements always span two calendar years ending in the current month. `App.tsx` always renders `2024 - Full Year`. At the snapshot date the payload covers 2025-11 to 2026-10 while the header claims 2024. |
| **R2** | PROPOSED | Medium | `frontend/src/lib/financial-utils.ts`, `frontend/src/lib/financial-utils.test.ts` | Treat `create_date` as a calendar date, not an instant. Read year/month from the string or use UTC getters consistently; never mix UTC parsing with local getters. | `create_date` is a date-only string, but `new Date("YYYY-MM-DD")` parses as UTC midnight and `toYearMonthKey` then reads it with local `getFullYear()` / `getMonth()`. In any time zone west of UTC a movement dated the 1st aggregates into the previous month. The cross-year test uses the 3rd, 5th, and 8th, so it passes while this boundary is untested. |

## 3. API contract & typing

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R3** | PROPOSED | Medium | `backend/app/routes.py` | Filter parameters must be uniform across endpoints that feed the same view. If a dashboard applies one population filter, every endpoint it calls must accept it. | `summary`, `categories/top`, `comparison`, and `alerts` accept `business_type`; `/api/metrics` does not and exposes separate `/b2b` and `/b2c` routes instead. A view applying one B2B/B2C selection to both movement rows and analytics must special-case `/api/metrics`, so panels can silently show different populations. |
| **R14** | PROPOSED | Low | `frontend/src/lib/financial-types.ts`, `backend/app/routes.py` | Model correlated fields together. When an API constrains one field by another, the client type must not accept combinations the API cannot emit. | `FinancialMovement` types `category` and `operation_type` independently, so `{ operation_type: "outcome", category: "sales" }` compiles, yet `_build_movement` only emits `sales` for income and draws outcomes from `OUTCOME_CATEGORIES`. Fixtures and UI filters can encode impossible states that no layer rejects at runtime. |

## 4. Naming & domain language

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R18** | PROPOSED | Low | `backend/app/routes.py`, `frontend/src/lib/*.ts`, `frontend/src/components/dashboard/*.tsx` | Pick one domain term per money direction and apply it to types, fields, aggregates, and UI labels. Do not pair two terms for the same concept, and do not name an aggregate with a singular noun. | `OperationType = Literal["income", "outcome"]` pairs a standard term with a non-standard one; `OUTCOME_CATEGORIES` derives from it; totals are named `totalOutcome` in `KPIMetrics` and `outcome_total` in `MetricsAlert`, while `summarize_movements` keys the accumulator as `values["outcome"]`. The token `outcome` appears 91 times across backend and frontend files, so the term is load-bearing and cannot be renamed in one place. |
| **R19** | PROPOSED | Low | `backend/app/routes.py` | Express the same filter the same way on every route. Do not expose one filter as both a path segment and a query parameter. | Business type is a path segment in `/api/metrics/b2b` and `/api/metrics/b2c` but a `business_type` query parameter on `summary`, `categories/top`, `comparison`, and `alerts`. A client cannot build one filter-application step, and generated API documentation presents two different shapes for the same concept. |

## 5. Testing & verification

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R21** | PROPOSED | Medium | `frontend/src/**/*.test.tsx`, `frontend/package.json`, `frontend/vite.config.ts` | Component behavior — loading, error, empty, and conditional branches — needs a test before it is considered covered. Adding a DOM test environment is a prerequisite, not an optional extra. | `frontend/src/lib/financial-utils.test.ts` is the only test file in the repository; every component in `frontend/src/components/dashboard/` has zero tests despite containing `loading`/`hasData` branches. `frontend/package.json` declares no `@testing-library/*`, `jsdom`, or `happy-dom`, and `vite.config.ts` has no `test` block, so Vitest runs in a Node environment with no DOM. |
| **R22** | PROPOSED | Low | `backend/tests/test_routes.py` | Cover rejection paths and value-level outcomes, not only successful shapes. A test that cannot fail when the computation is wrong is not a test of that computation. | `test_routes.py` has no case for an invalid enum value (the 422 from `Literal` validation), no assertion on `alerts` values (`if payload:` guards the only assertions), and no case for `build_metrics_facets([])`. `test_metrics_comparison_returns_delta_fields` asserts only key names for dates outside the generated range. |
| **R12** | PROPOSED | Low | `backend/tests/test_routes.py` | A generator test must assert the semantic range it claims, not only count and ordering. | `test_generate_mock_movements_returns_full_year_sorted_data` asserts only `len == 360` and sorted order, so the two-calendar-year span behind R1 passes unnoticed. The name also claims a "full year" while the generator produces a rolling window. |

## 6. Database & persistence

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R20** | PROPOSED | Medium | `backend/app/*.py`, `backend/requirements.txt` | Data acquisition must not live inside request handlers, and adding persistence requires an explicit boundary: a data-access module, a schema/migration source, and configuration read from the environment. Until then, the mock source must be visibly the only source. | No persistence dependency or import exists: `backend/requirements.txt` lists only `fastapi`, `uvicorn[standard]`, `debugpy`, `pytest`, `pytest-cov`, `httpx`, and a search of `backend/app/*.py` for `sqlalchemy`, `sqlite`, `psycopg`, `databases`, `sessionmaker`, `import os`, or `getenv` returns nothing. Instead, all 9 handlers call `generate_mock_movements(seed=42)` inline, so the data source, the request lifecycle, and the absence of configuration are fused in the route layer. |

## 7. UX, errors & accessibility

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R24** | PROPOSED | Medium | `frontend/src/App.tsx`, `frontend/src/components/dashboard/kpi-row.tsx` | A failed load must be visually distinct from an empty dataset; placeholder values must not be indistinguishable from real zero. | On failure `App.tsx` sets only an error string, then `finally` sets `loading` to `false` while `metrics` stays `null`. `KPIRow` therefore renders all four cards with the literal `—` placeholder and no error styling, alongside a red banner. All four KPI figures appear as absent-but-value-less cards, so a backend outage is presented as a dashboard with no numbers. |
| **R25** | PROPOSED | Low | `frontend/src/components/dashboard/income-outcome-chart.tsx`, `frontend/src/components/dashboard/profit-percent-chart.tsx`, `frontend/src/App.tsx` | A chart must expose its data in a non-visual form: an accessible name, and a text or table equivalent for the series. | Both chart components render Recharts `LineChart` inside `ResponsiveContainer` with no `role`, `aria-label`, `figcaption`, or data table. `App.tsx` supplies `aria-label` only on the two `<section>` wrappers, so a screen-reader or text-only consumer reaches a section label and no values. |
| **R13** | PROPOSED | Low | `frontend/src/App.tsx` | Error handlers must preserve the captured error, and user-facing text must use the language of the surrounding UI. | `.catch(() => { ... })` discards the thrown error, including the HTTP status built by `fetchFinancialData`, and replaces it with the fixed Spanish string `"No se pudo cargar la informacion financiera..."` in an otherwise English UI. Users cannot distinguish a down backend from a bad response, and maintainers lose the status code. |
| **R5** | PROPOSED | Medium | `docker-compose.yml`, `frontend/src/App.tsx` | Startup ordering is not readiness. A single fetch on mount with no retry must not be the only path to data when a dependency may still be starting. | Compose declares only `depends_on` with no healthcheck, which orders startup but does not wait for API readiness. `App.tsx` fetches once in a `useEffect` with an empty dependency array, never retries, and offers no reload action, so a failed first request stays visible until a manual browser refresh. |
| **R7** | PROPOSED | Low | `backend/app/routes.py` | Helpers that derive a range from a collection must define empty-input semantics instead of indexing the first and last element. | `build_metrics_facets` reads `ordered[0]` and `ordered[-1]` with no guard, so `[]` raises `IndexError`. The current `/api/metrics/facets` route always passes an unfiltered generated list, so the defect is unreachable today; it becomes reachable as soon as facets are computed from filtered or supplied movements. |

## 8. Documentation & agent guidance

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R23** | PROPOSED | Medium | `README.md`, `README.es.md`, `verification.md`, `rules-proposed.md` | Runtime documentation must not contradict the running configuration, and repository-level analysis artifacts must be reachable from the README. | Both READMEs state backend `http://localhost:8000` and its `/docs`, while `docker-compose.yml` publishes host `8001` mapped to container `8000`. Both also claim the Vite proxy is the default, while `App.tsx` uses the absolute `http://localhost:8001` origin. Neither README references `verification.md` or `rules-proposed.md`, so the two work products are discoverable only by directory listing. |
| **R15** | PROPOSED | Low | `AGENTS.md`, `README.md`, `README.es.md` | Agent instructions must reference paths that exist, or state explicitly that they are optional and currently absent. | `AGENTS.md` requires reviewing `./.agents/rules`, `./.agents/skills`, and `./memory-bank` before acting, and both READMEs document an `.agents/rules` + `.agents/skills` layout. None of the three paths exists, so the first required step cannot be completed and the reason is ambiguous (deleted, never created, or deliberately empty). This file is the proposal source for `./.agents/rules` and sits outside it until accepted. |

## 9. Build, deployment & security

| ID | Status | Severity | Scope | Rule | Evidence |
| --- | --- | --- | --- | --- | --- |
| **R4** | DEPLOYMENT | Medium | `backend/app/main.py` | A wildcard CORS origin must not survive into a configuration that serves private or authenticated financial data. Use an explicit origin allowlist. | `CORSMiddleware` uses `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` together with `allow_credentials=True`, so any origin can call the API from a browser. There is no authentication in the snapshot, so this is not a present data leak, but the setting is not an allowlist. |
| **R8** | PROPOSED | Low | `.dockerignore`, `backend/.dockerignore`, `frontend/.dockerignore`, `frontend/Dockerfile`, `backend/Dockerfile` | Every build context must exclude host-only content. Git ignore rules do not apply to Docker. | Neither build context has a `.dockerignore` while both Dockerfiles run `COPY . .`. Host-only content is therefore eligible to enter the image, including a local `frontend/.env`/`.env.*` that the root `.gitignore` excludes from Git. The local `frontend/node_modules` is currently empty, so no contamination exists today; the exposure appears with the first local install. |
| **R9** | PROPOSED | Low | `frontend/Dockerfile`, `frontend/package-lock.json` | Image builds must consume the committed lockfile rather than resolving it again. | A lockfile is committed, but the image runs `npm install`, which may rewrite or relax the resolution instead of asserting the committed tree, so container builds and local installs can diverge without any repository change. |
| **R10** | PROPOSED | Low | `backend/requirements.txt`, `backend/Dockerfile` | Runtime images must not install test and debugger tooling that the runtime does not use. | The single requirements file lists `pytest`, `pytest-cov`, `httpx`, and `debugpy`, and the Dockerfile installs it directly, so test tooling and a debugger are part of the runtime layer that starts Uvicorn under debugpy. |

---

## 10. Conventions already in force (preserve these)

These are **CONFIRMED**: present in the checked code. The rule column states what to keep doing.

| ID | Convention | Scope | Evidence |
| --- | --- | --- | --- |
| **C1** | Define API inputs and outputs as explicit types at the boundary. | `backend/app/routes.py` | `Literal` aliases (`OperationType`, `Category`, `BusinessType`, `GroupBy`) plus Pydantic response models on every route, so invalid enum values are rejected and response shapes are explicit. |
| **C2** | Validate numeric query parameters with explicit bounds. | `backend/app/routes.py` | Top-category `limit` uses `ge=1, le=20`; alert `threshold` uses `ge=0`. Consumers cannot request unbounded results or negative thresholds. |
| **C3** | Keep financial calculations in pure helpers, separate from transport. | `backend/app/routes.py`, `backend/tests/test_routes.py` | `filter_movements`, `summarize_movements`, `build_top_categories`, and `detect_outcome_alerts` are imported and tested directly without HTTP; route handlers stay thin. |
| **C4** | Handle zero-income denominators explicitly. | `frontend/src/lib/financial-utils.ts`, `frontend/src/lib/financial-utils.test.ts` | `computeKPIs` and `computeMonthlyData` guard `income > 0`, and a focused test covers outcomes with no income. |
| **C5** | Make variant styling exhaustive at compile time. | `frontend/src/components/dashboard/kpi-card.tsx` | `variantStyles` is typed as `Record<KPICardProps["variant"], ...>`, so adding a variant becomes a compile error instead of a silently unstyled card. |
| **C6** | Keep secret files out of Git while tracking the documented example. | `.gitignore` | Root `.gitignore` lists `.env` and `.env.*` then negates `!.env.example`. Note that Docker does not honour this file; see R8. |
| **C7** | Protect container dependencies from the host bind mount. | `docker-compose.yml` | The frontend service declares the anonymous volume `/app/node_modules`, so bind-mounting `./frontend` does not replace the modules installed in the image. |
| **C8** | Cover ordering, date-edge inclusion, and cross-year aggregation with tests. | `backend/tests/test_routes.py`, `frontend/src/lib/financial-utils.test.ts` | Tests assert sorted output, inclusive `start_date`/`end_date` edges, and chronological year-month keys across a year boundary. Extend these at the date/time boundaries named in R2 and R12. |

---

## Open decisions

Rules marked PROPOSED describe behavior that must be chosen deliberately, not silently changed. The decisions they need are:

1. Whether the dashboard shows a fixed calendar year or a rolling window (R1), which also determines what the generator and the header must express.
2. Whether `business_type` becomes a parameter of `/api/metrics` or the B2B/B2C split stays documented as intentional (R3, R19).
3. Whether the client keeps absolute-origin requests or moves to relative `/api` paths, which decides the proxy-target rule (R16).
4. Whether `mock-data.ts` is a fixture to maintain or dead weight to remove (R11).
5. Whether `.agents/rules` and `./memory-bank` are created, or `AGENTS.md` is amended to describe the current, empty state (R15).
6. Whether `outcome` is kept as the domain term or replaced by `expense` across the 91 occurrences (R18); either way the choice must be applied everywhere at once.
7. Whether `routes.py` is split before the next endpoint is added, and how much of the split is required now (R17).
8. Whether a DOM test environment is added now or component rules stay unverifiable until then (R21).
9. Whether persistence is in scope for the next iteration, which decides when R20 starts binding.

## Rule-to-fact map

Every rule above is anchored to a repository fact. This table exists so a reviewer can confirm the anchor without re-reading the narrative column.

| Rule | Category | Anchor type | Anchor |
| --- | --- | --- | --- |
| R1 | Data correctness | Code + live date | `routes.py::_year_for_month`, `App.tsx` header literal, snapshot 2026-11-03 |
| R2 | Data correctness | Code + test gap | `financial-utils.ts::toYearMonthKey`, test dates 2026-01-08 / 2025-12-05 / 2025-12-03 |
| R3 | API contract | Route signatures | `business_type` present on 4 routes, absent on `/api/metrics` |
| R4 | Deployment | Middleware config | `main.py` CORS wildcard + `allow_credentials=True` |
| R5 | UX | Compose + effect | `depends_on` only, `useEffect` with `[]` |
| R6 | Architecture | Code | `random.seed(seed)` in `generate_mock_movements` |
| R7 | UX | Code | `ordered[0]` / `ordered[-1]` in `build_metrics_facets` |
| R8 | Build | Missing files | no `.dockerignore`, both Dockerfiles `COPY . .` |
| R9 | Build | Dockerfile command | `npm install` with `package-lock.json` committed |
| R10 | Build | Dependency list | `requirements.txt` includes `pytest`, `pytest-cov`, `httpx`, `debugpy` |
| R11 | Architecture | Unused module | `mock-data.ts` exported, zero importers |
| R12 | Testing | Test bodies | generator test asserts len/sort only |
| R13 | UX | Code | `.catch(() => ...)` discards error, Spanish string in English UI |
| R14 | API typing | Type definition | `FinancialMovement` independent fields vs `_build_movement` constraints |
| R15 | Documentation | Missing paths | `.agents/rules`, `.agents/skills`, `memory-bank` absent |
| R16 | Architecture | Config | proxy target `http://backend:8000` vs absolute `localhost:8001` |
| R17 | Architecture | File size | `routes.py` 391 lines, 35 top-level declarations, 9 handlers |
| R18 | Naming | Token usage | `outcome` 91 occurrences; `totalOutcome` vs `outcome_total` vs `values["outcome"]` |
| R19 | Naming | Route shapes | `/metrics/b2b` path segment vs `business_type` query parameter |
| R20 | Database | Absent dependency | no persistence import; all 9 handlers call `generate_mock_movements(seed=42)` |
| R21 | Testing | File inventory | one test file in `frontend/src`; no DOM deps, no `test` block in `vite.config.ts` |
| R22 | Testing | Test bodies | no 422 case, `if payload:` guard, no empty-list case |
| R23 | Documentation | Docs vs config | README `8000` vs Compose `8001`; no README link to `verification.md`/`rules-proposed.md` |
| R24 | UX | Code path | `finally` clears `loading` while `metrics` stays `null`; `KPIRow` renders `—` |
| R25 | UX | Component markup | no `role`/`aria-label`/table in either chart; `aria-label` only on `<section>` |

