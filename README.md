# OLIST Delay Alert System

Sistema analitico de alerta temprana para anticipar retrasos logisticos en
pedidos de ecommerce usando datos historicos de Olist Brasil.

El proyecto integra preparacion de datos, machine learning, API y dashboard
interactivo para convertir un caso academico en una herramienta presentable de
monitoreo operativo.

## Objetivo

Responder una pregunta de negocio:

> Que pedidos tienen mayor riesgo de llegar tarde y requieren seguimiento
> logistico prioritario?

La salida del sistema es una probabilidad de retraso, un nivel de riesgo
(`bajo`, `medio`, `alto`) y una recomendacion operativa.

## Estructura

```text
00_datos_crudos/          CSV originales de Olist
01_datos_procesados/      Dataset maestro en parquet
02_scripts/               Preparacion, entrenamiento, API y dashboard
03_cuadernos/             Espacio para notebooks
04_resultados/            Modelo, metricas e interpretabilidad
05_referencias/           Documentacion auxiliar
06_archivo/               Archivo comprimido original
07_CONTEXTO_FILE/         Contexto de negocio y desafio
```

## Pipeline

1. `build_dataset.py`
   - Une pedidos, clientes, items, productos, vendedores, pagos, reviews y
     geolocalizacion.
   - Filtra pedidos entregados con fecha real y fecha estimada para construir
     una etiqueta supervisada consistente.
   - Calcula `dias_retraso`, `entrego_tarde`, `distancia_aprox` como proxy
     euclidiana en grados y `distancia_km_haversine` para lectura operativa.

2. `train_model.py`
   - Entrena modelos con pipeline de scikit-learn.
   - Evalua precision, recall, F1, ROC AUC y average precision.
   - Ajusta un umbral operativo basado en F1.
   - Guarda modelo, metricas, importancia de variables y riesgo por categoria.

3. `api.py`
   - Expone predicciones con FastAPI.
   - Incluye health check, payload de ejemplo y endpoint de categorias de alto
     riesgo.

4. `dashboard.py`
   - Dashboard ejecutivo en Streamlit con filtros, KPIs, visualizaciones y
     simulador de riesgo.

5. `business_rules.py`
   - Catalogo de estados de Brasil, nombres legibles y acciones operativas por
     nivel de riesgo.

## Instalacion

```bash
pip install -r 02_scripts/requirements.txt
```

## Ejecucion

Reconstruir dataset:

```bash
python 02_scripts/build_dataset.py
```

Entrenar modelo:

```bash
python 02_scripts/train_model.py
```

Levantar API:

```bash
uvicorn api:app --app-dir 02_scripts --reload
```

Abrir documentacion interactiva:

```text
http://127.0.0.1:8000/docs
```

Levantar dashboard:

```bash
streamlit run 02_scripts/dashboard.py
```

## Resultados actuales

Dataset maestro:

```text
Filas: 96,470
Columnas: 44
Pedidos tardios: 6,534
Pedidos a tiempo o antes: 89,936
Tasa historica de retraso: 6.77%
```

Modelo seleccionado: `gradient_boosting`

Metricas con umbral operativo (`threshold = 0.6418`):

```text
Precision: 23.15%
Recall: 37.11%
F1: 0.285
ROC AUC: 0.742
Average precision: 0.206
Tasa de alertas: 10.86%
```

Interpretacion de negocio:

- El dataset esta desbalanceado: menos de 7 de cada 100 pedidos llegan tarde.
- El modelo no debe usarse como decision automatica, sino como cola de
  priorizacion operativa.
- La precision del 23.15% concentra retrasos en la cola de alertas por encima
  de la tasa base historica.
- El recall del 37.11% indica que el sistema captura una parte relevante de los
  retrasos con una tasa de alertas manejable.

## API

### Health check

```http
GET /health
```

### Catalogo de estados

```http
GET /catalog/states
```

Devuelve codigo, nombre y etiqueta legible de cada estado usado por el proyecto.

### Payload de ejemplo

```http
GET /orders/example_payload
```

### Prediccion de riesgo

```http
POST /orders/delay_risk
```

Ejemplo:

```json
{
  "seller_state": "SP - Sao Paulo",
  "customer_state": "BA - Bahia",
  "product_category_name_english": "furniture_decor",
  "payment_type": "credit_card",
  "total_price": 120.0,
  "total_freight": 25.0,
  "item_count": 1,
  "payment_installments": 2
}
```

Respuesta:

```json
{
  "delay_probability": 0.4854,
  "risk_level": "bajo",
  "model": "gradient_boosting",
  "threshold_used": 0.6418,
  "recommendation": "Mantener flujo logistico normal. Monitorear solo por reglas operativas estandar.",
  "operational_actions": [
    "Mantener flujo logistico normal.",
    "Monitorear solo por reglas operativas estandar."
  ]
}
```

### Categorias de mayor riesgo

```http
GET /orders/top_risk_categories?limit=10&min_orders=30
```

### Rutas de mayor riesgo

```http
GET /orders/top_risk_routes?limit=10&min_orders=30
```

Devuelve rutas vendedor-cliente con codigo de estado, nombre completo, tasa de
retraso, volumen, distancia media y review promedio.

## Dashboard

El dashboard incluye:

- Filtros por fecha, estado cliente, estado vendedor, tipo de pago, categoria y
  nivel de riesgo.
- Estados en formato `UF - Nombre`, por ejemplo `SP - Sao Paulo`.
- KPIs ejecutivos de pedidos, retraso real, alertas, riesgo alto y dias de
  retraso.
- Evolucion mensual de pedidos, retrasos y alertas del modelo.
- Cola operativa de pedidos con mayor riesgo.
- Mapa coropletico de Brasil por estado del cliente o vendedor.
- Grafico de barras de satisfaccion promedio por categoria de producto.
- Analisis por estado, categoria, distancia, tipo de pago y rutas criticas.
- Simulador de riesgo de retraso con recomendacion operativa.
- Vista de modelo con metricas, importancia de variables y matriz de confusion.

## Artefactos generados

```text
01_datos_procesados/master_dataset.parquet
04_resultados/delay_model.pkl
04_resultados/metrics.json
04_resultados/feature_importance.csv
04_resultados/category_risk.csv
05_referencias/brazil_states.geojson
05_referencias/03_diagrama_relacional_y_joins.md
```

## Prompt de producto

El brief profesional usado para esta segunda iteracion esta documentado en:

```text
05_referencias/02_prompt_profesional_producto.md
```

## Nota metodologica

La etiqueta `entrego_tarde` se calcula solo en pedidos entregados con fecha real
de entrega y fecha estimada. Esto evita tratar pedidos cancelados, no entregados
o sin fecha final como si hubieran llegado a tiempo.

La columna `distancia_aprox` conserva la definicion de la rubrica: distancia
euclidiana en grados entre coordenadas de vendedor y cliente. Para lectura de
negocio se agrega `distancia_km_haversine`, usada en tablas y graficos donde la
unidad esperada es kilometros.
