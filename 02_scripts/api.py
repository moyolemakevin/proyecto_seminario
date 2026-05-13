from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from business_rules import (
    actions_for,
    code_from_state_label,
    recommendation_for,
    state_catalog,
    state_label,
    state_name,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "04_resultados" / "delay_model.pkl"
DATA_PATH = ROOT / "01_datos_procesados" / "master_dataset.parquet"

app = FastAPI(
    title="OLIST Delay Alert API",
    description=(
        "API para estimar riesgo de retraso logistico en pedidos de ecommerce "
        "con datos historicos de Olist."
    ),
    version="2.1.0",
)


def load_model_bundle() -> dict:
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"No se encontro el modelo en {MODEL_PATH}. Ejecuta train_model.py."
        )
    return joblib.load(MODEL_PATH)


def load_master_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise RuntimeError(
            f"No se encontro el dataset en {DATA_PATH}. Ejecuta build_dataset.py."
        )
    return pd.read_parquet(DATA_PATH)


bundle = load_model_bundle()
model = bundle["model"]
features = bundle["features"]
baseline_values = bundle["baseline_values"]
route_distance = bundle["route_distance"]
route_distance_km = bundle.get("route_distance_km", route_distance)
risk_thresholds = bundle.get("risk_thresholds", {"medium": 0.31, "high": 0.61})
master_df = load_master_dataset()


class DelayRiskRequest(BaseModel):
    seller_state: str = Field(..., min_length=2, max_length=40)
    customer_state: str = Field(..., min_length=2, max_length=40)
    product_category_name_english: str = Field(..., min_length=1)
    payment_type: str | None = None
    distancia_aprox: float | None = Field(default=None, ge=0)
    distancia_km_haversine: float | None = Field(default=None, ge=0)
    total_price: float | None = Field(default=None, ge=0)
    avg_price: float | None = Field(default=None, ge=0)
    total_freight: float | None = Field(default=None, ge=0)
    avg_freight: float | None = Field(default=None, ge=0)
    item_count: float | None = Field(default=None, ge=1)
    total_product_weight_g: float | None = Field(default=None, ge=0)
    avg_product_weight_g: float | None = Field(default=None, ge=0)
    max_product_volume_cm3: float | None = Field(default=None, ge=0)
    avg_product_volume_cm3: float | None = Field(default=None, ge=0)
    payment_installments: float | None = Field(default=None, ge=0)
    payment_value: float | None = Field(default=None, ge=0)
    payment_count: float | None = Field(default=None, ge=0)
    approval_time_hours: float | None = Field(default=None, ge=0)
    purchase_month: int | None = Field(default=None, ge=1, le=12)
    purchase_dayofweek: int | None = Field(default=None, ge=0, le=6)
    purchase_hour: int | None = Field(default=None, ge=0, le=23)
    is_weekend: int | None = Field(default=None, ge=0, le=1)


class DelayRiskResponse(BaseModel):
    delay_probability: float
    risk_level: str
    model: str
    model_trained_at: str | None
    threshold_used: float
    risk_thresholds: dict[str, float]
    recommendation: str
    operational_actions: list[str]
    input_summary: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    dataset_loaded: bool
    model: str
    trained_at: str | None
    rows_available: int


class CategoryRiskResponse(BaseModel):
    product_category_name_english: str
    orders: int
    late_rate: float
    avg_review_score: float


class StateCatalogResponse(BaseModel):
    code: str
    name: str
    label: str


class RouteRiskResponse(BaseModel):
    seller_state: str
    seller_state_name: str
    seller_state_label: str
    customer_state: str
    customer_state_name: str
    customer_state_label: str
    orders: int
    late_rate: float
    avg_distance_km: float
    avg_review_score: float


def payload_to_dict(payload: BaseModel) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


def normalize_payload(values: dict) -> dict:
    normalized = values.copy()
    for state_field in ["seller_state", "customer_state"]:
        if normalized.get(state_field):
            normalized[state_field] = code_from_state_label(normalized[state_field])
    if normalized.get("payment_type"):
        normalized["payment_type"] = normalized["payment_type"].strip().lower()
    if normalized.get("product_category_name_english"):
        normalized["product_category_name_english"] = normalized[
            "product_category_name_english"
        ].strip()
    return normalized


def enrich_input_summary(values: dict) -> dict:
    summary = normalize_payload(values)
    summary["seller_state_name"] = state_name(summary.get("seller_state"))
    summary["seller_state_label"] = state_label(summary.get("seller_state"))
    summary["customer_state_name"] = state_name(summary.get("customer_state"))
    summary["customer_state_label"] = state_label(summary.get("customer_state"))
    return summary


def risk_level(probability: float) -> str:
    if probability >= risk_thresholds["high"]:
        return "alto"
    if probability >= risk_thresholds["medium"]:
        return "medio"
    return "bajo"


