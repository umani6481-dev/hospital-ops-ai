"""
Model 3 — Emergency / Department Waiting Time Prediction

Run: python -m ml.training.train_waiting_time_model
"""
import json
import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor

from ml.features.build_features import load_daily_stats, add_lag_features, WAITING_TIME_FEATURES
from ml.training.train_demand_model import time_aware_split, evaluate

ARTIFACT_DIR = "ml/models/artifacts"


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = add_lag_features(load_daily_stats())
    df_encoded = pd.get_dummies(df, columns=["department"], prefix="dept")
    dept_cols = [c for c in df_encoded.columns if c.startswith("dept_")]
    feature_cols = WAITING_TIME_FEATURES + dept_cols

    train, val, test = time_aware_split(df_encoded)
    X_train, y_train = train[feature_cols], train["avg_waiting_time"]
    X_test, y_test = test[feature_cols], test["avg_waiting_time"]

    candidates = {
        "GradientBoosting": GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42),
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

    model_path = os.path.join(ARTIFACT_DIR, "waiting_time_model.joblib")
    joblib.dump({"model": best_model, "features": feature_cols, "dept_columns": dept_cols}, model_path)

    metadata = {
        "model_name": "waiting_time_prediction",
        "algorithm": best_name,
        "version": f"v{int(datetime.utcnow().timestamp())}",
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_list": feature_cols,
        "dataset_version": "synthetic_v1",
    }
    with open(os.path.join(ARTIFACT_DIR, "waiting_time_model.meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
