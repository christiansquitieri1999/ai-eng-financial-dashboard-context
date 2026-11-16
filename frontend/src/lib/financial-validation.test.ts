import { describe, expect, it } from "vitest";
import { parseFinancialMovements } from "./financial-validation";

const validIncome = {
  create_date: "2025-11-01",
  amount: 123.45,
  operation_type: "income",
  category: "sales",
  business_type: "B2B",
};

const validOutcome = {
  create_date: "2026-10-28",
  amount: 98.76,
  operation_type: "outcome",
  category: "administrative",
  business_type: "B2C",
};

describe("parseFinancialMovements", () => {
  it("accepts backend-conforming income and outcome records", () => {
    expect(parseFinancialMovements([validIncome, validOutcome])).toEqual([
      validIncome,
      validOutcome,
    ]);
  });

  it("accepts an empty collection", () => {
    expect(parseFinancialMovements([])).toEqual([]);
  });

  it.each([
    ["non-array response", { data: [validIncome] }],
    ["missing required field", [{ ...validIncome, category: undefined }]],
    ["non-finite amount", [{ ...validIncome, amount: Number.NaN }]],
    ["non-numeric amount", [{ ...validIncome, amount: "123.45" }]],
    ["invalid calendar date", [{ ...validIncome, create_date: "2025-02-30" }]],
    ["invalid business type", [{ ...validIncome, business_type: "enterprise" }]],
    ["income with outcome-only category", [{ ...validIncome, category: "suppliers" }]],
    ["outcome with income-only category", [{ ...validOutcome, category: "sales" }]],
    ["unknown operation type", [{ ...validIncome, operation_type: "refund" }]],
  ])("rejects %s", (_description, payload) => {
    expect(() => parseFinancialMovements(payload)).toThrow(
      "The financial data response has an invalid format.",
    );
  });
});
