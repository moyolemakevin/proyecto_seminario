# Resumen para exposicion: OLIST Delay Alert System

## 1. Nombre del proyecto

El proyecto se llama **
Sistema de alerta de retraso OLIST**.

Es un sistema analitico de alerta temprana para anticipar retrasos logisticos
en pedidos de e-commerce usando datos historicos de Olist Brasil.

## 2. Pregunta principal

La pregunta de negocio que responde el proyecto es:

> Que pedidos tienen mayor riesgo de llegar tarde y requieren seguimiento
> logistico prioritario?

El sistema recibe informacion de un pedido y devuelve:

- Probabilidad de retraso.
- Nivel de riesgo: bajo, medio o alto.
- Recomendacion operativa.
- Acciones sugeridas para el equipo logistico.

## 3. Contexto de negocio

Olist es un marketplace de e-commerce de Brasil. En un marketplace, muchos
vendedores ofrecen productos y muchos clientes realizan compras.

Olist conecta al vendedor con el cliente y ayuda a gestionar el pedido, el pago
y la experiencia de compra.

El flujo basico es:

1. El cliente compra un producto.
2. El pedido queda registrado.
3. El pago se aprueba.
4. El vendedor prepara el producto.
5. El pedido entra al proceso logistico.
6. El pedido llega al cliente.
7. El cliente puede dejar una calificacion.

El punto critico del negocio es la entrega. Si el pedido llega despues de la
fecha estimada, la experiencia del cliente empeora y puede generar reclamos,
malas calificaciones o perdida de confianza.

## 4. Problema que resuelve

El problema principal es anticipar si un pedido puede llegar tarde.

No todos los pedidos tienen el mismo riesgo. Por ejemplo:

- Un pedido donde vendedor y cliente estan en el mismo estado puede tener menor
  riesgo.
- Un pedido donde vendedor y cliente estan en estados muy lejanos puede tener
  mayor riesgo logistico.

Por eso el sistema analiza caracteristicas como:

- Estado del vendedor.
- Estado del cliente.
- Categoria del producto.
- Tipo de pago.
- Precio.
- Flete.
- Peso y volumen.
- Distancia entre vendedor y cliente.
- Fecha y hora de compra.

## 5. Valor para el negocio

El proyecto ayuda a Olist a:

- Detectar pedidos con riesgo antes de que el cliente reclame.
- Priorizar seguimiento logistico.
- Revisar rutas problematicas.
- Contactar vendedores o transportistas.
- Preparar comunicacion preventiva al cliente.
- Identificar categorias de producto con mas retrasos.
- Mejorar la promesa de fecha estimada.
- Reducir malas calificaciones.

La idea no es reemplazar al equipo logistico, sino darle una lista priorizada de
pedidos que merecen atencion.

## 6. Estructura del proyecto

```text
00_datos_crudos/
```

Contiene los archivos CSV originales de Olist.

```text
01_datos_procesados/
```

Contiene el dataset maestro procesado:

```text
master_dataset.parquet
```

```text
02_scripts/
```

Contiene el codigo principal:

- `build_dataset.py`: prepara y une los datos.
- `train_model.py`: entrena el modelo de machine learning.
- `api.py`: publica el modelo mediante FastAPI.
- `dashboard.py`: crea el dashboard en Streamlit.
- `business_rules.py`: contiene reglas y recomendaciones de negocio.

```text
04_resultados/
```

Contiene los artefactos generados:

- `delay_model.pkl`: modelo entrenado.
- `metrics.json`: metricas del modelo.
- `feature_importance.csv`: importancia de variables.
- `category_risk.csv`: riesgo por categoria.

```text
05_referencias/
```

Contiene documentacion auxiliar, diagramas y archivos de referencia.

## 7. Flujo general del proyecto

El proyecto sigue este pipeline:

1. Cargar datos crudos.
2. Limpiar y transformar fechas.
3. Unir tablas de pedidos, clientes, productos, vendedores, pagos, reviews y
   geolocalizacion.
4. Calcular si cada pedido llego tarde.
5. Crear variables explicativas.
6. Entrenar modelos.
7. Evaluar metricas.
8. Guardar el mejor modelo.
9. Exponer predicciones por API.
10. Visualizar resultados en un dashboard.

## 8. Explicacion del archivo build_dataset.py

Este archivo construye el dataset maestro.

Primero define los archivos crudos:

```python
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
```

Luego lee los CSV y convierte columnas de fecha.

Las fechas mas importantes son:

- `order_purchase_timestamp`: fecha de compra.
- `order_approved_at`: fecha de aprobacion del pago.
- `order_delivered_customer_date`: fecha real de entrega.
- `order_estimated_delivery_date`: fecha estimada de entrega.

Despues calcula:

```python
dias_retraso = order_delivered_customer_date - order_estimated_delivery_date
```

Y crea la variable objetivo:

