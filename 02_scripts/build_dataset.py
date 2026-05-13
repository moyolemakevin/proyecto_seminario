from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "00_datos_crudos"
PROCESSED_DIR = ROOT / "01_datos_procesados"
OUTPUT_PATH = PROCESSED_DIR / "master_dataset.parquet"

RAW_FILES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "translation": "product_category_name_translation.csv",
}


def read_csv(name: str) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo requerido: {path}")
    return pd.read_csv(path)


def haversine_distance_km(
    lat_origin: pd.Series,
    lng_origin: pd.Series,
    lat_destination: pd.Series,
    lng_destination: pd.Series,
) -> pd.Series:
    """Calcula distancia aproximada en kilometros entre vendedor y cliente."""
    radius_km = 6371.0
    lat_1 = np.radians(lat_origin)
    lat_2 = np.radians(lat_destination)
    delta_lat = np.radians(lat_destination - lat_origin)
    delta_lng = np.radians(lng_destination - lng_origin)

    haversine = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat_1) * np.cos(lat_2) * np.sin(delta_lng / 2) ** 2
    )
    return 2 * radius_km * np.arcsin(np.sqrt(haversine))


def euclidean_distance_degrees(
    lat_origin: pd.Series,
    lng_origin: pd.Series,
    lat_destination: pd.Series,
    lng_destination: pd.Series,
) -> pd.Series:
    """Distancia proxy pedida por el caso: euclidiana sobre lat/lon."""
    return np.sqrt((lat_origin - lat_destination) ** 2 + (lng_origin - lng_destination) ** 2)


