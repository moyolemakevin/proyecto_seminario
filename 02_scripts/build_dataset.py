from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "00_datos_crudos"
PROCESSED_DIR = ROOT / "01_datos_procesados"
OUTPUT_PATH = PROCESSED_DIR / "master_dataset.parquet"


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / name)


def build_master_dataset() -> pd.DataFrame:
    orders = read_csv("olist_orders_dataset.csv")
    customers = read_csv("olist_customers_dataset.csv")
    items = read_csv("olist_order_items_dataset.csv")
    products = read_csv("olist_products_dataset.csv")
    reviews = read_csv("olist_order_reviews_dataset.csv")
    payments = read_csv("olist_order_payments_dataset.csv")
    sellers = read_csv("olist_sellers_dataset.csv")
    geolocation = read_csv("olist_geolocation_dataset.csv")
    translation = read_csv("product_category_name_translation.csv")

    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    orders["dias_retraso"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.days
    orders["entrego_tarde"] = (orders["dias_retraso"] > 0).astype(int)
    orders["approval_time_hours"] = (
        orders["order_approved_at"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 3600

    products = products.merge(
        translation,
        on="product_category_name",
        how="left",
    )
    products["product_category_name_english"] = products[
        "product_category_name_english"
    ].fillna(products["product_category_name"]).fillna("unknown")

    item_details = (
        items.merge(products, on="product_id", how="left")
        .merge(sellers, on="seller_id", how="left")
    )

    item_numeric = (
        item_details.groupby("order_id", as_index=False)
        .agg(
            item_count=("order_item_id", "count"),
            total_price=("price", "sum"),
            avg_price=("price", "mean"),
            total_freight=("freight_value", "sum"),
            avg_freight=("freight_value", "mean"),
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
    item_agg = item_numeric.merge(item_main, on="order_id", how="left")

    review_agg = (
        reviews.groupby("order_id")
        .agg(
            review_score=("review_score", "mean"),
            review_count=("review_id", "count"),
        )
        .reset_index()
    )

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
    payment_agg = payment_numeric.merge(payment_main, on="order_id", how="left")

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

    master = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(item_agg, on="order_id", how="inner")
        .merge(review_agg, on="order_id", how="left")
        .merge(payment_agg, on="order_id", how="left")
        .merge(customer_geo, on="customer_zip_code_prefix", how="left")
        .merge(seller_geo, on="seller_zip_code_prefix", how="left")
    )

    master["distancia_aprox"] = np.sqrt(
        (master["seller_lat"] - master["customer_lat"]) ** 2
        + (master["seller_lng"] - master["customer_lng"]) ** 2
    )

    master["purchase_month"] = master["order_purchase_timestamp"].dt.month
    master["purchase_dayofweek"] = master["order_purchase_timestamp"].dt.dayofweek
    master["review_score"] = master["review_score"].fillna(master["review_score"].median())
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