```python
entrego_tarde = 1 si dias_retraso > 0
entrego_tarde = 0 si llego a tiempo o antes
```

Esta variable es la que el modelo aprende a predecir.

Tambien crea variables adicionales:

- `approval_time_hours`: horas entre compra y aprobacion.
- `purchase_month`: mes de compra.
- `purchase_dayofweek`: dia de la semana.
- `purchase_hour`: hora de compra.
- `is_weekend`: si la compra fue fin de semana.

Tambien agrega informacion de productos:

- Cantidad de items.
- Precio total.
- Precio promedio.
- Flete total.
- Flete promedio.
- Peso total.
- Volumen del producto.
- Categoria del producto.

Para la parte logistica calcula distancia entre vendedor y cliente:

```python
distancia_aprox
```

Es una distancia aproximada usando latitud y longitud.

```python
distancia_km_haversine
```

Es una distancia mas interpretable porque esta en kilometros.

Finalmente guarda el dataset en:

```text
01_datos_procesados/master_dataset.parquet
```

## 9. Explicacion del archivo train_model.py

Este archivo entrena el modelo predictivo.

Define variables categoricas:

```python
seller_state
customer_state
product_category_name_english
payment_type
```

Define variables numericas:

```python
distancia_aprox
distancia_km_haversine
total_price
avg_price
total_freight
avg_freight
item_count
total_product_weight_g
avg_product_weight_g
max_product_volume_cm3
avg_product_volume_cm3
payment_installments
payment_value
payment_count
approval_time_hours
purchase_month
purchase_dayofweek
purchase_hour
is_weekend
```

La variable objetivo es:

```python
entrego_tarde
```

El codigo usa un pipeline de scikit-learn. Para variables categoricas aplica:

- Imputacion de valores faltantes.
- One Hot Encoding.

Para variables numericas aplica:

- Imputacion con la mediana.

Luego entrena dos modelos:

- Random Forest.
- Gradient Boosting.

El proyecto compara los modelos y selecciona el mejor segun el F1 con umbral
optimizado.

El mejor modelo actual es:

```text
gradient_boosting
```

El modelo entrenado se guarda en:

```text
04_resultados/delay_model.pkl
```

## 10. Metricas del modelo

El dataset maestro tiene:

```text
Filas: 96,470
Columnas: 44
Pedidos tardios: 6,534
Pedidos a tiempo o antes: 89,936
Tasa historica de retraso: 6.77%
```

Esto indica que el problema esta desbalanceado: pocos pedidos llegan tarde.

Metricas del mejor modelo:

```text
Modelo: gradient_boosting
Threshold operativo: 0.6418
Precision: 23.15%
Recall: 37.11%
F1: 0.285
ROC AUC: 0.742
Average precision: 0.206
Tasa de alertas: 10.86%
```

Interpretacion:

- La tasa historica de retraso es 6.77%.
- La precision del modelo es 23.15%, por encima de la tasa base.
- Esto significa que la cola de alertas concentra mas pedidos tardios que si se
  eligieran pedidos al azar.
- El recall de 37.11% indica que el modelo captura una parte relevante de los
  retrasos.
- El modelo se usa como herramienta de priorizacion, no como decision
  automatica final.

## 11. Variables mas importantes

Las variables mas influyentes del modelo fueron:

```text
purchase_month
distancia_km_haversine
customer_state_RJ
avg_freight
customer_state_SP
approval_time_hours
seller_state_SP
distancia_aprox
customer_state_MG
avg_price
```

Esto muestra que el riesgo de retraso depende bastante de:

- El mes de compra.
- La distancia logistica.
- El estado del cliente.
- El estado del vendedor.
- El valor del flete.
- El tiempo de aprobacion.
- El precio promedio.

## 12. Categorias con mayor riesgo

Algunas categorias con mayor tasa de retraso son:

```text
furniture_mattress_and_upholstery
audio
home_confort
fashion_underwear_beach
books_technical
baby
office_furniture
electronics
health_beauty
bed_bath_table
```

Esto permite que el negocio identifique categorias que necesitan mas control o
seguimiento.

## 13. Explicacion del archivo api.py

Este archivo usa FastAPI para publicar el modelo como servicio.

Cuando se inicia la API, carga:

- El modelo entrenado.
- Las variables del modelo.
- Los valores base.
- Las distancias por ruta.
- El dataset maestro.

El endpoint principal es:

```http
POST /orders/delay_risk
```

Ejemplo de entrada:

```json
{
  "seller_state": "SP",
  "customer_state": "BA",
  "product_category_name_english": "furniture_decor",
  "payment_type": "credit_card",
  "total_price": 120.0,
  "total_freight": 25.0,
  "item_count": 1,
  "payment_installments": 2
}
```

La API construye una fila con esos datos, completa valores faltantes con valores
base y calcula la probabilidad:

```python
probability = model.predict_proba(X)[0, 1]
```

Luego convierte esa probabilidad en nivel de riesgo:

