---
name: dashboard-api-contracts
description: Internal draft for reviewing or implementing API-to-panel integration in this financial dashboard. Check endpoint-specific filters, business populations, response semantics, and evidence of correctness. Load this file explicitly when requested; its draft status does not authorize application changes.
---

# Dashboard API Contracts

**Status:** refined draft; explicit-use trial only, not a team-wide policy.
**Source snapshot:** 2026-11-16; recheck current code before using these facts.

## 1. Objective

Ensure that each dashboard panel displays the selected financial population and
meaning, not merely a successful HTTP response with compatible TypeScript types.
Produce a bounded, actionable contract review or implement an explicitly approved
integration with evidence that its results are correct.

### Why this skill is local

The inherited API uses different business-filter mechanisms across endpoints.
Some unsupported parameters are silently ignored, and three feature
specifications exist without their UI implementation. Community accessibility,
React performance, and advanced TypeScript skills do not encode these local
integration semantics.

### Scope and authorization

- In scope: movement/KPI/chart date filters; planned alerts and B2B/B2C
  category/summary panels; directly related requests, mapping, and tests.
- Out of scope without separate approval: deployment, backend contract changes,
  new dependencies/routing, monetary precision changes, replacing the data source,
  and implementing features other than the requested target.
- Review mode is read-only. Implementation requires explicit allowed files and
  behavior changes. Loading this draft is not implementation approval.
- Records currently come from a mock generator, not an external financial feed.

## 2. Defined inputs

Read these from the request and repository. Ask for missing product decisions;
do not fabricate requirements. Derive technical facts from current source.

| Input | Required content |
| --- | --- |
| `mode` | `review` or `implement`; draft-use approval and allowed changes. Default to read-only review when implementation is not authorized. |
| `target` | Named panel/feature, implemented or planned status, and relevant component/specification files. |
| `population` | Date bounds, business line (`all`, `B2B`, `B2C`), operation/category selection, and panels that must share these filters. |
| `meaning` | Grouping, threshold if applicable, displayed units, and denominator for each percentage/total. Distinguish an accepted requirement from a draft proposal. |
| `runtime` | Host/Compose context, frontend URL, effective API origin/proxy, backend reachability, and permitted read-only probes. Never include credentials. |
| `evidence` | Source contracts, existing tests, and sanitized fixtures or generated mock responses with expected values. State when runtime evidence is unavailable. |

### Repository evidence

Read the relevant parts, not unrelated subsystems:

- [Frontend transport and rendered panels](../../frontend/src/App.tsx).
- [Backend handlers and calculations](../../backend/app/routes.py).
- [API specification](../../frontend/specs/README.md),
  [parameter types](../../frontend/specs/param-types.ts),
  [response types](../../frontend/specs/api-types.ts), and
  [component specification](../../frontend/specs/components.md).
- [Vite proxy](../../frontend/vite.config.ts) and
  [environment example](../../frontend/.env.example).
- [Financial helpers](../../frontend/src/lib/financial-utils.ts),
  [frontend tests](../../frontend/src/lib/financial-utils.test.ts), and
  [backend tests](../../backend/tests/test_routes.py).
- [Project rules](../../.agents/rules/project-rules.draft.md), especially R2, R3,
  R13, R16, R19, R24 and C1-C4/C8; distinguish proposals from conventions.

Use handlers and, when reachable, `/openapi.json` for the wire contract; use
calculations/tests for semantics the schema cannot express. Specifications are
intended UI, not implementation evidence. Report source/spec/runtime conflicts
before changing behavior. If runtime is unavailable, continue a static review
with explicit limitations rather than inventing a passing result.

### Local checkpoints to reverify

| Endpoint | Contract and integration trap |
| --- | --- |
| `GET /api/metrics` | Movement array; declares `start_date`, `end_date`, `category`, `operation_type`, but not `business_type`. |
| `GET /api/metrics/b2b`, `/api/metrics/b2c` | Business-specific movement arrays with the same four filters. Path suffixes are lowercase; business values are uppercase. |
| `GET /api/metrics/facets` | Unfiltered options/date-range object; declares no filters. |
| `GET /api/metrics/summary` | Array of `{ period, income, outcome, net }`; supports dates, category, operation, business, and `group_by`. |
| `GET /api/metrics/categories/top` | Array with `total_amount`; supports dates, business, operation, and integer `limit` 1-20. Default operation is **outcome**; no category filter. |
| `GET /api/metrics/alerts` | Array with `outcome_total`, `baseline_average`, `increase_ratio`; supports dates, business, threshold, grouping, but not category/operation. Backend threshold >= 0 differs from the draft UI range 0.01-1.0. |
| `GET /api/metrics/comparison` | Current-versus-previous date-window net comparison, not a two-business-line comparison. |

### Trial input for this repository

```text
mode: review
draft_use_approved: yes
target: planned B2B/B2C top-income category panel
allowed_changes: none
population: both business lines; same inclusive date range derived from facets
meaning: top 5 income categories; percentages of each line's entire income;
         monthly income summaries for totals
runtime: local frontend/backend; read-only HTTP probes permitted if reachable
evidence: current routes/specs and backend-generated mock movements;
          independently calculate expected totals from raw movements
```