def build_input(payload: DelayRiskRequest) -> pd.DataFrame:
    row = baseline_values.copy()
    user_values = normalize_payload(payload_to_dict(payload))
    row.update({key: value for key, value in user_values.items() if value is not None})

    if payload.distancia_aprox is None:
        key = (row["seller_state"], row["customer_state"])
        row["distancia_aprox"] = route_distance.get(
            key,
            baseline_values["distancia_aprox"],
        )
    if user_values.get("distancia_km_haversine") is None:
        key = (row["seller_state"], row["customer_state"])
        row["distancia_km_haversine"] = route_distance_km.get(
            key,
            baseline_values.get("distancia_km_haversine", row["distancia_aprox"]),
        )

    item_count = max(float(row.get("item_count", 1) or 1), 1)
    if user_values.get("total_price") is not None and user_values.get("avg_price") is None:
        row["avg_price"] = float(row["total_price"]) / item_count
    if (
        user_values.get("total_freight") is not None
        and user_values.get("avg_freight") is None
    ):
        row["avg_freight"] = float(row["total_freight"]) / item_count
    if user_values.get("payment_value") is None:
        row["payment_value"] = float(row["total_price"]) + float(row["total_freight"])

    return pd.DataFrame([row], columns=features)


@app.get("/")
def root() -> dict:
    return {
        "service": "OLIST Delay Alert API",
        "version": "2.1.0",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/catalog/states",
            "/orders/example_payload",
            "/orders/delay_risk",
            "/orders/top_risk_categories",
            "/orders/top_risk_routes",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        dataset_loaded=not master_df.empty,
        model=bundle["best_model"],
        trained_at=bundle.get("trained_at"),
        rows_available=int(len(master_df)),
    )


@app.get("/catalog/states", response_model=list[StateCatalogResponse])
def catalog_states() -> list[dict]:
    used_codes = sorted(
        set(master_df["seller_state"].dropna().unique())
        | set(master_df["customer_state"].dropna().unique())
    )
    return state_catalog(used_codes)


@app.get("/orders/example_payload")
def example_payload() -> dict:
    return {
        "seller_state": "SP",
        "customer_state": "BA",
        "product_category_name_english": "furniture_decor",
        "payment_type": "credit_card",
        "total_price": 120.0,
        "total_freight": 25.0,
        "item_count": 1,
        "payment_installments": 2,
    }


@app.post("/orders/delay_risk", response_model=DelayRiskResponse)
def delay_risk(payload: DelayRiskRequest) -> DelayRiskResponse:
    try:
        X = build_input(payload)
        probability = float(model.predict_proba(X)[0, 1])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    level = risk_level(probability)
    return DelayRiskResponse(
        delay_probability=round(probability, 4),
        risk_level=level,
        model=bundle["best_model"],
        model_trained_at=bundle.get("trained_at"),
        threshold_used=risk_thresholds["medium"],
        risk_thresholds=risk_thresholds,
        recommendation=recommendation_for(level),
        operational_actions=actions_for(level),
        input_summary=enrich_input_summary(payload_to_dict(payload)),
    )


@app.get("/orders/top_risk_categories", response_model=list[CategoryRiskResponse])
def top_risk_categories(
    limit: int = Query(10, ge=1, le=50),
    min_orders: int = Query(30, ge=1),
) -> list[dict]:
    result = (
        master_df.groupby("product_category_name_english")
        .agg(
            late_rate=("entrego_tarde", "mean"),
            orders=("order_id", "count"),
            avg_review_score=("review_score", "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values("late_rate", ascending=False)
        .head(limit)
        .reset_index()
    )
    result["late_rate"] = result["late_rate"].round(4)
    result["avg_review_score"] = result["avg_review_score"].round(2)
    return result.to_dict(orient="records")


@app.get("/orders/top_risk_routes", response_model=list[RouteRiskResponse])
def top_risk_routes(
    limit: int = Query(10, ge=1, le=50),
    min_orders: int = Query(30, ge=1),
) -> list[dict]:
    result = (
        master_df.groupby(["seller_state", "customer_state"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            avg_distance_km=("distancia_km_haversine", "mean"),
            avg_review_score=("review_score", "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values(["late_rate", "orders"], ascending=[False, False])
        .head(limit)
        .reset_index(drop=True)
    )
    result["seller_state_name"] = result["seller_state"].map(state_name)
    result["seller_state_label"] = result["seller_state"].map(state_label)
    result["customer_state_name"] = result["customer_state"].map(state_name)
    result["customer_state_label"] = result["customer_state"].map(state_label)
    result["late_rate"] = result["late_rate"].round(4)
    result["avg_distance_km"] = result["avg_distance_km"].round(0)
    result["avg_review_score"] = result["avg_review_score"].round(2)
    columns = [
        "seller_state",
        "seller_state_name",
        "seller_state_label",
        "customer_state",
        "customer_state_name",
        "customer_state_label",
        "orders",
        "late_rate",
        "avg_distance_km",
        "avg_review_score",
    ]
    return result[columns].to_dict(orient="records")