```python
if probability >= risk_thresholds["high"]:
    return "alto"
if probability >= risk_thresholds["medium"]:
    return "medio"
return "bajo"
```

Ejemplo de respuesta:

```json
{
  "delay_probability": 0.4854,
  "risk_level": "bajo",
  "model": "gradient_boosting",
  "recommendation": "Mantener flujo logistico normal.",
  "operational_actions": [
    "Mantener flujo logistico normal.",
    "Monitorear solo por reglas operativas estandar."
  ]
}
```

Otros endpoints importantes:

```http
GET /health
```

Sirve para verificar que el modelo y el dataset cargaron bien.

```http
GET /catalog/states
```

Devuelve los estados de Brasil usados por el sistema.

```http
GET /orders/top_risk_categories
```

Devuelve categorias con mayor tasa de retraso.

```http
GET /orders/top_risk_routes
```

Devuelve rutas vendedor-cliente con mayor riesgo.

## 14. Explicacion del archivo dashboard.py

Este archivo crea el dashboard visual con Streamlit.

El dashboard permite analizar el negocio desde varias vistas:

- Resumen ejecutivo.
- Operacion.
- Drivers logisticos.
- Simulador.
- Modelo.

Incluye KPIs como:

- Pedidos filtrados.
- Tasa de retraso real.
- Alertas del modelo.
- Pedidos de riesgo alto.
- Dias promedio de retraso.

Tambien incluye graficos:

- Evolucion mensual de pedidos y retrasos.
- Distribucion por nivel de riesgo.
- Mapa coropletico de Brasil.
- Riesgo por estado.
- Riesgo por categoria.
- Satisfaccion promedio por categoria.
- Retraso por distancia.
- Retraso por tipo de pago.

La vista de operacion muestra una cola de pedidos en riesgo. Esta cola sirve
como lista diaria para que el equipo logistico revise primero los pedidos mas
criticos.

El dashboard tambien tiene un simulador. El usuario puede ingresar un pedido
nuevo con estado del vendedor, estado del cliente, categoria, pago, precio,
flete y distancia. Luego el sistema calcula el riesgo y muestra una
recomendacion.

## 15. Explicacion del archivo business_rules.py

Este archivo contiene reglas de negocio.

Primero tiene un catalogo de estados de Brasil:

```python
BRAZIL_STATES = {
    "SP": "Sao Paulo",
    "RJ": "Rio de Janeiro",
    "BA": "Bahia",
    ...
}
```

Tambien contiene acciones recomendadas por nivel de riesgo:

Riesgo bajo:

```text
Mantener flujo logistico normal.
Monitorear solo por reglas operativas estandar.
```

Riesgo medio:

```text
Revisar ruta, vendedor y promesa de entrega.
Confirmar despacho si existen pedidos similares acumulados.
Preparar comunicacion preventiva si el cliente es sensible al plazo.
```

Riesgo alto:

```text
Priorizar seguimiento logistico antes del corte operativo.
Validar despacho con el vendedor y transportista.
Escalar si la ruta aparece repetidamente en la cola de riesgo.
Preparar comunicacion proactiva al cliente.
```

Esto hace que el modelo sea mas util, porque no solo entrega un numero, sino
tambien una accion concreta.

## 16. Como se ejecuta el proyecto

Instalar dependencias:

```bash
pip install -r 02_scripts/requirements.txt
```

Reconstruir el dataset:

```bash
python 02_scripts/build_dataset.py
```

Entrenar el modelo:

```bash
python 02_scripts/train_model.py
```

Levantar la API:

```bash
uvicorn api:app --app-dir 02_scripts --reload
```

Abrir documentacion de la API:

```text
http://127.0.0.1:8000/docs
```

Levantar dashboard:

```bash
streamlit run 02_scripts/dashboard.py
```

## 17. Explicacion de formulas y calculos

### 17.1 Dias de retraso

Esta es una de las formulas principales del proyecto.

```python
dias_retraso = order_delivered_customer_date - order_estimated_delivery_date
```

Significado:

- `order_delivered_customer_date`: fecha real en la que el cliente recibio el
  pedido.
- `order_estimated_delivery_date`: fecha prometida o estimada de entrega.

Interpretacion:

- Si `dias_retraso > 0`, el pedido llego tarde.
- Si `dias_retraso <= 0`, el pedido llego a tiempo o antes.

Ejemplo:

```text
Fecha estimada: 10 de mayo
Fecha real: 13 de mayo
dias_retraso = 3
```

Ese pedido llego 3 dias tarde.

### 17.2 Variable objetivo: entrego_tarde

Esta variable convierte el retraso en una etiqueta para machine learning.

```python
entrego_tarde = 1 si dias_retraso > 0
entrego_tarde = 0 si dias_retraso <= 0
```

Esta es la variable que el modelo aprende a predecir.

### 17.3 Tasa de retraso

