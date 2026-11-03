"""Audit which rules in the draft carry executed evidence and which do not.

The draft's header makes a claim about how thoroughly each rule was
re-examined. This script checks that claim against the file itself so the
header can state the truth rather than an impression.

Run from the repository root:
    python .agents/rules/_validation/val_rule_coverage.py
"""

from __future__ import annotations

import re
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1] / "project-rules.draft.md"

RULE_HEADING = re.compile(r"^### (R\d+)\b", re.MULTILINE)
CONVENTION_ROW = re.compile(r"^\| \*\*(C\d)\*\*", re.MULTILINE)

# A rule counts as having executed evidence when one of its bullets was
# written from a run rather than from reading. The draft uses these lead-ins.
EXECUTED_LEADINS = (
    "**Validated:",
    "**Validated —",
    "**Validated.**",
    "**Current state:**",
)
READ_ONLY_LEADINS = (
    "**In practice:",
    "**In practice —",
    "**Open decision:",
    "**Aggregate naming:",
    "**Relationship to",
    "**Boundary this rule requires:",
    "**Trap for",
    "**Consequence for",
    "**Reproduced by:",
    "**Scope:",
    "**Status:",
    "**Rule:",
    "**Why:",
)


def split_sections(text: str) -> dict[str, str]:
    """Map each rule ID to the text of its section."""
    matches = list(RULE_HEADING.finditer(text))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start() : end]
    return sections


def classify(body: str) -> str:
    has_executed = any(marker in body for marker in EXECUTED_LEADINS)
    return "executed" if has_executed else "read-only"


def main() -> None:
    text = DRAFT.read_text(encoding="utf-8")
    sections = split_sections(text)
    conventions = CONVENTION_ROW.findall(text)

    executed: list[str] = []
    read_only: list[str] = []
    for rule_id, body in sections.items():
        (executed if classify(body) == "executed" else read_only).append(rule_id)

    def sort_key(rid: str) -> int:
        return int(rid[1:])

    executed.sort(key=sort_key)
    read_only.sort(key=sort_key)

    print(f"Draft: {DRAFT.name}")
    print(f"Rules found: {len(sections)} R-rules, {len(conventions)} C-conventions")
    print()

    print(f"Rules with a 'Validated' evidence bullet ({len(executed)}):")
    print("    " + ", ".join(executed))
    print()

    print(f"Rules with no 'Validated' bullet ({len(read_only)}):")
    print("    " + (", ".join(read_only) if read_only else "(none)"))
    print()

    print(f"C-conventions in the table: {', '.join(conventions)}")
    print()

    # The draft's index must list every rule exactly once, or a reader
    # following it will look in the wrong section for a rule.
    # Slice from the "**Index**" marker to the next horizontal rule that sits
    # on its own line. Searching for the first "---" is wrong: the index is a
    # markdown table, so its header separator "| --- | --- |" matches first
    # and the slice comes back empty.
    index_start = text.find("**Index**")
    index_end = re.search(r"^---$", text[index_start:], re.MULTILINE)
    index_block = (
        text[index_start : index_start + index_end.start()]
        if index_end
        else text[index_start:]
    )
    indexed = set(re.findall(r"R\d+", index_block))
    indexed.update(re.findall(r"C\d+", index_block))
    # The index writes conventions compactly as "C1–C8". Expand any such
    # range, otherwise every convention after the first looks unlisted.
    for family, start, end in re.findall(r"([RC])(\d+)\s*[–-]\s*[RC]?(\d+)", index_block):
        indexed.update(f"{family}{n}" for n in range(int(start), int(end) + 1))
    all_ids = set(sections) | set(conventions)
    missing = sorted(all_ids - indexed, key=lambda r: (r[0], int(r[1:])))
    print(f"Rule IDs missing from the index: {missing if missing else 'none'}")
    unknown = sorted(indexed - all_ids, key=lambda r: (r[0], int(r[1:])))
    print(f"Index IDs that name no rule: {unknown if unknown else 'none'}")

    # The header once promised bracketed markers. Report whether they are
    # still in use, because an unused marker convention is its own defect.
    corrected = len(re.findall(r"\[corrected\]", text))
    narrowed = len(re.findall(r"\[scope-narrowed\]", text))
    print(f"Bracketed '[corrected]' occurrences: {corrected}")
    print(f"Bracketed '[scope-narrowed]' occurrences: {narrowed}")
    if corrected == 0 and narrowed == 0:
        print("  -> neither marker is used; the header must not promise them")


if __name__ == "__main__":
    main()
