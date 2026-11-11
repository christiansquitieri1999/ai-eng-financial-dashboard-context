/**
 * @file API response type definitions for the Financial Metrics Dashboard.
 *
 * Response shapes are derived from the OpenAPI spec served at /docs. Runtime
 * behavior and constraints not expressed by OpenAPI are identified separately
 * in the JSDoc rather than encoded as schema guarantees.
 *
 * Backend base URL: http://localhost:8001
 * OpenAPI endpoint: /docs (OAS 3.1, "Financial Metrics API 0.1.0")
 */

// ---------------------------------------------------------------------------
// Shared enums — also used by the backend Pydantic models
// ---------------------------------------------------------------------------

/**
 * Financial operation type.
 * - `"income"`:  money received (revenue)
 * - `"outcome"`: money spent (expenditure)
 */
export type OperationType = "income" | "outcome";

/**
 * Movement category.
 * - `"suppliers"`:      payments to vendors / cost of goods
 * - `"sales"`:          revenue from sales
 * - `"operational"`:    day-to-day operating expenses
 * - `"administrative"`: administrative overhead
 * - `"others"`:         uncategorised movements
 */
export type Category =
  | "suppliers"
  | "sales"
  | "operational"
  | "administrative"
  | "others";

/**
 * Business line identifier.
 * - `"B2B"`: business-to-business transactions
 * - `"B2C"`: business-to-consumer transactions
 */
export type BusinessType = "B2B" | "B2C";

/**
 * Grouping granularity for aggregated summaries.
 * - `"day"`:   group by calendar date (ISO 8601)
 * - `"week"`:  group by ISO week  ("2026-W03")
 * - `"month"`: group by calendar month ("2026-01")
 */
export type GroupBy = "day" | "week" | "month";

// ---------------------------------------------------------------------------
// Feature 1 — Date range filter on the home dashboard
// ---------------------------------------------------------------------------

/**
 * Response from `GET /api/metrics/facets`.
 *
 * Provides the set of available filter values and the full date range
 * covered by the dataset.  Used by Feature 1 to show the valid date
 * range near the date inputs and by Feature 3 to list available
 * categories and business types.
 *
 * @example
 * {
 *   "operation_types": ["income", "outcome"],
 *   "business_types": ["B2B", "B2C"],
 *   "categories": ["administrative", "operational", "others", "sales", "suppliers"],
 *   "min_date": "2025-11-01",
 *   "max_date": "2026-10-28"
 * }
 */
export interface FacetsResponse {
  /** Operation types present in the dataset. OpenAPI defines this as an array. */
  readonly operation_types: readonly OperationType[];

  /** Business types present in the dataset. OpenAPI defines this as an array. */
  readonly business_types: readonly BusinessType[];

  /** Available categories; OpenAPI defines an array, and the current dataset has up to five. */
  readonly categories: readonly Category[];

  /**
   * Earliest movement date in the dataset.
   * Format: `YYYY-MM-DD` (ISO 8601 calendar date).
   */
  readonly min_date: string;

  /**
   * Latest movement date in the dataset.
   * Format: `YYYY-MM-DD` (ISO 8601 calendar date).
   */
  readonly max_date: string;
}

// ---------------------------------------------------------------------------
// Feature 2 — Anomaly alerts table on the home dashboard
// ---------------------------------------------------------------------------

/**
 * A single alert entry returned by `GET /api/metrics/alerts`.
 *
 * Represents a period whose total outcome exceeded a rolling baseline
 * average by more than the configured threshold.
 *
 * @example
 * {
 *   "period": "2026-03",
 *   "outcome_total": 88076.9,
 *   "baseline_average": 51426.41,
 *   "increase_ratio": 0.5597
 * }
 */
export interface AlertEntry {
  /**
   * The period identifier for which the anomaly was detected.
   * Format depends on the `group_by` query parameter:
   * - `"month"`: `"YYYY-MM"`     e.g. `"2026-03"`
   * - `"week"`:  `"YYYY-WNN"`    e.g. `"2026-W09"`
   * - `"day"`:   `"YYYY-MM-DD"`  e.g. `"2026-03-15"`
   */
  readonly period: string;

  /** Current backend returns positive totals rounded to 2 decimals; OpenAPI specifies only number. */
  readonly outcome_total: number;

  /**
   * Rolling baseline — the average outcome of all historical periods
   * preceding this one (NOTE: currently the average of ALL previous
   * periods, NOT a sliding window of 3 as the PM spec requires).
   * In USD, rounded to 2 decimal places.
   */
  readonly baseline_average: number;

  /** Fractional increase; current backend rounds to 4 decimals. OpenAPI specifies only number. */
  readonly increase_ratio: number;
}

/**
 * Response from `GET /api/metrics/alerts`.
 *
 * Returns an array of anomaly entries.  When no period exceeds the
 * threshold the API returns an empty array `[]` — the frontend MUST
 * show an explicit empty-state message in that case.
 */
export type AlertsResponse = AlertEntry[];

// ---------------------------------------------------------------------------
// Feature 3 — B2B vs B2C comparison view
// ---------------------------------------------------------------------------

/**
 * A single ranked category entry returned by `GET /api/metrics/categories/top`.
 *
 * @example
 * {
 *   "category": "sales",
 *   "operation_type": "income",
 *   "total_amount": 557903.97
 * }
 */
export interface CategoryEntry {
  /**
   * The movement category.
   * One of: `"suppliers"`, `"sales"`, `"operational"`, `"administrative"`, `"others"`.
   */
  readonly category: Category;

  /**
   * The operation type this entry was filtered by.
   * Always the value passed in the `operation_type` query parameter.
   */
  readonly operation_type: OperationType;

  /** Current backend rounds this aggregate to 2 decimals; OpenAPI specifies only number. */
  readonly total_amount: number;
}

/**
 * Response from `GET /api/metrics/categories/top`.
 *
 * The array is sorted descending by `total_amount`.  Its length is
 * limited by the `limit` query parameter (default 5, max 20).
 */
export type TopCategoriesResponse = CategoryEntry[];

// ---------------------------------------------------------------------------
// Shared / utility — also needed for the three features
// ---------------------------------------------------------------------------

/**
 * Aggregated summary for a single period, returned by
 * `GET /api/metrics/summary`.
 *
 * Used by Feature 3 to compute the total income figure for each
 * business line when the categories/top endpoint alone does not
 * provide a grand total.
 *
 * @example
 * {
 *   "period": "2026-01",
 *   "income": 54757.96,
 *   "outcome": 0.0,
 *   "net": 54757.96
 * }
 */
export interface MetricsSummaryItem {
  /**
   * Period identifier.  Format depends on `group_by`:
   * - `"month"`: `"YYYY-MM"`
   * - `"week"`:  `"YYYY-WNN"`
   * - `"day"`:   `"YYYY-MM-DD"`
   */
  readonly period: string;

  /** Total income in this period, in USD.  0.0 if none. */
  readonly income: number;

  /** Total outcome in this period, in USD.  0.0 if none. */
  readonly outcome: number;

  /** Net value (income − outcome) in this period, in USD. */
  readonly net: number;
}

/**
 * Response from `GET /api/metrics/summary`.
 */
export type MetricsSummaryResponse = MetricsSummaryItem[];