La tasa de retraso mide que porcentaje de pedidos llegaron tarde.

```text
tasa_retraso = pedidos_tardios / total_pedidos
```

En codigo:

```python
late_rate = data["entrego_tarde"].mean()
```

Esto funciona porque `entrego_tarde` vale 1 para pedidos tardios y 0 para
pedidos a tiempo. El promedio de una variable 0/1 es igual al porcentaje de
casos positivos.

Ejemplo:

```text
100 pedidos
7 llegaron tarde
tasa_retraso = 7 / 100 = 7%
```

### 17.4 Distancia aproximada

Esta distancia usa las coordenadas del vendedor y del cliente.

```python
distancia_aprox = sqrt(
    (seller_lat - customer_lat) ** 2
    + (seller_lng - customer_lng) ** 2
)
```

Sirve como proxy de distancia logistica. No es distancia real por carretera,
pero ayuda al modelo a entender si vendedor y cliente estan cerca o lejos.

### 17.5 Distancia Haversine en kilometros

Esta formula calcula una distancia mas interpretable entre dos puntos de la
Tierra usando latitud y longitud.

```python
distancia_km_haversine
```

En el codigo se usa:

```python
radius_km = 6371.0
```

Ese valor representa el radio promedio de la Tierra en kilometros.

Esta distancia se usa en el dashboard porque es mas facil de explicar:

```text
La ruta tiene aproximadamente 800 km.
```

### 17.6 Tiempo de aprobacion

Mide cuantas horas pasaron entre la compra y la aprobacion del pago.

```python
approval_time_hours = order_approved_at - order_purchase_timestamp
```

Si el pago tarda mucho en aprobarse, puede afectar el inicio del proceso
logistico.

### 17.7 Precio promedio

```text
avg_price = total_price / item_count
```

Sirve para saber el precio promedio por item dentro del pedido.

### 17.8 Flete promedio

```text
avg_freight = total_freight / item_count
```

Sirve para analizar si el costo logistico por item es alto o bajo.

### 17.9 Valor total de pago

Cuando el usuario no envia el valor de pago, la API lo estima asi:

```text
payment_value = total_price + total_freight
```

Esto representa el valor pagado por productos mas envio.

### 17.10 Probabilidad de retraso

El modelo calcula una probabilidad usando:

```python
probability = model.predict_proba(X)[0, 1]
```

Significado:

- `X`: datos del pedido.
- `[0, 1]`: probabilidad de la clase 1.
- Clase 1 significa `entrego_tarde = 1`.

Ejemplo:

```text
probability = 0.72
```

Significa que el modelo estima 72% de probabilidad de retraso.

### 17.11 Nivel de riesgo

El sistema convierte la probabilidad en una categoria:

```python
if probability >= risk_thresholds["high"]:
    risk_level = "alto"
elif probability >= risk_thresholds["medium"]:
    risk_level = "medio"
else:
    risk_level = "bajo"
```

En los resultados actuales:

```text
Riesgo medio desde: 0.6418
Riesgo alto desde: 0.6918
```

Esto significa:

- Menor a 64.18%: riesgo bajo.
- Desde 64.18% hasta menos de 69.18%: riesgo medio.
- Desde 69.18% o mas: riesgo alto.

## 18. Explicacion de cada grafico del dashboard

### 18.1 Evolucion mensual de pedidos, retrasos y alertas

Este es el grafico que aparece en la imagen.

Muestra tres elementos:

- Barras azules: cantidad de pedidos por mes.
- Linea naranja: tasa real de retraso.
- Linea verde: tasa de alertas generadas por el modelo.

El calculo se hace agrupando los pedidos por mes:

```python
monthly = data.assign(
    order_month=data["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
).groupby("order_month").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean"),
    alert_rate=("risk_level_model", lambda value: (value != "Bajo").mean()),
)
```

Formula de pedidos:

```text
pedidos_mes = cantidad de order_id en el mes
```

Formula de retraso real:

```text
retraso_real_mes = pedidos_tardios_mes / pedidos_totales_mes
```

Formula de alertas del modelo:

```text
alertas_modelo_mes = pedidos_riesgo_medio_o_alto_mes / pedidos_totales_mes
```

Como explicarlo:

> Este grafico permite comparar el volumen mensual de pedidos contra el
> comportamiento de retrasos reales y alertas del modelo. Las barras muestran
> cuantos pedidos hubo cada mes. La linea naranja muestra que porcentaje llego
> tarde realmente. La linea verde muestra que porcentaje fue marcado por el
> modelo como riesgo medio o alto.

### 18.2 Distribucion de pedidos por nivel de riesgo

Este grafico muestra cuantos pedidos hay en cada grupo:

- Bajo.
- Medio.
- Alto.

Calculo:

```python
data.groupby("risk_level_model").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean")
)
```

Formula:

```text
pedidos_por_riesgo = cantidad de pedidos en cada nivel
tasa_retraso_por_riesgo = pedidos_tardios_del_nivel / pedidos_totales_del_nivel
```

