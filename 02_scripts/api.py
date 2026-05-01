from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "04_resultados" / "delay_model.pkl"
DATA_PATH = ROOT / "01_datos_procesados" / "master_dataset.parquet"

app = FastAPI(title="OLIST Delay Alert API")
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
features = bundle["features"]
baseline_values = bundle["baseline_values"]
route_distance = bundle["route_distance"]
master_df = pd.read_parquet(DATA_PATH)


class DelayRiskRequest(BaseModel):
    seller_state: str
    customer_state: str
    product_category_name_english: str
    payment_type: str | None = None
    distancia_aprox: float | None = None
    total_price: float | None = None
    avg_price: float | None = None
    total_freight: float | None = None
    avg_freight: float | None = None
    item_count: float | None = None
    payment_installments: float | None = None
    payment_value: float | None = None
    payment_count: float | None = None
    approval_time_hours: float | None = None
    purchase_month: float | None = None
    purchase_dayofweek: float | None = None


def risk_level(probability: float) -> str:
    if probability >= 0.61:
        return "alto"
    if probability >= 0.31:
        return "medio"
    return "bajo"


def build_input(payload: DelayRiskRequest) -> pd.DataFrame:
    row = baseline_values.copy()
    user_values = payload.model_dump()
    row.update({key: value for key, value in user_values.items() if value is not None})

    if payload.distancia_aprox is None:
        key = (payload.seller_state, payload.customer_state)
        row["distancia_aprox"] = route_distance.get(
            key,
            baseline_values["distancia_aprox"],
        )

    return pd.DataFrame([row], columns=features)


@app.get("/")
def root() -> dict:
    return {
        "service": "OLIST Delay Alert API",
        "endpoints": ["/orders/delay_risk", "/orders/top_risk_categories"],
    }


@app.post("/orders/delay_risk")
def delay_risk(payload: DelayRiskRequest) -> dict:
    X = build_input(payload)
    probability = float(model.predict_proba(X)[0, 1])
    return {
        "delay_probability": round(probability, 4),
        "risk_level": risk_level(probability),
        "model": bundle["best_model"],
    }


@app.get("/orders/top_risk_categories")
def top_risk_categories(limit: int = 10) -> list[dict]:
    result = (
        master_df.groupby("product_category_name_english")
        .agg(
            late_rate=("entrego_tarde", "mean"),
            orders=("order_id", "count"),
            avg_review_score=("review_score", "mean"),
        )
        .query("orders >= 30")
        .sort_values("late_rate", ascending=False)
        .head(limit)
        .reset_index()
    )
    result["late_rate"] = result["late_rate"].round(4)
    result["avg_review_score"] = result["avg_review_score"].round(2)
    return result.to_dict(orient="records")
