# Project rules — draft

**Status: DRAFT. Not yet authoritative.** This is the single working file for agent and contributor guidance in this repository.

It is a condensed, project-specific derivative of [`../../rules-proposed.md`](../../rules-proposed.md), which remains the historical proposal record: it carries the original finding catalog, status key, open decisions, and rule-to-fact map. For a factual disagreement, prefer newer executable evidence in `_validation/` over the proposal's earlier static measurements; update this draft to reflect that evidence without rewriting the protected proposal.

Rule IDs (`R1`–`R25`, `C1`–`C8`) are the same IDs used in `rules-proposed.md`, so every entry below is traceable back to its evidence row without duplicating it here.

Evidence for every rule was gathered by static inspection on **2026-11-03**. Static inspection only — no tests, linters, or containers were executed at that time.

On **2026-11-03** the draft was checked against executable probes where feasible and against measured or read evidence where runtime execution was not possible; that pass corrected several entries. The evidence is reproducible and committed under [`_validation/`](./_validation/), with a README that lists every artefact and how to re-run it. A **"Validated"** bullet means the claim has supporting evidence, not necessarily a runtime test; the evidence-strength marker identifies whether it was **Executed**, **Measured**, **Read**, or **Not executable**. **"In practice"** is guidance derived from a repository fact rather than a separate measurement.

The current coverage audit finds that **all 25 R-rules carry a `Validated` bullet** and that all 8 C-conventions are present in the table. `_validation/val_rule_coverage.py` checks R-rule marker presence and ID/index consistency; it does not certify runtime execution or measure C-convention evidence depth. CORS behavior (R4) and cold-start failure behavior (R5) were not exercised. Docker image builds (R9, R10) have since completed, though one successful build does not prove reproducibility. Other evidence includes executed tests, mechanical measurements, and source reads; the distinction is marked per rule rather than averaged away.

**Evidence strength.** Not all rules could be tested to the same depth, and the markers say which is which:

| Marker | Meaning |
| --- | --- |
| **Executed** | A probe or test was run and produced a measured result (a status code, a rendered payload, a count, a compile error). |
| **Measured** | The artefact was parsed or counted mechanically (AST, import graph, regex over source), with no runtime behaviour involved. |
| **Read** | Confirmed by reading source that cannot be executed in this environment. Trustworthy for a fact, weaker than a run. |
| **Not executable** | The rule is about a deployment or failure condition that cannot be produced here without changing the system. |

Where a rule rests on **Read** or **Not executable**, that is stated in the entry itself rather than hidden. A reviewer should treat "Read" as a starting point, not as a clearance.

Documentation of constraints only — this file does not authorise a refactor and describes no approved change to the current snapshot.

---

## How to use this file

1. Read section 10 first. Those are conventions the codebase already follows; a change that breaks one is a regression.
2. Find the section matching the area you are about to touch.
3. If a rule says a decision is open, treat it as a question to raise, not a directive to apply.

**Status values**

| Status | Meaning |
| --- | --- |
| **PROPOSED** | Behaviour future work should avoid, preserve, or consciously decide on. Not a defect report. |
| **CONFIRMED** | Convention already followed in the code, recorded so it survives refactors. |
| **DEPLOYMENT** | Binding only once the API is exposed outside local development or serves non-public data. |

**Rule anatomy.** Every entry states a specific `Name`, its `Scope` (the files it applies to), the `Rule` itself, and `Why` (the repository fact behind it). A rule without a verifiable fact does not belong in this file.

**Index**

| Section | Rules |
| --- | --- |
| 1. Architecture and module boundaries | R17, R6, R11, R16 |
| 2. Data correctness and time handling | R1, R2 |
| 3. API contract and typing | R3, R19, R14 |
| 4. Naming and domain language | R18 |
| 5. Testing and verification | R21, R22, R12 |
| 6. Persistence and data access | R20 |
| 7. UX, errors and accessibility | R24, R25, R13, R5, R7 |
| 8. Documentation and agent guidance | R23, R15 |
| 9. Build, deployment and security | R4, R8, R9, R10 |
| 10. Conventions in force | C1–C8 |

---

## 1. Architecture and module boundaries

Applies when adding an endpoint, moving code between modules, or wiring the frontend to the backend at development time.

### R17 — Do not let one module host the whole domain

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `backend/app/*.py`
- **Rule:** One module must not host the domain models, the data source, the aggregations, and the HTTP handlers together. Split by responsibility before adding routes.
- **Why:** `backend/app/routes.py` is a single 391-line module with 32 named top-level declarations — 6 Pydantic models, the `Literal` aliases, `_year_for_month`, `_build_movement`, `generate_mock_movements`, 8 calculation helpers, and 9 route handlers. Every new endpoint grows the same file.
- **In practice:** if a change adds an endpoint, a model, and a calculation together, that is the signal to ask whether the split is now required rather than deferred again.
- **Validated — measured, and the count in the draft was wrong.** Parsing `routes.py` with `ast` gives **32** named top-level declarations, not 35: 6 `ClassDef` (models) + 20 `FunctionDef` + 6 module-level assignments (`OperationType`, `Category`, `BusinessType`, `GroupBy`, `OUTCOME_CATEGORIES`, `router`). Imports (7 statements) are excluded. The 20 functions decompose exactly as described — 9 route handlers, 3 generator helpers, 8 calculation helpers — so only the total was off by three.
- **Validated — the HTTP surface really is 9 endpoints in one file:** `/health`, `/api/metrics`, `/metrics/facets`, `/metrics/summary`, `/metrics/categories/top`, `/metrics/comparison`, `/metrics/alerts`, `/metrics/b2b`, `/metrics/b2c`, all declared as `@router.get` in the same module.
- **Validated — the concentration is measurable, not a matter of taste:** **311 of 391 lines (80%)** sit inside a named definition, and the largest is `get_metrics_comparison` at 34 lines. There is no single runaway function; the problem is breadth, which is why the rule asks for a horizontal split rather than a refactor of any one handler.
- **Trap for anyone writing this probe:** the routes use an `APIRouter`, so the decorators are `@router.get`, **not** `@app.get`. A check for `@app.` returns zero and would wrongly report "no routes in this module".
- **Trap for anyone re-running the probe:** `val_r17_structure.py` prints a `TOTAL 39` line that does **not** match the 32 above. The script's total includes the 6 `ImportFrom` and 1 `Import` statements (32 + 7 = 39); the 32 counts named declarations only. Both numbers are correct — they answer different questions. Reading `TOTAL 39` as a contradiction and "correcting" the draft back to 39 would introduce the error this validation removed. The same script also lists `filter_movements` at line 125, which is a **different** function from `filter_movements_by_date` at line 107; both exist, and only the latter is imported by the tests.
- **Reproduced by:** `.agents/rules/_validation/val_r17_structure.py`.

