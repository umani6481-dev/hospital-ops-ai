"""
Prediction service: loads serialized models once (singleton) and exposes
predict_* functions consumed by the FastAPI /api/predictions endpoints.

Models are NEVER trained inside a request — only loaded from disk artifacts
produced by ml/training/*.py. If artifacts are missing, callers get a clear
error telling them to run the training pipeline first.
"""
import json
import os
from datetime import datetime, timedelta
from functools import lru_cache

import joblib
import pandas as pd

from ml.explainability.explain import explain_prediction
from ml.features.build_features import overload_label

ARTIFACT_DIR = os.getenv("MODEL_PATH", "ml/models/artifacts")


class ModelNotTrainedError(Exception):
    pass


def _load(name: str):
    path = os.path.join(ARTIFACT_DIR, f"{name}.joblib")
    if not os.path.exists(path):
        raise ModelNotTrainedError(
            f"Model '{name}' is not trained yet. Run: python -m ml.training.train_{name.replace('_model', '')}_model"
        )
    return joblib.load(path)


@lru_cache(maxsize=None)
def get_demand_model():
    return _load("demand_model")


@lru_cache(maxsize=None)
def get_overload_model():
    return _load("overload_model")


@lru_cache(maxsize=None)
def get_waiting_time_model():
    return _load("waiting_time_model")


@lru_cache(maxsize=None)
def get_bed_model():
    return _load("bed_model")


@lru_cache(maxsize=None)
def get_noshow_model():
    return _load("noshow_model")


def _build_feature_row(dept_name: str, dept_cols: list, base: dict) -> dict:
    row = {c: 0 for c in dept_cols}
    key = f"dept_{dept_name}"
    if key in row:
        row[key] = 1
    row.update(base)
    return row


def predict_demand(department_name: str, capacity: int, doctors_available: int,
                    prev_day_demand: float, prev_week_demand: float, ma_7: float, ma_14: float,
                    target_date: datetime | None = None, had_event: bool = False) -> dict:
    bundle = get_demand_model()
    model, feature_cols, dept_cols = bundle["model"], bundle["features"], bundle["dept_columns"]
    target_date = target_date or (datetime.utcnow() + timedelta(days=1))

    base = {
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "is_monday": 1 if target_date.weekday() == 0 else 0,
        "is_weekend": 1 if target_date.weekday() >= 5 else 0,
        "prev_day_demand": prev_day_demand,
        "prev_week_demand": prev_week_demand,
        "ma_7": ma_7,
        "ma_14": ma_14,
        "capacity": capacity,
        "doctors_available": doctors_available,
        "had_event_flag": int(had_event),
    }
    row = _build_feature_row(department_name, dept_cols, base)
    X = pd.DataFrame([row])[feature_cols]
    pred = float(model.predict(X)[0])
    explanation = explain_prediction(model, row, feature_cols)
    ci_low, ci_high = round(pred * 0.92), round(pred * 1.08)
    return {
        "department": department_name,
        "target_date": target_date.date().isoformat(),
        "predicted_patients": round(pred),
        "confidence_interval": {"low": ci_low, "high": ci_high},
        "explanation": explanation,
    }


def predict_overload(department_name: str, expected_patients: int, capacity: int, doctors_available: int,
                      target_date: datetime | None = None, had_event: bool = False) -> dict:
    bundle = get_overload_model()
    model, feature_cols, dept_cols, labels = bundle["model"], bundle["features"], bundle["dept_columns"], bundle["labels"]
    target_date = target_date or (datetime.utcnow() + timedelta(days=1))

    base = {
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "is_monday": 1 if target_date.weekday() == 0 else 0,
        "is_weekend": 1 if target_date.weekday() >= 5 else 0,
        "expected_patients": expected_patients,
        "capacity": capacity,
        "doctors_available": doctors_available,
        "had_event_flag": int(had_event),
    }
    row = _build_feature_row(department_name, dept_cols, base)
    X = pd.DataFrame([row])[feature_cols]
    pred_code = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    confidence = float(max(proba))
    explanation = explain_prediction(model, row, feature_cols)
    return {
        "department": department_name,
        "target_date": target_date.date().isoformat(),
        "risk_level": labels[pred_code],
        "overload_probability": round(confidence * 100, 1),
        "expected_patients": expected_patients,
        "capacity": capacity,
        "explanation": explanation,
    }


