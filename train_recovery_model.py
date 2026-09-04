import json
import os

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# RecoverAI - Recovery Prediction Model
# ============================================================

DATA_PATH = "data/payment_transactions.csv"

MODEL_DIR = "models"
MODEL_PATH = os.path.join(
    MODEL_DIR,
    "recovery_model.pkl"
)

METRICS_PATH = os.path.join(
    MODEL_DIR,
    "model_metrics.json"
)


# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

print("=" * 70)
print("RecoverAI - Recovery Prediction Model")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(
    f"\nLoaded {len(df):,} transactions."
)


# ------------------------------------------------------------
# 2. Define features and target
# ------------------------------------------------------------

FEATURES = [
    "amount",
    "payment_method",
    "failure_reason",
    "retry_count",
    "previous_payment_count",
    "previous_success_count",
    "customer_success_rate",
    "days_since_last_payment",
    "customer_lifetime_value"
]

TARGET = "recovered"


X = df[FEATURES]

y = df[TARGET]


print("\nFeatures:")
for feature in FEATURES:
    print(f" - {feature}")

print(
    f"\nTarget: {TARGET}"
)


# ------------------------------------------------------------
# 3. Train/test split
# ------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print(
    f"\nTraining records: {len(X_train):,}"
)

print(
    f"Test records: {len(X_test):,}"
)


# ------------------------------------------------------------
# 4. Identify feature types
# ------------------------------------------------------------

categorical_features = [
    "payment_method",
    "failure_reason"
]

numeric_features = [
    "amount",
    "retry_count",
    "previous_payment_count",
    "previous_success_count",
    "customer_success_rate",
    "days_since_last_payment",
    "customer_lifetime_value"
]


# ------------------------------------------------------------
# 5. Preprocessing
# ------------------------------------------------------------

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            )
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            )
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    ]
)


# ------------------------------------------------------------
# 6. ML model
# ------------------------------------------------------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


# ------------------------------------------------------------
# 7. Complete ML pipeline
# ------------------------------------------------------------

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# ------------------------------------------------------------
# 8. Train
# ------------------------------------------------------------

print("\nTraining model...")

pipeline.fit(
    X_train,
    y_train
)

print("Training completed.")


# ------------------------------------------------------------
# 9. Predictions
# ------------------------------------------------------------

y_pred = pipeline.predict(
    X_test
)

y_probability = pipeline.predict_proba(
    X_test
)[:, 1]


# ------------------------------------------------------------
# 10. Evaluation
# ------------------------------------------------------------

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred
)

recall = recall_score(
    y_test,
    y_pred
)

f1 = f1_score(
    y_test,
    y_pred
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

confusion = confusion_matrix(
    y_test,
    y_pred
)


print("\n" + "=" * 70)
print("MODEL PERFORMANCE")
print("=" * 70)

print(
    f"\nAccuracy : {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall   : {recall:.4f}"
)

print(
    f"F1 Score : {f1:.4f}"
)

print(
    f"ROC-AUC  : {roc_auc:.4f}"
)


print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred
    )
)


print("\nConfusion Matrix:")

print(confusion)


# ------------------------------------------------------------
# 11. Feature importance
# ------------------------------------------------------------

feature_names = (
    pipeline
    .named_steps["preprocessor"]
    .get_feature_names_out()
)

importances = (
    pipeline
    .named_steps["model"]
    .feature_importances_
)

feature_importance = (
    pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    })
    .sort_values(
        "importance",
        ascending=False
    )
)


print("\nTop Feature Importance:")

print(
    feature_importance
    .head(15)
    .to_string(index=False)
)


# ------------------------------------------------------------
# 12. Save model
# ------------------------------------------------------------

joblib.dump(
    pipeline,
    MODEL_PATH
)


# ------------------------------------------------------------
# 13. Save metrics
# ------------------------------------------------------------

metrics = {
    "accuracy": round(
        accuracy,
        4
    ),
    "precision": round(
        precision,
        4
    ),
    "recall": round(
        recall,
        4
    ),
    "f1_score": round(
        f1,
        4
    ),
    "roc_auc": round(
        roc_auc,
        4
    ),
    "training_samples": len(X_train),
    "test_samples": len(X_test)
}


with open(
    METRICS_PATH,
    "w"
) as file:

    json.dump(
        metrics,
        file,
        indent=4
    )


print("\n" + "=" * 70)

print(
    f"Model saved to: {MODEL_PATH}"
)

print(
    f"Metrics saved to: {METRICS_PATH}"
)

print("=" * 70)