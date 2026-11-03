"""Probe the exact behaviour of /api/metrics and /api/metrics/summary
with respect to the business_type filter, to resolve the R3/R19 ambiguity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

cases = [
    ("/api/metrics", None),
    ("/api/metrics", {"business_type": "b2b"}),
    ("/api/metrics", {"business_type": "b2c"}),
    ("/api/metrics", {"business_type": "nonsense"}),
    ("/api/metrics/summary", None),
    ("/api/metrics/summary", {"business_type": "b2b"}),
    ("/api/metrics/summary", {"business_type": "b2c"}),
    ("/api/metrics/summary", {"business_type": "nonsense"}),
    ("/api/metrics/b2b", None),
    ("/api/metrics/b2c", None),
]

print(f"{'endpoint':<26} {'param':<26} {'status':<7} payload-size / signal")
print("-" * 90)
for path, params in cases:
    response = client.get(path, params=params)
    label = "none" if params is None else str(params)
    if response.status_code == 200:
        body = response.json()
        size = len(body) if isinstance(body, list) else "obj"
        extra = ""
        if isinstance(body, list) and body:
            extra = f" first={body[0]}"
        elif isinstance(body, dict):
            extra = f" keys={sorted(body)[:6]}"
        print(f"{path:<26} {label:<26} {response.status_code:<7} {size}{extra}")
    else:
        print(f"{path:<26} {label:<26} {response.status_code:<7} {str(response.json())[:90]}")

print()
print("=== Does the business_type value change /api/metrics output? ===")
default = client.get("/api/metrics").json()
b2b = client.get("/api/metrics", params={"business_type": "b2b"}).json()
b2c = client.get("/api/metrics", params={"business_type": "b2c"}).json()
print(f"default row count = {len(default)}")
print(f"b2b     row count = {len(b2b)}")
print(f"b2c     row count = {len(b2c)}")
print(f"b2b identical to default: {b2b == default}")
print(f"b2c identical to default: {b2c == default}")
print("=> if identical, the parameter is silently ignored, not honoured")

print()
print("=== Do the /b2b and /b2c paths differ from each other? ===")
slash_b2b = client.get("/api/metrics/b2b").json()
slash_b2c = client.get("/api/metrics/b2c").json()
print(f"/metrics/b2b identical to /metrics/b2c: {slash_b2b == slash_b2c}")
print(f"/metrics/b2b identical to /metrics     : {slash_b2b == default}")

print()
print("=== Alerts: actual payload shape and emptiness ===")
alerts = client.get("/api/metrics/alerts", params={"threshold": 0}).json()
print(f"alert count = {len(alerts)}")
if alerts:
    print(f"first alert keys = {sorted(alerts[0])}")
