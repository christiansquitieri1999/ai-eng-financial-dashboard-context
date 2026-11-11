# Frontend Component Specification

> Branch: `feature/frontend-specs`  
> Status: **draft** — aligned with `api-types.ts` and `param-types.ts`  
> Type-check: the specification types are checked directly; the app project is checked with `npx tsc -b`.

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

Render the two navigation links in the shared dashboard header using React Router `<Link>` components. Do not add an `onNavigate` callback; route navigation belongs to the router.

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
| `minDate` | `string \| undefined` | yes | `min_date` from facets — format `YYYY-MM-DD`; `undefined` if facets fail |
| `maxDate` | `string \| undefined` | yes | `max_date` from facets — format `YYYY-MM-DD`; `undefined` if facets fail |
| `startDate` | `string \| undefined` | yes | Controlled value for the start input |
| `endDate` | `string \| undefined` | yes | Controlled value for the end input |
| `onStartDateChange` | `(value: string \| undefined) => void` | yes | Called when start date changes; `undefined` when cleared |
| `onEndDateChange` | `(value: string \| undefined) => void` | yes | Called when end date changes; `undefined` when cleared |
| `rangeError` | `string \| null` | yes | Validation message when the proposed range is invalid; `null` when valid |

**Behavior:**
- When facets are available, both inputs are bounded by the dataset range. The start input's maximum is the selected end date (or `maxDate`); the end input's minimum is the selected start date (or `minDate`).
- If facets fail, keep both inputs usable without date bounds or an available-range hint; movement fetching remains independent and continues to work.
- Clearing either input calls its callback with `undefined`. With both inputs empty, omit both query parameters and show the full dataset.
- With only `startDate`, show movements from that date through the available upper bound. With only `endDate`, show movements from the available lower bound through that date.
- Equal start and end dates mean that single calendar day. If a change would make start later than end, reject it, retain the previous valid value, show an inline validation message, and do not fetch until the range is valid.
- Render `rangeError` beside the inputs when non-null.
- Apply each valid change immediately, without debounce. If facets are unavailable and a valid date outside the dataset is entered, show the normal no-data state.

#### Modified: `DashboardHeader`

Render navigation links to `/` and `/b2b-b2c` here. The period badge reflects the current date filter: both dates, `From {startDate}`, `Through {endDate}`, or `All available dates` when both are empty.

| Prop | Type | Required | Description |
|---|---|---|---|
| `startDate?` | `string` | no | Inclusive selected start date |
| `endDate?` | `string` | no | Inclusive selected end date |

If both are present, the badge reads `"2026-01-01 — 2026-06-30"`; never display the stale hard-coded `"2024 - Full Year"` label.

#### Modified: `App.tsx` → `HomePage`

The current `App.tsx` becomes `HomePage`. Changes:

1. Fetch `GET /api/metrics/facets` on mount.
2. Add `DateRangeFilter` state (`startDate`, `endDate`).
3. Pass date params to `fetchFinancialData`.
4. Pass `DateRangeFilter` component to the render tree.
5. Pass the alerts table (Feature 2) below the charts.
6. Convert to a named export so the router can use it.

**Props:** none. `HomePage` owns the facet, date, movement, threshold, and alert state. Keep the facet, movement, and alert requests' loading/error states independent. If the movement response is `[]`, pass `metrics={null}` to `KPIRow` so its existing null state renders `—`; pass an empty `MonthlyDataPoint[]` to both charts so they render their existing "No data available to display" state. A movement request error uses the page error banner; an alert request error affects only `AlertsTable`.

#### Reused dashboard components

These existing components remain in use and their public props are part of the feature contract:

| Component | Props | Conditional rendering |
|---|---|---|
| `KPIRow` | `metrics: KPIMetrics \| null`; `loading?: boolean` | Loading renders KPI skeletons; `metrics === null` renders `—` values; otherwise render computed metrics. |
| `IncomeOutcomeChart` | `data: MonthlyDataPoint[]`; `loading?: boolean` | Loading renders a chart skeleton; no positive income/outcome values renders "No data available to display"; otherwise render the chart. |
| `ProfitPercentChart` | `data: MonthlyDataPoint[]`; `loading?: boolean` | Loading renders a chart skeleton; no nonzero margin values renders "No data available to display"; otherwise render the chart. |

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

