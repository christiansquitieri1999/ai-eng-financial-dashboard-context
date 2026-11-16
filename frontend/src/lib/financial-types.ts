export type OperationType = 'income' | 'outcome'
export type IncomeCategory = 'sales' | 'others'
export type OutcomeCategory = 'suppliers' | 'operational' | 'administrative' | 'others'
export type Category = IncomeCategory | OutcomeCategory
export type BusinessType = 'B2B' | 'B2C'

interface FinancialMovementBase {
  create_date: string // ISO calendar date: YYYY-MM-DD
  amount: number
  business_type: BusinessType
}

export type FinancialMovement =
  | (FinancialMovementBase & {
      operation_type: 'income'
      category: IncomeCategory
    })
  | (FinancialMovementBase & {
      operation_type: 'outcome'
      category: OutcomeCategory
    })

export interface KPIMetrics {
  totalIncome: number
  totalOutcome: number
  profit: number
  profitPercent: number
}

export interface MonthlyDataPoint {
  month: string
  income: number
  outcome: number
  profitPercent: number
}
