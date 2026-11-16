# Progress — skills and agent-readiness work

**Branch:** `feature/agent-skills` (local only, no pushes)
**Status checked:** 2026-11-16
**Scope:** skills installation/application and documentation. Detailed evidence lives in [README](./README.md); this file is the progress index.

## Skills applied

| # | Skill | Source | Commit | What it changed |
| --- | --- | --- | --- | --- |
| 1 | `accessibility` | `addyosmani/web-quality-skills` | `bbd545d` | Dashboard audit fixes: descriptive title, skip link/`main` target, English API error with `role="alert"`, loading/success/error status with `aria-busy`, `h2` card titles, named chart wrappers, screen-reader-only tables, focus-visible/reduced-motion CSS. |
| 2 | `vercel-react-best-practices` | `vercel-labs/agent-skills` | `a018313` | Literal `React.lazy` for both charts, separate Suspense boundaries, shared `ChartSkeleton`, logged chart error boundary, static description meta tag, layout-stable KPI skeletons. |
| 3 | `typescript-advanced-types` | `wshobson/agents` | `917a92d` | Applied at the `/api/metrics` boundary: discriminated income/outcome domain type and runtime validation of unknown JSON against the observed backend contract. |
| 4 | `dashboard-api-contracts` (internal, authored here) | this repository | not committed yet | Refined draft under `.skills/`, read-only practical trial completed. |

Installed skills live under `.agents/skills/` with `.claude/skills/` compatibility copies; provenance and hashes are in [skills-lock.json](../skills-lock.json). The internal skill is intentionally local and is not listed by `npx skills list` — load it explicitly from `.skills/`.

## Verified changes

- **Current checklist corrections (local, pending commit):** chart period labels now derive from the actual monthly data; decorative dashboard/KPI icons are explicitly hidden from assistive technology; API JSON is parsed from `unknown` using a runtime guard and discriminated domain types. Validation rejects malformed collections, missing/invalid fields, invalid calendar dates, non-finite amounts and category/operation mismatches. The stale R13 language assertion was updated to match the intentional English UI; the R14 draft was corrected against current backend source.
- **Current checks:** `npm test` **PASS** (20 tests across 3 files); `npm run build` **PASS** (`tsc -b && vite build`, no warnings); `npm run lint` **PASS**. Browser loaded the frontend but backend was unavailable (`ERR_CONNECTION_REFUSED`), so API data/loaded-chart rendering were not exercised in this pass. Skip link is present and focusable; the integrated browser did not reliably advance keyboard focus or perform Enter activation, so full Tab/Shift+Tab reachability and activation remain **NOT VERIFIED**. Computed color samples were inspected, but a numeric contrast ratio audit was **NOT RUN**.
- **Accessibility (`bbd545d`):** build passed and the axe scan reported no violations. Earlier caveat: some contrast/table checks were incomplete; keyboard reachability was not rigorously proven.
- **Performance/layout (`a018313`):** `npm run build` passed with no warnings (existing >500 kB warning gone without threshold changes); entry JS 585.87 kB → 188.52 kB, largest chunk 342.30 kB — code splitting, not fewer downloaded bytes (charts still load on first render). Loading vs loaded chart/KPI rectangles were identical at 1440px and 390px. Simulated chart-chunk failure showed the logged error alert while KPIs and the other chart kept working. Lint, type check, and 5 focused tests passed; full suite: 8 pass, 1 pre-existing R13 failure (obsolete Spanish error copy).
- **TypeScript skill (`917a92d`):** CLI discovery, provenance, and canonical/compatibility file hashes verified. No type-safety fixes applied — installation/documentation only.
- **Internal skill trial (uncommitted):** explicit full-file load by an agent, then a read-only review of the planned B2B/B2C feature. Backend/facets/OpenAPI HTTP 200; date range `2025-11-01`–`2026-10-28`; raw movements independently matched summary income: B2B **615,540.72 USD**, B2C **642,606.15 USD** (two income categories, `sales` + `others`). A `limit=1` probe proved the denominator rule: correct shares 90.6% / 89.4% versus an erroneous 100% top-1 subtotal. Acceptance: A1/A2/A4/A7 passed for backend/review scope only; A3/A5/A6 **NOT RUN** (no UI, no frontend tests/build). No feature was implemented.

