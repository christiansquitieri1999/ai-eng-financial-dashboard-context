# Validation evidence

These files are **not rules**. They hold the reproducible evidence behind claims in `../project-rules.draft.md`: executed tests where feasible, and measured or source-read checks where runtime execution is not appropriate or available. Re-run the artefacts instead of relying on prose alone; see `validation.md` for evidence-strength limits.

If a probe and the draft disagree, the probe is right and the draft needs correcting. That has already happened several times during this validation pass — see "Corrections found by validating" below.

**This file is the index, not the report.** It says what each probe does and how to re-run it. It does not give a verdict per rule, and it does not say what could not be validated. That analysis lives in [`validation.md`](validation.md) alongside this file.

## Contents

| File | Rules | What it proves |
| --- | --- | --- |
| `test_rules_validation.py` | R1, R2, R3, R6, R7, R12, R18, R19, R22 | Main pytest suite. `test_ok_*` cases must pass; `test_defect_*` cases are marked `xfail(strict=True)` so that fixing the defect turns them into XPASS and the suite goes red until the marker is removed. |
| `val_probe_filters.py` | R3, R19 | Endpoint behaviour for `business_type` on every route. Established that undeclared query parameters are silently ignored. |
| `val_counts.py` | R6, R18 | Corrected control for the global-reseed check, plus a three-method recount of `outcome` occurrences. |
| `r2_date_probe.js` | R2 | Date-key computation under two timezones. |
| `val_docs_config.py` | R8, R9, R10, R15, R16, R23, C6, C7 | 13 machine checks over docs and config. Run to `13/13 CONFIRMED`. |
| `val_r17_structure.py` | R17 | AST measurement of `routes.py`: 391 lines, 32 named declarations, 9 routes, 80% of lines inside a definition. |
| `val_r20_r4_absence.py` | R20, R4 | Import-graph proof that no database client and no environment read exists, plus the literal CORS configuration. |
| `val_c3_c8_tests.py` | C3, C8 | Classification of all 15 backend tests by whether they call a helper or the HTTP client. |
| `val_c1_c2_bounds.py` | C1, C2 | 16 boundary cases for `limit` and `threshold`, and enum rejection. Run to `16/16 matched`. |
| `val_r18_recount.py` | R18 | Recount of the `outcome` token with probe directories excluded. Establishes 108 occurrences (92 in product code, 16 in tests), 83 whole-word, and the per-area split. |
| `val_rule_coverage.py` | all | Self-audit of the draft: which rules carry a `Validated` bullet, which C-conventions exist, whether the index lists every ID, and whether any marker the header promises is unused. Currently 25/25 rules covered, 0 index gaps. |
| `val_report_consistency.py` | all | Self-audit of the report: parses the verdict table in `validation.md` and checks that it accounts for every declared ID exactly once and that its stated subtotals add up. Guards against a miscounted summary. |
| `validation.md` | all | **The report, not a probe.** Verdict per rule, corrections, what could not be validated, and the two verification traps. Read this after the index. |
| `r13-error-handling.test.ts` | R13 | 4 tests asserting on `App.tsx` read through Vite's `?raw` import. |
| `r24-empty-vs-loading.test.tsx` | R24, R21 | 3 tests rendering `KPIRow` with `react-dom/server`, no DOM environment needed. |

All probes now live in this one folder. The two frontend tests are `.test.ts(x)` files, but Vitest's root is `frontend/`, so a plain `npx vitest run` there does **not** discover them — they must be pointed at explicitly with `--dir`. They sit outside `frontend/src/` on purpose: `tsconfig.app.json` has `"include": ["src"]`, so a test placed under `src/` becomes part of the app type-check and build, which is wrong for a probe that exists to demonstrate a defect.

## How to run

