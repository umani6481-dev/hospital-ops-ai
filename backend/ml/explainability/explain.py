"""
Lightweight explainability layer.

For tree-based models we surface built-in feature_importances_ combined with
the actual feature values for this specific prediction, to produce a
human-readable "why" for each prediction (SHAP is used where available/
affordable; this module provides a fast, always-available fallback that is
used by the prediction API so every response includes reasoning, never a
bare number).
"""
from typing import Any

FRIENDLY_NAMES = {
    "prev_day_demand": "Previous day's patient volume",
    "prev_week_demand": "Same day last week's volume",
    "ma_7": "7-day average demand",
    "ma_14": "14-day average demand",
    "capacity": "Department capacity",
    "doctors_available": "Doctors available",
    "had_event_flag": "Active hospital event",
    "is_monday": "Monday surge pattern",
    "is_weekend": "Weekend dip pattern",
    "expected_patients": "Expected patient volume",
    "occupancy_ratio": "Current occupancy ratio",
    "day_of_week": "Day of week",
    "month": "Month / seasonality",
    "lead_time_days": "Appointment lead time",
    "previous_cancellations": "Previous cancellations",
}


def friendly(name: str) -> str:
    if name in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[name]
    if name.startswith("dept_"):
        return f"Department: {name.replace('dept_', '')}"
    return name.replace("_", " ").title()


def explain_prediction(model: Any, feature_row: dict, feature_cols: list[str], top_n: int = 4) -> list[dict]:
    """Return top contributing factors for a single prediction row.

    Combines global feature importance (how much the model relies on a
    feature overall) with the feature's actual value for this row, to flag
    which factors were meaningfully "active" for this specific prediction —
    a fast approximation used in place of full SHAP for interactive latency.
    """
    importances = getattr(model, "feature_importances_", None)
    if importances is None and hasattr(model, "coef_"):
        importances = abs(model.coef_[0]) if model.coef_.ndim > 1 else abs(model.coef_)
    if importances is None:
        return []

    scored = []
    for name, imp in zip(feature_cols, importances):
        value = feature_row.get(name, 0)
        # weight importance by whether the feature is "active"/elevated for this row
        activity = 1.0
        if name.startswith("dept_") or name in ("had_event_flag", "is_monday", "is_weekend"):
            activity = 1.5 if value else 0.2
        scored.append({
            "feature": friendly(name),
            "importance": round(float(imp), 4),
            "value": value,
            "weighted_score": float(imp) * activity,
        })

    scored.sort(key=lambda x: x["weighted_score"], reverse=True)
    top = scored[:top_n]
    return [{"factor": s["feature"], "importance": s["importance"], "value": s["value"]} for s in top]
