/**
 * @file Query-parameter type definitions for the Financial Metrics Dashboard API.
 *
 * Every type in this file corresponds to the query parameters accepted by one
 * or more backend endpoints. Types are derived from the OpenAPI spec at
 * `/docs`; UI-only constraints that are stricter than the backend are called out.
 *
 * Backend base URL: http://localhost:8001
 * OpenAPI endpoint: /docs (OAS 3.1, "Financial Metrics API 0.1.0")
 */

// ---------------------------------------------------------------------------
// Shared — used by multiple features
// ---------------------------------------------------------------------------

/**
 * Optional date-range filter accepted by several endpoints.
 *
 * When both fields are omitted the endpoint returns data for the full
 * available period. Omit an unset field from the query string; an empty
 * string is not a valid ISO date.
 */
export interface DateRangeFilter {
  /**
   * Inclusive start of the date range.
   * Format: `YYYY-MM-DD` (ISO 8601 calendar date).
   * Example: `"2026-01-01"`
   *
   * When `undefined`, omit the parameter to leave the range without a lower bound.
   */
  readonly start_date?: string;

  /**
   * Inclusive end of the date range.
   * Format: `YYYY-MM-DD` (ISO 8601 calendar date).
   * Example: `"2026-12-31"`
   *
   * When `undefined`, omit the parameter to leave the range without an upper bound.
   */
  readonly end_date?: string;
}

// ---------------------------------------------------------------------------
// Feature 1 — Date range filter on the home dashboard
//
// Uses DateRangeFilter directly (passed as query params to /api/metrics).
// No additional endpoint-specific parameters are needed for this feature.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Feature 2 — Anomaly alerts table on the home dashboard
// ---------------------------------------------------------------------------

/**
 * Query parameters for `GET /api/metrics/alerts`.
 */
export interface AlertsParams extends DateRangeFilter {
  /**
   * Anomaly detection threshold as a decimal ratio.
   * A period is flagged as anomalous when its outcome exceeds the
   * baseline average by more than this ratio.
   *
   * Valid range: `0.01` to `1.0` (inclusive).
   * Default: `0.3` (30% above baseline).
   *
   * **Note:** The PM spec says 0.01–1.0 but the backend currently only
   * enforces ≥0.  The spec tightens this until the backend is updated.
   *
   * @default 0.3
   */
  readonly threshold?: number;

  /**
   * Temporal granularity for grouping outcomes before anomaly detection.
   *
   * - `"month"`: group by calendar month (`"YYYY-MM"`)
   * - `"week"`:  group by ISO week  (`"YYYY-WNN"`)
   * - `"day"`:   group by calendar date (`"YYYY-MM-DD"`)
   *
   * @default "month"
   */
  readonly group_by?: "month" | "week" | "day";

  /**
   * Optional business-type filter.
   * When provided, only movements of this business line are considered.
   * - `"B2B"`: business-to-business transactions
   * - `"B2C"`: business-to-consumer transactions
   */
  readonly business_type?: "B2B" | "B2C";
}

// ---------------------------------------------------------------------------
// Feature 3 — B2B vs B2C comparison view
// ---------------------------------------------------------------------------

/**
 * Query parameters for `GET /api/metrics/categories/top`.
 *
 * Returns the top-N categories ranked by total amount for a given
 * operation type, optionally filtered by business line and date range.
 */
export interface TopCategoriesParams extends DateRangeFilter {
  /**
   * Operation type to rank categories for.
   *
   * - `"income"`:  rank by income (revenue)
   * - `"outcome"`: rank by outcome (expenditure)
   *
   * The B2B-vs-B2C feature always passes `"income"`.
   *
   * @default "outcome"
   */
  readonly operation_type?: "income" | "outcome";

  /**
   * Maximum number of categories to return.
   * Valid range: `1` to `20` (inclusive).
   *
   * @default 5
   */
  readonly limit?: number;

  /**
   * Optional business-type filter.
   * When provided, only movements of this business line are ranked.
   * - `"B2B"`: business-to-business transactions
   * - `"B2C"`: business-to-consumer transactions
   */
  readonly business_type?: "B2B" | "B2C";
}

// ---------------------------------------------------------------------------
// Supporting types for Feature 3 — summary-based totals
// ---------------------------------------------------------------------------

/**
 * Query parameters for `GET /api/metrics/summary`.
 *
 * Used by Feature 3 to obtain the grand-total income for a business line
 * when the top-5 categories need to be expressed as a percentage of the
 * group total.
 */
export interface SummaryParams extends DateRangeFilter {
  /**
   * Temporal granularity for the summary periods.
   *
   * - `"month"`: group by calendar month
   * - `"week"`:  group by ISO week
   * - `"day"`:   group by calendar date
   *
   * @default "month"
   */
  readonly group_by?: "month" | "week" | "day";

  /**
   * Optional category filter.
   * One of: `"suppliers"`, `"sales"`, `"operational"`, `"administrative"`, `"others"`.
   */
  readonly category?:
    | "suppliers"
    | "sales"
    | "operational"
    | "administrative"
    | "others";

  /**
   * Optional operation-type filter.
   * - `"income"`:  only income movements
   * - `"outcome"`: only outcome movements
   */
  readonly operation_type?: "income" | "outcome";

  /**
   * Optional business-type filter.
   * - `"B2B"`: business-to-business transactions
   * - `"B2C"`: business-to-consumer transactions
   */
  readonly business_type?: "B2B" | "B2C";
}