Como explicarlo:

> Este grafico ayuda a ver como se reparte la carga operativa. Si hay muchos
> pedidos en riesgo medio o alto, el equipo logistico tiene una cola mas grande
> para revisar.

### 18.3 Rutas que requieren atencion

Esta tabla muestra combinaciones de estado vendedor y estado cliente con mayor
riesgo.

Calculo:

```python
filtered_df.groupby(["seller_state_label", "customer_state_label"]).agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean"),
    avg_distance_km=("distancia_km_haversine", "mean"),
    avg_probability=("delay_probability", "mean"),
)
```

Formulas:

```text
pedidos_ruta = cantidad de pedidos en la ruta
tasa_retraso_ruta = pedidos_tardios_ruta / pedidos_totales_ruta
distancia_promedio = promedio de distancia_km_haversine
probabilidad_promedio = promedio de delay_probability
```

Como explicarlo:

> Esta tabla identifica rutas logisticas problematicas. Por ejemplo, si una ruta
> entre dos estados tiene muchos pedidos y alta tasa de retraso, debe revisarse
> la capacidad logistica, transportista o promesa de entrega.

### 18.4 Cola operativa de pedidos en riesgo

Esta tabla lista los pedidos que el modelo considera mas urgentes.

Calculo:

```python
data.loc[data["risk_level_model"].isin(["Medio", "Alto"])]
    .sort_values("delay_probability", ascending=False)
    .head(25)
```

Formula:

```text
cola_operativa = pedidos con riesgo medio o alto ordenados por probabilidad
```

Como explicarlo:

> Esta es la vista mas operativa. Sirve como lista diaria para que el equipo
> logistico revise primero los pedidos con mayor probabilidad de retraso.

### 18.5 Carga operativa por nivel de riesgo

Es un grafico tipo dona o pie que muestra cuantos pedidos hay en cada nivel de
riesgo.

Calculo:

```python
filtered_df.groupby("risk_level_model").agg(
    orders=("order_id", "count")
)
```

Formula:

```text
porcentaje_nivel = pedidos_del_nivel / total_pedidos
```

Como explicarlo:

> Este grafico resume la carga de trabajo. Permite saber que porcentaje de
> pedidos esta en bajo, medio o alto riesgo.

### 18.6 Mapa coropletico de Brasil

El mapa colorea los estados de Brasil segun la metrica seleccionada.

Puede mostrar:

- Tasa de retraso.
- Probabilidad promedio.
- Cantidad de pedidos.
- Tasa de riesgo alto.

Calculo:

```python
state_summary = data.groupby([state_column, label_column]).agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean"),
    avg_probability=("delay_probability", "mean"),
    high_risk_rate=("risk_level_model", lambda value: (value == "Alto").mean()),
    avg_distance_km=("distancia_km_haversine", "mean"),
)
```

Formulas:

```text
tasa_retraso_estado = pedidos_tardios_estado / pedidos_totales_estado
probabilidad_promedio_estado = promedio de delay_probability
tasa_riesgo_alto_estado = pedidos_alto_riesgo_estado / pedidos_totales_estado
```

Como explicarlo:

> El mapa permite detectar regiones con mayor concentracion de riesgo o retraso.
> Se puede analizar desde el punto de vista del cliente o del vendedor.

### 18.7 Estados destino con mayor tasa de retraso

Este grafico muestra los estados del cliente con mayor tasa de retraso.

Calculo:

```python
data.groupby("customer_state_label").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean"),
    avg_distance=("distancia_km_haversine", "mean"),
)
```

Formula:

```text
tasa_retraso_estado_cliente = pedidos_tardios_estado / pedidos_totales_estado
```

Como explicarlo:

> Este grafico ayuda a identificar estados destino donde las entregas tienen
> mas problemas. Puede indicar rutas lejanas, baja cobertura logistica o
> promesas de entrega poco realistas.

### 18.8 Categorias: volumen, retraso y satisfaccion

Este grafico relaciona tres dimensiones:

- Volumen de pedidos.
- Tasa de retraso.
- Calificacion promedio.

Calculo:

```python
data.groupby("product_category_name_english").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean"),
    avg_review_score=("review_score", "mean"),
    avg_delay_days=("dias_retraso", "mean"),
)
```

Formulas:

```text
pedidos_categoria = cantidad de pedidos de la categoria
tasa_retraso_categoria = pedidos_tardios_categoria / pedidos_totales_categoria
review_promedio = promedio de review_score
dias_retraso_promedio = promedio de dias_retraso
```

Como explicarlo:

> Este grafico permite encontrar categorias problematicas. Una categoria con
> mucho volumen, alta tasa de retraso y bajo review score deberia ser priorizada
> por el negocio.

### 18.9 Satisfaccion promedio por categoria

Este grafico muestra las categorias con menor calificacion promedio.

