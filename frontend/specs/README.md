# Financial Metrics Dashboard — Frontend API Contract

> **Status:** Draft — aligned with OpenAPI spec at `/docs` (OAS 3.1, "Financial Metrics API 0.1.0")  
> **Backend base URL:** `http://localhost:8001` (configurable via `VITE_API_BASE_URL`)  
> **Branch:** `feature/frontend-specs`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Shared types](#2-shared-types)
3. [Feature 1 — Date range filter on the home dashboard](#3-feature-1--date-range-filter-on-the-home-dashboard)
4. [Feature 2 — Anomaly alerts table on the home dashboard](#4-feature-2--anomaly-alerts-table-on-the-home-dashboard)
5. [Feature 3 — B2B vs B2C comparison view](#5-feature-3--b2b-vs-b2c-comparison-view)
6. [Endpoints quick reference](#6-endpoints-quick-reference)
7. [Edge cases](#7-edge-cases)

---

## 1. Overview

This document defines the exact API contract between the frontend and the backend for the three features planned in this project. Every endpoint, response shape, query parameter, constraint, and edge case is documented here.

**Key files in this directory (`frontend/specs/`):**

| File | Purpose | Must read? |
|---|---|---|
| `api-types.ts` | TypeScript interfaces for every API response payload | ✅ Yes — import these types directly |
| `param-types.ts` | TypeScript interfaces for every query parameter set | ✅ Yes — import these types directly |
| `components.md` | Component props, data flow, routing, and PM ambiguity resolutions | ✅ Yes — defines every component's props, states, and layout decisions |
| `README.md` | **This file** — the single entry point for an agent to understand the data contract | This file |

**Also relevant outside this directory:**

| File | Purpose |
|---|---|
| `frontend/src/lib/financial-types.ts` | Client-side types (`KPIMetrics`, `MonthlyDataPoint`, `FinancialMovement`) — used by current charts |
| `frontend/src/lib/financial-utils.ts` | `computeKPIs()`, `computeMonthlyData()`, `formatCurrency()`, `formatPercent()` |
| `frontend/src/lib/mock-data.ts` | Static mock data (exists but currently unused — backend generates mock data dynamically) |
| `frontend/vite.config.ts` | Vite proxy config; `/api` → `http://backend:8000` (only relevant when NOT using absolute URLs) |
| `frontend/.env.example` | Documents `VITE_API_BASE_URL` environment variable |

---

## 2. Shared types

These types are used by multiple features. They are defined in `api-types.ts` with full JSDoc. Import them directly:

```typescript
import type {
  OperationType, Category, BusinessType, GroupBy,
  FacetsResponse, AlertEntry, AlertsResponse,
  CategoryEntry, MetricsSummaryItem, MetricsSummaryResponse,
} from "../specs/api-types";

import type {
  DateRangeFilter, AlertsParams, TopCategoriesParams, SummaryParams,
} from "../specs/param-types";
```

```typescript
// ── Operation type ─────────────────────────────────────────────────────
export type OperationType = "income" | "outcome";

// ── Movement category ──────────────────────────────────────────────────
export type Category =
  | "suppliers"
  | "sales"
  | "operational"
  | "administrative"
  | "others";

// ── Business line ──────────────────────────────────────────────────────
export type BusinessType = "B2B" | "B2C";

// ── Grouping granularity for aggregated summaries ──────────────────────
export type GroupBy = "day" | "week" | "month";
```

---

## 3. Feature 1 — Date range filter on the home dashboard

### Purpose

Allow the finance team to focus on a specific period. Two date inputs at the top of the dashboard filter all data displayed on the page. When both inputs are empty, the full dataset is shown.

### Endpoints consumed

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/metrics/facets` | Retrieve the available date range (`min_date`, `max_date`) to show as a hint |
| `GET` | `/api/metrics` | Retrieve movements filtered by date range |

### Request: `GET /api/metrics`

#### Query parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `start_date` | `string` (date) | no | `null` | Inclusive start of range. Format: `YYYY-MM-DD`. Example: `"2026-01-01"`. When absent, no lower bound. |
| `end_date` | `string` (date) | no | `null` | Inclusive end of range. Format: `YYYY-MM-DD`. Example: `"2026-06-30"`. When absent, no upper bound. |
| `category` | `string` | no | `null` | Filter by category. One of: `suppliers`, `sales`, `operational`, `administrative`, `others`. |
| `operation_type` | `string` | no | `null` | Filter by operation type. One of: `income`, `outcome`. |

> **Note:** `category` and `operation_type` are not used by this feature. They exist on the endpoint but are outside scope.

#### Response: `FinancialMovement[]`

```typescript
interface FinancialMovement {
  /** ISO date string. Example: "2026-01-15" */
  create_date: string;
  /** Monetary amount in USD. Always positive, rounded to 2 decimals. */
  amount: number;
  /** "income" or "outcome" */
  operation_type: OperationType;
  /** One of: "suppliers", "sales", "operational", "administrative", "others" */
  category: Category;
  /** "B2B" or "B2C" */
  business_type: BusinessType;
}
```

**Example response:**
```json
[
  {
    "create_date": "2026-01-15",
    "amount": 48200.00,
    "operation_type": "income",
    "category": "sales",
    "business_type": "B2B"
  }
]
```

### Request: `GET /api/metrics/facets`

#### Query parameters

None.

#### Response: `FacetsResponse`

```typescript
interface FacetsResponse {
  /** Always ["income", "outcome"] */
  operation_types: [OperationType, OperationType];
  /** Always ["B2B", "B2C"] */
  business_types: [BusinessType, BusinessType];
  /** Always 5 entries, alphabetically sorted */
  categories: Category[];
  /** Earliest date in dataset. Format: YYYY-MM-DD */
  min_date: string;
  /** Latest date in dataset. Format: YYYY-MM-DD */
  max_date: string;
}
```

**Example response:**
```json
{
  "operation_types": ["income", "outcome"],
  "business_types": ["B2B", "B2C"],
  "categories": ["administrative", "operational", "others", "sales", "suppliers"],
  "min_date": "2025-11-01",
  "max_date": "2026-10-28"
}
```

---

## 4. Feature 2 — Anomaly alerts table on the home dashboard

### Purpose

Display a table highlighting periods where spending spiked unexpectedly. The user can configure the sensitivity threshold. The table appears below the charts on the home dashboard.

### Endpoints consumed

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/metrics/alerts` | Retrieve periods whose outcome exceeds a baseline by the configured threshold |

### Request: `GET /api/metrics/alerts`

#### Query parameters

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `threshold` | `number` | no | `0.3` | `0.01` – `1.0` (PM spec; backend currently enforces `≥0`) | The minimum increase ratio to flag a period as anomalous. A period is flagged when `(outcome - baseline) / baseline > threshold`. |
| `group_by` | `string` | no | `"month"` | `"month"`, `"week"`, `"day"` | How to group movements before computing totals. Affects the `period` format in the response. |
| `start_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive start of the date range to scan for anomalies. Movements outside this range are excluded from both the baseline and the period being checked. |
| `end_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive end of the date range. |
| `business_type` | `string` | no | — | `"B2B"`, `"B2C"` | Optional filter to scan only one business line. |

> **Known issue (PM vs backend):** The PM says "rolling average of the previous 3 periods" but the backend averages **all** historical periods. The `baseline_average` field in the response reflects this all-periods average. A backend fix is tracked separately. The frontend must display whatever `baseline_average` contains and label it "Rolling Average" (without specifying "3 periods").

#### Response: `AlertEntry[]`

```typescript
interface AlertEntry {
  /**
   * Period identifier. Format depends on group_by:
   * - "month" → "YYYY-MM"     (e.g. "2026-03")
   * - "week"  → "YYYY-WNN"    (e.g. "2026-W09")
   * - "day"   → "YYYY-MM-DD"  (e.g. "2026-03-15")
   */
  period: string;
  /** Total outcome (expenditure) in this period, in USD. Positive number, 2 decimals. */
  outcome_total: number;
  /**
   * Baseline average of all previous periods' outcomes, in USD.
   * NOTE: This is NOT a 3-period rolling average as the PM requested.
   * It is the mean of ALL periods before this one.
   */
  baseline_average: number;
  /**
   * Fractional increase: (outcome_total - baseline_average) / baseline_average.
   * Always positive. Rounded to 4 decimals.
   * Display as percentage: value * 100 + "%"  (e.g. 0.4065 → "40.7%").
   */
  increase_ratio: number;
}
```

**Example response (threshold=0.3, group_by=month):**
```json
[
  {
    "period": "2025-12",
    "outcome_total": 103378.98,
    "baseline_average": 41404.44,
    "increase_ratio": 1.4968
  },
  {
    "period": "2026-03",
    "outcome_total": 88076.90,
    "baseline_average": 55334.29,
    "increase_ratio": 0.5917
  }
]
```

**Empty response** (threshold too high, or no anomalies):
```json
[]
```

---

## 5. Feature 3 — B2B vs B2C comparison view

### Purpose

A dedicated page (`/b2b-b2c`) comparing revenue performance between the B2B and B2C business lines. Two side-by-side tables show the top 5 income categories for each group, and a bar chart below compares total income.

### Endpoints consumed

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/metrics/categories/top` | Top income categories per business line |
| `GET` | `/api/metrics/summary` | Grand total income per business line (for percentage calculation) |
| `GET` | `/api/metrics/facets` | Available categories and date range hints |

### Request: `GET /api/metrics/categories/top`

#### Query parameters

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `operation_type` | `string` | no | `"outcome"` | `"income"`, `"outcome"` | The operation type to rank categories for. This feature always passes `"income"`. |
| `limit` | `number` | no | `5` | `1` – `20` | Maximum number of categories to return. |
| `start_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive start of date range. |
| `end_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive end of date range. |
| `business_type` | `string` | no | — | `"B2B"`, `"B2C"` | Filter to a specific business line. This feature calls the endpoint twice: once per business type. |

#### Response: `CategoryEntry[]`

```typescript
interface CategoryEntry {
  /** Category name. One of the 5 valid categories. */
  category: Category;
  /** The operation type that was passed as query parameter. Always "income" for this feature. */
  operation_type: OperationType;
  /** Total amount for this category, in USD. Rounded to 2 decimals. Descending order. */
  total_amount: number;
}
```

**Example response (operation_type=income, limit=5, business_type=B2B):**
```json
[
  { "category": "sales", "operation_type": "income", "total_amount": 557903.97 },
  { "category": "others", "operation_type": "income", "total_amount": 57636.75 }
]
```

> **Note:** The response may contain fewer than `limit` entries if the business type has fewer categories with that operation type. The frontend must handle sparse results gracefully.

### Request: `GET /api/metrics/summary`

#### Query parameters

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `group_by` | `string` | no | `"month"` | `"month"`, `"week"`, `"day"` | Not directly rendered; the frontend sums all periods' income values for the grand total. |
| `start_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive start of date range. |
| `end_date` | `string` (date) | no | — | `YYYY-MM-DD` | Inclusive end of date range. |
| `operation_type` | `string` | no | — | `"income"`, `"outcome"` | This feature passes `"income"`. |
| `business_type` | `string` | no | — | `"B2B"`, `"B2C"` | This feature calls the endpoint twice (once per business type). |

#### Response: `MetricsSummaryItem[]`

```typescript
interface MetricsSummaryItem {
  /** Period identifier. For "month" group_by: "YYYY-MM". */
  period: string;
  /** Total income in this period, USD. 0.0 if none. */
  income: number;
  /** Total outcome in this period, USD. 0.0 if none. */
  outcome: number;
  /** Net: income - outcome, USD. */
  net: number;
}
```

**Usage in this feature:** The frontend sums `income` across all periods in the response to obtain the grand total income for the business line. This grand total is used to calculate `% of Group Total` in the category table: `(category.total_amount / grandTotal) * 100`.

---

## 6. Endpoints quick reference

| Method | Path | Used by | Key parameters |
|---|---|---|---|
| `GET` | `/api/metrics` | F1 | `start_date`, `end_date` |
| `GET` | `/api/metrics/facets` | F1, F3 | *(none)* |
| `GET` | `/api/metrics/alerts` | F2 | `threshold`, `group_by`, `start_date`, `end_date`, `business_type` |
| `GET` | `/api/metrics/categories/top` | F3 | `operation_type`, `limit`, `start_date`, `end_date`, `business_type` |
| `GET` | `/api/metrics/summary` | F3 | `group_by`, `operation_type`, `business_type`, `start_date`, `end_date` |

---

## 7. Implementation prerequisites

Before implementing, a fresh agent needs to be aware of these items not captured in the individual feature sections.

### 7.1 Routing

`react-router-dom` is **not currently installed**. Add it to `package.json`:

```bash
npm install react-router-dom
```

Two routes are needed (details in `components.md` section 1):

| Route | Page component | Features |
|---|---|---|
| `/` | `HomePage` | F1 (date filter) + F2 (alerts table) |
| `/b2b-b2c` | `B2bB2cPage` | F3 (B2B vs B2C comparison) |

### 7.2 API base URL

The frontend uses `VITE_API_BASE_URL` (from `import.meta.env.VITE_API_BASE_URL`) defaulting to `http://localhost:8001`. See `frontend/.env.example`.

For development with the Vite proxy (no CORS needed), use relative paths like `/api/metrics` instead of absolute URLs.

### 7.3 Data fetching pattern

All API calls follow the same pattern documented in `components.md` section 5.1 (useState triplet + useEffect with cancellation flag). Inline `fetch` calls are acceptable for this draft.

### 7.4 Client-computed types

The current dashboard computes `KPIMetrics` and `MonthlyDataPoint` client-side from raw `FinancialMovement[]` data. These types live in `src/lib/financial-types.ts`. The utility functions `computeKPIs()` and `computeMonthlyData()` in `src/lib/financial-utils.ts` transform movements into these types.

When implementing Feature 1, the existing `fetchFinancialData()` function and these compute functions can be reused — just pass the filtered movements from the API.

### 7.5 Component specifications

For every UI component's exact props, states (loading/error/empty/success), and layout decisions, refer to `frontend/specs/components.md`. The component spec also resolves all PM ambiguities (section 6 of that file).

---

## 8. Edge cases

Every edge case below has been verified against the live backend. The UI must handle each one explicitly.

### Feature 1 — Date range filter

| # | Scenario | Backend behaviour | UI requirement |
|---|---|---|---|
| 1.1 | **Both inputs empty** | `GET /api/metrics` called with no date params → returns all 360 movements | Show full dataset. Dashboard header badge shows `"Full Year"` or similar generic label. |
| 1.2 | **Only `start_date` provided** | `GET /api/metrics?start_date=2026-06-01` → movements from June 2026 onwards | Show data from start date to end of dataset. |
| 1.3 | **Only `end_date` provided** | `GET /api/metrics?end_date=2026-03-01` → movements up to March 2026 | Show data from beginning of dataset to end date. |
| 1.4 | **`start_date` = `end_date`** (single-day range) | `?start_date=2026-01-15&end_date=2026-01-15` → movements on that exact date only | Show a single day's data. All charts/KPIs reflect only that day. |
| 1.5 | **Date range with no matching data** | `?start_date=2027-01-01&end_date=2027-12-31` → returns empty array `[]` | KPI cards show `—` (dash). Charts show "No data available to display" (existing pattern). Header badge shows the selected range. |
| 1.6 | **`start_date` > `end_date`** (inverted) | Backend does NOT validate this — it returns movements where `create_date >= start_date AND create_date <= end_date`, which will be empty | The UI should either prevent this via `min`/`max` HTML attributes on the date inputs, or handle the empty response gracefully. |
| 1.7 | **Facets API fails** | Network error or non-200 response from `GET /api/metrics/facets` | Show the date inputs without min/max hints (no "Available range" text). The rest of the dashboard should still load from `/api/metrics`. |

### Feature 2 — Anomaly alerts

| # | Scenario | Backend behaviour | UI requirement |
|---|---|---|---|
| 2.1 | **No anomalies for current threshold** | Returns `[]` | Show explicit empty state: "No anomalies detected for the current threshold." — not an empty table, not a hidden component. |
| 2.2 | **Threshold = 0.01** (most sensitive) | Returns many entries (all periods except the first) | Table renders all available rows. Performance is not an issue (max 12 monthly periods). |
| 2.3 | **Threshold = 1.0** (least sensitive) | Returns only extreme spikes | Show whatever entries remain. May be empty. |
| 2.4 | **Threshold input out of range** | User types `1.5` or `-0.1` | The `<input type="number" min={0.01} max={1.0}>` clamps/prevents this natively. The UI does NOT send invalid values to the API. |
| 2.5 | **Alerts API fails** | Network error or non-200 response | Show error banner: "Failed to load anomaly alerts." The rest of the dashboard remains functional. |
| 2.6 | **Alerts with active date filter** | `?start_date=2026-01-01&end_date=2026-06-30&threshold=0.3` → only anomalies within the date range (baseline computed only from periods in range) | The date range from Feature 1 must be passed to the alerts endpoint. The table should reflect the filtered data. |
| 2.7 | **Only one period of data in range** | If the date range contains a single period, there is no "previous period" to compare against. Backend returns `[]` because `historical_outcomes` will be empty for the first period. | Show empty state: "No anomalies detected for the current threshold." |

### Feature 3 — B2B vs B2C comparison

| # | Scenario | Backend behaviour | UI requirement |
|---|---|---|---|
| 3.1 | **No date range selected** | Calls without date params → shows all available data for both business lines | Full dataset comparison. |
| 3.2 | **Date range with no data for one business line** | `?business_type=B2B&start_date=2025-01-01&end_date=2025-01-31` returns `[]` for categories/top and 0 income for summary | That business line's table shows "No income data for this business line." The comparison chart shows 0 for that bar. |
| 3.3 | **Fewer than 5 categories returned** | If a business line has fewer income-generating categories, the response contains fewer entries | The table renders however many entries are returned. The `% of Group Total` still sums correctly because it uses the grand total from the summary endpoint. |
| 3.4 | **Grand total from summary is 0** | `GET /api/metrics/summary?operation_type=income&business_type=B2B` returns entries where `income` sums to `0` | The `% of Group Total` column shows `"0.0%"` for all categories. Division by zero is avoided because `total_amount` would also be 0. |
| 3.5 | **Categories/top returns different order for B2B vs B2C** | Each business line has its own ranking | Tables are independent — each shows its own top 5 in descending order. |
| 3.6 | **One API call fails, the other succeeds** | e.g. B2B categories/top returns 200, B2C returns 500 | Show the successful business line's data. Show error banner for the failed one. The page does NOT crash entirely. |
| 3.7 | **Both API calls fail** | All fetches return errors | Show generic error page or error banners for both tables and chart. |