def prepare_orders(orders: pd.DataFrame) -> pd.DataFrame:
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    supervised_orders = orders.loc[
        orders["order_status"].eq("delivered")
        & orders["order_delivered_customer_date"].notna()
        & orders["order_estimated_delivery_date"].notna()
    ].copy()

    supervised_orders["dias_retraso"] = (
        supervised_orders["order_delivered_customer_date"]
        - supervised_orders["order_estimated_delivery_date"]
    ).dt.days
    supervised_orders["entrego_tarde"] = (
        supervised_orders["dias_retraso"] > 0
    ).astype(int)
    supervised_orders["approval_time_hours"] = (
        supervised_orders["order_approved_at"]
        - supervised_orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 3600
    supervised_orders["purchase_month"] = supervised_orders[
        "order_purchase_timestamp"
    ].dt.month
    supervised_orders["purchase_dayofweek"] = supervised_orders[
        "order_purchase_timestamp"
    ].dt.dayofweek
    supervised_orders["purchase_hour"] = supervised_orders[
        "order_purchase_timestamp"
    ].dt.hour
    supervised_orders["is_weekend"] = supervised_orders["purchase_dayofweek"].isin(
        [5, 6]
    ).astype(int)

    return supervised_orders


def prepare_products(
    products: pd.DataFrame,
    translation: pd.DataFrame,
) -> pd.DataFrame:
    products = products.merge(translation, on="product_category_name", how="left")
    products["product_category_name_english"] = (
        products["product_category_name_english"]
        .fillna(products["product_category_name"])
        .fillna("unknown")
    )
    products["product_volume_cm3"] = (
        products["product_length_cm"]
        * products["product_height_cm"]
        * products["product_width_cm"]
    )
    return products


def aggregate_items(
    items: pd.DataFrame,
    products: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    item_details = items.merge(products, on="product_id", how="left").merge(
        sellers, on="seller_id", how="left"
    )

    item_numeric = (
        item_details.groupby("order_id", as_index=False)
        .agg(
            item_count=("order_item_id", "count"),
            total_price=("price", "sum"),
            avg_price=("price", "mean"),
            total_freight=("freight_value", "sum"),
            avg_freight=("freight_value", "mean"),
            total_product_weight_g=("product_weight_g", "sum"),
            avg_product_weight_g=("product_weight_g", "mean"),
            max_product_volume_cm3=("product_volume_cm3", "max"),
            avg_product_volume_cm3=("product_volume_cm3", "mean"),
        )
    )
    item_main = (
        item_details.sort_values(["order_id", "price"], ascending=[True, False])
        .drop_duplicates("order_id")
        [
            [
                "order_id",
                "seller_id",
                "seller_state",
                "seller_zip_code_prefix",
                "product_category_name_english",
            ]
        ]
    )
    return item_numeric.merge(item_main, on="order_id", how="left")


def aggregate_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    return (
        reviews.groupby("order_id")
        .agg(
            review_score=("review_score", "mean"),
            review_count=("review_id", "count"),
        )
        .reset_index()
    )


def aggregate_payments(payments: pd.DataFrame) -> pd.DataFrame:
    payment_numeric = (
        payments.groupby("order_id", as_index=False)
        .agg(
            payment_installments=("payment_installments", "max"),
            payment_value=("payment_value", "sum"),
            payment_count=("payment_sequential", "count"),
        )
    )
    payment_main = (
        payments.sort_values(["order_id", "payment_value"], ascending=[True, False])
        .drop_duplicates("order_id")[["order_id", "payment_type"]]
    )
    return payment_numeric.merge(payment_main, on="order_id", how="left")


def aggregate_geolocation(geolocation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    geo_agg = (
        geolocation.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
        )
    )
    customer_geo = geo_agg.rename(
        columns={
            "geolocation_zip_code_prefix": "customer_zip_code_prefix",
            "geolocation_lat": "customer_lat",
            "geolocation_lng": "customer_lng",
        }
    )
    seller_geo = geo_agg.rename(
        columns={
            "geolocation_zip_code_prefix": "seller_zip_code_prefix",
            "geolocation_lat": "seller_lat",
            "geolocation_lng": "seller_lng",
        }
    )
    return customer_geo, seller_geo


def build_master_dataset() -> pd.DataFrame:
    raw = {name: read_csv(file_name) for name, file_name in RAW_FILES.items()}

    orders = prepare_orders(raw["orders"])
    products = prepare_products(raw["products"], raw["translation"])
    item_agg = aggregate_items(raw["items"], products, raw["sellers"])
    review_agg = aggregate_reviews(raw["reviews"])
    payment_agg = aggregate_payments(raw["payments"])
    customer_geo, seller_geo = aggregate_geolocation(raw["geolocation"])

    master = (
        orders.merge(raw["customers"], on="customer_id", how="left")
        .merge(item_agg, on="order_id", how="inner")
        .merge(review_agg, on="order_id", how="left")
        .merge(payment_agg, on="order_id", how="left")
        .merge(customer_geo, on="customer_zip_code_prefix", how="left")
        .merge(seller_geo, on="seller_zip_code_prefix", how="left")
    )

    master["distancia_aprox"] = euclidean_distance_degrees(
        master["seller_lat"],
        master["seller_lng"],
        master["customer_lat"],
        master["customer_lng"],
    )
    master["distancia_km_haversine"] = haversine_distance_km(
        master["seller_lat"],
        master["seller_lng"],
        master["customer_lat"],
        master["customer_lng"],
    )

    master["review_score"] = master["review_score"].fillna(
        master["review_score"].median()
    )
    master["review_count"] = master["review_count"].fillna(0)
    master["payment_type"] = master["payment_type"].fillna("unknown")
    master["product_category_name_english"] = master[
        "product_category_name_english"
    ].fillna("unknown")

    return master


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    master = build_master_dataset()
    master.to_parquet(OUTPUT_PATH, index=False)

    target_rate = master["entrego_tarde"].mean()
    late_orders = int(master["entrego_tarde"].sum())
    on_time_orders = int((master["entrego_tarde"] == 0).sum())
    print(f"Dataset maestro: {OUTPUT_PATH}")
    print(f"Filas: {len(master):,}")
    print(f"Columnas: {len(master.columns):,}")
    print(f"Pedidos tardios: {late_orders:,}")
    print(f"Pedidos a tiempo o antes: {on_time_orders:,}")
    print(f"Tasa de entregas tardias: {target_rate:.2%}")


if __name__ == "__main__":
    main()