Calculo:

```python
data.groupby("product_category_name_english").agg(
    orders=("order_id", "count"),
    avg_review_score=("review_score", "mean"),
    late_rate=("entrego_tarde", "mean"),
)
```

Formula:

```text
review_promedio_categoria = suma de reviews / cantidad de reviews
```

Como explicarlo:

> Este grafico conecta logistica con experiencia del cliente. Si una categoria
> tiene baja calificacion y alta tasa de retraso, el retraso puede estar
> afectando la satisfaccion.

### 18.10 Riesgo real por banda de distancia

Este grafico divide los pedidos en grupos de distancia y calcula la tasa de
retraso de cada grupo.

Calculo:

```python
distance_data["distance_band"] = pd.qcut(
    distance_data["distancia_km_haversine"],
    q=5
)
```

Luego:

```python
distance_summary = distance_data.groupby("distance_band").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean")
)
```

Formula:

```text
tasa_retraso_banda = pedidos_tardios_en_banda / pedidos_totales_en_banda
```

Como explicarlo:

> Este grafico muestra si los pedidos mas lejanos tienen mayor riesgo de
> retraso. Ayuda a validar la importancia de la distancia logistica.

### 18.11 Retraso por tipo de pago

Este grafico compara la tasa de retraso segun el tipo de pago.

Calculo:

```python
data.groupby("payment_type").agg(
    orders=("order_id", "count"),
    late_rate=("entrego_tarde", "mean")
)
```

Formula:

```text
tasa_retraso_pago = pedidos_tardios_tipo_pago / pedidos_totales_tipo_pago
```

Como explicarlo:

> Este grafico permite ver si algun metodo de pago esta asociado con mas
> retrasos. Por ejemplo, un pago que tarda mas en aprobarse podria retrasar el
> inicio del despacho.

### 18.12 Variables mas influyentes

Este grafico muestra que variables fueron mas importantes para el modelo.

Calculo:

```python
feature_importances_
```

En modelos de arboles, la importancia mide cuanto aporta cada variable a separar
mejor los casos de pedidos tardios y no tardios.

Como explicarlo:

> Este grafico ayuda a interpretar el modelo. Permite ver si el riesgo esta
> explicado por variables logisticas, geograficas, temporales o comerciales.

### 18.13 Matriz de confusion

La matriz de confusion compara lo que paso realmente contra lo que predijo el
modelo.

Tiene cuatro valores:

```text
True Negative: pedido era a tiempo y el modelo dijo a tiempo.
False Positive: pedido era a tiempo, pero el modelo genero alerta.
False Negative: pedido llego tarde, pero el modelo no lo alerto.
True Positive: pedido llego tarde y el modelo lo alerto.
```

En los resultados actuales:

```text
True Negative: 16,377
False Positive: 1,610
False Negative: 822
True Positive: 485
```

Como explicarlo:

> La matriz de confusion permite ver los aciertos y errores. En este proyecto,
> un falso positivo significa revisar un pedido que finalmente no se retraso.
> Un falso negativo es mas grave, porque significa que un pedido llego tarde y
> el sistema no lo detecto.

### 18.14 Simulador operativo de riesgo

El simulador permite ingresar datos de un pedido nuevo.

El usuario selecciona:

- Estado del vendedor.
- Estado del cliente.
- Categoria.
- Tipo de pago.
- Cantidad de items.
- Precio.
- Flete.
- Distancia.
- Peso.
- Volumen.
- Mes y dia de compra.

El sistema construye una fila con esas variables:

```python
row = bundle["baseline_values"].copy()
row.update(values)
```

Luego calcula:

```python
probability = model.predict_proba(row)[0, 1]
```

Y muestra:

- Probabilidad de retraso.
- Nivel de riesgo.
- Acciones recomendadas.

Como explicarlo:

> El simulador convierte el modelo en una herramienta practica. Permite probar
> escenarios y ver como cambia el riesgo si cambia la ruta, categoria, flete o
> distancia.

## 19. Guion corto para exposicion

Mi proyecto es un sistema de alerta temprana para pedidos de Olist. El objetivo
es predecir que pedidos tienen riesgo de llegar tarde antes de que ocurra el
problema.

Para eso use datos historicos de pedidos, clientes, vendedores, productos,
pagos, reviews y geolocalizacion. Primero construi un dataset maestro uniendo
varias tablas. Luego calcule la variable objetivo `entrego_tarde`, comparando
la fecha real de entrega contra la fecha estimada. Si la entrega real fue
despues de la estimada, el pedido se marca como tardio.

Despues entrene modelos de machine learning usando variables como estado del
vendedor, estado del cliente, categoria del producto, tipo de pago, precio,
flete, peso, volumen, mes de compra y distancia entre vendedor y cliente.

Probe Random Forest y Gradient Boosting. El mejor modelo fue Gradient Boosting,
con un ROC AUC de 0.742. Como solo 6.77% de los pedidos llegan tarde, el modelo
se usa como herramienta de priorizacion, no como decision automatica.

