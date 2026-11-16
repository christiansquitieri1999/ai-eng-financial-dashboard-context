# Project Memory Bank

**Status checked:** 2026-11-16
**Purpose:** evidence-backed working context for contributors and coding agents. This is a snapshot of the repository, not a product specification or an approved roadmap. Update it when source, configuration, or verified test results change.

**Progress index:** [progress.md](./progress.md) summarizes the skills applied, their verified outcomes, the ecosystem skill chosen (and why), and the internally authored skill, linking back to the detailed sections below.

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
- Frontend product suite: **1 file, 5 tests** with `npx vitest run src/lib/financial-utils.test.ts` from `frontend/`. The broader default `npm test` also discovers `frontend/validation/r13-error-handling.test.ts`; its test expecting the old Spanish error text currently fails against the English UI copy.
- Relocated frontend evidence probes: **2 files, 7 tests** with `npx vitest run --dir ../.agents/rules/_validation` from `frontend/`.
- `npx tsc --noEmit -p tsconfig.app.json`, `npx tsc -b`, and `npx eslint .` passed in the last recorded frontend verification.
- The validation scripts report 25 R-rules and 8 C-conventions, with no missing rule IDs in their index.
- `docker compose config --quiet` and `docker compose build` succeeded; both development services started with `docker compose up -d`.
- Runtime smoke tests passed: backend `/health` returns `ok`; backend and Vite-proxied `/api/metrics` each return 360 movements; frontend `/` returns HTTP 200. The running backend image contains pytest 9.2.0 and debugpy 1.8.22.
- `backend/.dockerignore` and `frontend/.dockerignore` exclude local dependencies, caches, and env files from image contexts. Their measured build contexts were about 898 B and 1.75 kB respectively.
- The frontend performance review on 2026-11-16 applied literal `React.lazy` imports for both Recharts views and kept chart/KPI loading placeholders dimensionally aligned with rendered content. It also added a static HTML description meta tag. `npm run lint`, `npx tsc --noEmit -p tsconfig.app.json`, and the focused product test (`npx vitest run src/lib/financial-utils.test.ts`, 5 tests) passed. The full `npm test` command reported 8 passing and 1 failing test: the existing R13 evidence probe still expects the prior Spanish error string, while `App.tsx` already uses English. The final documented production command, `npm run build` from `frontend/`, passed with no warnings: the entry JavaScript chunk changed from 585.87 kB to 188.52 kB, and the largest generated chunk is 342.30 kB. The prior >500 kB chunk warning disappeared without changing the warning threshold or bundler configuration. These are entry/chunk sizes, not a reduction in total page downloads.

### Frontend delivery-pattern review (2026-11-16)

- **Applied:** Installed skill rule `bundle-dynamic-imports` (with the statically analyzable literal paths recommended by `bundle-analyzable-paths`) through `React.lazy`/`Suspense` for the two chart components. The skill's `next/dynamic` example is Next-specific; this Vite SPA uses React's native lazy loading. Since the charts render on the initial page, this splits them from the entry chunk but does not defer their requests until a user interaction. A chart error boundary logs import/render failures and presents an accessible, fixed-size error state so a failed lazy chunk does not replace the rest of the dashboard.
- **Applied, as a layout-stability companion:** `async-suspense-boundaries` warns against fallback/content shifts. Suspense and API-loading chart fallbacks now share the same titled card and fixed 280px plot placeholder. KPI labels, icons, and helper text render immediately; only the numeric value uses a placeholder with the same line height as the loaded value, so text wrapping is consistent at different viewport widths. Production-preview browser checks with the API request held and released showed identical loading/loaded chart positions and card heights at widths 1440px and 390px. At 1440px, the previous 27px KPI-region and 8px chart-card height increases were eliminated. This verifies the measured loading transition, not a comprehensive Core Web Vitals/CLS certification.
- **Metadata:** the existing title, viewport, and favicon remain; a descriptive `<meta name="description">` was added. General page metadata is not a standalone rule in the installed skill.
- **Not applicable / no change:** no app `<img>` elements or rendered photo assets exist, so `next/image` is unsupported and unnecessary in this Vite SPA (the source `hero.png` is unused; the favicon remains a static SVG link). No custom font file or font network request is present; the Inter-first system font stack falls back locally, so no font swap/layout-shift or font-loading request was found. `server-hoist-static-io` concerns server/route-handler I/O and does not apply to this client-only app. Vite's `type="module"` entry is already non-blocking; no extra script defer/async change or resource hint is warranted.
- **Not applied:** `bundle-conditional` would load an always-visible chart only after user activation, changing the current initial dashboard behavior; that trade-off is not justified. No Next.js migration, Next-only dependency, image optimization library, font service, vendor chunk override, or warning-threshold change was introduced.
- **Failure-path verification:** aborting the production income/outcome JavaScript chunk produced a logged chart error and an alert directing the user to reload; KPI values and the profit chart/table remained available. Removing the interception and reloading restored both 12-row chart tables.

