"""
Model 1 — Patient Demand Forecasting
Trains and compares Linear Regression / Random Forest / XGBoost,
selects the best model by MAE on a time-aware holdout split, and
saves it (with metadata) to ml/models/artifacts/.

Run: python -m ml.training.train_demand_model
"""
import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from ml.features.build_features import load_daily_stats, add_lag_features, DEMAND_FEATURES

ARTIFACT_DIR = "ml/models/artifacts"


def time_aware_split(df: pd.DataFrame):
    """Train: first 75% of dates, Validation: next 12.5%, Test: last 12.5% (per department, time ordered)."""
    df = df.sort_values("date")
    dates = df["date"].unique()
    n = len(dates)
    train_end = dates[int(n * 0.75)]
    val_end = dates[int(n * 0.875)]
    train = df[df["date"] <= train_end]
    val = df[(df["date"] > train_end) & (df["date"] <= val_end)]
    test = df[df["date"] > val_end]
    return train, val, test


def evaluate(y_true, y_pred) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100)
    r2 = r2_score(y_true, y_pred) if len(set(y_true)) > 1 else 0.0
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE": round(mape, 2), "R2": round(float(r2), 3)}


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = add_lag_features(load_daily_stats())
    df_encoded = pd.get_dummies(df, columns=["department"], prefix="dept")
    dept_cols = [c for c in df_encoded.columns if c.startswith("dept_")]
    feature_cols = DEMAND_FEATURES + dept_cols

    train, val, test = time_aware_split(df_encoded)
    X_train, y_train = train[feature_cols], train["expected_patients"]
    X_test, y_test = test[feature_cols], test["expected_patients"]

    candidates = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42),
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

    version = f"v{int(datetime.utcnow().timestamp())}"
    model_path = os.path.join(ARTIFACT_DIR, "demand_model.joblib")
    joblib.dump({"model": best_model, "features": feature_cols, "dept_columns": dept_cols}, model_path)

    metadata = {
        "model_name": "demand_forecast",
        "algorithm": best_name,
        "version": version,
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_list": feature_cols,
        "dataset_version": "synthetic_v1",
    }
    with open(os.path.join(ARTIFACT_DIR, "demand_model.meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
