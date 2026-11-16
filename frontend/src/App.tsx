import { lazy, Suspense, useEffect, useState } from "react";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { KPIRow } from "@/components/dashboard/kpi-row";
import { ChartErrorBoundary } from "@/components/dashboard/chart-error-boundary";
import { ChartSkeleton } from "@/components/dashboard/chart-skeleton";
import {
  type FinancialMovement,
  type KPIMetrics,
  type MonthlyDataPoint,
} from "@/lib/financial-types";
import { computeKPIs, computeMonthlyData } from "@/lib/financial-utils";
import { parseFinancialMovements } from "@/lib/financial-validation";

const IncomeOutcomeChart = lazy(() =>
  import("@/components/dashboard/income-outcome-chart").then((module) => ({
    default: module.IncomeOutcomeChart,
  })),
);
const ProfitPercentChart = lazy(() =>
  import("@/components/dashboard/profit-percent-chart").then((module) => ({
    default: module.ProfitPercentChart,
  })),
);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";
  
async function fetchFinancialData(): Promise<FinancialMovement[]> {
  const response = await fetch(`${API_BASE_URL}/api/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch financial data: ${response.status}`);
  }
  const payload: unknown = await response.json();
  return parseFinancialMovements(payload);
}

function App() {
  const [metrics, setMetrics] = useState<KPIMetrics | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFinancialData()
      .then((movements) => {
        setMetrics(computeKPIs(movements));
        setMonthlyData(computeMonthlyData(movements));
      })
      .catch(() => {
              // Skill §Error handling (4.1.3 / 3.1.2): English text, announced via role="alert"
        setError(
                "Couldn't load financial data. Check the backend API connection.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <main id="main-content" tabIndex={-1} className="dark min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8">
          <DashboardHeader period="2024 - Full Year" />

          {error ? (
                <div
                  role="alert"
                  className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive-foreground"
                >
              {error}
            </div>
          ) : null}

              {/* Skill §Live regions: announce loading without moving focus */}
              <div role="status" aria-live="polite" className="sr-only">
                {loading
                  ? "Loading financial metrics…"
                  : error
                    ? "Financial metrics failed to load"
                    : "Financial metrics loaded"}
              </div>

              <section aria-label="Key performance indicators" aria-busy={loading}>
            <KPIRow metrics={metrics} loading={loading} />
          </section>

          <section
            aria-label="Financial charts"
            aria-busy={loading}
            className="grid grid-cols-1 gap-4 xl:grid-cols-2"
          >
            <ChartErrorBoundary title="Income vs. Outcome">
              <Suspense
                fallback={
                  <ChartSkeleton
                    title="Income vs. Outcome"
                    description="Monthly revenue and expenditure evolution"
                  />
                }
              >
                <IncomeOutcomeChart data={monthlyData} loading={loading} />
              </Suspense>
            </ChartErrorBoundary>
            <ChartErrorBoundary title="Profit Margin %">
              <Suspense
                fallback={
                  <ChartSkeleton
                    title="Profit Margin %"
                    description="Monthly profit as a percentage of total income"
                  />
                }
              >
                <ProfitPercentChart data={monthlyData} loading={loading} />
              </Suspense>
            </ChartErrorBoundary>
          </section>
        </div>
      </div>
    </main>
  );
}

export default App;
