from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "01_datos_procesados" / "master_dataset.parquet"
MODEL_PATH = ROOT / "04_resultados" / "delay_model.pkl"


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_parquet(DATA_PATH)


@st.cache_resource
def load_model() -> dict:
    return joblib.load(MODEL_PATH)


def risk_level(probability: float) -> str:
    if probability >= 0.61:
        return "Alto"
    if probability >= 0.31:
        return "Medio"
    return "Bajo"


df = load_data()
bundle = load_model()
model = bundle["model"]
features = bundle["features"]
baseline_values = bundle["baseline_values"]
route_distance = bundle["route_distance"]

st.set_page_config(page_title="OLIST Delay Alert", layout="wide")
st.title("OLIST Delay Alert System")

late_rate = df["entrego_tarde"].mean()
col1, col2, col3 = st.columns(3)
col1.metric("Pedidos historicos", f"{len(df):,}")
col2.metric("Tasa de entregas tardias", f"{late_rate:.2%}")
col3.metric("Modelo activo", bundle["best_model"].replace("_", " ").title())

state_delay = (
    df.groupby("customer_state")
    .agg(late_rate=("entrego_tarde", "mean"), orders=("order_id", "count"))
    .reset_index()
)

category_score = (
    df.groupby("product_category_name_english")
    .agg(
        avg_review_score=("review_score", "mean"),
        late_rate=("entrego_tarde", "mean"),
        orders=("order_id", "count"),
    )
    .query("orders >= 30")
    .sort_values("avg_review_score", ascending=True)
    .head(15)
    .reset_index()
)

left, right = st.columns(2)
with left:
    fig_state = px.bar(
        state_delay.sort_values("late_rate", ascending=False),
        x="customer_state",
        y="late_rate",
        hover_data=["orders"],
        title="Tasa de retraso por estado del cliente",
        labels={"customer_state": "Estado cliente", "late_rate": "Tasa de retraso"},
    )
    fig_state.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_state, use_container_width=True)

with right:
    fig_score = px.bar(
        category_score,
        x="avg_review_score",
        y="product_category_name_english",
        color="late_rate",
        orientation="h",
        title="Categorias con menor satisfaccion promedio",
        labels={
            "avg_review_score": "Score promedio",
            "product_category_name_english": "Categoria",
            "late_rate": "Tasa de retraso",
        },
    )
    st.plotly_chart(fig_score, use_container_width=True)

st.subheader("Simulador de riesgo de retraso")

form_left, form_right = st.columns(2)
with form_left:
    seller_state = st.selectbox(
        "Estado del vendedor",
        sorted(df["seller_state"].dropna().unique()),
        index=sorted(df["seller_state"].dropna().unique()).index("SP"),
    )
    customer_state = st.selectbox(
        "Estado del cliente",
        sorted(df["customer_state"].dropna().unique()),
    )
    category = st.selectbox(
        "Categoria de producto",
        sorted(df["product_category_name_english"].dropna().unique()),
    )
    payment_type = st.selectbox(
        "Tipo de pago",
        sorted(df["payment_type"].dropna().unique()),
    )

with form_right:
    route_key = (seller_state, customer_state)
    default_distance = float(
        route_distance.get(route_key, baseline_values["distancia_aprox"])
    )
    distancia_aprox = st.number_input("Distancia aproximada", value=default_distance)
    total_price = st.number_input("Precio total", value=float(baseline_values["total_price"]))
    total_freight = st.number_input(
        "Flete total",
        value=float(baseline_values["total_freight"]),
    )
    payment_installments = st.number_input(
        "Cuotas",
        min_value=0.0,
        value=float(baseline_values["payment_installments"]),
    )

if st.button("Calcular riesgo"):
    row = baseline_values.copy()
    row.update(
        {
            "seller_state": seller_state,
            "customer_state": customer_state,
            "product_category_name_english": category,
            "payment_type": payment_type,
            "distancia_aprox": distancia_aprox,
            "total_price": total_price,
            "avg_price": total_price,
            "total_freight": total_freight,
            "avg_freight": total_freight,
            "payment_value": total_price + total_freight,
            "payment_installments": payment_installments,
        }
    )
    X = pd.DataFrame([row], columns=features)
    probability = float(model.predict_proba(X)[0, 1])

    metric_col, text_col = st.columns([1, 2])
    metric_col.metric("Probabilidad de retraso", f"{probability:.2%}")
    text_col.write(f"Nivel de riesgo: **{risk_level(probability)}**")
    text_col.write(
        "Accion sugerida: priorizar seguimiento logistico si el riesgo es medio o alto."
    )