Finalmente construi una API con FastAPI para consultar el riesgo de un pedido
nuevo y un dashboard con Streamlit para visualizar KPIs, rutas criticas,
categorias de riesgo, mapa por estados y un simulador operativo.

El valor de negocio es que Olist puede anticiparse a retrasos, priorizar pedidos
criticos, contactar vendedores o transportistas y mejorar la experiencia del
cliente.

## 20. Cierre recomendado

En conclusion, este proyecto convierte datos historicos de e-commerce en una
herramienta practica de decision logistica. No solo predice una probabilidad,
sino que transforma esa prediccion en acciones operativas para reducir retrasos
y mejorar la satisfaccion del cliente.

## 21. Exposicion dividida para Kevin, Paulo y Sebastian

### Kevin: contexto, datos y modelo

**Tema principal:** explicar el negocio, el problema, los datos usados y el
modelo de machine learning.

Guion:

> Buenos dias. Nuestro proyecto se llama OLIST Delay Alert System. Es un
> sistema de alerta temprana para predecir que pedidos de e-commerce tienen
> riesgo de llegar tarde.

> El caso se basa en Olist, un marketplace de Brasil. En este modelo de negocio,
> muchos vendedores ofrecen productos y muchos clientes compran en la
> plataforma. Olist conecta al vendedor con el cliente y ayuda a gestionar el
> pedido, el pago y la experiencia de compra.

> El problema principal aparece en la entrega. Si un pedido llega despues de la
> fecha estimada, el cliente puede reclamar, dejar una mala calificacion o perder
> confianza en la plataforma.

> Por eso la pregunta de negocio es: que pedidos tienen mayor riesgo de llegar
> tarde y necesitan seguimiento logistico prioritario?

> Para responder esa pregunta usamos datos historicos de Olist. El proyecto usa
> tablas de pedidos, clientes, vendedores, productos, pagos, reviews y
> geolocalizacion.

> Primero construimos un dataset maestro. Unimos la informacion del pedido con
> el cliente, vendedor, producto, pago, resena y coordenadas geograficas.

> La variable principal se llama `entrego_tarde`. Para calcularla comparamos la
> fecha real de entrega con la fecha estimada. Si la fecha real fue despues de
> la estimada, el pedido se marca como tardio.

Formula que puede explicar:

```text
dias_retraso = fecha_real_entrega - fecha_estimada_entrega

si dias_retraso > 0:
    entrego_tarde = 1
si dias_retraso <= 0:
    entrego_tarde = 0
```

> Tambien calculamos variables como distancia entre vendedor y cliente, precio,
> flete, peso, volumen, tipo de pago, categoria del producto, mes de compra y
> tiempo de aprobacion del pago.

> Con esto dejamos lista la base para que el modelo aprenda patrones de pedidos
> que llegaron tarde y pedidos que llegaron a tiempo.

> Despues entrenamos modelos de machine learning para estimar la probabilidad
> de retraso de un pedido. Este es un problema de clasificacion binaria, porque
> solo tenemos dos posibles resultados: llego tarde o no llego tarde.

> Probamos dos modelos: Random Forest y Gradient Boosting. Random Forest combina
> muchos arboles de decision independientes y toma una decision conjunta.
> Gradient Boosting tambien usa arboles, pero los construye de forma secuencial:
> cada arbol intenta corregir los errores del anterior.

> El mejor modelo fue Gradient Boosting. Lo usamos porque funciona bien con
> datos tabulares como estados, categorias, pagos, precios, fletes, distancias y
> fechas. Ademas puede capturar relaciones complejas entre variables logisticas,
> comerciales y geograficas.

> El modelo devuelve una probabilidad de retraso. Por ejemplo, si devuelve 0.70,
> significa que, segun los patrones historicos, ese pedido tiene 70% de
> probabilidad estimada de llegar tarde.

> Luego esa probabilidad se convierte en un nivel de riesgo: bajo, medio o alto.
> Es importante aclarar que el modelo no adivina el futuro exactamente, sino que
> compara pedidos nuevos con patrones aprendidos de pedidos historicos.

Transicion para la siguiente persona:

> Ahora Paulo explicara las metricas, los resultados y los graficos principales
> del analisis.

### Paulo: metricas, resultados y graficos

**Tema principal:** explicar como se evaluo el modelo, que significan las
metricas y como leer los graficos del dashboard.

Guion:

> Para evaluar el modelo separamos los datos en entrenamiento y prueba. El
> modelo aprende con una parte de los datos y luego se prueba con datos que no
> habia visto.

Resultados que debe mencionar:

```text
Dataset: 96,470 pedidos
Pedidos tardios: 6,534
Tasa historica de retraso: 6.77%
Mejor modelo: Gradient Boosting
Precision: 23.15%
Recall: 37.11%
F1: 0.285
ROC AUC: 0.742
Tasa de alertas: 10.86%
```

