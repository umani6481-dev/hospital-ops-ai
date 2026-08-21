import pandas as pd

from ml.features.build_features import add_lag_features, overload_label


def test_overload_label_thresholds():
    assert overload_label(0.5) == "normal"
    assert overload_label(0.75) == "moderate"
    assert overload_label(0.95) == "high"
    assert overload_label(1.2) == "critical"


def test_add_lag_features_produces_expected_columns():
    df = pd.DataFrame({
        "department": ["Emergency"] * 10,
        "date": pd.date_range("2026-01-01", periods=10, freq="D"),
        "day_of_week": [d.weekday() for d in pd.date_range("2026-01-01", periods=10, freq="D")],
        "month": 1,
        "expected_patients": list(range(50, 60)),
        "capacity": 100,
        "occupancy_ratio": [0.5] * 10,
        "avg_waiting_time": [20.0] * 10,
        "doctors_available": 5,
        "had_event": [0] * 10,
        "event_severity": ["none"] * 10,
    })
    result = add_lag_features(df)
    assert "prev_day_demand" in result.columns
    assert "ma_7" in result.columns
    # first 7 rows dropped due to prev_week_demand requiring 7-day lag
    assert len(result) == 3
