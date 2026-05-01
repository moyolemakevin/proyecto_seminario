# Plan de preparacion - OLIST Delay Alert

## 1. Contexto del negocio

OLIST es un marketplace de e-commerce en Brasil. El problema del proyecto es
anticipar si un pedido puede llegar tarde, usando informacion historica de
pedidos, clientes, vendedores, productos, pagos, reviews y ubicacion.

El objetivo de negocio es construir una alerta temprana para que la empresa
pueda priorizar seguimiento logistico, avisar al cliente y reducir reclamos.

## 2. Estructura del proyecto

00_datos_crudos/       datos originales OLIST en CSV
01_datos_procesados/   dataset maestro en parquet
02_scripts/            scripts de preparacion y entrenamiento
03_cuadernos/          espacio para notebooks de analisis
04_resultados/         modelo, metricas y resultados generados
05_referencias/        documentacion y plan de preparacion
06_archivo/            archivo comprimido original
07_CONTEXTO_FILE/      contexto del negocio y desafio

## 3. Datos crudos

Los CSV originales estan en:

00_datos_crudos/

Tablas usadas:

olist_orders_dataset.csv
olist_customers_dataset.csv
olist_order_items_dataset.csv
olist_products_dataset.csv
olist_order_reviews_dataset.csv
olist_order_payments_dataset.csv
olist_sellers_dataset.csv
olist_geolocation_dataset.csv
product_category_name_translation.csv

## 4. Dataset maestro

El dataset procesado se guarda en:

01_datos_procesados/master_dataset.parquet

Actualmente contiene:

98,666 filas
37 columnas

El script que lo genera es:

02_scripts/build_dataset.py

Comando:

python 02_scripts/build_dataset.py

## 5. Variable objetivo

La variable que queremos predecir es:

entrego_tarde

Se calcula asi:

dias_retraso = order_delivered_customer_date - order_estimated_delivery_date
entrego_tarde = 1 si dias_retraso > 0
entrego_tarde = 0 si dias_retraso <= 0

Interpretacion:

- Si el pedido llego despues de la fecha estimada, se marca como tardio.
- Si llego el mismo dia o antes, se marca como no tardio.

Tasa historica actual:

6.62% de entregas tardias

Eso equivale a:

6,535 pedidos tardios
92,131 pedidos a tiempo o antes
98,666 pedidos totales

## 6. Preparacion de datos

`02_scripts/build_dataset.py` hace lo siguiente:

1. Lee todos los CSV desde `00_datos_crudos/`.
2. Convierte columnas de fecha a datetime.
3. Calcula `dias_retraso`.
4. Calcula `entrego_tarde`.
5. Calcula `approval_time_hours`.
6. Une productos con traduccion de categoria.
7. Agrupa items por pedido.
8. Selecciona vendedor y categoria principal del pedido.
9. Agrupa reviews por pedido.
10. Agrupa pagos por pedido.
11. Agrupa geolocalizacion por codigo postal.
12. Une clientes, items, reviews, pagos, vendedores y coordenadas.
13. Calcula `distancia_aprox`.
14. Extrae `purchase_month` y `purchase_dayofweek`.
15. Rellena valores faltantes importantes.
16. Guarda el parquet final.

## 7. Columnas principales

Identificadores:

order_id
customer_id
customer_unique_id
seller_id

Fechas:

order_purchase_timestamp
order_approved_at
order_delivered_carrier_date
order_delivered_customer_date
order_estimated_delivery_date

Retraso:

dias_retraso
entrego_tarde
approval_time_hours

Cliente y vendedor:

customer_state
customer_city
seller_state
customer_lat
customer_lng
seller_lat
seller_lng
distancia_aprox

Producto, pago y review:

product_category_name_english
item_count
total_price
avg_price
total_freight
avg_freight
payment_type
payment_installments
payment_value
payment_count
review_score
review_count

## 8. Entrenamiento del modelo

El entrenamiento esta en:

02_scripts/train_model.py

Comando:

python 02_scripts/train_model.py

El modelo intenta predecir:

entrego_tarde

Modelos comparados:

random_forest
gradient_boosting

El mejor modelo actual es:

gradient_boosting

Metricas actuales:

precision: 0.1431
recall:    0.6236
f1:        0.2328
roc_auc:   0.7369

Artefactos generados:

04_resultados/delay_model.pkl
04_resultados/metrics.json
04_resultados/feature_importance.csv
04_resultados/category_risk.csv

## 9. API

La API esta en:

02_scripts/api.py

Comando:

uvicorn api:app --app-dir 02_scripts --reload

Endpoints:

GET /
POST /orders/delay_risk
GET /orders/top_risk_categories

## 10. Dashboard

El dashboard esta en:

02_scripts/dashboard.py

Comando:

streamlit run 02_scripts/dashboard.py

Muestra:

- Pedidos historicos.
- Tasa de entregas tardias.
- Modelo activo.
- Tasa de retraso por estado del cliente.
- Categorias con menor satisfaccion promedio.
- Simulador de riesgo de retraso.

## 11. Flujo completo

00_datos_crudos/
  -> 02_scripts/build_dataset.py
  -> 01_datos_procesados/master_dataset.parquet
  -> 02_scripts/train_model.py
  -> 04_resultados/delay_model.pkl
  -> 02_scripts/api.py / 02_scripts/dashboard.py
  -> prediccion de riesgo de retraso

## 12. Mejoras pendientes

1. Definir metrica de negocio y ajustar umbrales de riesgo.
2. Calcular distancia real aproximada con Haversine.
3. Revisar pedidos sin fecha real de entrega.
4. Agregar analisis exploratorio por estado, categoria y vendedor.
5. Probar modelos adicionales si se permite instalar dependencias.
6. Agregar explicaciones por prediccion en API y dashboard.
