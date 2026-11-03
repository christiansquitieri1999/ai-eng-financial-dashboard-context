"""Verify that validation.md's verdict table is arithmetically sound.

The report claims 18 + 5 + 2 = 25 rules and 5 + 3 = 8 conventions. This
checks the claim against the table itself, so a miscounted summary is caught
here rather than by a reader.

Run from the repository root:
    python .agents/rules/_validation/val_report_consistency.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# The report lives beside this script, not at the repository root.
REPORT = Path(__file__).resolve().parent / "validation.md"
DRAFT = ROOT / ".agents" / "rules" / "project-rules.draft.md"


def ids_in(text: str, family: str) -> set[str]:
    return set(re.findall(rf"\b{family}(\d+)\b", text))


def main() -> None:
    report = REPORT.read_text(encoding="utf-8")

    # Scope the parse to the "Verdict by rule" section only. The correction
    # tables later in the report also use bold rule IDs as row labels, and
    # letting them in would double-count every corrected rule.
    section = report.split("### Verdict by rule", 1)[1].split("\n---", 1)[0]
    rows = [
        line
        for line in section.splitlines()
        if line.startswith("| **") and re.search(r"\bR\d+\b", line)
    ]

    verdicts: dict[str, set[str]] = {}
    for line in rows:
        label = re.match(r"\| \*\*([^*]+)\*\*", line)
        if not label:
            continue
        name = label.group(1).strip()
        r_ids = {f"R{n}" for n in re.findall(r"\bR(\d+)\b", line)}
        c_ids = {f"C{n}" for n in re.findall(r"\bC(\d+)\b", line)}
        if r_ids or c_ids:
            verdicts[name] = r_ids | c_ids

    print("Verdict table, parsed from validation.md:")
    all_listed: set[str] = set()
    for name, listed in verdicts.items():
        all_listed |= listed
        print(f"  {name:<58} {len(listed):>2}  {', '.join(sorted(listed, key=lambda x: (x[0], int(x[1:]))))}")
    print()

    draft = DRAFT.read_text(encoding="utf-8")
    all_r = {f"R{n}" for n in ids_in(draft, "R")}
    all_c = {f"C{n}" for n in ids_in(draft, "C")}
    expected = all_r | all_c

    print(f"Draft declares: {len(all_r)} rules, {len(all_c)} conventions")
    print(f"Report lists:   {len(all_listed)} IDs")

    missing = sorted(expected - all_listed, key=lambda x: (x[0], int(x[1:])))
    extra = sorted(all_listed - expected, key=lambda x: (x[0], int(x[1:])))
    print(f"Declared but never given a verdict: {missing if missing else 'none'}")
    print(f"Given a verdict but not declared:   {extra if extra else 'none'}")
    print()

    # Check the stated subtotals in the Total row, if present.
    total_row = next(
        (line for line in report.splitlines() if line.startswith("| **Total**")), None
    )
    if total_row:
        stated = total_row.split("|")[3].strip()
        print(f"Total row states: {stated}")
        numbers = [int(n) for n in re.findall(r"\d+", stated)]
        sum_expr = re.search(r"([\d\s+]+)=\s*(\d+)", stated)
        sum_expr_c = re.search(r"([\d\s+]+)=\s*(\d+)\s*$", stated)
        ok = True
        for expr in (sum_expr, sum_expr_c):
            if expr:
                parts = [int(x) for x in re.findall(r"\d+", expr.group(1))]
                claimed = int(expr.group(2))
                if sum(parts) != claimed:
                    print(f"  ARITHMETIC ERROR: {'+'.join(map(str, parts))} = {sum(parts)}, not {claimed}")
                    ok = False
        if ok:
            print("  arithmetic in the Total row checks out")

    overlap: set[str] = set()
    seen: set[str] = set()
    for listed in verdicts.values():
        overlap |= seen & listed
        seen |= listed
    if overlap:
        print(f"\nIDs given two verdicts: {sorted(overlap)}")
    else:
        print("\nNo ID appears under more than one verdict.")


if __name__ == "__main__":
    main()
