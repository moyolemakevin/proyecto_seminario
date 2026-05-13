from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from business_rules import (
    actions_for,
    code_from_state_label,
    recommendation_for,
    state_label,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "01_datos_procesados" / "master_dataset.parquet"
MODEL_PATH = ROOT / "04_resultados" / "delay_model.pkl"
METRICS_PATH = ROOT / "04_resultados" / "metrics.json"
IMPORTANCE_PATH = ROOT / "04_resultados" / "feature_importance.csv"
GEOJSON_PATH = ROOT / "05_referencias" / "brazil_states.geojson"

st.set_page_config(
    page_title="OLIST Delay Alert",
    layout="wide",
    initial_sidebar_state="expanded",
)

RISK_COLORS = {
    "Bajo": "#0f766e",
    "Medio": "#f59e0b",
    "Alto": "#dc2626",
}
CHART_BLUE = "#2563eb"
CHART_TEAL = "#0f766e"
CHART_ORANGE = "#f97316"
DISTANCE_KM_COLUMN = "distancia_km_haversine"


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_parquet(DATA_PATH)
    data["order_purchase_timestamp"] = pd.to_datetime(
        data["order_purchase_timestamp"],
        errors="coerce",
    )
    data["seller_state_label"] = data["seller_state"].map(state_label)
    data["customer_state_label"] = data["customer_state"].map(state_label)
    return data


@st.cache_resource
def load_model() -> dict:
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics() -> dict:
    if not METRICS_PATH.exists():
        return {}
    with METRICS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_feature_importance() -> pd.DataFrame:
    if not IMPORTANCE_PATH.exists():
        return pd.DataFrame(columns=["feature", "importance"])
    return pd.read_csv(IMPORTANCE_PATH)


@st.cache_data
def load_brazil_states_geojson() -> dict:
    if not GEOJSON_PATH.exists():
        return {}
    with GEOJSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def risk_level(probability: float, thresholds: dict) -> str:
    if probability >= thresholds["high"]:
        return "Alto"
    if probability >= thresholds["medium"]:
        return "Medio"
    return "Bajo"


@st.cache_data(show_spinner="Calculando riesgo historico...")
def score_data(data: pd.DataFrame, model_mtime: float) -> pd.DataFrame:
    bundle_local = joblib.load(MODEL_PATH)
    thresholds = bundle_local.get("risk_thresholds", {"medium": 0.31, "high": 0.61})
    scored = data.copy()
    probabilities = bundle_local["model"].predict_proba(
        scored[bundle_local["features"]]
    )[:, 1]
    scored["delay_probability"] = probabilities
    scored["risk_level_model"] = [
        risk_level(probability, thresholds) for probability in probabilities
    ]
    return scored


def style_figure(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=55, b=35),
        font=dict(family="Arial", size=12, color="#1f2937"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


def metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_sidebar_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("Filtros")
    min_date = data["order_purchase_timestamp"].min().date()
    max_date = data["order_purchase_timestamp"].max().date()
    date_range = st.sidebar.date_input(
        "Rango de compra",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    customer_states = sorted(data["customer_state_label"].dropna().unique())
    seller_states = sorted(data["seller_state_label"].dropna().unique())
    payment_types = sorted(data["payment_type"].dropna().unique())
    categories = sorted(data["product_category_name_english"].dropna().unique())

    selected_customer_states = st.sidebar.multiselect(
        "Estado del cliente",
        customer_states,
        default=customer_states,
    )
    selected_seller_states = st.sidebar.multiselect(
        "Estado del vendedor",
        seller_states,
        default=seller_states,
    )
    selected_payments = st.sidebar.multiselect(
        "Tipo de pago",
        payment_types,
        default=payment_types,
    )
    selected_risk = st.sidebar.multiselect(
        "Riesgo estimado",
        ["Bajo", "Medio", "Alto"],
        default=["Bajo", "Medio", "Alto"],
    )
    selected_categories = st.sidebar.multiselect(
        "Categorias",
        categories,
        default=categories,
    )
    min_orders = st.sidebar.slider("Minimo de pedidos por grupo", 20, 500, 50, 10)
    st.session_state["min_orders"] = min_orders

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    mask = (
        data["order_purchase_timestamp"].dt.date.between(start_date, end_date)
        & data["customer_state_label"].isin(selected_customer_states)
        & data["seller_state_label"].isin(selected_seller_states)
        & data["payment_type"].isin(selected_payments)
        & data["risk_level_model"].isin(selected_risk)
        & data["product_category_name_english"].isin(selected_categories)
    )
    return data.loc[mask].copy()


def plot_monthly_trend(data: pd.DataFrame) -> go.Figure:
    monthly = (
        data.assign(order_month=data["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp())
        .groupby("order_month", as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            alert_rate=("risk_level_model", lambda value: (value != "Bajo").mean()),
        )
    )
    fig = go.Figure()
    fig.add_bar(
        x=monthly["order_month"],
        y=monthly["orders"],
        name="Pedidos",
        marker_color="#dbeafe",
        yaxis="y1",
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["order_month"],
            y=monthly["late_rate"],
            name="Retraso real",
            mode="lines+markers",
            line=dict(color=CHART_ORANGE, width=3),
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["order_month"],
            y=monthly["alert_rate"],
            name="Alertas modelo",
            mode="lines+markers",
            line=dict(color=CHART_TEAL, width=3),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Evolucion mensual de pedidos, retrasos y alertas",
        yaxis=dict(title="Pedidos"),
        yaxis2=dict(title="Tasa", overlaying="y", side="right", tickformat=".0%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return style_figure(fig, height=390)


def plot_risk_segments(data: pd.DataFrame) -> go.Figure:
    risk_order = ["Bajo", "Medio", "Alto"]
    risk_summary = (
        data.groupby("risk_level_model", as_index=False)
        .agg(orders=("order_id", "count"), late_rate=("entrego_tarde", "mean"))
        .set_index("risk_level_model")
        .reindex(risk_order)
        .dropna()
        .reset_index()
    )
    fig = px.bar(
        risk_summary,
        x="risk_level_model",
        y="orders",
        color="risk_level_model",
        color_discrete_map=RISK_COLORS,
        text="orders",
        title="Distribucion de pedidos por nivel de riesgo",
        labels={
            "risk_level_model": "Nivel de riesgo",
            "orders": "Pedidos",
            "late_rate": "Tasa de retraso",
        },
        hover_data={"late_rate": ":.2%"},
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    return style_figure(fig, height=390)


def plot_state_risk(data: pd.DataFrame, min_orders: int) -> go.Figure:
    state_risk = (
        data.groupby("customer_state_label", as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            avg_distance=(DISTANCE_KM_COLUMN, "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values("late_rate", ascending=False)
        .head(15)
    )
    fig = px.bar(
        state_risk,
        x="late_rate",
        y="customer_state_label",
        color="avg_distance",
        orientation="h",
        color_continuous_scale=["#e0f2fe", "#f97316", "#dc2626"],
        title="Estados destino con mayor tasa de retraso",
        labels={
            "late_rate": "Tasa de retraso",
            "customer_state_label": "Estado cliente",
            "avg_distance": "Distancia media km",
        },
        hover_data={"orders": True, "avg_distance": ":.0f", "late_rate": ":.2%"},
    )
    fig.update_xaxes(tickformat=".0%")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return style_figure(fig)


def plot_brazil_choropleth(
    data: pd.DataFrame,
    geojson: dict,
    state_role: str,
    metric: str,
) -> go.Figure:
    state_column = "customer_state" if state_role == "Cliente" else "seller_state"
    label_column = (
        "customer_state_label" if state_role == "Cliente" else "seller_state_label"
    )

    state_summary = (
        data.groupby([state_column, label_column], as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            avg_probability=("delay_probability", "mean"),
            high_risk_rate=("risk_level_model", lambda value: (value == "Alto").mean()),
            avg_distance_km=(DISTANCE_KM_COLUMN, "mean"),
        )
        .rename(columns={state_column: "state_code", label_column: "state_label"})
    )

    metric_config = {
        "Tasa de retraso": {
            "column": "late_rate",
            "label": "Tasa de retraso",
            "tickformat": ".0%",
            "hover": ":.2%",
            "scale": ["#dcfce7", "#f59e0b", "#dc2626"],
        },
        "Probabilidad promedio": {
            "column": "avg_probability",
            "label": "Probabilidad promedio",
            "tickformat": ".0%",
            "hover": ":.2%",
            "scale": ["#dbeafe", "#f59e0b", "#dc2626"],
        },
        "Pedidos": {
            "column": "orders",
            "label": "Pedidos",
            "tickformat": ",",
            "hover": ":,",
            "scale": ["#e0f2fe", "#2563eb"],
        },
        "Riesgo alto": {
            "column": "high_risk_rate",
            "label": "Tasa riesgo alto",
            "tickformat": ".0%",
            "hover": ":.2%",
            "scale": ["#dcfce7", "#f59e0b", "#dc2626"],
        },
    }
    config = metric_config[metric]

    fig = px.choropleth(
        state_summary,
        geojson=geojson,
        locations="state_code",
        featureidkey="properties.sigla",
        color=config["column"],
        hover_name="state_label",
        hover_data={
            "state_code": False,
            "orders": ":,",
            "late_rate": ":.2%",
            "avg_probability": ":.2%",
            "high_risk_rate": ":.2%",
            "avg_distance_km": ":.0f",
        },
        color_continuous_scale=config["scale"],
        labels={config["column"]: config["label"]},
        title=f"Mapa coropletico por estado del {state_role.lower()}",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=config["label"],
            tickformat=config["tickformat"],
        )
    )
    return style_figure(fig, height=520)


def plot_category_risk(data: pd.DataFrame, min_orders: int) -> go.Figure:
    category_risk = (
        data.groupby("product_category_name_english", as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            avg_review_score=("review_score", "mean"),
            avg_delay_days=("dias_retraso", "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values("late_rate", ascending=False)
        .head(25)
    )
    category_risk["delay_size"] = category_risk["avg_delay_days"].clip(lower=0.1)
    fig = px.scatter(
        category_risk,
        x="orders",
        y="late_rate",
        size="delay_size",
        color="avg_review_score",
        color_continuous_scale=["#dc2626", "#f59e0b", "#0f766e"],
        title="Categorias: volumen, retraso y satisfaccion",
        labels={
            "orders": "Pedidos",
            "late_rate": "Tasa de retraso",
            "avg_review_score": "Review score",
            "avg_delay_days": "Dias promedio",
        },
        hover_name="product_category_name_english",
        hover_data={"late_rate": ":.2%", "avg_review_score": ":.2f"},
    )
    fig.update_yaxes(tickformat=".0%")
    return style_figure(fig)


def plot_category_review_score(data: pd.DataFrame, min_orders: int) -> go.Figure:
    category_score = (
        data.groupby("product_category_name_english", as_index=False)
        .agg(
            orders=("order_id", "count"),
            avg_review_score=("review_score", "mean"),
            late_rate=("entrego_tarde", "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values("avg_review_score", ascending=True)
        .head(18)
    )
    fig = px.bar(
        category_score,
        x="avg_review_score",
        y="product_category_name_english",
        color="late_rate",
        orientation="h",
        color_continuous_scale=["#0f766e", "#f59e0b", "#dc2626"],
        title="Satisfaccion promedio por categoria",
        labels={
            "avg_review_score": "Score promedio de resena",
            "product_category_name_english": "Categoria",
            "late_rate": "Tasa de retraso",
        },
        hover_data={"orders": True, "late_rate": ":.2%", "avg_review_score": ":.2f"},
    )
    fig.update_xaxes(range=[0, 5])
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return style_figure(fig, height=470)


def plot_distance_and_payment(data: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    distance_data = data.dropna(subset=[DISTANCE_KM_COLUMN]).copy()
    if distance_data[DISTANCE_KM_COLUMN].nunique() >= 2:
        distance_data["distance_band"] = pd.qcut(
            distance_data[DISTANCE_KM_COLUMN],
            q=min(5, distance_data[DISTANCE_KM_COLUMN].nunique()),
            duplicates="drop",
        ).astype(str)
        distance_summary = (
            distance_data.groupby("distance_band", as_index=False)
            .agg(orders=("order_id", "count"), late_rate=("entrego_tarde", "mean"))
        )
    else:
        distance_summary = pd.DataFrame(
            {
                "distance_band": ["Sin variacion"],
                "orders": [len(distance_data)],
                "late_rate": [distance_data["entrego_tarde"].mean()],
            }
        )
    fig_distance = px.line(
        distance_summary,
        x="distance_band",
        y="late_rate",
        markers=True,
        title="Riesgo real por banda de distancia",
        labels={"distance_band": "Banda de distancia km", "late_rate": "Tasa"},
    )
    fig_distance.update_traces(line=dict(color=CHART_BLUE, width=3))
    fig_distance.update_yaxes(tickformat=".0%")

    payment_summary = (
        data.groupby("payment_type", as_index=False)
        .agg(orders=("order_id", "count"), late_rate=("entrego_tarde", "mean"))
        .sort_values("late_rate", ascending=False)
    )
    fig_payment = px.bar(
        payment_summary,
        x="payment_type",
        y="late_rate",
        color="orders",
        color_continuous_scale=["#dbeafe", "#2563eb"],
        title="Retraso por tipo de pago",
        labels={"payment_type": "Tipo de pago", "late_rate": "Tasa"},
        hover_data={"orders": True, "late_rate": ":.2%"},
    )
    fig_payment.update_yaxes(tickformat=".0%")
    return style_figure(fig_distance), style_figure(fig_payment)


def build_operational_queue(data: pd.DataFrame, limit: int = 25) -> pd.DataFrame:
    queue = (
        data.loc[data["risk_level_model"].isin(["Medio", "Alto"])]
        .sort_values("delay_probability", ascending=False)
        .head(limit)
        .copy()
    )
    if queue.empty:
        return pd.DataFrame(
            columns=[
                "order_id",
                "risk_level_model",
                "delay_probability",
                "seller_state_label",
                "customer_state_label",
                "product_category_name_english",
                "payment_type",
                DISTANCE_KM_COLUMN,
                "recommended_action",
            ]
        )

    queue["delay_probability"] = queue["delay_probability"].map(lambda value: f"{value:.2%}")
    queue[DISTANCE_KM_COLUMN] = queue[DISTANCE_KM_COLUMN].round(0)
    queue["recommended_action"] = queue["risk_level_model"].map(recommendation_for)
    return queue[
        [
            "order_id",
            "risk_level_model",
            "delay_probability",
            "seller_state_label",
            "customer_state_label",
            "product_category_name_english",
            "payment_type",
            DISTANCE_KM_COLUMN,
            "recommended_action",
        ]
    ].rename(
        columns={
            "order_id": "pedido",
            "risk_level_model": "riesgo",
            "delay_probability": "probabilidad",
            "seller_state_label": "estado_vendedor",
            "customer_state_label": "estado_cliente",
            "product_category_name_english": "categoria",
            "payment_type": "pago",
            DISTANCE_KM_COLUMN: "distancia_km",
            "recommended_action": "accion_recomendada",
        }
    )


def build_executive_actions(data: pd.DataFrame) -> list[str]:
    high_risk = int((data["risk_level_model"] == "Alto").sum())
    medium_risk = int((data["risk_level_model"] == "Medio").sum())
    top_state = (
        data.groupby("customer_state_label")["entrego_tarde"]
        .mean()
        .sort_values(ascending=False)
    )
    top_state_label = top_state.index[0] if not top_state.empty else "sin datos"
    return [
        f"Atender primero {high_risk:,} pedidos de riesgo alto.",
        f"Mantener {medium_risk:,} pedidos de riesgo medio en monitoreo preventivo.",
        f"Revisar capacidad y promesa de entrega hacia {top_state_label}.",
        "Usar la cola operativa como lista diaria de seguimiento logistico.",
    ]


def build_simulator_row(bundle: dict, values: dict) -> pd.DataFrame:
    row = bundle["baseline_values"].copy()
    row.update({key: value for key, value in values.items() if value is not None})

    route_key = (row["seller_state"], row["customer_state"])
    if values.get("distancia_aprox") is None:
        row["distancia_aprox"] = bundle["route_distance"].get(
            route_key,
            row["distancia_aprox"],
        )
    if values.get(DISTANCE_KM_COLUMN) is None:
        row[DISTANCE_KM_COLUMN] = bundle.get("route_distance_km", {}).get(
            route_key,
            row.get(DISTANCE_KM_COLUMN, row["distancia_aprox"]),
        )

    item_count = max(float(row.get("item_count", 1) or 1), 1)
    row["avg_price"] = float(row["total_price"]) / item_count
    row["avg_freight"] = float(row["total_freight"]) / item_count
    row["payment_value"] = float(row["total_price"]) + float(row["total_freight"])
    return pd.DataFrame([row], columns=bundle["features"])


def render_simulator(data: pd.DataFrame, bundle: dict) -> None:
    model = bundle["model"]
    thresholds = bundle.get("risk_thresholds", {"medium": 0.31, "high": 0.61})
    baseline = bundle["baseline_values"]
    states = sorted(
        set(data["seller_state_label"].dropna())
        | set(data["customer_state_label"].dropna())
    )
    categories = sorted(data["product_category_name_english"].dropna().unique())
    payment_types = sorted(data["payment_type"].dropna().unique())

    st.subheader("Simulador operativo de riesgo")
    with st.form("risk_simulator"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            seller_state = st.selectbox(
                "Estado vendedor",
                states,
                index=states.index("SP - Sao Paulo")
                if "SP - Sao Paulo" in states
                else 0,
            )
            customer_state = st.selectbox(
                "Estado cliente",
                states,
                index=states.index("BA - Bahia") if "BA - Bahia" in states else 0,
            )
            category = st.selectbox("Categoria", categories)
        with col_b:
            payment_type = st.selectbox("Tipo de pago", payment_types)
            item_count = st.number_input(
                "Cantidad de items",
                min_value=1.0,
                value=float(baseline["item_count"]),
                step=1.0,
            )
            payment_installments = st.number_input(
                "Cuotas",
                min_value=0.0,
                value=float(baseline["payment_installments"]),
                step=1.0,
            )
        with col_c:
            total_price = st.number_input(
                "Precio total",
                min_value=0.0,
                value=float(baseline["total_price"]),
            )
            total_freight = st.number_input(
                "Flete total",
                min_value=0.0,
                value=float(baseline["total_freight"]),
            )
            route_distance_km = bundle.get("route_distance_km", {}).get(
                (
                    code_from_state_label(seller_state),
                    code_from_state_label(customer_state),
                ),
                baseline.get(DISTANCE_KM_COLUMN, baseline["distancia_aprox"]),
            )
            distancia_km_haversine = st.number_input(
                "Distancia estimada km",
                min_value=0.0,
                value=float(route_distance_km),
            )

        with st.expander("Variables logisticas avanzadas"):
            adv_a, adv_b, adv_c = st.columns(3)
            with adv_a:
                total_weight = st.number_input(
                    "Peso total g",
                    min_value=0.0,
                    value=float(baseline["total_product_weight_g"]),
                )
                avg_weight = st.number_input(
                    "Peso promedio g",
                    min_value=0.0,
                    value=float(baseline["avg_product_weight_g"]),
                )
            with adv_b:
                max_volume = st.number_input(
                    "Volumen maximo cm3",
                    min_value=0.0,
                    value=float(baseline["max_product_volume_cm3"]),
                )
                avg_volume = st.number_input(
                    "Volumen promedio cm3",
                    min_value=0.0,
                    value=float(baseline["avg_product_volume_cm3"]),
                )
            with adv_c:
                purchase_month = st.number_input(
                    "Mes de compra",
                    min_value=1,
                    max_value=12,
                    value=int(baseline["purchase_month"]),
                )
                purchase_dayofweek = st.number_input(
                    "Dia semana 0-6",
                    min_value=0,
                    max_value=6,
                    value=int(baseline["purchase_dayofweek"]),
                )

        submitted = st.form_submit_button("Calcular riesgo")

    if submitted:
        row = build_simulator_row(
            bundle,
            {
                "seller_state": code_from_state_label(seller_state),
                "customer_state": code_from_state_label(customer_state),
                "product_category_name_english": category,
                "payment_type": payment_type,
                "item_count": item_count,
                "payment_installments": payment_installments,
                "total_price": total_price,
                "total_freight": total_freight,
                DISTANCE_KM_COLUMN: distancia_km_haversine,
                "total_product_weight_g": total_weight,
                "avg_product_weight_g": avg_weight,
                "max_product_volume_cm3": max_volume,
                "avg_product_volume_cm3": avg_volume,
                "purchase_month": purchase_month,
                "purchase_dayofweek": purchase_dayofweek,
                "is_weekend": int(purchase_dayofweek in [5, 6]),
            },
        )
        probability = float(model.predict_proba(row)[0, 1])
        level = risk_level(probability, thresholds)

        result_col, action_col = st.columns([1, 1.5])
        with result_col:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=probability * 100,
                    number={"suffix": "%", "font": {"size": 34}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": RISK_COLORS[level]},
                        "steps": [
                            {
                                "range": [0, thresholds["medium"] * 100],
                                "color": "#dcfce7",
                            },
                            {
                                "range": [
                                    thresholds["medium"] * 100,
                                    thresholds["high"] * 100,
                                ],
                                "color": "#fef3c7",
                            },
                            {
                                "range": [thresholds["high"] * 100, 100],
                                "color": "#fee2e2",
                            },
                        ],
                    },
                    title={"text": "Probabilidad de retraso"},
                )
            )
            st.plotly_chart(style_figure(fig, height=300), width="stretch")
        with action_col:
            action_items = "".join(
                f"<li>{action}</li>" for action in actions_for(level)
            )
            st.markdown(
                f"""
                <div class="recommendation {level.lower()}">
                    <div class="recommendation-title">Riesgo {level}</div>
                    <div class="recommendation-prob">{probability:.2%}</div>
                    <div>{recommendation_for(level)}</div>
                    <ul>{action_items}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }
    .hero {
        border-left: 6px solid #0f766e;
        padding: 0.2rem 0 1.1rem 1rem;
        margin-bottom: 1rem;
    }
    .hero h1 {
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
        color: #111827;
    }
    .hero p {
        max-width: 980px;
        color: #4b5563;
        font-size: 1.02rem;
        margin: 0;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem 1.05rem;
        min-height: 118px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }
    .metric-label {
        color: #6b7280;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0;
        font-weight: 700;
    }
    .metric-value {
        color: #111827;
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.2;
        margin-top: 0.35rem;
    }
    .metric-caption {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: 0.35rem;
    }
    .recommendation {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.2rem;
        min-height: 220px;
        background: #ffffff;
    }
    .recommendation.bajo { border-left: 6px solid #0f766e; }
    .recommendation.medio { border-left: 6px solid #f59e0b; }
    .recommendation.alto { border-left: 6px solid #dc2626; }
    .recommendation-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #111827;
    }
    .recommendation-prob {
        font-size: 2.4rem;
        font-weight: 900;
        color: #111827;
        margin: 0.7rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

df = load_data()
bundle = load_model()
metrics = load_metrics()
feature_importance = load_feature_importance()
brazil_states_geojson = load_brazil_states_geojson()
df = score_data(df, MODEL_PATH.stat().st_mtime)

filtered_df = apply_sidebar_filters(df)
if filtered_df.empty:
    st.warning("No hay pedidos para los filtros seleccionados.")
    st.stop()

thresholds = bundle.get("risk_thresholds", {"medium": 0.31, "high": 0.61})
best_model = bundle["best_model"].replace("_", " ").title()
late_rate = filtered_df["entrego_tarde"].mean()
alert_rate = (filtered_df["risk_level_model"] != "Bajo").mean()
high_risk_orders = int((filtered_df["risk_level_model"] == "Alto").sum())
late_orders = int(filtered_df["entrego_tarde"].sum())
avg_delay_late = filtered_df.loc[
    filtered_df["entrego_tarde"].eq(1),
    "dias_retraso",
].mean()

st.markdown(
    f"""
    <div class="hero">
        <h1>OLIST Delay Alert System</h1>
        <p>
        Monitoreo logistico para anticipar entregas tardias, priorizar pedidos
        con mayor riesgo y traducir el modelo en acciones operativas.
        Modelo activo: <strong>{best_model}</strong>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
with kpi_1:
    metric_card("Pedidos filtrados", f"{len(filtered_df):,}", "Base historica entregada")
with kpi_2:
    metric_card("Tasa retraso real", f"{late_rate:.2%}", f"{late_orders:,} pedidos tarde")
with kpi_3:
    metric_card("Alertas modelo", f"{alert_rate:.2%}", "Riesgo medio o alto")
with kpi_4:
    metric_card("Riesgo alto", f"{high_risk_orders:,}", "Pedidos en maxima prioridad")
with kpi_5:
    metric_card(
        "Dias de retraso",
        f"{avg_delay_late:.1f}" if not np.isnan(avg_delay_late) else "0.0",
        "Promedio en pedidos tardios",
    )

tab_overview, tab_operation, tab_drivers, tab_simulator, tab_model = st.tabs(
    ["Resumen ejecutivo", "Operacion", "Drivers logisticos", "Simulador", "Modelo"]
)

with tab_overview:
    col_left, col_right = st.columns([1.4, 1])
    with col_left:
        st.plotly_chart(plot_monthly_trend(filtered_df), width="stretch")
    with col_right:
        st.plotly_chart(plot_risk_segments(filtered_df), width="stretch")

    min_orders = st.session_state["min_orders"]
    route_summary = (
        filtered_df.groupby(["seller_state_label", "customer_state_label"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_rate=("entrego_tarde", "mean"),
            avg_distance_km=(DISTANCE_KM_COLUMN, "mean"),
            avg_probability=("delay_probability", "mean"),
        )
        .query("orders >= @min_orders")
        .sort_values(["late_rate", "orders"], ascending=[False, False])
        .head(12)
    )
    route_summary["late_rate"] = route_summary["late_rate"].map(lambda value: f"{value:.2%}")
    route_summary["avg_probability"] = route_summary["avg_probability"].map(
        lambda value: f"{value:.2%}"
    )
    route_summary["avg_distance_km"] = route_summary["avg_distance_km"].round(0)
    st.subheader("Rutas que requieren atencion")
    st.dataframe(route_summary, width="stretch", hide_index=True)

with tab_operation:
    st.subheader("Cola operativa de pedidos en riesgo")
    action_left, action_right = st.columns([1, 1])
    with action_left:
        st.markdown("**Acciones sugeridas para el corte operativo**")
        for action in build_executive_actions(filtered_df):
            st.write(f"- {action}")
    with action_right:
        queue_counts = (
            filtered_df.groupby("risk_level_model", as_index=False)
            .agg(orders=("order_id", "count"))
            .sort_values("orders", ascending=False)
        )
        fig_queue = px.pie(
            queue_counts,
            names="risk_level_model",
            values="orders",
            color="risk_level_model",
            color_discrete_map=RISK_COLORS,
            hole=0.55,
            title="Carga operativa por nivel de riesgo",
        )
        st.plotly_chart(style_figure(fig_queue, height=320), width="stretch")

    queue = build_operational_queue(filtered_df)
    st.dataframe(queue, width="stretch", hide_index=True)

with tab_drivers:
    min_orders = st.session_state["min_orders"]
    st.subheader("Mapa coropletico de riesgo logistico")
    map_col_a, map_col_b = st.columns([1, 1])
    with map_col_a:
        state_role = st.radio(
            "Agrupar por estado",
            ["Cliente", "Vendedor"],
            horizontal=True,
        )
    with map_col_b:
        map_metric = st.selectbox(
            "Metrica del mapa",
            ["Tasa de retraso", "Probabilidad promedio", "Pedidos", "Riesgo alto"],
        )
    if brazil_states_geojson:
        st.plotly_chart(
            plot_brazil_choropleth(
                filtered_df,
                brazil_states_geojson,
                state_role,
                map_metric,
            ),
            width="stretch",
        )
    else:
        st.warning(
            "No se encontro el archivo 05_referencias/brazil_states.geojson."
        )

    driver_a, driver_b = st.columns(2)
    with driver_a:
        st.plotly_chart(plot_state_risk(filtered_df, min_orders), width="stretch")
    with driver_b:
        st.plotly_chart(plot_category_risk(filtered_df, min_orders), width="stretch")

    st.plotly_chart(
        plot_category_review_score(filtered_df, min_orders),
        width="stretch",
    )

    distance_fig, payment_fig = plot_distance_and_payment(filtered_df)
    driver_c, driver_d = st.columns(2)
    with driver_c:
        st.plotly_chart(distance_fig, width="stretch")
    with driver_d:
        st.plotly_chart(payment_fig, width="stretch")

with tab_simulator:
    render_simulator(df, bundle)

with tab_model:
    selected_model = metrics.get("best_model", bundle["best_model"])
    optimized_metrics = (
        metrics.get("models", {})
        .get(selected_model, {})
        .get("optimized_threshold", {})
    )

    model_cols = st.columns(5)
    with model_cols[0]:
        metric_card("Modelo", selected_model.replace("_", " ").title(), "Seleccionado por F1")
    with model_cols[1]:
        metric_card("Precision", f"{optimized_metrics.get('precision', 0):.2%}", "Alertas correctas")
    with model_cols[2]:
        metric_card("Recall", f"{optimized_metrics.get('recall', 0):.2%}", "Retrasos capturados")
    with model_cols[3]:
        metric_card("F1", f"{optimized_metrics.get('f1', 0):.3f}", "Balance precision-recall")
    with model_cols[4]:
        metric_card("ROC AUC", f"{optimized_metrics.get('roc_auc', 0):.3f}", "Ranking del modelo")

    model_left, model_right = st.columns([1.2, 1])
    with model_left:
        if not feature_importance.empty:
            importance = feature_importance.head(18).sort_values("importance")
            fig_importance = px.bar(
                importance,
                x="importance",
                y="feature",
                orientation="h",
                title="Variables mas influyentes",
                labels={"importance": "Importancia", "feature": "Variable"},
                color="importance",
                color_continuous_scale=["#dbeafe", "#2563eb"],
            )
            st.plotly_chart(style_figure(fig_importance, height=520), width="stretch")
    with model_right:
        matrix = optimized_metrics.get("confusion_matrix", {})
        confusion = np.array(
            [
                [matrix.get("true_negative", 0), matrix.get("false_positive", 0)],
                [matrix.get("false_negative", 0), matrix.get("true_positive", 0)],
            ]
        )
        fig_matrix = px.imshow(
            confusion,
            text_auto=True,
            color_continuous_scale=["#eff6ff", "#2563eb"],
            title="Matriz de confusion con umbral operativo",
            labels=dict(x="Prediccion", y="Real", color="Pedidos"),
            x=["A tiempo", "Tarde"],
            y=["A tiempo", "Tarde"],
        )
        st.plotly_chart(style_figure(fig_matrix, height=420), width="stretch")

    st.info(
        "El modelo esta optimizado como sistema de alerta temprana: prioriza "
        "capturar pedidos tardios manteniendo una cola operativa manejable."
    )
