"""Feature engineering shared across ML models."""
import pandas as pd
import numpy as np


def load_daily_stats(path: str = "ml/data/raw/daily_department_stats.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values(["department", "date"]).reset_index(drop=True)
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["prev_day_demand"] = df.groupby("department")["expected_patients"].shift(1)
    df["prev_week_demand"] = df.groupby("department")["expected_patients"].shift(7)
    df["ma_7"] = df.groupby("department")["expected_patients"].transform(
        lambda s: s.shift(1).rolling(7, min_periods=1).mean()
    )
    df["ma_14"] = df.groupby("department")["expected_patients"].transform(
        lambda s: s.shift(1).rolling(14, min_periods=1).mean()
    )
    df["is_monday"] = (df["day_of_week"] == 0).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["had_event_flag"] = df["had_event"].fillna(0).astype(int)
    df = df.dropna(subset=["prev_day_demand", "prev_week_demand"])
    return df


DEMAND_FEATURES = [
    "day_of_week", "month", "is_monday", "is_weekend",
    "prev_day_demand", "prev_week_demand", "ma_7", "ma_14",
    "capacity", "doctors_available", "had_event_flag",
]

OVERLOAD_FEATURES = [
    "day_of_week", "month", "is_monday", "is_weekend",
    "expected_patients", "capacity", "doctors_available", "had_event_flag",
]

WAITING_TIME_FEATURES = [
    "day_of_week", "month", "expected_patients", "capacity",
    "occupancy_ratio", "doctors_available", "had_event_flag",
]


def overload_label(occupancy_ratio: float) -> str:
    if occupancy_ratio < 0.7:
        return "normal"
    if occupancy_ratio < 0.9:
        return "moderate"
    if occupancy_ratio < 1.1:
        return "high"
    return "critical"
