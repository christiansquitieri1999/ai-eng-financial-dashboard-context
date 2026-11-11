# Frontend Component Specification

> Branch: `feature/frontend-specs`  
> Status: **draft** — aligned with `api-types.ts` and `param-types.ts`  
> Verified: `tsc --noEmit --strict` (0 errors)

---

## Table of contents

1. [Routing architecture](#1-routing-architecture)
2. [Feature 1 — Date range filter on the home dashboard](#2-feature-1--date-range-filter-on-the-home-dashboard)
3. [Feature 2 — Anomaly alerts table on the home dashboard](#3-feature-2--anomaly-alerts-table-on-the-home-dashboard)
4. [Feature 3 — B2B vs B2C comparison view](#4-feature-3--b2b-vs-b2c-comparison-view)
5. [Shared patterns](#5-shared-patterns)
6. [PM ambiguities resolved](#6-pm-ambiguities-resolved)

---

## 1. Routing architecture

### Current state (AS-IS)

- No router library installed (`react-router-dom` is absent from `package.json`).
- `App.tsx` renders a single page (home dashboard) unconditionally.

### Required change (TO-BE)

Add `react-router-dom` and define two top-level routes:

| Route | Page component | Description |
|---|---|---|
| `/` | `HomePage` | Current dashboard + Feature 1 date filter + Feature 2 alerts table |
| `/b2b-b2c` | `B2bB2cPage` | Feature 3 — B2B vs B2C comparison view |

Navigation should be added to the dashboard header for switching between pages. Use `<Link>` or a simple nav bar — no nested layouts needed for this scope.

```tsx
// Conceptual route definition (not part of the component props below)
<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/b2b-b2c" element={<B2bB2cPage />} />
</Routes>
```

---

## 2. Feature 1 — Date range filter on the home dashboard

### 2.1 High-level behaviour

1. On mount, the page fetches `GET /api/metrics/facets` to obtain `min_date` and `max_date`.
2. Two date inputs (`<input type="date">`) are rendered below the dashboard header, labelled "Start Date" and "End Date".
3. Below or beside the inputs, a subtle text shows: `Available range: 2025-11-01 — 2026-10-28`.
4. When the user picks a date range, `GET /api/metrics` is re-fetched with `?start_date=...&end_date=...`.
5. When both inputs are empty, the full dataset is shown (API called with no date params).
6. The KPI cards, income/outcome chart, profit margin chart, and alerts table all receive the date-filtered data.

### 2.2 New & modified components

#### `DateRangeFilter`

| Prop | Type | Required | Description |
|---|---|---|---|
| `minDate` | `string` | yes | `min_date` from facets — format `YYYY-MM-DD` |
| `maxDate` | `string` | yes | `max_date` from facets — format `YYYY-MM-DD` |
| `startDate` | `string \| undefined` | yes | Controlled value for the start input |
| `endDate` | `string \| undefined` | yes | Controlled value for the end input |
| `onStartDateChange` | `(value: string \| undefined) => void` | yes | Called when start date changes; `undefined` when cleared |
| `onEndDateChange` | `(value: string \| undefined) => void` | yes | Called when end date changes; `undefined` when cleared |

**Notes:**
- Both `<input type="date">` elements use `min` / `max` HTML attributes from `minDate`/`maxDate`.
- When the user clears an input, the value passed to the callback is `undefined`.
- No "Apply" button — the filter applies **on change** (debounced? — see ambiguity 6.1).

#### Modified: `DashboardHeader`

Add an optional `onNavigate` prop or render navigation links here. The period badge should show the selected date range when filtering is active.

| Additional Prop | Type | Required | Description |
|---|---|---|---|
| `startDate?` | `string` | no | When set, overrides the fixed period label |
| `endDate?` | `string` | no | When set, overrides the fixed period label |

If both are present, the badge reads `"2026-01-01 — 2026-06-30"` instead of `"2024 - Full Year"`.

#### Modified: `App.tsx` → `HomePage`

The current `App.tsx` becomes `HomePage`. Changes:

1. Fetch `GET /api/metrics/facets` on mount.
2. Add `DateRangeFilter` state (`startDate`, `endDate`).
3. Pass date params to `fetchFinancialData`.
4. Pass `DateRangeFilter` component to the render tree.
5. Pass the alerts table (Feature 2) below the charts.
6. Convert to a named export so the router can use it.

**Data flow for date filter:**

```
HomePage
 ├─ useEffect → fetch /api/metrics/facets → store facets
 ├─ DateRangeFilter ←→ state: startDate, endDate
 ├─ useEffect(facets + startDate + endDate) → fetch /api/metrics?start_date&end_date
 │   └─ movements → computeKPIs → KPIRow
 │   └─ movements → computeMonthlyData → IncomeOutcomeChart + ProfitPercentChart
 │   └─ movements → fetch /api/metrics/alerts?threshold&start_date&end_date → AlertsTable
 └─ props drilling: KPIRow, charts, AlertsTable all receive filtered data
```

---

## 3. Feature 2 — Anomaly alerts table on the home dashboard

### 3.1 High-level behaviour

1. Displays below the existing charts section.
2. Four columns: **Period**, **Recorded Outcome**, **Rolling Average**, **Increase %**.
3. A numeric `<input type="number">` above the table lets the user set the threshold (range `0.01`–`1.0`, step `0.01`, default `0.3`).
4. When the alerts endpoint returns `[]`, an explicit empty-state message is shown: *"No anomalies detected for the current threshold."*
5. The table respects the date range from Feature 1 — if a date range is active, it's passed to `GET /api/metrics/alerts`.
6. Loading state: skeleton rows.
7. Error state: inline error banner.

### 3.2 New components

#### `AlertsControls`

| Prop | Type | Required | Description |
|---|---|---|---|
| `threshold` | `number` | yes | Current threshold value (0.01 – 1.0) |
| `onThresholdChange` | `(value: number) => void` | yes | Called when the user changes the threshold input |

Renders a labelled `<input type="number" min={0.01} max={1.0} step={0.01}>` with the current threshold value. Displayed above the alerts table.

#### `AlertsTable`

| Prop | Type | Required | Description |
|---|---|---|---|
| `alerts` | `AlertEntry[]` | yes | Array of anomaly entries (may be empty) |
| `loading` | `boolean` | yes | When `true`, render skeleton rows |
| `error` | `string \| null` | no | Error message to display instead of the table |

**Columns:**

| Column header | Data source | Format |
|---|---|---|
| Period | `alert.period` | Raw string (e.g. `"2026-03"`) |
| Recorded Outcome | `alert.outcome_total` | `formatCurrency()` — `$88,077` |
| Rolling Average (3 periods) | `alert.baseline_average` | `formatCurrency()` — `$51,426` |
| Increase % | `alert.increase_ratio` | `(increase_ratio * 100).toFixed(1) + "%"` — `"56.0%"` |

**States:**

| State | Rendering |
|---|---|
| `loading === true` | 4 skeleton rows via `<Skeleton>` |
| `error !== null` | Red error banner: "Failed to load anomaly alerts." |
| `alerts.length === 0 && !loading && !error` | Centered italic text: "No anomalies detected for the current threshold." |
| `alerts.length > 0` | Full table rendering |

**Notes:**
- **PM ambiguity resolved (see 6.2):** The PM says "rolling average of the previous 3 periods" but the backend computes an average of ALL historical periods. The spec tables this mismatch — the component displays whatever `baseline_average` returns and labels it "Rolling Average". The column name deliberately omits "3 periods" until the backend is fixed.
- **PM ambiguity resolved (see 6.3):** The PM says "percentage increase" but the API returns `increase_ratio` as a decimal. The component converts it: `(increase_ratio * 100).toFixed(1) + "%"`.

---

## 4. Feature 3 — B2B vs B2C comparison view

### 4.1 High-level behaviour

1. New page at route `/b2b-b2c`.
2. Two side-by-side sections: B2B (left) and B2C (right).
3. Each section shows a table with top 5 income categories: **Category**, **Total Income**, **% of Group Total**.
4. Below both sections, a single bar chart comparing total income of B2B vs B2C.
5. An optional date range filter at the top of the page (reuse `DateRangeFilter` component).
6. Available categories come from `GET /api/metrics/facets` (full list — same for both groups).

### 4.2 New components

#### `B2bB2cPage`

Page-level component. Responsibilities:

1. Fetch facets on mount for available categories and date range hints.
2. Maintain `startDate` / `endDate` state.
3. Fetch two `GET /api/metrics/categories/top?operation_type=income&limit=5&business_type=B2B` calls — one for B2B, one for B2C.
4. Compute the grand total income for each group:
   - Option A: Use `GET /api/metrics/summary?operation_type=income&business_type=B2B` (backend does the aggregation).
   - Option B: Compute from the categories/top response (less accurate if categories < 5).
   - **Decision (see 6.4):** Use Option A (`/api/metrics/summary`) for the grand total, because the top-5 may not represent 100% of income.
5. Pass data down to child components.

| Prop | Type | Required | Description |
|---|---|---|---|
| *(none — page is self-contained)* | | | |

**Data flow:**

```
B2bB2cPage
 ├─ useEffect → fetch facets → min_date, max_date, categories
 ├─ DateRangeFilter ←→ state: startDate, endDate
 ├─ useEffect(startDate, endDate) →
 │   ├─ fetch /api/metrics/categories/top? ...business_type=B2B → b2bCategories
 │   ├─ fetch /api/metrics/categories/top? ...business_type=B2C → b2cCategories
 │   ├─ fetch /api/metrics/summary? ...business_type=B2B → compute b2bTotal
 │   └─ fetch /api/metrics/summary? ...business_type=B2C → compute b2cTotal
 ├─ B2bB2cCategoryTable side-by-side (B2B, B2C)
 └─ B2bB2cComparisonChart (bar chart: B2B vs B2C total income)
```

#### `B2bB2cCategoryTable`

| Prop | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | yes | Section title: `"B2B"` or `"B2C"` |
| `entries` | `CategoryEntry[]` | yes | Top categories for this business line |
| `groupTotal` | `number` | yes | Total income for this business line (from summary endpoint) |
| `loading` | `boolean` | yes | Skeleton state |
| `error` | `string \| null` | no | Error state |

**Columns:**

| Column header | Data source | Format |
|---|---|---|
| Category | `entry.category` | Capitalized: `"Sales"` |
| Total Income | `entry.total_amount` | `formatCurrency()` — `$557,904` |
| % of Group Total | `entry.total_amount / groupTotal * 100` | `(pct).toFixed(1) + "%"` — `"90.6%"` |

**States:**
- `loading`: 5 skeleton rows.
- `error`: inline error message.
- `entries.length === 0 && !loading && !error`: "No income data for this business line."

#### `B2bB2cComparisonChart`

| Prop | Type | Required | Description |
|---|---|---|---|
| `b2bTotal` | `number` | yes | Total income from B2B line |
| `b2cTotal` | `number` | yes | Total income from B2C line |
| `loading` | `boolean` | yes | Skeleton state |

**Visual:** A simple bar chart (Recharts `<BarChart>`) with two bars — "B2B Income" and "B2C Income". Y-axis formatted in dollars. Tooltip shows formatted currency.

---

## 5. Shared patterns

### 5.1 Data fetching pattern

All API calls follow a consistent pattern:

```
const [data, setData] = useState<T | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  let cancelled = false;
  setLoading(true);
  setError(null);

  fetch(url)
    .then(r => { if (!r.ok) throw new Error(...); return r.json(); })
    .then(json => { if (!cancelled) setData(json); })
    .catch(e => { if (!cancelled) setError(e.message); })
    .finally(() => { if (!cancelled) setLoading(false); });

  return () => { cancelled = true; };
}, [deps]);
```

For future refactoring, consider extracting an `apiClient` module. For this draft, inline fetch calls are acceptable.

### 5.2 Error display

Inline error banners use the existing pattern from `App.tsx`:
```tsx
<div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive-foreground">
  {errorMessage}
</div>
```

### 5.3 Loading display

Skeleton components from `@/components/ui/skeleton` are used for loading states. Each data-driven component accepts `loading?: boolean`.

### 5.4 Empty state

When data is an empty array `[]` and the component is not loading or errored, a centred italic message is displayed:
```tsx
<div className="flex h-[120px] items-center justify-center text-muted-foreground text-sm italic">
  {emptyMessage}
</div>
```

---

## 6. PM ambiguities resolved

The PM brief left several details open. The following decisions are encoded in this spec so implementers have a single source of truth.

| # | Ambiguity | PM wording | Decision |
|---|---|---|---|
| 6.1 | **When does the date filter apply?** | "Add two date inputs… that filter all the data" | Apply **on change** with no debounce. Date inputs have native validation and users expect immediate feedback. |
| 6.2 | **Rolling average window size** | "rolling average of the previous 3 periods" | Backend returns `baseline_average` (ALL periods). Table column header says **"Rolling Average"** (without "3 periods"). Backend change tracked in verification.md. |
| 6.3 | **Percentage increase display** | "percentage increase" | API returns `increase_ratio` as decimal. Component renders `(ratio * 100).toFixed(1) + "%"` — e.g. `0.4065` → `"40.7%"`. |
| 6.4 | **Grand total for group percentage** | "percentage of the group total" | Use `GET /api/metrics/summary?operation_type=income&business_type=X` to get the definitive group total. Not the sum of top-5 (which may exclude categories with less income). |
| 6.5 | **B2B/B2C comparison chart type** | "a single chart compares the total income" | A **bar chart** (`<BarChart>` from Recharts) with two bars, one per business line. Tooltip shows formatted currency. |
| 6.6 | **Table sort direction** | (not specified) | Tables are sorted descending by `total_amount` / `increase_ratio` as returned by the API. No client-side re-sorting. |
| 6.7 | **Responsive layout for side-by-side tables** | "two sections side by side" | Use CSS grid: `grid-cols-1 lg:grid-cols-2`. On mobile (< 1024px) they stack vertically. |
| 6.8 | **Threshold input step** | "numeric input (a ratio between 0.01 and 1.0)" | Use `step={0.01}` so the user can adjust in 1% increments. Default `0.30`. |
