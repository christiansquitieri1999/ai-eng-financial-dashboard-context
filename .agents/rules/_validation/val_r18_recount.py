"""Recount the load-bearing status of the token "outcome".

R18 claims the token appears 91 times across backend and frontend.
This recount exists because the validation directories added during this
audit (`.agents/rules/_validation/`) themselves contain the word "outcome",
so a naive repo-wide grep inflates the number with probe artifacts rather
than product code.

Run from the repository root:
    python .agents/rules/_validation/val_r18_recount.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    "_validation",
    "validation",
}

INCLUDED_SUFFIXES = {".py", ".ts", ".tsx"}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def count_in_files(paths: list[Path], pattern: re.Pattern[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        found = len(pattern.findall(text))
        if found:
            # as_posix() so area prefixes match on Windows, where str(Path)
            # uses backslashes and would make every startswith() check fail.
            counts[path.relative_to(ROOT).as_posix()] = found
    return counts


def summarise(label: str, counts: dict[str, int]) -> None:
    total = sum(counts.values())
    print(f"{label}: {total} occurrences in {len(counts)} files")
    for path, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {n:>3}  {path}")
    print()


def main() -> None:
    files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.suffix in INCLUDED_SUFFIXES
        and not is_excluded(p.relative_to(ROOT))
    ]
    print(f"Scanning {len(files)} product files under {ROOT}")
    print(f"Excluded directory names: {sorted(EXCLUDED_DIRS)}")
    print()

    substring = re.compile(r"outcome", re.IGNORECASE)
    whole_word = re.compile(r"\boutcome\b", re.IGNORECASE)

    sub_counts = count_in_files(files, substring)
    word_counts = count_in_files(files, whole_word)

    summarise('Substring "outcome" (case-insensitive)', sub_counts)
    summarise('Whole word "outcome" (case-insensitive)', word_counts)

    # Break the numbers down by area so the claim can be checked per region.
    areas = {
        "backend/": lambda rel: rel.startswith("backend/"),
        "frontend/src/lib/": lambda rel: rel.startswith("frontend/src/lib/"),
        "frontend/src/components/": lambda rel: rel.startswith(
            "frontend/src/components/"
        ),
    }
    print("Area breakdown (substring):")
    for name, predicate in areas.items():
        subtotal = sum(n for rel, n in sub_counts.items() if predicate(rel))
        print(f"    {name:<28} {subtotal}")
    other = sum(
        n
        for rel, n in sub_counts.items()
        if not any(pred(rel) for pred in areas.values())
    )
    print(f"    {'everywhere else':<28} {other}")
    print()

    # Guard: prove the probe directories were genuinely skipped.
    leak = [
        rel for rel in sub_counts if "_validation" in rel or "validation/" in rel
    ]
    print(f"Probe files that leaked into the count: {len(leak)} (expected 0)")
    print()

    # The draft originally recorded 91. Show where the difference comes from
    # so the corrected figure is auditable rather than merely asserted.
    with_tests = dict(sub_counts)
    without_tests = {
        rel: n
        for rel, n in with_tests.items()
        if not rel.startswith("backend/tests/")
        and not rel.endswith(".test.ts")
        and not rel.endswith(".test.tsx")
    }
    print(f"Substring total, product code only (no test files): {sum(without_tests.values())}")
    print(
        "Substring total, including test files:              "
        f"{sum(with_tests.values())}"
    )


if __name__ == "__main__":
    main()