Renders a labelled `<input type="number" min={0.01} max={1.0} step={0.01}>` above the alerts table. Keep an editable draft string so the user can clear or type intermediate values. Commit and call `onThresholdChange` only for finite values in `[0.01, 1.0]` on 0.01 increments; otherwise retain the last committed threshold, show an inline validation message, and do not fetch. HTML `min`, `max`, and `step` attributes alone do not clamp or prevent invalid input.

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
| Rolling Average | `alert.baseline_average` | `formatCurrency()` — `$51,426` |
| Increase % | `alert.increase_ratio` | `(increase_ratio * 100).toFixed(1) + "%"` — `"56.0%"` |

**States (evaluated in this precedence):**

| State | Rendering |
|---|---|
| `loading === true` | 4 skeleton rows via `<Skeleton>` |
| `error != null` | Red error banner: "Failed to load anomaly alerts." |
| `alerts.length === 0 && !loading && error == null` | Centered italic text: "No anomalies detected for the current threshold." |
| `alerts.length > 0 && error == null` | Full table rendering |

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

1. Fetch facets on mount for the available date range hint and the global list of valid category values. Facets categories are not business-line-specific; table rows and ranking come from each top-category response. A facets failure does not block the two category tables or summary requests.
2. Maintain `startDate` / `endDate` state.
3. Fetch two `GET /api/metrics/categories/top?operation_type=income&limit=5&business_type=B2B` calls — one for B2B, one for B2C.
4. Compute each grand total by summing `income` across the matching `/api/metrics/summary` response. This is the source for percentages and chart values; do not derive it from top categories.
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
| `groupTotal` | `number \| null` | yes | Total income for this business line; `null` if the summary request failed |
| `loading` | `boolean` | yes | Skeleton state |
| `error` | `string \| null` | no | Error state |
| `summaryError` | `string \| null` | no | Summary request failure; show category rows but render percentages as `—` |

**Columns:**

| Column header | Data source | Format |
|---|---|---|
| Category | `entry.category` | Capitalized: `"Sales"` |
| Total Income | `entry.total_amount` | `formatCurrency()` — `$557,904` |
| % of Group Total | `entry.total_amount / groupTotal * 100` | One decimal place; render `—` if `groupTotal` is unavailable or zero |

**States (evaluated in this precedence):**
- `loading`: 5 skeleton rows.
- `error != null`: inline error for this business line; do not hide the other business line.
- `entries.length === 0 && !loading && error == null`: "No income data for this business line."
- Entries with a failed summary request still render; percentage cells show `—` and a separate summary error is shown.
- A zero `groupTotal` never causes division. If rows are present despite a zero total, render `—` for their percentages.

#### `B2bB2cComparisonChart`

| Prop | Type | Required | Description |
|---|---|---|---|
| `b2bTotal` | `number \| null` | yes | Total income from B2B line; `null` if unavailable |
| `b2cTotal` | `number \| null` | yes | Total income from B2C line; `null` if unavailable |
| `loading` | `boolean` | yes | Skeleton state |
| `error` | `string \| null` | no | Summary error when either group's total failed; render an inline chart error instead of bars |

**Visual and states:** A Recharts `<BarChart>` with two bars — "B2B Income" and "B2C Income". Format the Y-axis and tooltip as currency. While loading, show a skeleton; on summary error, show an inline error and no chart; when both totals are zero, show the chart with two zero bars and an explicit no-income caption.

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

### 5.3 Page-level request states

- `HomePage` keeps facets, movement, and alert loading/error states independent. Facets failure removes date bounds/hint only; movement failure affects dashboard data; alert failure affects only the alerts table.
- `B2bB2cPage` keeps category and summary requests independent for B2B and B2C. A failure in one group's category request must not hide the other group's table. A summary failure leaves category rows visible with percentage `—`; the comparison chart shows its own error if either total is unavailable.
- `DateRangeFilter` remains usable if facets fail. A failed data request is distinct from a successful empty response; show an error for the former and the feature-specific empty state for the latter.

### 5.4 Loading display

Skeleton components from `@/components/ui/skeleton` are used for loading states. Each data-driven component accepts `loading?: boolean`.

### 5.5 Empty state

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
