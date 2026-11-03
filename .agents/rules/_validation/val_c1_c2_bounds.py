"""C1 / C2 probe: are the declared bounds actually enforced?

C2 claims `limit` ge=1,le=20 and `threshold` ge=0 are enforced.
C1 claims invalid enums are rejected rather than ignored.
Run every boundary and record the real status code.
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

CASES = [
    # (label, url, params, expected)
    ("C2 limit=1 (lower bound, valid)", "/api/metrics/categories/top", {"limit": 1}, 200),
    ("C2 limit=20 (upper bound, valid)", "/api/metrics/categories/top", {"limit": 20}, 200),
    ("C2 limit=21 (above max)", "/api/metrics/categories/top", {"limit": 21}, 422),
    ("C2 limit=0 (below min)", "/api/metrics/categories/top", {"limit": 0}, 422),
    ("C2 limit=-5 (negative)", "/api/metrics/categories/top", {"limit": -5}, 422),
    ("C2 limit=abc (not an int)", "/api/metrics/categories/top", {"limit": "abc"}, 422),
    ("C2 threshold=0 (lower bound, valid)", "/api/metrics/alerts", {"threshold": 0}, 200),
    ("C2 threshold=-0.1 (negative)", "/api/metrics/alerts", {"threshold": -0.1}, 422),
    ("C2 threshold=1 (valid)", "/api/metrics/alerts", {"threshold": 1}, 200),
    ("C1 operation_type=income (valid)", "/api/metrics", {"operation_type": "income"}, 200),
    ("C1 operation_type=bogus", "/api/metrics", {"operation_type": "bogus"}, 422),
    ("C1 category=bogus", "/api/metrics", {"category": "bogus"}, 422),
    ("C1 group_by=bogus", "/api/metrics/summary", {"group_by": "bogus"}, 422),
    ("C1 business_type=B2B (valid, uppercase)", "/api/metrics/summary", {"business_type": "B2B"}, 200),
    ("C1 business_type=b2b (lowercase)", "/api/metrics/summary", {"business_type": "b2b"}, 422),
    ("C1 business_type=b2b on /api/metrics (undeclared)", "/api/metrics", {"business_type": "b2b"}, 200),
]

failures = 0
for label, url, params, expected in CASES:
    response = client.get(url, params=params)
    ok = response.status_code == expected
    if not ok:
        failures += 1
    mark = "OK  " if ok else "FAIL"
    print(f"{mark} {label:48} -> {response.status_code} (expected {expected})")

print()
print(f"{len(CASES) - failures}/{len(CASES)} matched")

# The undeclared-parameter case deserves its result size, not just a status.
undeclared = client.get("/api/metrics", params={"business_type": "b2b"})
unfiltered = client.get("/api/metrics")
print()
print("R3 detail - undeclared parameter is accepted and ignored:")
print(f"  /api/metrics                     -> {len(unfiltered.json())} rows")
print(f"  /api/metrics?business_type=b2b   -> {len(undeclared.json())} rows")
print(f"  byte-identical payload: {undeclared.json() == unfiltered.json()}")

sys.exit(1 if failures else 0)