### R6 — Never reseed a process-global generator from request code

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/app/routes.py`
- **Rule:** Never reseed a process-global random generator from request-handling code; use a locally seeded instance.
- **Why:** `generate_mock_movements` calls `random.seed(seed)` on every request, reseeding Python's module-global generator. Output stays deterministic, but any other code relying on `random` in the same process inherits a sequence reset by an HTTP call, making future randomised behaviour order-dependent.
- **In practice:** `random.Random(seed)` gives the same determinism without the global side effect.
- **Validated:** three draws from a freshly seeded global generator are `[917, 893, 581]` undisturbed, but `[108, 326, 247]` after a single request handler runs. The reseed is observable and the stream is genuinely reset, exactly as the rule describes. Reproduced by `test_defect_r6_generator_does_not_reseed_global_random`.

### R11 — One source of truth for sample financial data

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/src/lib/mock-data.ts`
- **Rule:** A repository must have one source of truth for sample financial data. Additional datasets must be declared as fixtures and kept aligned.
- **Why:** the file hardcodes a separate 2024 dataset (`mockMovements`) that no module imports. It duplicates the concept of the backend generator with no test asserting agreement, so fixtures and documentation can drift from the data the app actually renders.
- **In practice:** before adding data to this file, check whether it is a fixture a test consumes or dead weight.
- **Validated — zero importers, confirmed two ways:** a case-insensitive search for `mock-data` across `frontend/src`, `frontend/*.ts`, `frontend/*.json`, `index.html`, and `backend` returns **nothing**. The file exists (7,097 bytes, 72 lines) but no module, test, or config references it. It is dead weight today.
- **Validated — and it has already drifted:** the fixture holds **57 movements, all in calendar year 2024, spanning 12 months**. The backend generator it nominally mirrors produces **360 movements across two calendar years** (see R1/R12). So the "no test asserts agreement" risk is not hypothetical — the two datasets already disagree on both record count and year span, and nothing detects it.
- **Consequence:** if this file were adopted as a test fixture tomorrow, every assertion written against it would encode 2024-only, 57-record behaviour that no endpoint produces. That is the concrete cost of the duplicated source of truth.

### R16 — A Compose-only proxy target must be environment-driven

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/vite.config.ts`, `frontend/src/App.tsx`
- **Rule:** Keep the browser API origin strategy aligned with its execution environment. Treat `backend:8000` as a Compose service address, not as the host-published API origin; if the Vite proxy is used outside Compose, make its target configurable.
- **Why:** the proxy forwards `/api` to `http://backend:8000`, while Compose publishes the backend as host `8001` to container `8000`. `App.tsx` currently calls the absolute `http://localhost:8001` origin and bypasses the proxy. The service name may resolve differently through a host DNS search suffix, so it is not safe to assume that a host resolution reaches the Compose service.
- **In practice:** the two mechanisms currently coexist. Changing one without the other silently swaps which origin serves data.
- **Validated — configuration measured, DNS behavior kept as a caveat:** the Vite target is `http://backend:8000`, Compose publishes `8001:8000`, and `App.tsx` bypasses the proxy via its absolute `http://localhost:8001` default. A host lookup in the validation environment returned `backend.wind3.hub`, which is not evidence that the Compose service is host-reachable; it demonstrates why the service name must not be assumed to have portable host semantics. Docker runtime behavior was not exercised.
- **In practice:** treat the proxy as currently unused until `App.tsx` switches to a relative URL. Do not assume the proxy is serving traffic.

---

## 2. Data correctness and time handling

Applies when a figure is rendered with a period label, or when a date is parsed, compared, or bucketed.

### R1 — A displayed period must come from the data

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `backend/app/routes.py`, `frontend/src/App.tsx`
- **Rule:** A displayed period must be derived from the data actually rendered, never hardcoded independently of the payload's date range.
- **Why:** `_year_for_month` maps months before the current month to the current year and the remaining months to the previous year, so the 360 generated movements always span two calendar years ending in the current month. `App.tsx` always renders `2024 - Full Year`. At the snapshot date the payload covers 2025-11 to 2026-10 while the header claims 2024.
- **In practice:** the header and the payload are two independent facts today. Any change to the generator's window makes the label wrong without any code error.
- **Open decision:** fixed calendar year or rolling window. See `rules-proposed.md`.
- **Validated:** `generate_mock_movements(seed=None)` produced `first=2025-11-01`, `last=2026-10-28`, `count=360`, `years=[2025, 2026]` — a rolling window spanning two calendar years, while the header renders `2024 - Full Year`. The header is wrong in **both** its year and its "full year" claim, so a partial fix that only corrects the year would still be wrong.