def predict_waiting_time(department_name: str, expected_patients: int, capacity: int, occupancy_ratio: float,
                          doctors_available: int, target_date: datetime | None = None,
                          had_event: bool = False) -> dict:
    bundle = get_waiting_time_model()
    model, feature_cols, dept_cols = bundle["model"], bundle["features"], bundle["dept_columns"]
    target_date = target_date or datetime.utcnow()

    base = {
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "expected_patients": expected_patients,
        "capacity": capacity,
        "occupancy_ratio": occupancy_ratio,
        "doctors_available": doctors_available,
        "had_event_flag": int(had_event),
    }
    row = _build_feature_row(department_name, dept_cols, base)
    X = pd.DataFrame([row])[feature_cols]
    pred = float(model.predict(X)[0])

    row_2h = dict(row)
    row_2h["occupancy_ratio"] = min(1.5, occupancy_ratio * 1.08)
    X2 = pd.DataFrame([row_2h])[feature_cols]
    pred_2h = float(model.predict(X2)[0])

    explanation = explain_prediction(model, row, feature_cols)
    risk = "low"
    if pred > 60:
        risk = "critical"
    elif pred > 40:
        risk = "high"
    elif pred > 25:
        risk = "medium"
    return {
        "department": department_name,
        "current_waiting_time_minutes": round(pred, 1),
        "predicted_in_2_hours_minutes": round(pred_2h, 1),
        "risk": risk,
        "explanation": explanation,
    }


def predict_bed_availability(department_name: str, total_beds: int, capacity: int,
                              prev_day_demand: float, prev_week_demand: float, ma_7: float, ma_14: float,
                              target_date: datetime | None = None, had_event: bool = False) -> dict:
    bundle = get_bed_model()
    model, feature_cols, dept_cols = bundle["model"], bundle["features"], bundle["dept_columns"]
    target_date = target_date or (datetime.utcnow() + timedelta(days=1))

    base = {
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "is_monday": 1 if target_date.weekday() == 0 else 0,
        "is_weekend": 1 if target_date.weekday() >= 5 else 0,
        "prev_day_demand": prev_day_demand,
        "prev_week_demand": prev_week_demand,
        "ma_7": ma_7,
        "ma_14": ma_14,
        "capacity": capacity,
        "had_event_flag": int(had_event),
    }
    row = _build_feature_row(department_name, dept_cols, base)
    X = pd.DataFrame([row])[feature_cols]
    predicted_occupancy_ratio = float(model.predict(X)[0])
    predicted_occupied = min(total_beds, round(predicted_occupancy_ratio * total_beds))
    predicted_available = max(0, total_beds - predicted_occupied)
    explanation = explain_prediction(model, row, feature_cols)
    risk = overload_label(predicted_occupancy_ratio)
    return {
        "department": department_name,
        "target_date": target_date.date().isoformat(),
        "total_beds": total_beds,
        "predicted_occupied_beds": predicted_occupied,
        "predicted_available_beds": predicted_available,
        "predicted_occupancy_ratio": round(predicted_occupancy_ratio, 3),
        "risk": risk,
        "explanation": explanation,
    }


def predict_no_show(lead_time_days: int, day_of_week: int, previous_cancellations: int,
                     department_name: str, appointment_type: str, age_group: str) -> dict:
    bundle = get_noshow_model()
    model, feature_cols = bundle["model"], bundle["features"]
    row = {c: 0 for c in feature_cols}
    row["lead_time_days"] = lead_time_days
    row["day_of_week"] = day_of_week
    row["previous_cancellations"] = previous_cancellations
    for key, val in (("dept_", department_name), ("type_", appointment_type), ("age_", age_group)):
        col = f"{key}{val}"
        if col in row:
            row[col] = 1
    X = pd.DataFrame([row])[feature_cols]
    proba = float(model.predict_proba(X)[0][1])
    explanation = explain_prediction(model, row, feature_cols)
    return {
        "no_show_probability": round(proba * 100, 1),
        "risk": "high" if proba > 0.5 else ("medium" if proba > 0.25 else "low"),
        "explanation": explanation,
    }


def load_model_metadata(model_file_prefix: str) -> dict:
    path = os.path.join(ARTIFACT_DIR, f"{model_file_prefix}.meta.json")
    if not os.path.exists(path):
        raise ModelNotTrainedError(f"No metadata found for {model_file_prefix}")
    with open(path) as f:
        return json.load(f)