```powershell
# Backend suite (expect: 6 passed, 6 xfailed)
Set-Location C:\Users\chris\ai-eng-financial-dashboard-context
python -m pytest .agents\rules\_validation\test_rules_validation.py -q

# Docker build and runtime smoke test (requires Docker Desktop/daemon)
docker compose config --quiet
docker compose up --build -d
(Invoke-RestMethod http://localhost:8001/health).status       # ok
(Invoke-RestMethod http://localhost:8001/api/metrics).Count   # 360
(Invoke-RestMethod http://localhost:5173/api/metrics).Count   # 360 via Vite proxy
(Invoke-WebRequest http://localhost:5173/ -UseBasicParsing).StatusCode # 200

# Individual probes
python .agents\rules\_validation\val_docs_config.py
python .agents\rules\_validation\val_r17_structure.py
python .agents\rules\_validation\val_r20_r4_absence.py
python .agents\rules\_validation\val_c3_c8_tests.py
python .agents\rules\_validation\val_c1_c2_bounds.py
python .agents\rules\_validation\val_r18_recount.py
python .agents\rules\_validation\val_rule_coverage.py
python .agents\rules\_validation\val_report_consistency.py

# Timezone-dependent date check (must be run under both)
$env:TZ="America/Los_Angeles"; node .agents\rules\_validation\r2_date_probe.js
$env:TZ="Europe/Rome";         node .agents\rules\_validation\r2_date_probe.js

# Frontend probes (expect: 7 passed across 2 files)
# These live in this folder, outside Vitest's root, so --dir is required.
Set-Location C:\Users\chris\ai-eng-financial-dashboard-context\frontend
npx vitest run                                        # product suite: 1 file, 5 tests
npx vitest run --dir ../.agents/rules/_validation      # probes: 2 files, 7 tests
```

## Two verification traps

**`npx tsc --noEmit` from `frontend/` checks nothing.** `tsconfig.json` is solution-style (`"files": []` plus `references`), so a bare invocation type-checks no source files and exits 0 on any input. Use `npx tsc --noEmit -p tsconfig.app.json` or `npm run build`.

**Node builtins are untyped inside `frontend/src/`.** `tsconfig.app.json` sets `"types": ["vite/client"]`, so `import { readFileSync } from "node:fs"` fails with `TS2591` even though `@types/node` is installed. A test that needs file contents must use Vite's `?raw` import suffix. The failure is a type failure only — `vitest` passes — so a probe that is never type-checked can ship a broken `npm run build`.

## Corrections found by validating

Recorded because they show the draft was not simply transcribed from the code:

- **R3 was worse than drafted.** `/api/metrics` accepts `?business_type=b2b` and returns all 360 rows, byte-identical to the unfiltered response — a success status with the filter silently dropped.
- **R8's evidence was wrong.** `frontend/node_modules` is not empty; it holds 16,507 of 16,553 entries. The rule was also scope-narrowed: a bind mount reaches the container regardless of `.dockerignore`.
- **R17's count was wrong.** 32 named top-level declarations, not 35. The route count also had to be measured against `@router.`, not `@app.` — the app uses `APIRouter`, so searching for `@app.` returns zero and looks like "no routes".
- **C3 named helpers that are not imported.** Only `filter_movements_by_date` and `generate_mock_movements` are; the other three are reached through HTTP only.
- **R18's breakdown was wrong even though its total was close.** 108 substring occurrences, not 91, and the split is `backend/` 33 / `frontend/src/lib/` 54 / `frontend/src/components/` 18 / `App.tsx` 3 — not 31 / 47 / 12. A third of the live weight sits in `mock-data.ts`, which has no importers at all.
- **R21 was too broad.** "Writing a `.test.tsx` today would fail at import time" is true only for `@testing-library/*`. `react-dom/server` is already installed and runs in the plain Node environment, so markup tests work with no new dependency — proven by the R24 probe, 3 tests passing.
- **C8 was narrower than stated.** Cross-year aggregation is covered on the frontend only; the backend's "full year" test asserts a count and an ordering, and never checks the month span its name implies.
- **C2 was measured before it was claimed.** `threshold=-1` was untested when the row was first written; the boundary script then showed the real edge is `-0.1` → 422.
- **R23's README claims are exact, not approximate.** Both READMEs mention `:8000` twice and `8001` zero times, and reference neither added artifact. Line 45 also recommends the proxy "in Codespaces", where the absolute `localhost:8001` default cannot work — the doc points at the failing configuration.
- **R15's referenced paths were checked per bullet.** A first attempt sliced the file after the first `./.agents/skills` occurrence and read the optional marker belonging to a different line, which flipped the result. `.agents/rules` exists; `.agents/skills` and `memory-bank` do not.
- **R2 cannot be cleared on this machine.** Under `Europe/Rome` zero of four dates are wrong; under `America/Los_Angeles` three of four are.
- **A green test can mean the feature is absent.** The first R3 probe asserted `200` for `?business_type=b2b` and passed, because FastAPI ignores the parameter entirely. Writing the assertion against the source, not the status code, is what exposed it.
- **The coverage audit caught its own document lying.** The draft's header claimed "every rule was re-examined with an executed check" and promised `[corrected]` / `[scope-narrowed]` markers. `val_rule_coverage.py` found 24/25 rules carried a `Validated` bullet, R8 used `Corrected —` / `Scope-narrowed —` instead, and neither bracketed marker appeared anywhere outside the header. Both fixed by changing the labels and the header, not by weakening the check.
