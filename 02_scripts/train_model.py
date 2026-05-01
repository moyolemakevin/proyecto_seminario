from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.class_weight import compute_sample_weight


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "01_datos_procesados" / "master_dataset.parquet"
MODEL_DIR = ROOT / "04_resultados"
MODEL_PATH = MODEL_DIR / "delay_model.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"
IMPORTANCE_PATH = MODEL_DIR / "feature_importance.csv"


CATEGORICAL_FEATURES = [
    "seller_state",
    "customer_state",
    "product_category_name_english",
    "payment_type",
]
NUMERIC_FEATURES = [
    "distancia_aprox",
    "total_price",
    "avg_price",
    "total_freight",
    "avg_freight",
    "item_count",
    "payment_installments",
    "payment_value",
    "payment_count",
    "approval_time_hours",
    "purchase_month",
    "purchase_dayofweek",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "entrego_tarde"


def make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def evaluate(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    return {
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }


def get_feature_importance(model: Pipeline) -> pd.DataFrame:
    preprocessor = model.named_steps["preprocessor"]
    estimator = model.named_steps["model"]
    names = preprocessor.get_feature_names_out()
    importances = getattr(estimator, "feature_importances_", None)
    if importances is None:
        return pd.DataFrame(columns=["feature", "importance"])
    return (
        pd.DataFrame({"feature": names, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATA_PATH)
    model_df = df[FEATURES + [TARGET]].copy()
    model_df[CATEGORICAL_FEATURES] = model_df[CATEGORICAL_FEATURES].fillna("unknown")
    model_df[NUMERIC_FEATURES] = model_df[NUMERIC_FEATURES].fillna(
        model_df[NUMERIC_FEATURES].median(numeric_only=True)
    )

    X = model_df[FEATURES]
    y = model_df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", make_encoder(), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )

    candidates = {
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=80,
                        max_depth=10,
                        min_samples_leaf=20,
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=80,
                        learning_rate=0.07,
                        max_depth=3,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }

    metrics = {
        "target_balance": {
            "late_rate": float(y.mean()),
            "on_time_rate": float(1 - y.mean()),
            "late_count": int(y.sum()),
            "on_time_count": int((1 - y).sum()),
        },
        "models": {},
    }

    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    fitted = {}
    for name, pipeline in candidates.items():
        if name == "gradient_boosting":
            pipeline.fit(X_train, y_train, model__sample_weight=sample_weight)
        else:
            pipeline.fit(X_train, y_train)
        fitted[name] = pipeline
        metrics["models"][name] = evaluate(pipeline, X_test, y_test)

    best_name = max(metrics["models"], key=lambda key: metrics["models"][key]["f1"])
    best_model = fitted[best_name]
    metrics["best_model"] = best_name

    baseline_values = {}
    for feature in CATEGORICAL_FEATURES:
        baseline_values[feature] = X[feature].mode().iat[0]
    for feature in NUMERIC_FEATURES:
        baseline_values[feature] = float(X[feature].median())

    route_distance = (
        df.groupby(["seller_state", "customer_state"])["distancia_aprox"]
        .median()
        .dropna()
        .to_dict()
    )
    category_risk = (
        df.groupby("product_category_name_english")[TARGET]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    bundle = {
        "model": best_model,
        "features": FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "baseline_values": baseline_values,
        "route_distance": route_distance,
        "best_model": best_name,
    }
    joblib.dump(bundle, MODEL_PATH)

    with METRICS_PATH.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    get_feature_importance(best_model).head(30).to_csv(IMPORTANCE_PATH, index=False)
    category_risk.to_csv(MODEL_DIR / "category_risk.csv", index=False)

    print(f"Modelo guardado: {MODEL_PATH}")
    print(f"Mejor modelo: {best_name}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
