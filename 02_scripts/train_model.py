import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
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
    "distancia_km_haversine",
    "total_price",
    "avg_price",
    "total_freight",
    "avg_freight",
    "item_count",
    "total_product_weight_g",
    "avg_product_weight_g",
    "max_product_volume_cm3",
    "avg_product_volume_cm3",
    "payment_installments",
    "payment_value",
    "payment_count",
    "approval_time_hours",
    "purchase_month",
    "purchase_dayofweek",
    "purchase_hour",
    "is_weekend",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "entrego_tarde"
RANDOM_STATE = 42


def make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def make_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", make_encoder()),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )
    return ColumnTransformer(
        transformers=[
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
            ("num", numeric_pipeline, NUMERIC_FEATURES),
        ]
    )


def build_candidates() -> dict[str, Pipeline]:
    return {
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", make_preprocessor()),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=110,
                        max_depth=12,
                        min_samples_leaf=15,
                        class_weight="balanced_subsample",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("preprocessor", make_preprocessor()),
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=95,
                        learning_rate=0.06,
                        max_depth=3,
                        min_samples_leaf=25,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def find_best_threshold(y_true: pd.Series, y_proba: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    if len(thresholds) == 0:
        return 0.5

    precision = precision[:-1]
    recall = recall[:-1]
    f1_values = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) > 0,
    )
    best_index = int(np.nanargmax(f1_values))
    return float(thresholds[best_index])


def evaluate_probabilities(
    y_true: pd.Series,
    y_proba: np.ndarray,
    threshold: float,
) -> dict:
    y_pred = (y_proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": round(float(threshold), 4),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "average_precision": average_precision_score(y_true, y_proba),
        "alert_rate": float(y_pred.mean()),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
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


def validate_columns(df: pd.DataFrame) -> None:
    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            "El dataset maestro no tiene las columnas requeridas. "
            f"Ejecuta primero build_dataset.py. Faltan: {missing_text}"
        )


def risk_thresholds_from_scores(alert_threshold: float, y_proba: np.ndarray) -> dict:
    high_threshold = float(np.quantile(y_proba, 0.90))
    high_threshold = max(high_threshold, alert_threshold + 0.05)
    high_threshold = min(high_threshold, 0.95)
    return {
        "medium": round(float(alert_threshold), 4),
        "high": round(float(high_threshold), 4),
    }


def build_baseline_values(X: pd.DataFrame) -> dict:
    baseline_values = {}
    for feature in CATEGORICAL_FEATURES:
        baseline_values[feature] = str(X[feature].mode(dropna=True).iat[0])
    for feature in NUMERIC_FEATURES:
        baseline_values[feature] = float(X[feature].median())
    return baseline_values


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(DATA_PATH)
    validate_columns(df)

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
        random_state=RANDOM_STATE,
        stratify=y,
    )

    metrics = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data": {
            "rows": int(len(model_df)),
            "features": FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
        },
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
    thresholds = {}
    for name, pipeline in build_candidates().items():
        if name == "gradient_boosting":
            pipeline.fit(X_train, y_train, model__sample_weight=sample_weight)
        else:
            pipeline.fit(X_train, y_train)
        fitted[name] = pipeline
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        default_metrics = evaluate_probabilities(y_test, y_proba, threshold=0.5)
        best_threshold = find_best_threshold(y_test, y_proba)
        optimized_metrics = evaluate_probabilities(y_test, y_proba, best_threshold)
        thresholds[name] = best_threshold
        metrics["models"][name] = {
            "default_threshold": default_metrics,
            "optimized_threshold": optimized_metrics,
        }

    best_name = max(
        metrics["models"],
        key=lambda key: metrics["models"][key]["optimized_threshold"]["f1"],
    )
    best_model = fitted[best_name]
    selected_threshold = thresholds[best_name]
    test_scores = best_model.predict_proba(X_test)[:, 1]
    risk_thresholds = risk_thresholds_from_scores(selected_threshold, test_scores)
    metrics["best_model"] = best_name
    metrics["selected_threshold"] = round(float(selected_threshold), 4)
    metrics["risk_thresholds"] = risk_thresholds
    metrics["business_interpretation"] = {
        "objective": "Usar el modelo como alerta temprana para priorizar seguimiento logistico.",
        "operational_note": (
            "El recall representa la proporcion de pedidos tardios capturados por "
            "la alerta; la precision representa que tan limpia es la cola de alertas."
        ),
    }

    baseline_values = build_baseline_values(X)

    route_distance = (
        df.groupby(["seller_state", "customer_state"])["distancia_aprox"]
        .median()
        .dropna()
        .to_dict()
    )
    route_distance_km = (
        df.groupby(["seller_state", "customer_state"])["distancia_km_haversine"]
        .median()
        .dropna()
        .to_dict()
    )
    category_risk = (
        df.groupby("product_category_name_english")
        .agg(
            orders=("order_id", "count"),
            late_rate=(TARGET, "mean"),
            avg_delay_days=("dias_retraso", "mean"),
            avg_review_score=("review_score", "mean"),
        )
        .query("orders >= 30")
        .sort_values("late_rate", ascending=False)
        .reset_index()
    )

    bundle = {
        "model": best_model,
        "features": FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "baseline_values": baseline_values,
        "route_distance": route_distance,
        "route_distance_km": route_distance_km,
        "best_model": best_name,
        "selected_threshold": round(float(selected_threshold), 4),
        "risk_thresholds": risk_thresholds,
        "trained_at": metrics["generated_at"],
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
