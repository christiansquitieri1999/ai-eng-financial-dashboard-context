"""C3 / C8 probe: what the backend tests actually import and assert.

C3 claims financial helpers are tested directly without HTTP.
C8 claims ordering, date-edge inclusion, and cross-year aggregation are covered.
Both are claims about test content, so read the test module's structure rather
than trusting the summary.
"""

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEST = ROOT / "backend" / "tests" / "test_routes.py"

source = TEST.read_text(encoding="utf-8")
tree = ast.parse(source)

print(f"file: {TEST.relative_to(ROOT)}")
print(f"lines: {len(source.splitlines())}")
print()

# C3: are app internals imported directly?
imported: list[str] = []
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        names = ", ".join(a.name for a in node.names)
        imported.append(f"from {node.module} import {names}")
print("C3 imports:")
for line in imported:
    print(f"  {line}")
print()

tests = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
print(f"test functions: {len(tests)}")

direct_call_tests = []
http_only_tests = []
for t in tests:
    body_src = ast.get_source_segment(source, t) or ""
    uses_http = "client." in body_src
    uses_helper = any(
        name in body_src
        for name in (
            "filter_movements", "summarize_movements", "build_top_categories",
            "detect_outcome_alerts", "generate_mock_movements", "build_metrics_facets",
            "_build_movement", "_year_for_month",
        )
    )
    if uses_helper and not uses_http:
        direct_call_tests.append(t.name)
    elif uses_http and not uses_helper:
        http_only_tests.append(t.name)

print(f"C3 tests calling helpers with NO http client: {len(direct_call_tests)}")
for n in direct_call_tests:
    print(f"  {n}")
print(f"C3 tests going through the http client only: {len(http_only_tests)}")
for n in http_only_tests:
    print(f"  {n}")
print(f"C3 tests mixing both: {len(tests) - len(direct_call_tests) - len(http_only_tests)}")
print()

# HTTP method calls, to name the endpoints exercised.
print("client calls by test:")
for t in tests:
    seg = ast.get_source_segment(source, t) or ""
    calls = [ln.strip() for ln in seg.splitlines() if "client.get(" in ln]
    for c in calls:
        print(f"  {t.name}: {c}")
print()

# C8: which boundary keywords appear inside assertions?
KEYWORDS = {
    "ordering/sorted": ("sorted", "== sorted", "sort"),
    "date edge inclusion": ("start_date", "end_date"),
    "cross-year": ("year", "12", "01"),
    "empty input": ("[]", "empty", "no data"),
    "invalid enum (422)": ("422",),
    "exact value": ("==",),
}
print("C8 assertion keywords present in the test module:")
for label, needles in KEYWORDS.items():
    hits = [n for n in needles if n in source]
    print(f"  {label:22} {hits if hits else 'NONE'}")
print()

# The specific blind spot: does any test assert the year span?
print("C8 blind spot check:")
for t in tests:
    seg = ast.get_source_segment(source, t) or ""
    if "360" in seg:
        print(f"  '{t.name}' asserts 360 records")
        print(f"    asserts a year span? {'yes' if 'year' in seg else 'NO'}")
        print(f"    asserts month span? {'yes' if 'month' in seg else 'NO'}")