## 3. Expected output

Return an actionable report in this order:

1. **Input summary and readiness:** `READY_TO_IMPLEMENT`, `BLOCKED`, or
   `VERIFIED_IMPLEMENTATION`. A review may be ready for implementation, but it
   cannot claim that an unimplemented panel works.
2. **Panel contract map:** one row per panel with endpoint, exact query,
   response shape, business/date population, units/denominator, and file/symbol
   evidence. Include concrete request examples when runtime facts permit them.
3. **Findings and next actions:** identify the failure mode, affected file/symbol,
   smallest proposed change, and test that would prove it. Distinguish proposed
   changes from changes actually made; do not make out-of-scope fixes.
4. **Acceptance results:** report A1-A7 below with evidence, commands/conditions,
   actual outcomes, baseline failures, and explicit unverified checks.
5. **Remaining decisions and limitations:** state what needs approval or further
   evidence before implementation or acceptance.

### Procedure for producing that output

1. Map current behavior separately from the requested target. Do not equate
   committed specifications with implemented filters, tables, or navigation.
2. Resolve actual traffic: `App.tsx` defaults to `http://localhost:8001`; Vite
   proxies `/api` to `http://backend:8000`. An unset API base uses the default;
   an empty string produces relative requests. Absolute requests bypass the
   proxy. Do not change the origin strategy to make a review pass.
3. Serialize only supported parameters. Omit unset `start_date`/`end_date`
   instead of sending empty strings; date bounds are inclusive calendar dates.
   Use uppercase `B2B`/`B2C` queries and lowercase business route suffixes.
   Never treat HTTP 200 as proof that an undeclared parameter was applied.
4. Align related populations. Pass `operation_type=income` explicitly for
   top-income categories, and use matching summary income as the group
   denominator. Never divide by an unfiltered total or assume a truncated top-N
   list is the entire income population.
5. Preserve meaning: alert `increase_ratio=0.3` means 30%, while the current
   `formatPercent` helper expects percentage points. Convert once. The current
   alert baseline uses all preceding returned periods, not a three-period sliding
   window. Surface that mismatch; do not change the algorithm incidentally.
6. Preserve calendar-date semantics and existing money formatting unless
   authorized otherwise. Consult the [TypeScript skill](../../.agents/skills/typescript-advanced-types/SKILL.md)
   for guards/types, but do not confuse typing with runtime validation.
   Keep loading, successful-empty, and failure distinct; never replace failed
   requests or malformed payloads with zero-valued financial success data.
7. Prefer focused semantic checks. For isolation tests include both business
   lines and excluded dates; for aggregate checks independently compute expected
   values. Do not hardcode the generator's current dates, row count, or totals.
   If top-5 includes every available category, it cannot distinguish a full-income
   denominator from a top-N subtotal. Use a permitted read-only `limit=1` probe
   when at least two categories exist, or specify a truncated-response fixture;
   verify that the denominator remains the matching summary's entire income.

## 4. Acceptance criteria

Report **PASS**, **FAIL**, **BLOCKED**, **NOT RUN**, or **N/A** for each item.
Every PASS requires evidence; every N/A requires a scope-based reason.

| ID | Evidence required for implementation acceptance |
| --- | --- |
| A1 | Current source backs each panel's endpoint/query/population/shape map; requirement conflicts are explicitly resolved. |
| A2 | Mixed-business data with excluded dates produces exactly the expected selected rows/totals. Test both lines when filtering changes; empty results alone cannot prove isolation. |
| A3 | Date queries omit unset bounds. If date mapping changes, first-of-month/cross-year cases give identical buckets under UTC and `America/Los_Angeles`. |
| A4 | Totals, percentage denominators, and ratio conversions match independently calculated fixture values. Do not invent extra categories to fill a top-N table. |
| A5 | Relevant empty, HTTP-error, and invalid-payload paths are explicit and distinguishable from legitimate zero results. |
| A6 | Focused tests and the documented frontend build pass with no new unexplained warnings or suppressed checks; unrelated baseline failures are reported separately. |
| A7 | Only authorized files/behavior changed, and the report separates source inspection, executed checks, and unverified claims. |

### Review completion versus implementation acceptance

- A review is complete when it supplies the contract map, concrete file-level
  actions and proving tests, and honest A1-A7 statuses. Read-only API checks may
  verify backend behavior, but cannot prove a planned UI works.
- Mark unexecuted UI/error tests and builds **NOT RUN**; do not mark them PASS
  merely because the guidance describes them. Report the exact checked portion
  of a criterion when evidence is partial.
- An implementation is accepted only when all applicable A1-A7 checks pass.
  Draft-use approval does not waive missing evidence or grant broader scope.

### Validation commands and limits

For frontend code changes, run the focused changed-behavior tests and
`npm run build` from `frontend` (`tsc -b && vite build`). Bare `npx tsc --noEmit`
against the solution configuration is not acceptance evidence. If backend
changes are explicitly approved, run relevant route tests in the configured
Python environment. Missing runtime/DOM tooling is a reported limitation, not
permission to claim success or install new dependencies.
