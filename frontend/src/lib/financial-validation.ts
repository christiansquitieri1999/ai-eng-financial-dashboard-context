import {
  type FinancialMovement,
  type OutcomeCategory,
  type IncomeCategory,
} from "./financial-types";

const incomeCategories: readonly IncomeCategory[] = ["sales", "others"];
const outcomeCategories: readonly OutcomeCategory[] = [
  "suppliers",
  "operational",
  "administrative",
  "others",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isCalendarDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }

  const [year, month, day] = value.split("-").map(Number);
  if (year < 1 || month < 1 || month > 12) return false;

  const isLeapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day >= 1 && day <= daysInMonth[month - 1];
}

function isBusinessType(value: unknown): value is FinancialMovement["business_type"] {
  return value === "B2B" || value === "B2C";
}

function isIncomeCategory(value: unknown): value is IncomeCategory {
  return incomeCategories.some((category) => category === value);
}

function isOutcomeCategory(value: unknown): value is OutcomeCategory {
  return outcomeCategories.some((category) => category === value);
}

function isFinancialMovement(value: unknown): value is FinancialMovement {
  if (
    !isRecord(value) ||
    !isCalendarDate(value.create_date) ||
    typeof value.amount !== "number" ||
    !Number.isFinite(value.amount) ||
    !isBusinessType(value.business_type)
  ) {
    return false;
  }

  if (value.operation_type === "income") {
    return isIncomeCategory(value.category);
  }

  if (value.operation_type === "outcome") {
    return isOutcomeCategory(value.category);
  }

  return false;
}

/** Validate untrusted JSON against the backend movement contract. */
export function parseFinancialMovements(value: unknown): FinancialMovement[] {
  if (!Array.isArray(value) || !value.every(isFinancialMovement)) {
    throw new Error("The financial data response has an invalid format.");
  }

  return value;
}