Evidence: [app boundaries](../frontend/src/App.tsx), [chart placeholder](../frontend/src/components/dashboard/chart-skeleton.tsx), [chart error boundary](../frontend/src/components/dashboard/chart-error-boundary.tsx), [KPI layout](../frontend/src/components/dashboard/kpi-card.tsx), [HTML metadata](../frontend/index.html), and the installed skill rules [dynamic imports](../.agents/skills/vercel-react-best-practices/rules/bundle-dynamic-imports.md), [analyzable paths](../.agents/skills/vercel-react-best-practices/rules/bundle-analyzable-paths.md), and [Suspense boundaries](../.agents/skills/vercel-react-best-practices/rules/async-suspense-boundaries.md).

### Third skill: TypeScript Advanced Types (2026-11-16)

**Status:** user-approved and installed as the third project skill, alongside accessibility and Vercel React best practices. This change installs guidance and records the decision; it does not yet change application types or validate API payloads. Discovery used `npx skills find performance` and `npx skills find typescript`; selection is based on reviewed instructions and repository needs, not install counts.

| Candidate | Reviewed coverage | Project fit |
| --- | --- | --- |
| [`wshobson/agents@typescript-advanced-types`](https://skills.sh/wshobson/agents/typescript-advanced-types) | Discriminated unions, typed API contracts, `unknown`, type guards, strict checking, and type tests. | **Selected and installed:** adds a data-type correctness layer to the existing accessibility and React performance coverage. |
| [`addyosmani/web-quality-skills@performance`](https://skills.sh/addyosmani/web-quality-skills/performance) | Evidence-led loading/runtime analysis, Core Web Vitals, repeatable lab measurements, resource delivery, images, fonts, and caching. | Considered but not installed: valuable for measured end-to-end performance, with more overlap with the Vercel skill than the selected TypeScript guidance. |

**Why TypeScript first:** [FinancialMovement](../frontend/src/lib/financial-types.ts) currently permits `operation_type` and `category` independently, including incompatible domain combinations documented by [R14](../.agents/rules/project-rules.draft.md#r14--model-correlated-fields-together). [The fetch boundary](../frontend/src/App.tsx) returns `response.json()` without runtime shape validation; a declared return type alone does not validate network data. The [three-feature component specification](../frontend/specs/components.md) and [query contracts](../frontend/specs/param-types.ts) will add more API/UI boundaries. Targeted unions and guards would address these concrete risks without introducing Next.js or a new framework. These are candidate improvements, not fixes already made.

**Financial-domain rationale:** the user selected this skill as an additional control against incoherent financial-data combinations. For example, the current independent types accept both `outcome` with `sales` and `income` with `suppliers`, although the documented generator emits neither pairing. Modeling the correlation can reject invalid objects before they enter KPI/chart calculations, while runtime guards are needed for JSON received from the API. Accessibility covers access to the information, the Vercel skill covers delivery/rendering patterns, and this third layer targets the shape and consistency of the information itself. The application still uses deterministic mock financial movements; installing a skill does not certify accounting accuracy, monetary precision, or production readiness.

**Intended bounded application and acceptance criteria (not implemented in this installation commit):**

1. Verify allowed movement/category combinations against backend contracts, then use a discriminated union keyed on `operation_type` rather than unrelated field unions.
2. Treat external JSON as `unknown` until explicit guards validate its required fields and correlated values. Malformed payloads must enter the visible error path, not be silently cast, discarded, or converted to zero-valued financial results.
3. Keep the existing API/query contracts aligned when implementing the date filter, alerts table, and B2B/B2C view; reuse simple existing types rather than introducing a generic API framework.
4. Add focused valid/invalid payload tests and negative type cases for incoherent combinations. Preserve KPI/chart results for valid input and validate with `npm run build` (`tsc -b && vite build`), not bare `tsc --noEmit` against the solution configuration.

**Installation and provenance:** installed project-locally with `npx skills add wshobson/agents --skill typescript-advanced-types --agent github-copilot claude-code --yes --json`. The CLI downloaded the selected skill from GitHub repository `wshobson/agents`; skills.sh was the discovery registry. The canonical [installed instructions](../.agents/skills/typescript-advanced-types/SKILL.md) and [detailed patterns](../.agents/skills/typescript-advanced-types/references/details.md) are available under `.agents/skills/typescript-advanced-types/`, with a Claude Code compatibility path under `.claude/skills/typescript-advanced-types/`. [skills-lock.json](../skills-lock.json) records the source path and content hash. No frontend package dependency was added.

**Installation verification:** `npx skills list` reports all three project skills, including `typescript-advanced-types` from `wshobson/agents`. The installed instructions were read, and the lockfile addition was checked against the selected source. No application source or build configuration changed; this step is installation/documentation, not an executed type-safety audit.

**Review caveats:** the TypeScript skill includes illustrative `any`/assertion-heavy examples and advice to skip production type checking. Do not copy those shortcuts: retain the repository's typed production build and explicit validation. For the performance alternative, local layout measurements and chunk sizes are lab evidence, not proof of good LCP/INP/CLS for real users. Its measurement reference requests equivalent conditions and at least three navigations for headline lab metrics; field data for this localhost app is unavailable.

Sources reviewed: [TypeScript instructions](https://github.com/wshobson/agents/blob/main/plugins/javascript-typescript/skills/typescript-advanced-types/SKILL.md), [worked patterns and guards](https://github.com/wshobson/agents/blob/main/plugins/javascript-typescript/skills/typescript-advanced-types/references/details.md), [performance instructions](https://github.com/addyosmani/web-quality-skills/blob/HEAD/skills/performance/SKILL.md), and [performance measurement workflow](https://github.com/addyosmani/web-quality-skills/blob/HEAD/skills/performance/references/MEASUREMENT.md).

### Checklist corrections (2026-11-16)

- Applied the TypeScript Advanced Types layer to the real financial-data boundary: `FinancialMovement` is now discriminated by `operation_type`, and API JSON is treated as `unknown` and validated before KPI/chart calculations. The runtime validator enforces the backend generator's observed income categories (`sales`/`others`) versus outcome categories (`suppliers`, `operational`, `administrative`, `others`), valid ISO calendar dates, finite numeric amounts, and supported business/operation values. It does not assume amounts are positive or encode integer cents because those rules are not documented by the backend contract.
- Corrected both chart accessible names to derive their month range from actual data, including the empty-data case; marked header and KPI glyphs decorative (`aria-hidden`, non-focusable).
- Updated R13's legacy Spanish-copy assertion to match the existing English UI; corrected R14 draft notes based on `backend/app/routes.py`.
- Verification: frontend tests **20/20 PASS**; `npm run build` and `npm run lint` **PASS**, no build warnings. Integrated browser loaded the UI, but backend was unreachable, so loaded chart labels/data were not visually/accessibly verified in-browser. Skip-link presence and focusability were inspected; keyboard event dispatch was unreliable, so Tab sequence, Shift+Tab, Enter activation and trap absence remain **NOT VERIFIED**. Computed text colors were sampled, but a full numeric contrast audit was **NOT RUN**.

### Internal skill draft (2026-11-16)
[Dashboard API Contracts](../.skills/dashboard-api-contracts/SKILL.md) is a local draft under the requested `.skills/` directory, not an approved team-wide policy. It addresses a repository-specific gap beyond the three community skills: proving that a panel's endpoint, supported filters, business population, and financial meaning agree. In particular, movement business filters use separate routes while analytical endpoints use query parameters; a successful response alone does not establish that a filter was applied. The refined structure explicitly defines the objective/scope, required inputs, expected output, and acceptance criteria. Review completion is distinguished from product implementation acceptance. The old `.agents/skills/dashboard-api-contracts/` draft has been moved rather than duplicated. Load the new file explicitly for the requested read-only trial; do not assume `.skills/` is automatically discovered by every agent. No application change or registry installation accompanies this refinement.

**Explicit-load trial:** an agent read the full skill and followed its review workflow for the planned B2B/B2C top-income tables and comparison chart. Local frontend/backend, facets, and OpenAPI were reachable. The agent produced concrete category/summary requests for each business line, file-level implementation steps, proving tests, and A1-A7 statuses. Readiness was limited to the data-wiring contract; routing/dependency approval and UI implementation remain separate.

**Observed mock-data evidence (2026-11-16, not fixed expectations):** facets yielded `2025-11-01` through `2026-10-28`. Independently grouped raw movements matched the analytical responses: B2B income **615,540.72 USD** and B2C income **642,606.15 USD**, each with 12 monthly summary rows and two income categories (`sales`, `others`). A narrower inclusive range, `2026-01-01` through `2026-03-31`, matched raw filtering and summary income totals of **149,498.45 USD** and **179,962.82 USD**, respectively. These are local mock API checks, not real financial records or proof of a functioning B2B/B2C UI.

**Discriminating denominator check:** because top-5 contains both available income categories, that response alone cannot expose a top-N denominator mistake. Following the refined skill's procedure 7, the agent repeated the full-range category requests with `operation_type=income&limit=1` and each business filter. Both returned HTTP 200: B2B sales **557,903.97 USD** represents **90.6%** of full summary income; B2C sales **574,193.41 USD** represents **89.4%**. Dividing by the returned top-1 subtotal would incorrectly show **100%** in both cases. This strengthens backend contract evidence, not UI verification. The current generator's `_build_movement` in [routes.py](../backend/app/routes.py) allows income in `sales` or `others`; the older R14 draft's "only sales" wording is inaccurate and must not override current source/runtime evidence.

**Actionability and limits:** the report names the proposed `B2bB2cPage`, `B2bB2cCategoryTable`, and `B2bB2cComparisonChart` from the [component specification](../frontend/specs/components.md), requires explicit `operation_type=income`, matching business/date filters, summary-based denominators, and no invented rows to fill a top-5 table. Backend/review evidence supports the checked portions of A1/A2/A4/A7 only. UI request construction, failure/empty states, frontend tests, and builds remain **NOT RUN** for this read-only trial; no product acceptance is claimed. Skill-file checks confirmed the four required sections and all 13 local references. `npx skills list` still lists only the three community installations, so this trial used explicit file loading rather than claiming automatic discovery.

The two evidence tests are outside Vitest's `frontend/` root. A plain `npx vitest run` does **not** discover them; the explicit `--dir` command is required. Bare `npx tsc --noEmit` is not a valid project type-check here; use the app project or build command above.

### Known gaps and constraints

These are observed implementation gaps, not assertions that a fix has been approved:

- **Mock data only:** the current request path has no database, persistence, or external transaction source. The UI must not be described as a live financial-data product.
- **Analytics not fully connected:** backend analytical routes exist, but `App.tsx` currently calls only `/api/metrics`; KPI and chart aggregation runs in the frontend.
- **API origin and proxy differ:** Vite proxies `/api` to `http://backend:8000`, but `App.tsx` defaults to the absolute `http://localhost:8001` origin. The current absolute request bypasses the Vite proxy and may not suit forwarded development environments such as Codespaces.
- **Period label can mislead:** the UI says `2024 - Full Year`, while generated data is relative to the current date.
- **Documentation is stale:** the READMEs describe backend host port `8000` and claim the Vite proxy is the default; Compose publishes host port `8001`, and the current `App.tsx` default is absolute. See the [verification and gap analysis](../verification.md).
- **Development configuration only:** the backend container starts Uvicorn with reload and debugpy, and CORS allows all origins. Production deployment, access control, and security requirements are not established by this repository snapshot.
- **Evidence-strength distinction:** the executable [`coverage audit`](../.agents/rules/_validation/val_rule_coverage.py) confirms that all 25 R-rules have a `Validated` bullet and that rule IDs are indexed; it does not prove that every claim was runtime-tested or audit C-convention evidence depth. The [`validation report`](../.agents/rules/_validation/validation.md) identifies R4, R5, R9, and R10 as not validated by execution. Prefer the report's per-rule strength labels over interpreting marker coverage as runtime coverage.
- **Historical proposal measurements:** [`rules-proposed.md`](../rules-proposed.md) preserves the original static findings and contains measurements later corrected by executable evidence (for example, R17's declaration count and R18's `outcome` count). It remains unchanged as the proposal record; use the validation report and current draft for corrected measurements.

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