### R2 — Treat `create_date` as a calendar date, not an instant

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `frontend/src/lib/financial-utils.ts`, `frontend/src/lib/financial-utils.test.ts`
- **Rule:** Read year/month from the string, or use UTC getters consistently. Never mix UTC parsing with local getters.
- **Why:** `create_date` is a date-only string, but `new Date("YYYY-MM-DD")` parses as UTC midnight and `toYearMonthKey` then reads it with local `getFullYear()` / `getMonth()`. In any time zone west of UTC a movement dated the 1st aggregates into the previous month. The cross-year test uses the 3rd, 5th, and 8th, so it passes while this boundary is untested.
- **In practice:** when adding a date test, include a movement dated the 1st. That is the day that exposes the bug.
- **Validated:** `_validation/r2_date_probe.js` parses four date-only strings under two zones. At `America/Los_Angeles` (UTC−8) it returns the **previous month for every 1st**: `2026-01-01` → `2025-12`, `2026-03-01` → `2026-02`, `2026-12-01` → `2026-11` — 3 of 4 dates wrong. At `Europe/Rome` (UTC+1, this machine's zone) it returns **0 of 4 wrong**.
- **Consequence for reviewers:** the defect is *not reproducible on the current development machine*. A reviewer who checks "it works for me" will clear this rule. Validation of any date fix must set `TZ=America/Los_Angeles` explicitly, or the test proves nothing. A test written only on a UTC-positive machine is a false negative, which is why R21's "the environment comes first" applies to the clock as much as to the DOM.

---

## 3. API contract and typing

Applies when adding a filter, a query parameter, a path segment, or a client type that mirrors a response model.

### R3 — Filter parameters must be uniform across endpoints feeding one view

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `backend/app/routes.py`
- **Rule:** If a dashboard applies one population filter, every endpoint it calls must accept it.
- **Why:** `summary`, `categories/top`, `comparison`, and `alerts` accept `business_type`; `/api/metrics` does not and exposes separate `/b2b` and `/b2c` routes instead. A view applying one B2B/B2C selection to both movement rows and analytics must special-case `/api/metrics`, so panels can silently show different populations.
- **Validated — worse than stated:** `/api/metrics` does not reject the filter, it **ignores it**. `GET /api/metrics?business_type=B2B` returns **200 with all 360 rows**, byte-identical to the unfiltered call, and `?business_type=nonsense` also returns 200. FastAPI drops undeclared query parameters, so a caller who applies the dashboard filter to this endpoint gets the full population *and a success status*. A 422 would at least be visible; silence is not. See `_validation/test_rules_validation.py::test_defect_r3_*`.
- **In practice:** any client-side filter wiring must treat `/api/metrics` as unfiltered. Do not assume a 200 means the filter was honoured.

### R19 — Same filter, same shape

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/app/routes.py`
- **Rule:** Express the same filter the same way on every route. Do not expose one filter as both a path segment and a query parameter.
- **Why:** business type is a path segment in `/api/metrics/b2b` and `/api/metrics/b2c` but a `business_type` query parameter on `summary`, `categories/top`, `comparison`, and `alerts`. A client cannot build one filter-application step, and generated API documentation presents two different shapes for the same concept.
- **Validated — the two shapes also disagree on spelling:** `BusinessType = Literal["B2B", "B2C"]` is **uppercase**, while the path segments are **lowercase**. So `?business_type=b2b` is a `422 literal_error` on `/api/metrics/summary`, even though `/api/metrics/b2b` is a valid route. One user-facing "B2B" selection therefore has two incompatible encodings depending on which endpoint receives it. See `_validation/test_rules_validation.py::test_defect_r19_*`.
- **In practice:** the path form is live and filtered (`/b2b` → 203 rows, `/b2c` → 157 rows); the query form is live but case-strict. Unifying them changes a public URL, so it is a breaking change, not a tidy-up.
- **Relationship to R3:** R3 and R19 are the same underlying inconsistency seen from the caller side and the route side. Resolving one without the other leaves it half-fixed.

### R14 — Model correlated fields together

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/src/lib/financial-types.ts`, `backend/app/routes.py`
- **Rule:** When an API constrains one field by another, the client type must not accept combinations the API cannot emit.
- **Why:** `FinancialMovement` types `category` and `operation_type` independently, so `{ operation_type: "outcome", category: "sales" }` compiles, yet `_build_movement` only emits `sales` for income and draws outcomes from `OUTCOME_CATEGORIES`. Fixtures and UI filters can encode impossible states that no layer rejects at runtime.
- **In practice:** a discriminated union keyed on `operation_type` expresses the constraint the API already enforces.
- **Validated:** a probe object `{ operation_type: "outcome", category: "sales" }` and its mirror `{ operation_type: "income", category: "suppliers" }` both compile with **exit 0** against `tsconfig.app.json`, while the reachable combination compiles alongside them. TypeScript cannot tell the three apart, so the type gives no protection here.
- **Validated — the check itself is easy to get wrong:** `npx tsc --noEmit` in `frontend/` **checks nothing**, because the root `tsconfig.json` is a solution file (`"files": []` plus `references`). It exits 0 on any input. A type-level rule must be verified with `npx tsc --noEmit -p tsconfig.app.json`, or with `npm run build`, which runs `tsc -b`.

---

## 4. Naming and domain language

Applies when naming a type, a field, an aggregate, or a UI label that refers to money direction.

### R18 — One domain term per money direction

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/app/routes.py`, `frontend/src/lib/*.ts`, `frontend/src/components/dashboard/*.tsx`
- **Rule:** Pick one term and apply it to types, fields, aggregates, and UI labels. Do not pair two terms for the same concept, and do not name an aggregate with a singular noun.
- **Why:** `OperationType = Literal["income", "outcome"]` pairs a standard term with a non-standard one; `OUTCOME_CATEGORIES` derives from it; totals are named `totalOutcome` in `KPIMetrics` and `outcome_total` in `MetricsAlert`, while `summarize_movements` keys the accumulator as `values["outcome"]`. The token `outcome` appears **108 times** across backend and frontend (83 as a whole word), so the term is load-bearing and cannot be renamed in one place.
- **Validated — measured, and the earlier figure was wrong:** an earlier version of this rule said "91 times" with a breakdown of 31 / 47 / 12. Re-measured by `_validation/val_r18_recount.py` (excluding `node_modules`, `.git`, and every probe directory): **108** substring occurrences in 10 files, of which **92** are in product code and 16 in test files; **83** whole-word occurrences. The correct per-area split is `backend/` **33**, `frontend/src/lib/` **54**, `frontend/src/components/` **18**, `frontend/src/App.tsx` **3**. The total was near enough; the breakdown was not.
- **Validated — and a third of the weight is in a file nothing imports:** `frontend/src/lib/mock-data.ts` alone accounts for **33 of the 92** product occurrences (36%), and it has **zero importers** — a repo-wide search for `mock-data` across `frontend/src`, the frontend config files, `index.html`, and `backend/` returns nothing. The file is dead code whose contents nonetheless set the vocabulary a reader is likely to copy. Any cost estimate for the rename should not treat those 33 occurrences as if they were live call sites, and any fix that starts by deleting the dead file gets 36% of the work for free.
- **Validated — why a misleading name is a defect and not a preference:** `MetricsAlert.increase_ratio` is computed as `(outcome - baseline) / baseline`, a **fractional deviation**, so `0.5917` means *+59.17%*. Reading it as a multiplier and asserting `increase_ratio > 1` is the natural mistake, and it fails on correct data: a live alert batch returned `increase_ratio: 0.5917` for a period that genuinely exceeded its baseline. A name that invites an off-by-one-orders-of-magnitude reading costs a future reader real debugging time, which is what this rule is protecting against.
- **In practice:** treat `outcome` as a rename that crosses backend models, aggregation keys, API response fields, TypeScript types, and JSX labels. A partial rename is worse than none: the two vocabularies would then coexist.
- **Aggregate naming:** `totalOutcome` (singular) names a sum, `OUTCOME_CATEGORIES` names a set. When adding an aggregate, use the plural form for collections and a `total`/`sum` prefix for sums, consistently across backend and frontend.
- **Open decision:** whether `outcome` is kept or replaced by `expense`. Both answers are valid; either must be applied everywhere at once. See `rules-proposed.md`.

---

## 5. Testing and verification

Applies when adding a test, changing a component branch, or deciding whether existing coverage is real.

### R21 — Component behaviour needs a test, and the DOM environment is a prerequisite

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `frontend/src/**/*.test.tsx`, `.agents/rules/_validation/**`, `frontend/package.json`, `frontend/vite.config.ts`
- **Rule:** Loading, error, empty, and conditional branches need a test before the component is considered covered. Adding a DOM test environment is a prerequisite, not an optional extra.
- **Why:** `frontend/src/lib/financial-utils.test.ts` is the only test file in the repository; every component in `frontend/src/components/dashboard/` has zero tests despite containing `loading` branches. `frontend/package.json` declares no `@testing-library/*`, `jsdom`, or `happy-dom`, and `vite.config.ts` has no `test` block, so Vitest runs in a Node environment with no DOM.
- **In practice — narrowed by the run:** a `.test.tsx` that *interacts* with a component (clicks, state changes, focus) cannot be written today: importing `@testing-library/react` fails at import time, before any assertion. A `.test.tsx` that only asserts on **rendered markup** can be, and was. The original wording "writing a `.test.tsx` today would fail at import time" is therefore too broad.
- **Validated — both halves confirmed separately:** a minimal `<KPIRow metrics={null} loading={false} />` test dies with `Cannot find package '@testing-library/react'` (0 tests run), and after removing that import, `typeof document` and `typeof window` are both `"undefined"` under Vitest — so installing the library alone would still not be enough; the `test.environment` must be set as well. Two independent prerequisites, not one.
- **Validated — file placement, corrected and then re-measured:** Vitest's root is `frontend/`, so a test placed outside it is not discovered by a plain run. Inside the root, a test may live in **either** `frontend/src/` **or** a sibling folder such as `frontend/validation/`, and both were discovered by a plain `npx vitest run`. The distinction matters: `tsconfig.app.json` has `"include": ["src"]`, so a test under `src/` is part of the app type-check and a test outside it is not. Probes that intentionally fail to compile belong outside `src/`.
- **Validated — re-measured after the probes were consolidated under `.agents/rules/_validation/`:** all evidence now lives in one folder, which is **outside Vitest's root**. A plain `npx vitest run` in `frontend/` therefore reports only the product suite (**1 file, 5 tests**) and silently omits the probes; `npx vitest run --dir ../.agents/rules/_validation` reports **2 files, 7 tests**, and the `@` alias still resolves because the root remains `frontend/`. The trade-off is real and worth stating plainly: consolidation makes the evidence easy to find but makes the probes **not run by default**, so the command must be documented or they rot. An earlier version of this bullet claimed a plain run discovered both locations; that was true only while the probes sat inside `frontend/` and is false now.
- **Validated — and a partial path exists today:** the "fails at import time" claim holds for `@testing-library/*`, but **not** for component tests in general. `react-dom/server`'s `renderToStaticMarkup` is available with no new dependency and runs in the plain Node environment, so a `.test.tsx` that asserts on rendered markup **does** work now. R24 was validated exactly this way (3 tests passing, no jsdom, no `document`). Confirm the absence is total: `node_modules/jsdom`, `node_modules/happy-dom`, and `node_modules/@testing-library` are all missing, and `vite.config.ts` has no `test` block.
- **Consequence for the rule:** what is genuinely blocked is *interaction* — clicks, state changes, focus, anything needing a live `document`. What is **not** blocked is markup, conditional branches, placeholders, and attribute checks. A rule that says "components cannot be tested" is too broad; the accurate statement is "components cannot be tested *for behaviour*, but can be tested *for output* today".
- **Validated — the suite the rule asks for now exists and passes:** at the end of the audit, `npx vitest run` in `frontend/` plus `npx vitest run --dir ../.agents/rules/_validation` together covered **12 tests** (the original 5 in `financial-utils.test.ts`, plus 4 markup tests for R13 and 3 for R24), with `npx tsc --noEmit -p tsconfig.app.json`, `npx tsc -b`, and `npx eslint .` all exiting 0. The baseline before this audit was 1 test file. The delta is the concrete answer to "is the rule followable with what is installed": yes, for output, with no new dependency.
### R22 — Cover rejection paths and value-level outcomes

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/tests/test_routes.py`
- **Rule:** A test that cannot fail when the computation is wrong is not a test of that computation.
- **Why:** `test_routes.py` has no case for an invalid enum value (the 422 from `Literal` validation), no assertion on `alerts` values (`if payload:` guards the only assertions), and no case for `build_metrics_facets([])`. `test_metrics_comparison_returns_delta_fields` asserts only key names for dates outside the generated range.
- **In practice:** three concrete gaps are named above and each maps to another rule here — the `Literal` gap to section 3, the empty-list gap to R7, the key-only assertion to R12.
- **Validated:** the three missing tests are cheap and all three pass once written — invalid `operation_type` → 422, invalid `business_type` → 422, `limit=21` → 422, and the alerts assertions. The rejection paths behave correctly; the gap is purely that nothing checks them, so a regression there would ship silently.
- **Validated — the alerts test is weaker than it looks:** `test_metrics_alerts_returns_anomaly_candidates` asserts `set(first.keys())` on `payload[0]` **inside `if payload:`**. An empty alert list, a wrong `outcome_total`, or a wrong `increase_ratio` all pass. Value-level assertions added in `_validation/test_rules_validation.py` cover this and pass today.

### R12 — A generator test must assert the semantic range it claims

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/tests/test_routes.py`
- **Rule:** Asserting count and ordering does not prove the generated range is correct.
- **Why:** `test_generate_mock_movements_returns_full_year_sorted_data` asserts only `len == 360` and sorted order, so the two-calendar-year span behind R1 passes unnoticed. The name also claims a "full year" while the generator produces a rolling window.
- **In practice:** assert the first and last month the generator produces, derived from the same rule the code uses, so a change to `_year_for_month` fails the test.
- **Validated:** the shipped test's blind spot is reproducible — a check asserting the real span finds **2 distinct years and 12 distinct months**, i.e. two calendar years for a test whose name says "full year". Asserting `len(years) == 1` fails, which is precisely the assertion R1 needs and the shipped test omits.

**Current baseline:** **15** backend tests in `backend/tests/test_routes.py` (verified by `pytest --collect-only -q` and by counting `^def test_`: both report 15); 1 frontend test file (`financial-utils.test.ts`, 5 tests). No DOM test environment is configured. See C8 for the coverage pattern to extend.

---

## 6. Persistence and data access

Applies before any change that introduces a database, a cache, a file store, or an external data source.

### R20 — Data acquisition must not live inside request handlers

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `backend/app/*.py`, `backend/requirements.txt`
- **Rule:** Adding persistence requires an explicit boundary: a data-access module, a schema/migration source, and configuration read from the environment. Until then, the mock source must be visibly the only source.
- **Why:** no persistence dependency or import exists. `backend/requirements.txt` lists only `fastapi`, `uvicorn[standard]`, `debugpy`, `pytest`, `pytest-cov`, `httpx`, and a search of `backend/app/*.py` for `sqlalchemy`, `sqlite`, `psycopg`, `databases`, `sessionmaker`, `import os`, or `getenv` returns nothing. Instead, all 9 handlers call `generate_mock_movements(seed=42)` inline, so the data source, the request lifecycle, and the absence of configuration are fused in the route layer.
- **In practice:** the current architecture has no seam for a real repository. A first database change touches every handler at once, because each handler independently constructs its data. Introducing the seam is a separate change from switching the source.
- **Boundary this rule requires:** (1) a data-access module owning queries, so handlers do not know how data is produced; (2) a schema or migration source, so the shape of stored data is reviewable independently of the code that reads it; (3) configuration read from the environment, so connection details are not literals in `backend/app/`.
- **Current state:** no database, no cache, no persistence layer, no environment-variable reading in the backend. All data is a seeded in-memory generator invoked inline by every route handler.
- **Open decision:** whether persistence is in scope for the next iteration. See `rules-proposed.md`.
- **Validated — the absence is total, checked by import graph not by keyword.** Parsing every backend module with `ast` and collecting the full import set yields exactly: `__future__`, `app`, `collections`, `datetime`, `fastapi`, `pydantic`, `random`, `typing`. **Zero** of the 18 database clients probed (`sqlalchemy`, `sqlite3`, `psycopg2`, `asyncpg`, `redis`, `alembic`, `motor`, `duckdb`, …) appear. `os`, `dotenv`, `pydantic_settings`, and `configparser` are **absent too** — `os.environ` and `os.getenv` are never called anywhere in `backend/`.
- **Validated — the fusion with the request lifecycle is exact:** **8 of 9** handlers call `generate_mock_movements` directly — `get_metrics`, `get_metrics_facets`, `get_metrics_summary`, `get_top_categories`, `get_metrics_comparison`, `get_metrics_alerts`, `get_b2b_metrics`, `get_b2c_metrics`. The ninth, `/health`, does not, which is correct since it reports liveness only. So the "every handler constructs its own data" claim is literally true for every handler that serves data, and the seam a database would need does not exist.
- **Reproduced by:** `.agents/rules/_validation/val_r20_r4_absence.py`.

---

## 7. UX, errors and accessibility

Applies when handling a request failure, rendering a placeholder, exposing a chart, or relying on service startup order.

### R24 — A failed load must look different from an empty dataset

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `frontend/src/App.tsx`, `frontend/src/components/dashboard/kpi-row.tsx`
- **Rule:** Placeholder values must not be indistinguishable from real zero.
- **Why:** on failure `App.tsx` sets only an error string, then `finally` sets `loading` to `false` while `metrics` stays `null`. `KPIRow` therefore renders all four cards with the literal `—` placeholder and no error styling, alongside a red banner. All four KPI figures appear as absent-but-value-less cards, so a backend outage is presented as a dashboard with no numbers.
- **In practice:** the red banner is the only distinguishing signal and it sits apart from the cards. A screenshot of the failed state resembles an empty account.
- **Validated — and it is structurally unfixable at the card level:** a rendered comparison of `<KPIRow metrics={null} loading={false} />` against `<KPIRow metrics={null} />` produces **byte-identical markup**. There is no prop that carries "this absence is a failure", so no card-level styling can express the difference. The component accepts `metrics: KPIMetrics | null` and `loading?: boolean` and nothing else; the empty and failed inputs collapse to the same value before rendering.
- **Validated — what a user actually sees:** four value cells containing `—` and no explanatory text. Counting only the value cells (`>—</p>`) yields exactly 4. A naive count of U+2014 yields 5, because the Profit card's helper text is "Net profit — income minus total outcome"; that prose dash is a trap for anyone writing this assertion later.
- **Validated — the loading branch is the only branch:** `kpi-card.tsx` has exactly one conditional, `if (loading)`. There is no separate empty branch to extend. Distinguishing failure from emptiness therefore requires a **new prop on both components** (`hasData`, or an `error`/`status` union), not a styling change — which is why this rule cannot be satisfied by editing `kpi-card.tsx` alone.
- **Reproduced by:** `.agents/rules/_validation/r24-empty-vs-loading.test.tsx` (3 tests, passing, no DOM environment required). Not discovered by a plain `npx vitest run`; requires `--dir ../.agents/rules/_validation` from `frontend/`.

### R25 — A chart needs a non-visual equivalent

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/src/components/dashboard/income-outcome-chart.tsx`, `frontend/src/components/dashboard/profit-percent-chart.tsx`, `frontend/src/App.tsx`
- **Rule:** A chart must expose an accessible name and a text or table equivalent for its series.
- **Why:** both chart components render Recharts `LineChart` inside `ResponsiveContainer` with no `role`, `aria-label`, `figcaption`, or data table. `App.tsx` supplies `aria-label` only on the two `<section>` wrappers, so a screen-reader or text-only consumer reaches a section label and no values.
- **Validated:** scanning both `*-chart.tsx` files for `role=`, `aria-label`, `figcaption`, `<table`, `<title`, `aria-describedby` returns **none of them** in either file. `App.tsx` has exactly two `aria-*` attributes, both on `<section>` wrappers (lines 57 and 62). The rule's description matches the code exactly.

### R13 — Preserve the captured error and match the UI language

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/src/App.tsx`
- **Rule:** Error handlers must preserve the thrown error, and user-facing text must use the language of the surrounding UI.
- **Why:** `.catch(() => { ... })` discards the thrown error, including the HTTP status built by `fetchFinancialData`, and replaces it with the fixed Spanish string `"No se pudo cargar la informacion financiera..."` in an otherwise English UI. Users cannot distinguish a down backend from a bad response, and maintainers lose the status code.
- **Validated — the status is built and then thrown away:** `fetchFinancialData` constructs `Failed to fetch financial data: ${response.status}`, so the diagnostic exists. The handler is `.catch(() => {` with **no parameter binding**, so that error is unreachable by construction. Both halves are asserted in `.agents/rules/_validation/r13-error-handling.test.ts` (4 tests, passing).
- **Validated — the replacement carries no diagnostic:** the message is a fixed literal with no interpolation, no status digits, and no reference to `response`. There is no path by which a caller learns what went wrong.
- **Validated — language is inconsistent and the text is unaccented:** the message is `"No se pudo cargar la informacion financiera. Revisa la API de backend."` inside a UI whose other strings are English (`period="2024 - Full Year"`, `"Total Income"`, `"Profit Margin"`). It is also unaccented Spanish — correct Spanish is `información`, the shipped text is `informacion` — so even a Spanish-speaking user reads it as machine-generated. A probe for the accented form returns false.
- **Why this task could not be a render test:** the handler lives inside `useEffect`, which never runs during `renderToStaticMarkup`. The rule is therefore validated by asserting the source contract. This is a real limitation to state plainly, not a shortcut: a future DOM environment would let it be tested behaviourally.
- **Reproduced by:** `.agents/rules/_validation/r13-error-handling.test.ts` (4 tests, passing). Not discovered by a plain `npx vitest run`; requires `--dir ../.agents/rules/_validation` from `frontend/`. It reads `App.tsx` through Vite's `?raw` import rather than `node:fs` — see the verification note in section 10 for why the latter breaks the build.

### R5 — Startup ordering is not readiness

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `docker-compose.yml`, `frontend/src/App.tsx`
- **Rule:** A single fetch on mount with no retry must not be the only path to data when a dependency may still be starting.
- **Why:** Compose declares only `depends_on` with no healthcheck, which orders startup but does not wait for API readiness. `App.tsx` fetches once in a `useEffect` with an empty dependency array, never retries, and offers no reload action, so a failed first request stays visible until a manual browser refresh.
- **In practice:** `depends_on` guarantees the container started, not that Uvicorn accepts connections. This is the mechanism by which R24's failed state is reached on a cold start.
- **Validated — no readiness signal exists anywhere in the stack.** `docker-compose.yml` declares `depends_on: - backend` (list form, no condition) and **no `healthcheck` on either service**. The backend does expose `GET /health` returning `{"status": "ok"}` at `routes.py:243`, but nothing consumes it: there is no Compose healthcheck, no `depends_on: condition: service_healthy`, and no frontend probe. The endpoint is a ready-made readiness signal that is simply unwired.
- **Validated — the retry surface is genuinely absent:** `App.tsx` calls `fetchFinancialData()` once inside `useEffect(..., [])`. There is no retry, no backoff, no `AbortController` timeout, and no user-triggered reload control. A single cold-start rejection is terminal for that page view.
- **The concrete chain, now fully traced:** container starts → `depends_on` satisfied before Uvicorn binds → first `fetch` rejects → `.catch` sets a Spanish banner → `finally` sets `loading=false` with `metrics=null` → cards render `—` (R24) → user must refresh manually. Every link in that chain is verified code, not inference.
- **Why this is a rule and not a bug report:** the fix is two independent changes that must both land — a `healthcheck` on the backend with `condition: service_healthy` in Compose, and a retry or an explicit retry affordance in `App.tsx`. Either alone leaves the failure reachable.

### R7 — Define empty-input semantics in range helpers

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/app/routes.py`
- **Rule:** Helpers that derive a range from a collection must define empty-input semantics instead of indexing the first and last element.
- **Why:** `build_metrics_facets` reads `ordered[0]` and `ordered[-1]` with no guard, so `[]` raises `IndexError`. The current `/api/metrics/facets` route always passes an unfiltered generated list, so the defect is unreachable today; it becomes reachable as soon as facets are computed from filtered or supplied movements.
- **In practice:** this is the exact case R22 says has no test. The code path is latent, not broken.
- **Validated:** `build_metrics_facets([])` raises `IndexError: list index out of range` at `routes.py:156`, reproduced by `_validation/test_rules_validation.py::test_defect_r7_build_metrics_facets_handles_empty_list`. The rule's "unreachable today" claim also holds: the route only ever passes an unfiltered generated list, so this is a latent trap for the next caller, not a live bug.

---

## 8. Documentation and agent guidance

Applies when editing a README, adding an analysis artifact, or changing a path that `AGENTS.md` references.

### R23 — Runtime docs must not contradict the running configuration

- **Status:** PROPOSED · **Severity:** Medium
- **Scope:** `README.md`, `README.es.md`, `verification.md`, `rules-proposed.md`
- **Rule:** Repository-level analysis artifacts must also be reachable from the README, and no README statement may contradict the configuration that actually runs.
- **Why:** both READMEs state backend `http://localhost:8000` and its `/docs`, while `docker-compose.yml` publishes host `8001` mapped to container `8000`. Both also claim the Vite proxy is the default, while `App.tsx` uses the absolute `http://localhost:8001` origin. Neither README references `verification.md` or `rules-proposed.md`, so the two work products are discoverable only by directory listing.
- **In practice:** a reader following the README reaches a port nothing is listening on. The published port is the authoritative fact; the README is stale.
- **Validated:** machine-checked by `_validation/val_docs_config.py`, which compares the ports Compose publishes (`5173`, `8001`, `5678`) against those the README mentions (`5173`, `8000`) and confirms neither `verification.md` nor `rules-proposed.md` is referenced from the README. 13/13 documentation and configuration claims reproduced.
- **Validated — counted directly, both languages:** each README mentions `:8000` **twice** and `8001` **zero times**, references `5173` once, and references `verification.md`/`rules-proposed.md` **zero times**. The stale-port claim is exact, not approximately true.
- **Validated — the proxy claim, and where it becomes actively harmful:** both READMEs say at line 45 that the frontend uses the Vite proxy "by default, so no extra environment variables are required in local development **or Codespaces**". `App.tsx` instead defaults `API_BASE_URL` to the absolute `http://localhost:8001`, which is a host-local origin. In Codespaces a forwarded port is not `localhost:8001`, so the documented no-configuration path is precisely the configuration that cannot work there — while the proxy it advertises *would* have worked. The README does not merely describe a stale setup; it recommends the one combination that fails.
- **Why the port conflict matters concretely:** the backend container listens on `8000` and Compose publishes it as host `8001` (commit `dbac6d3` was titled "resolve backend port conflict and align frontend API target"). The README was never updated, so a reader following it reaches a port nothing is listening on, and the `/docs` link it gives is dead.

### R15 — Agent instructions must reference paths that exist

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `AGENTS.md`, `README.md`, `README.es.md`
- **Rule:** If a referenced path is optional and absent, say so explicitly.
- **Why:** `AGENTS.md` requires reviewing `./.agents/rules`, `./.agents/skills`, and `./memory-bank` before acting, and both READMEs document an `.agents/rules` + `.agents/skills` layout. At the time of the audit none of the three paths existed, so the first required step could not be completed and the reason was ambiguous.
- **Current state:** `./.agents/rules` exists and holds this file. `./memory-bank` now exists and contains the repository's evidence-backed project overview, technology stack, current status, and unapproved decision queue. `./.agents/skills` is still absent and referenced without qualification; `AGENTS.md` marks `./memory-bank` as optional ("if the directory exists").
- **In practice:** when adding an agent instructions path, either create it in the same change or qualify it as optional.
- **Validated — the three paths, checked individually:** `AGENTS.md` references `./.agents/rules` (line 6), `./.agents/skills` (line 9), `./memory-bank` (line 12). On disk: `.agents/rules` **exists**, `.agents/skills` **does not**, `memory-bank` **does not**. The optionality markers in `AGENTS.md` were inspected per bullet rather than by searching for the phrase once — an earlier version of this check sliced the file after the first `./.agents/skills` occurrence and picked up the optional marker belonging to a *different* line, which flipped the result.
- **Validated — the ambiguity that makes this worth a rule:** these are **relative** paths (`./`), and the repository has a `frontend/` subdirectory that is its own npm project with its own `AGENTS.md`-relevant tooling. An agent that has `cd`'d into `frontend/` resolves `./.agents/rules` to `frontend/.agents/rules`, which does not exist (checked). The first required step of the instruction therefore either succeeds or fails depending on the working directory, with no error to distinguish "wrong directory" from "file missing". This was observed directly during this validation pass: a probe run from `frontend/` reported a path as not found that existed at the repository root.

---

## 9. Build, deployment and security

Applies when changing a Dockerfile, a build context, a dependency file, or exposing the API beyond local development.

### R4 — A wildcard CORS origin must not survive into a real deployment

- **Status:** DEPLOYMENT · **Severity:** Medium
- **Scope:** `backend/app/main.py`
- **Rule:** Use an explicit origin allowlist once the API serves private or authenticated financial data.
- **Why:** `CORSMiddleware` uses `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` together with `allow_credentials=True`, so any origin can call the API from a browser. There is no authentication in the snapshot, so this is not a present data leak, but the setting is not an allowlist.
- **In practice:** the status is DEPLOYMENT, not PROPOSED — the rule binds at the point the API stops being local. It is not a request to change the current local configuration.
- **Validated — the exact configuration, read from source:** `backend/app/main.py` line 7-12 declares `CORSMiddleware` with `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`. All four wildcards, as described.
- **Validated — a subtlety the rule should state:** `allow_origins=["*"]` together with `allow_credentials=True` is a combination browsers **reject** for credentialed requests. Starlette echoes the wildcard, but a browser will not expose a response to an `XMLHttpRequest` with credentials when the allow-origin header is `*`. So the setting is simultaneously too open (any origin may make *uncredentialed* calls) and non-functional for the credentialed case someone clearly intended. The rule is therefore more urgent than "switch to an allowlist when you deploy" — the intent expressed by `allow_credentials=True` never works, and nobody has noticed because no request currently sends credentials.
- **What this means for a reviewer:** do not read `allow_credentials=True` as evidence that credential support is configured. It is inert. Adopting an explicit allowlist is what makes it meaningful.

### R8 — Every build context must exclude host-only content

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/.dockerignore`, `frontend/.dockerignore`, `frontend/Dockerfile`, `backend/Dockerfile`
- **Rule:** Git ignore rules do not apply to Docker.
- **Why:** `.gitignore` does not filter Docker build contexts. Both Dockerfiles use `COPY . .`, so every local-only file must be excluded by the corresponding context's `.dockerignore`; Compose bind mounts are a separate runtime boundary.
- **Validated — the original evidence was wrong, then the context was secured:** the earlier draft said `frontend/node_modules` was empty; it held **16,507 of 16,553** entries. Before the ignore files were added, those host dependencies entered the build context. The new frontend and backend `.dockerignore` files exclude dependencies, caches, and local env files; the measured contexts fell to **1.75 kB** and **898 B**, and both images built successfully.
- **Validated — scope narrowed, because a `.dockerignore` alone does not fix this:** `docker-compose.yml` bind-mounts `./frontend:/app` and `./backend:/app`. A bind mount overlays the image's `/app` at container start, so **host files reach the container regardless of any `.dockerignore`**. For the Compose workflow this repository actually uses, `.dockerignore` protects only the image layer, not the running container. The real remedy for `.env` exposure in Compose is to not place secrets in bind-mounted paths, or to mount explicitly per-file.
- **In practice:** `.gitignore` protects the repository and `.dockerignore` protects the image build context, but neither filters a bind-mounted container. Compose mounts `./frontend:/app` and `./backend:/app`; do not store secrets in those mounted paths. See C6 for the Git side.

### R9 — Image builds must consume the committed lockfile

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `frontend/Dockerfile`, `frontend/package-lock.json`
- **Rule:** A build must assert the committed dependency tree instead of resolving a fresh one.
- **Why:** a lockfile is committed, but the image runs `npm install`, which may rewrite or relax the resolution instead of asserting the committed tree, so container builds and local installs can diverge without any repository change.
- **In practice:** the lockfile's value depends on the build asserting it. `npm ci` is the command that reads it rather than resolves it.
- **Validated:** `package-lock.json` is present and `frontend/Dockerfile` runs `RUN npm install` with no `npm ci` anywhere in the file. Container and local dependency resolution can diverge with no repository change, as stated.
- **Validated — image build executed:** `docker compose build` completed and the frontend container reports its installed top-level dependency tree with `npm ls --depth=0`. This proves the current build works, not that repeated clean builds are byte-for-byte reproducible; the Dockerfile still uses `npm install`, not `npm ci`.

### R10 — Runtime images must not carry test and debugger tooling

- **Status:** PROPOSED · **Severity:** Low
- **Scope:** `backend/requirements.txt`, `backend/Dockerfile`
- **Rule:** Separate runtime dependencies from development and debug tooling.
- **Why:** the single requirements file lists `pytest`, `pytest-cov`, `httpx`, and `debugpy`, and the Dockerfile installs it directly, so test tooling and a debugger are part of the runtime layer that starts Uvicorn under debugpy.
- **In practice:** this is why a real deployment needs a split between runtime and development dependency sets, and why the debugger port is published in the same service as the API.
- **Validated — one fact stronger than written:** `requirements.txt` is **entirely unpinned**. All six entries (`fastapi`, `uvicorn[standard]`, `debugpy`, `pytest`, `pytest-cov`, `httpx`) carry no version specifier, so the runtime layer is not reproducible either. This is a separate concern from the dev/runtime split and deserves its own fix.
- **Validated — container contents inspected:** after the Compose build, `docker compose exec backend python -m pytest --version` reports **pytest 9.2.0** and `python -m debugpy --version` reports **1.8.22**. Both development tools are installed in the running backend image, as the rule predicts.

---

## 10. Conventions in force

**Status: CONFIRMED** — present in the checked code. These are not proposals. They are patterns the codebase already follows, recorded so a refactor does not silently regress them. The convention column states what to keep doing.

| ID | Convention | Scope | Evidence |
| --- | --- | --- | --- |
| **C1** | Define API inputs and outputs as explicit types at the boundary. | `backend/app/routes.py` | `Literal` aliases (`OperationType`, `Category`, `BusinessType`, `GroupBy`) plus Pydantic response models on every route, so invalid enum values are rejected and response shapes are explicit. **Validated:** all 8 data routes carry `response_model=`; `/health` returns a plain `dict[str, str]`, correctly, since it has one fixed shape. Invalid values are rejected with **422** — `operation_type=bogus`, `category=bogus`, `group_by=bogus`, `business_type=b2b`. Valid values pass: `operation_type=income` → 200, `business_type=B2B` → 200. The convention holds. **But the boundary has a hole:** `business_type=b2b` is rejected as 422 on `/metrics/summary` while being silently accepted (and ignored) on `/api/metrics`, where the parameter is not declared at all — see R3. |
| **C2** | Validate numeric query parameters with explicit bounds. | `backend/app/routes.py` | Top-category `limit` uses `ge=1, le=20`; alert `threshold` uses `ge=0`. Consumers cannot request unbounded results or negative thresholds. **Validated on the boundaries themselves:** **16/16** boundary cases matched the declared behaviour, covering `limit=1` → 200, `limit=20` → 200, `limit=21` → 422, `limit=0` → 422, `limit=-5` → 422, `limit=abc` → 422, `threshold=0` → 200, `threshold=-0.1` → 422, `threshold=1` → 200. The bounds are enforced, not merely declared. Note the bounds apply to *declared* parameters only; see R3 for parameters that are undeclared and therefore silently dropped instead of rejected. |
| **C3** | Keep financial calculations in pure helpers, separate from transport. | `backend/app/routes.py`, `backend/tests/test_routes.py` | `filter_movements_by_date` and `generate_mock_movements` are imported and tested directly without HTTP, so the helpers are genuinely separable from the transport layer. **Corrected:** the original row also named `summarize_movements`, `build_top_categories`, and `detect_outcome_alerts` as directly imported and tested, and called the filter `filter_movements`. The real import line is `from app.routes import filter_movements_by_date, generate_mock_movements` — **only those two**. The other three helpers are exercised exclusively through the HTTP client. The convention (pure helpers exist and *can* be called directly) holds; the claim that all four are tested directly does not. |
| **C4** | Handle zero-income denominators explicitly. | `frontend/src/lib/financial-utils.ts`, `frontend/src/lib/financial-utils.test.ts` | `computeKPIs` and `computeMonthlyData` guard `income > 0`, and a focused test covers outcomes with no income. **Validated:** the test exists verbatim at `financial-utils.test.ts:47` — `it("returns 0 profitPercent when there is no income")`. |
| **C5** | Make variant styling exhaustive at compile time. | `frontend/src/components/dashboard/kpi-card.tsx` | `variantStyles` is typed as `Record<KPICardProps["variant"], ...>`, so adding a variant becomes a compile error instead of a silently unstyled card. **Validated:** adding a `"neutral"` member to the union while leaving the map untouched fails with `TS2741: Property 'neutral' is missing`. The guarantee holds — but only under `tsc -p tsconfig.app.json`; see the verification note below. |
| **C6** | Keep secret files out of Git while tracking the documented example. | `.gitignore` | Root `.gitignore` lists `.env` and `.env.*` then negates `!.env.example`. Note that Docker does not honour this file; see R8. |
| **C7** | Protect container dependencies from the host bind mount. | `docker-compose.yml` | The frontend service declares the anonymous volume `/app/node_modules`, so bind-mounting `./frontend` does not replace the modules installed in the image. **Validated:** both volumes are present (`./frontend:/app` and `/app/node_modules`). Note the pair is what makes the mount safe — removing the second line breaks the container silently. |
| **C8** | Cover ordering, date-edge inclusion, and cross-year aggregation with tests. | `backend/tests/test_routes.py`, `frontend/src/lib/financial-utils.test.ts` | Tests assert sorted output, inclusive `start_date`/`end_date` edges, and chronological year-month keys across a year boundary. Extend these at the date/time boundaries named in R2 and R12. **Validated — and narrower than stated:** all 15 backend tests were classified by parameter binding. **2** call helpers directly (`test_generate_mock_movements_returns_full_year_sorted_data`, `test_filter_movements_by_date_includes_range_edges`); **13** go through `client.get` only; **0** mix both. The only "360 records" assertion is followed by an ordering assertion and **no month-span assertion** — it checks count and order, never the range its name claims. The `year` token that appears in that test is in its *name*, not its assertions. Cross-year aggregation is therefore covered on the frontend (`financial-utils.test.ts`) and **not** on the backend. |

### Verifying a frontend type rule

A type-level guarantee in this repository cannot be confirmed with a bare `npx tsc --noEmit` from `frontend/`. `frontend/tsconfig.json` is solution-style — `"files": []` with `references` to `tsconfig.app.json` and `tsconfig.node.json` — so a plain invocation type-checks **no source files at all** and exits 0 on any input. A rule about exhaustive variants, unused locals, or narrowing will appear to pass regardless of whether it holds.

Confirm with either:

```
npx tsc --noEmit -p tsconfig.app.json
npm run build
```

This matters beyond tooling: an agent that "checks types" with the bare command will report success on code that does not compile. It is the single most misleading verification step in the repository.

**A second trap, found while writing the validation probes.** Anything placed under `frontend/src/` is type-checked with `"types": ["vite/client"]` only. Importing a Node builtin there — `node:fs`, `node:url`, `node:path` — fails the build with `TS2591: Cannot find name 'node:fs' … add 'node' to the types field`, because `@types/node` is not in that `types` list. A test that reads a file to assert on its contents must therefore use Vite's `?raw` import suffix (`import src from "./App.tsx?raw"`), which `vite/client` types, instead of `readFileSync`. The failure is a *type* failure, not a runtime one: the test passes under `vitest` and only the build catches it, so a probe that is never type-checked can ship a broken `npm run build`.

When a refactor touches one of these patterns, the change is a regression unless it replaces the convention with a stronger one. Each row names the file that demonstrates it, so the intended shape can be read directly rather than inferred.

---

## Open decisions blocking some rules

These choices are not made. A rule that depends on one is a question to raise, not a directive to apply. They are recorded in full in `rules-proposed.md`.

1. Fixed calendar year or rolling window (R1) — decides what the generator and the header must express.
2. Whether `business_type` becomes a parameter of `/api/metrics` or the B2B/B2C split is documented as intentional (R3, R19).
3. Absolute-origin requests or relative `/api` paths (R16).
4. Whether `mock-data.ts` is a fixture to maintain or dead weight to remove (R11).
5. Whether `./memory-bank` and `./.agents/skills` are created, or `AGENTS.md` is amended (R15).
6. Whether `outcome` is kept or replaced by `expense` across its 91 occurrences (R18).
7. Whether `routes.py` is split before the next endpoint is added (R17).
8. Whether a DOM test environment is added now or component rules stay unverifiable (R21).
9. Whether persistence is in scope for the next iteration (R20).