## Ecosystem skill chosen, and why

Third skill selection compared `wshobson/agents@typescript-advanced-types` against `addyosmani/web-quality-skills@performance` (both discovered with `npx skills find`):

- **Chosen: TypeScript Advanced Types.** Financial data needs consistent shapes: `FinancialMovement` types `operation_type` and `category` independently (incompatible combinations are representable), and `fetchFinancialData` returns `response.json()` with no runtime validation. The upcoming three-feature work adds more API boundaries. Discriminated unions, `unknown` parsing, and guards add a distinct control layer that accessibility (access) and the Vercel skill (delivery/rendering) do not cover.
- **Not chosen: performance.** Valuable, but overlaps substantially with the already-installed Vercel skill; the performance evidence we needed (chunk sizes, layout stability) was obtained directly with measured builds and browser checks.
- **Caveat:** the TypeScript skill contains illustrative `any`/casts and advice to skip production type checking — those shortcuts were explicitly rejected; the typed production build stays.

Detailed rationale and intended bounded application: [README — Third skill](./README.md#third-skill-typescript-advanced-types-2026-11-16).

## Internal skill authored

**`.skills/dashboard-api-contracts/SKILL.md`** — a repository-specific gap that community skills do not cover: proving that a dashboard panel's endpoint, supported filters, business population, and financial meaning agree.

- **Why:** business filters use separate routes (`/api/metrics/b2b`, `/b2c`) while analytical endpoints use query parameters (`business_type=B2B|B2C`); unsupported parameters can be ignored despite HTTP 200; `/categories/top` defaults to `outcome` and returns a truncated list that must not be used as a denominator; `/comparison` is current-vs-previous window, not B2B-vs-B2C.
- **Structure:** exactly four sections — Objective, Defined inputs, Expected output, Acceptance criteria (A1–A7), with review readiness (`READY_TO_IMPLEMENT` / `BLOCKED` / `VERIFIED_IMPLEMENTATION`) separated from product implementation acceptance.
- **Trial:** see Verified changes above. The skill produced actionable, file-level guidance (explicit `operation_type=income`, matching business/date filters, summary-based denominators, no invented top-5 rows) without ambiguity.
- **Known discrepancy:** older R14 draft wording says the generator emits income only for `sales`; current source (`_build_movement` in [routes.py](../backend/app/routes.py)) and runtime evidence show `sales` or `others`. Current source wins over stale prose.
- **Status:** uncommitted local draft, explicit-load only, no registry installation, no application changes.

Detailed record: [README — Internal skill draft](./README.md#internal-skill-draft-2026-11-16).

## Follow-up live accessibility audit

- Backend API was live during the rendered-page audit; dashboard data loaded successfully. The accessibility tree exposed named chart images with associated monthly data tables, KPI and chart regions, and a loaded status. An API failure path had previously been verified to expose an alert and failure status.
- Reproduced the skip-link visibility problem under the browser's `prefers-reduced-motion: reduce` setting: the global reduced-motion rule forces a short transition, so the link's `top` remained `-40px` while focus-visible during the transition. Added `transition: none` to `.skip-link` so it can reveal immediately; CSS diagnostics are clean. A keyboard Tab check at 1440px showed the focused link at y=0 with a 178.6 × 40px rectangle. The browser keyboard sequence at 320px was inconsistent and did not reliably establish focus, so small-viewport keyboard reachability/Enter activation remains **NOT VERIFIED**.
- Validation after the CSS change: frontend build **PASS** (Vite produced no warnings), lint **PASS**, tests **PASS** (20 tests in 3 files). No axe/Lighthouse scan was run in this follow-up; do not claim a complete WCAG audit.

## Working state

- Uncommitted: `memory-bank/README.md` (modified), `memory-bank/progress.md` and `.skills/` (untracked).
- Commits on the branch: `bbd545d`, `a018313`, `917a92d`. Nothing pushed; nothing amended.
- No feature implementation (date filter, alerts table, B2B/B2C view), no new dependency, no router — specifications only, pending explicit approval.