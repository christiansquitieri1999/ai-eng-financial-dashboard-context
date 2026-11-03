"""Rule validation tasks for the backend rules in `project-rules.draft.md`.

Convention
----------
Each test is a *real task* a developer would perform while following one rule.

- `test_ok_*`    : must PASS. Proves the rule's guidance is satisfiable today.
- `test_defect_*`: marked `xfail(strict=True)`. The body encodes the behaviour the
  rule demands. It FAILS today, which is what proves the rule is grounded in a
  real defect. When the defect is fixed the marker turns into XPASS and, because
  `strict=True`, the run goes red -- the signal to delete the marker and keep the
  test as a regression guard.

A fully green run therefore means: every rule covered here was proven against
live behaviour.

Run from the repo root:
    python -m pytest .agents/rules/_validation/test_rules_validation.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.routes import build_metrics_facets, generate_mock_movements  # noqa: E402

client = TestClient(app)


def xfail(rule: str, reason: str):
    """Reproduce-a-defect marker. XPASS fails the run, so fixes are not silent."""
    return pytest.mark.xfail(strict=True, reason=f"{rule}: {reason}")


# =====================================================================
# R22 -- rejection paths and value-level outcomes
# =====================================================================

def test_ok_r22_invalid_operation_type_is_rejected():
    """`Literal` already rejects bad input; adding this test is cheap and real."""
    assert client.get("/api/metrics", params={"operation_type": "nonsense"}).status_code == 422


def test_ok_r22_invalid_business_type_is_rejected():
    assert client.get("/api/metrics/summary", params={"business_type": "nonsense"}).status_code == 422


def test_ok_r22_numeric_upper_bound_is_enforced():
    """C2 claims limit is ge=1 le=20; prove the ceiling actually rejects."""
    assert client.get("/api/metrics/categories/top", params={"limit": 21}).status_code == 422


def test_ok_r22_alerts_values_are_numeric_and_ordered():
    """Value-level assertions on alerts. The shipped
    `test_metrics_alerts_returns_anomaly_candidates` asserts `set(first.keys())`
    on `payload[0]` only, behind an `if payload:` guard -- so an empty list, a
    wrong `outcome_total`, or a wrong `increase_ratio` all pass.

    Alert payload fields (verified): period, outcome_total, baseline_average,
    increase_ratio.

    `increase_ratio` is a fractional deviation, (outcome - baseline) / baseline,
    NOT a multiplier: 0.5917 means +59.17%. Asserting `> 1` here is the exact
    mistake a reader makes from the name alone, which is what R18 warns about.
    """
    threshold = 0
    payload = client.get("/api/metrics/alerts", params={"threshold": threshold}).json()
    assert payload, "expected at least one alert so the assertions below are exercised"
    for alert in payload:
        assert isinstance(alert["outcome_total"], (int, float))
        assert isinstance(alert["baseline_average"], (int, float))
        assert isinstance(alert["increase_ratio"], (int, float))
        # Alerts are raised only on positive deviations above the threshold.
        assert alert["increase_ratio"] > threshold, alert
        assert alert["outcome_total"] > alert["baseline_average"], alert
        # Recompose the ratio from the reported values to prove the field order
        # of magnitude is consistent with its definition.
        recomposed = (alert["outcome_total"] - alert["baseline_average"]) / alert["baseline_average"]
        assert abs(recomposed - alert["increase_ratio"]) < 0.01, (recomposed, alert)


# =====================================================================
# R3 -- filter parameters must be uniform across endpoints feeding one view
# =====================================================================

@xfail("R3", "/api/metrics silently ignores an undeclared business_type instead of filtering")
def test_defect_r3_metrics_honours_business_type_filter():
    """The dashboard-wide B2B/B2C filter must narrow /api/metrics too.

    Today FastAPI ignores undeclared query parameters, so the call returns 200
    with the full unfiltered population -- worse than a 422, because a caller
    cannot tell the filter was dropped.
    """
    unfiltered = client.get("/api/metrics").json()
    filtered = client.get("/api/metrics", params={"business_type": "B2B"}).json()
    assert len(filtered) < len(unfiltered), "filter was ignored"
    assert {m["business_type"] for m in filtered} == {"B2B"}


@xfail("R3", "an unrecognised business_type on /api/metrics returns 200 instead of 422")
def test_defect_r3_metrics_rejects_unknown_business_type():
    """A typo must not silently return the whole population."""
    assert client.get("/api/metrics", params={"business_type": "nonsense"}).status_code == 422


# =====================================================================
# R19 -- same filter, same shape
# =====================================================================

def test_ok_r19_b2b_and_b2c_paths_stay_filtered():
    """Pins the split: path segments and query parameter both live, on different
    vocabularies. /api/metrics/b2b -> 203 rows, /api/metrics/b2c -> 157 rows.
    Two shapes exist for one concept; this catches a unification that breaks one.
    """
    assert len(client.get("/api/metrics/b2b").json()) == 203
    assert len(client.get("/api/metrics/b2c").json()) == 157


@xfail("R19", "business_type is UPPERCASE-only on query params but lowercase in the path segments")
def test_defect_r19_query_param_accepts_the_same_case_as_the_path_segment():
    """`BusinessType = Literal["B2B", "B2C"]` is uppercase, so the lowercase spelling
    used by `/api/metrics/b2b` is a 422 on `/api/metrics/summary`. A single
    client-side filter round-trips through two incompatible spellings.
    """
    assert client.get("/api/metrics/summary", params={"business_type": "b2b"}).status_code == 200


# =====================================================================
# R7 -- empty-input semantics
# =====================================================================

@xfail("R7", "build_metrics_facets([]) raises IndexError on ordered[0] / ordered[-1]")
def test_defect_r7_build_metrics_facets_handles_empty_list():
    """An empty movement list must yield empty facets, not crash.

    routes.py:156 indexes ordered[0] and ordered[-1] without a guard.
    """
    facets = build_metrics_facets([])
    assert facets is not None


# =====================================================================
# R1 / R12 -- generated range must match the range the caller claims
# =====================================================================

@xfail("R1", "the generator produces a rolling 12-month window spanning two calendar years")
def test_defect_r1_generated_range_matches_a_single_calendar_year():
    """`App.tsx` labels the dashboard "2024 - Full Year" while the generator
    emits a rolling window ending today."""
    movements = generate_mock_movements(seed=42)
    years = {m.create_date.year for m in movements}
    assert len(years) == 1, f"expected one calendar year, got {sorted(years)}"


def test_ok_r12_generator_spans_two_calendar_years():
    """Pins the fact R1 depends on, using the assertion the shipped test omits.

    `test_generate_mock_movements_returns_full_year_sorted_data` asserts only
    len == 360 and sorted order, so this two-year span passes unnoticed.
    """
    movements = generate_mock_movements(seed=42)
    years = sorted({m.create_date.year for m in movements})
    assert len(years) == 2, years
    months = sorted({m.create_date.strftime("%Y-%m") for m in movements})
    assert len(months) == 12, months


# =====================================================================
# R6 -- no global mutable state
# =====================================================================

@xfail("R6", "generate_mock_movements() reseeds the process-wide random module")
def test_defect_r6_generator_does_not_reseed_global_random():
    """Calling the generator must not perturb another caller's random stream.

    The probe (val_counts.py) showed the undisturbed draws [917, 893, 581]
    becoming [108, 326, 247] after one request.
    """
    import random

    random.seed(1234)
    undisturbed = [random.randint(1, 1000) for _ in range(3)]

    random.seed(1234)
    generate_mock_movements()
    after_call = [random.randint(1, 1000) for _ in range(3)]

    assert after_call == undisturbed


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-q", "--tb=line"]))