> El dataset esta desbalanceado, porque solo 6.77% de los pedidos llegaron
> tarde. Por eso no buscamos que el modelo tome una decision automatica final,
> sino que ayude a priorizar una cola de seguimiento logistico.

Explicacion de metricas:

```text
Precision:
de todas las alertas que genero el modelo, cuantas realmente eran pedidos
tardios.

Recall:
de todos los pedidos que realmente llegaron tarde, cuantos logro detectar el
modelo.

F1:
balance entre precision y recall.

ROC AUC:
capacidad del modelo para separar pedidos con mas riesgo de pedidos con menos
riesgo.
```

> Las variables mas importantes fueron el mes de compra, la distancia en
> kilometros, el estado del cliente, el flete promedio, el tiempo de aprobacion
> y el estado del vendedor. Esto tiene sentido porque el retraso depende de la
> ruta, el momento de compra y las condiciones logisticas.

Grafico principal:

> En el grafico de evolucion mensual, las barras muestran la cantidad de pedidos
> por mes. La linea naranja muestra la tasa real de retrasos y la linea verde
> muestra las alertas del modelo. Este grafico sirve para comparar el volumen de
> pedidos con los retrasos reales y ver si el modelo detecta periodos de mayor
> riesgo.

Formulas del grafico:

```text
Pedidos del mes = cantidad de pedidos registrados en ese mes

Retraso real = pedidos tardios del mes / total de pedidos del mes

Alertas modelo = pedidos con riesgo medio o alto / total de pedidos del mes
```

> Tambien tenemos graficos por categoria, por estado, por distancia y por tipo
> de pago. Estos graficos ayudan a entender donde se concentran los retrasos:
> si vienen de ciertas rutas, ciertos estados, ciertas categorias o pedidos mas
> lejanos.

Transicion para la siguiente persona:

> Ahora Sebastian explicara como se usa el modelo dentro de la API, el dashboard
> y el simulador.

### Sebastian: API, dashboard, simulador y valor final

**Tema principal:** explicar la herramienta final, como se consulta el modelo,
como funciona el dashboard y cual es el valor para el negocio.

Guion:

> Una vez entrenado el modelo, lo convertimos en una herramienta practica usando
> una API y un dashboard.

> La API esta hecha con FastAPI. Permite enviar los datos de un pedido nuevo y
> recibir la probabilidad de retraso, el nivel de riesgo y una recomendacion
> operativa.

Endpoint principal:

```text
POST /orders/delay_risk
```

Ejemplo:

```json
{
  "seller_state": "SP",
  "customer_state": "BA",
  "product_category_name_english": "furniture_decor",
  "payment_type": "credit_card",
  "total_price": 120.0,
  "total_freight": 25.0
}
```

> La respuesta indica si el riesgo es bajo, medio o alto. Si el riesgo es alto,
> el sistema recomienda priorizar seguimiento logistico, validar despacho con el
> vendedor y preparar comunicacion preventiva para el cliente.

> Tambien construimos un dashboard en Streamlit. El dashboard muestra KPIs,
> graficos, rutas criticas, categorias con mayor riesgo, mapa de Brasil y un
> simulador.

> El dashboard tambien muestra rutas que requieren atencion. Esa tabla agrupa
> por estado del vendedor y estado del cliente para encontrar rutas con alta
> tasa de retraso.

> El mapa de Brasil permite ver que estados tienen mas retraso o mayor
> probabilidad promedio.

> Los graficos por categoria permiten identificar productos que generan mas
> riesgo logistico o menor satisfaccion.

> La cola operativa muestra los pedidos de riesgo medio y alto ordenados por
> probabilidad. Esta es la parte mas util para el negocio, porque funciona como
> una lista diaria de seguimiento.

> Finalmente, el simulador permite ingresar un pedido futuro y calcular su
> riesgo. El modelo no adivina el futuro, sino que compara el pedido nuevo con
> patrones historicos.

Cierre:

> En conclusion, este proyecto convierte datos historicos de e-commerce en una
> herramienta practica de decision logistica. No solo calcula una probabilidad,
> sino que transforma esa prediccion en acciones concretas para reducir retrasos
> y mejorar la experiencia del cliente.

## 22. Reparto rapido si tienen poco tiempo

Si la exposicion debe ser corta, pueden dividirla asi:

```text
Kevin:
Problema de negocio, Olist, datos usados, variable entrego_tarde y modelo.

Paulo:
Metricas, resultados, variables importantes y explicacion de graficos.

Sebastian:
API, dashboard, simulador, recomendaciones, valor para el negocio y cierre.
```

## 23. Orden recomendado de presentacion

1. Kevin abre con el contexto, los datos y el modelo.
2. Paulo explica metricas, resultados y graficos.
3. Sebastian muestra la herramienta final y cierra con el valor de negocio.
