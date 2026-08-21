"""
Model 2 — Department Overload Prediction
Classifies department risk as normal / moderate / high / critical.

Run: python -m ml.training.train_overload_model
"""
import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from xgboost import XGBClassifier

from ml.features.build_features import load_daily_stats, add_lag_features, OVERLOAD_FEATURES, overload_label
from ml.training.train_demand_model import time_aware_split

ARTIFACT_DIR = "ml/models/artifacts"
LABELS = ["normal", "moderate", "high", "critical"]


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = add_lag_features(load_daily_stats())
    df["risk_label"] = df["occupancy_ratio"].apply(overload_label)
    df["risk_code"] = df["risk_label"].apply(LABELS.index)

    df_encoded = pd.get_dummies(df, columns=["department"], prefix="dept")
    dept_cols = [c for c in df_encoded.columns if c.startswith("dept_")]
    feature_cols = OVERLOAD_FEATURES + dept_cols

    train, val, test = time_aware_split(df_encoded)
    X_train, y_train = train[feature_cols], train["risk_code"]
    X_test, y_test = test[feature_cols], test["risk_code"]

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=250, max_depth=4, learning_rate=0.08, random_state=42,
                                  eval_metric="mlogloss"),
    }

    results = {}
    best_name, best_model, best_f1 = None, None, -1
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="macro")
        results[name] = {"accuracy": round(float(acc), 3), "f1_macro": round(float(f1), 3)}
        print(f"{name}: {results[name]}")
        if f1 > best_f1:
            best_f1 = f1
            best_name, best_model = name, model

    print(f"\nSelected best model: {best_name}")

    model_path = os.path.join(ARTIFACT_DIR, "overload_model.joblib")
    joblib.dump({"model": best_model, "features": feature_cols, "dept_columns": dept_cols, "labels": LABELS}, model_path)

    metadata = {
        "model_name": "overload_prediction",
        "algorithm": best_name,
        "version": f"v{int(datetime.utcnow().timestamp())}",
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_list": feature_cols,
        "labels": LABELS,
        "dataset_version": "synthetic_v1",
    }
    with open(os.path.join(ARTIFACT_DIR, "overload_model.meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
