"""
Model 4 — Bed Availability Forecasting
Predicts expected occupancy ratio (and thus available beds) for
tomorrow / next 24h per department based on historical admission patterns.

Run: python -m ml.training.train_bed_model
"""
import json
import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from ml.features.build_features import load_daily_stats, add_lag_features
from ml.training.train_demand_model import time_aware_split, evaluate

ARTIFACT_DIR = "ml/models/artifacts"

BED_FEATURES = [
    "day_of_week", "month", "is_monday", "is_weekend",
    "prev_day_demand", "prev_week_demand", "ma_7", "ma_14",
    "capacity", "had_event_flag",
]


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = add_lag_features(load_daily_stats())
    df_encoded = pd.get_dummies(df, columns=["department"], prefix="dept")
    dept_cols = [c for c in df_encoded.columns if c.startswith("dept_")]
    feature_cols = BED_FEATURES + dept_cols

    train, val, test = time_aware_split(df_encoded)
    X_train, y_train = train[feature_cols], train["occupancy_ratio"]
    X_test, y_test = test[feature_cols], test["occupancy_ratio"]

    candidates = {
        "RandomForest": RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=250, max_depth=4, learning_rate=0.05, random_state=42),
    }

    results = {}
    best_name, best_model, best_mae = None, None, float("inf")
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metrics = evaluate(y_test.values, preds)
        results[name] = metrics
        print(f"{name}: {metrics}")
        if metrics["MAE"] < best_mae:
            best_mae = metrics["MAE"]
            best_name, best_model = name, model

    print(f"\nSelected best model: {best_name}")

    model_path = os.path.join(ARTIFACT_DIR, "bed_model.joblib")
    joblib.dump({"model": best_model, "features": feature_cols, "dept_columns": dept_cols}, model_path)

    metadata = {
        "model_name": "bed_availability",
        "algorithm": best_name,
        "version": f"v{int(datetime.utcnow().timestamp())}",
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_list": feature_cols,
        "dataset_version": "synthetic_v1",
    }
    with open(os.path.join(ARTIFACT_DIR, "bed_model.meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
