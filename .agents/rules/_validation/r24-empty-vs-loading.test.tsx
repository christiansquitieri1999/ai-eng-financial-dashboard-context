import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { KPIRow } from "@/components/dashboard/kpi-row";

// R24 probe: can a caller distinguish "no data" from "still loading"
// using only the props KPIRow actually accepts?
//
// This file lives outside `frontend/` (in `.agents/rules/_validation/`). The
// `@` alias still resolves because Vitest keeps `frontend/` as its root; only
// the scan directory changes. See `README.md` for the exact command.
describe("R24 - empty state vs loading state", () => {
  it("renders identical markup for empty and non-loading-empty", () => {
    const emptyNotLoading = renderToStaticMarkup(<KPIRow metrics={null} loading={false} />);
    const emptyOmitted = renderToStaticMarkup(<KPIRow metrics={null} />);

    // No hasData-style prop exists, so NULL metrics and NOT-LOADING are the
    // same input. The two renders are byte-identical.
    expect(emptyNotLoading).toBe(emptyOmitted);

    // The only "no data" signal available is the em-dash placeholder.
    expect(emptyNotLoading).toContain("\u2014");

    // And it is NOT a skeleton: the loading branch is unreachable here.
    expect(emptyNotLoading).not.toContain("animate-pulse");
  });

  it("produces a visibly different render only when loading is toggled", () => {
    const loading = renderToStaticMarkup(<KPIRow metrics={null} loading={true} />);
    const empty = renderToStaticMarkup(<KPIRow metrics={null} loading={false} />);

    expect(loading).not.toBe(empty);
    expect(loading).toContain("animate-pulse");
  });

  it("shows the exact placeholders a user sees for an empty dataset", () => {
    const empty = renderToStaticMarkup(<KPIRow metrics={null} loading={false} />);
    // Count only the value cells (>—<), not em-dashes used as prose punctuation.
    // The "Net profit — income minus total outcome" helper text also contains one,
    // so a naive match on U+2014 returns 5, not 4.
    const valueCells = (empty.match(/>\u2014<\/p>/g) ?? []).length;
    expect(valueCells).toBe(4);

    const allDashes = (empty.match(/\u2014/g) ?? []).length;
    expect(allDashes).toBe(5); // 4 placeholders + 1 prose dash

    // Four placeholders and no explanation of why there is no data.
    expect(empty).not.toContain("No data");
    expect(empty).not.toContain("empty");
  });
});
