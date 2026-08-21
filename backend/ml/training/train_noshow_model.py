"""
Model 5 — Appointment No-Show Prediction

Run: python -m ml.training.train_noshow_model
"""
import json
import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score
from xgboost import XGBClassifier

ARTIFACT_DIR = "ml/models/artifacts"
NOSHOW_FEATURES = ["lead_time_days", "day_of_week", "previous_cancellations"]


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = pd.read_csv("ml/data/raw/appointments.csv")
    df["target"] = (df["status"] == "no_show").astype(int)
    df_encoded = pd.get_dummies(df, columns=["department", "appointment_type", "patient_age_group"], prefix=["dept", "type", "age"])
    extra_cols = [c for c in df_encoded.columns if c.startswith(("dept_", "type_", "age_"))]
    feature_cols = NOSHOW_FEATURES + extra_cols

    df_encoded = df_encoded.sort_values("appointment_date")
    split_idx = int(len(df_encoded) * 0.8)
    train, test = df_encoded.iloc[:split_idx], df_encoded.iloc[split_idx:]

    X_train, y_train = train[feature_cols], train["target"]
    X_test, y_test = test[feature_cols], test["target"]

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=250, max_depth=4, learning_rate=0.05, random_state=42,
                                  eval_metric="logloss"),
    }

    results = {}
    best_name, best_model, best_auc = None, None, -1
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        try:
            auc = roc_auc_score(y_test, proba)
        except ValueError:
            auc = 0.5
        results[name] = {"accuracy": round(float(acc), 3), "f1": round(float(f1), 3), "roc_auc": round(float(auc), 3)}
        print(f"{name}: {results[name]}")
        if auc > best_auc:
            best_auc = auc
            best_name, best_model = name, model

    print(f"\nSelected best model: {best_name}")

    model_path = os.path.join(ARTIFACT_DIR, "noshow_model.joblib")
    joblib.dump({"model": best_model, "features": feature_cols}, model_path)

    metadata = {
        "model_name": "no_show_prediction",
        "algorithm": best_name,
        "version": f"v{int(datetime.utcnow().timestamp())}",
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_list": feature_cols,
        "dataset_version": "synthetic_v1",
    }
    with open(os.path.join(ARTIFACT_DIR, "noshow_model.meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
