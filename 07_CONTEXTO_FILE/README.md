# Proyecto Seminario: Caso 09 - E-Commerce OLIST Brasil

## Descripcion

Proyecto desarrollado para construir un sistema predictivo de alertas de
entrega sobre el dataset publico de OLIST Brasil.

El proyecto integra varias tablas del negocio, construye un dataset maestro,
entrena modelos de clasificacion con scikit-learn y expone el resultado como
producto analitico mediante una API y un dashboard.

## Contexto del problema

OLIST es un marketplace de e-commerce de Brasil. En un marketplace, distintos
vendedores ofrecen productos y distintos clientes realizan compras en la misma
plataforma.

El dataset contiene informacion historica de pedidos, clientes, productos,
vendedores, pagos, resenas, items y geolocalizacion.

Las entregas tardias generan costos importantes para la plataforma:

- Reputacional: malas resenas y perdida de confianza del cliente.
- Operativo: reclamos, atencion reactiva y posibles compensaciones.
- Logistico: necesidad de revisar rutas, vendedores o categorias con problemas.

Por eso, el proyecto busca anticipar el riesgo de retraso antes de que el pedido
llegue tarde.

## Objetivo del proyecto

Construir un sistema predictivo que estime si un pedido de OLIST puede llegar
tarde a su destino.

El sistema debe permitir:

1. Analizar los pedidos historicos.
2. Calcular la variable de retraso.
3. Entrenar un modelo de clasificacion.
4. Consultar el riesgo de retraso para pedidos nuevos o simulados.
5. Visualizar resultados en un dashboard.
6. Exponer predicciones mediante una API.

## Pregunta de negocio

Es posible predecir, al momento de confirmar un pedido, si este tiene riesgo de
llegar tarde?

Tambien se busca entender que factores del vendedor, cliente, producto, pago y
ruta geografica aumentan ese riesgo.

## Variables clave

dias_retraso
Fecha real de entrega menos fecha estimada de entrega.

entrego_tarde
Variable objetivo del modelo. Vale 1 si el pedido llego tarde y 0 si llego a
tiempo o antes.

distancia_aprox
Distancia aproximada entre vendedor y cliente usando coordenadas geograficas.

seller_state
Estado de Brasil donde esta ubicado el vendedor.

customer_state
Estado de Brasil donde esta ubicado el cliente.

product_category_name_english
Categoria del producto.

payment_type
Tipo de pago utilizado por el cliente.

## Historias de usuario

### HU-01: Alerta proactiva al cliente

Como cliente de OLIST que acaba de realizar un pedido, quiero recibir una alerta
cuando exista alta probabilidad de que mi entrega se retrase, para poder
organizarme con anticipacion.

Criterios de aceptacion:

- El sistema evalua el riesgo de retraso usando datos del pedido.
- Si la probabilidad supera un umbral, el pedido se marca como riesgo medio o alto.
- La alerta permite actuar antes de que el cliente reclame.

### HU-02: Analisis de riesgo por categoria y estado

Como analista de logistica de OLIST, quiero visualizar que categorias de
producto y que estados presentan mayor tasa historica de retrasos, para
priorizar acciones de mejora.

Criterios de aceptacion:

- El dashboard muestra tasa de retraso por estado del cliente.
- El dashboard muestra categorias con menor satisfaccion promedio.
- El analista puede identificar patrones logisticos relevantes.

### HU-03: Prediccion bajo demanda

Como coordinador de logistica, quiero ingresar datos de un pedido nuevo y
obtener la probabilidad de retraso, para tomar decisiones operativas antes de
que el problema ocurra.

Criterios de aceptacion:

- El formulario acepta estado del vendedor, estado del cliente, categoria,
tipo de pago, precio, flete y cuotas.
- El sistema devuelve probabilidad de retraso.
- El sistema clasifica el riesgo como bajo, medio o alto.
- La API devuelve el resultado en formato JSON.

## Ficha del dataset

Nombre:
Brazilian E-Commerce Public Dataset by Olist

Fuente:
Kaggle - olistbr/brazilian-ecommerce

Periodo:
Septiembre 2016 a agosto 2018

Volumen:
Aproximadamente 100,000 pedidos

Idioma original:
Portugues de Brasil

Archivo original:
06_archivo/archive.zip

## Tablas usadas

El archivo comprimido contiene 9 CSV. El caso principal habla de 8 tablas
relacionales; la novena tabla corresponde a la traduccion de categorias.

olist_orders_dataset.csv
Pedidos con fechas, estado y cliente.

olist_order_items_dataset.csv
Items por pedido, precio, flete, producto y vendedor.

olist_customers_dataset.csv
Clientes con ciudad, estado y codigo postal.

olist_products_dataset.csv
Productos con categoria, peso y dimensiones.

olist_sellers_dataset.csv
Vendedores con ciudad, estado y codigo postal.

olist_order_reviews_dataset.csv
Resenas y calificaciones de satisfaccion.

olist_order_payments_dataset.csv
Metodos de pago, cuotas y valor pagado.

olist_geolocation_dataset.csv
Coordenadas por codigo postal.

product_category_name_translation.csv
Traduccion de categorias de portugues a ingles.

## Relacion entre tablas

orders -> customers
orders -> items -> products -> category_translation
items -> sellers
orders -> reviews
orders -> payments
customers -> geolocation
sellers -> geolocation

## Justificacion de joins

orders -> customers:
Left join para conservar pedidos aunque falte informacion del cliente.

orders -> items:
Inner join porque el modelo necesita pedidos con productos asociados.

items -> products:
Left join para no perder items con metadatos incompletos.

items -> sellers:
Left join para agregar el origen logistico del vendedor.

orders -> reviews:
Left join porque no todos los pedidos tienen resena.

orders -> payments:
Left join porque el pago agrega senales comerciales sin eliminar pedidos.

customers/sellers -> geolocation:
Left join porque algunas coordenadas pueden faltar.

## Estructura del proyecto

00_datos_crudos/       Datos originales OLIST en CSV.
01_datos_procesados/   Dataset maestro en formato parquet.
02_scripts/            Scripts de preparacion, entrenamiento, API y dashboard.
03_cuadernos/          Espacio para notebooks de analisis exploratorio.
04_resultados/         Modelo, metricas y resultados generados.
05_referencias/        Plan de preparacion y documentacion.
06_archivo/            Archivo comprimido original.
07_CONTEXTO_FILE/      Contexto del negocio, desafio y README.

## Como ejecutar

Instalar dependencias:

pip install -r 02_scripts/requirements.txt

Construir el dataset maestro:

python 02_scripts/build_dataset.py

Entrenar modelos:

python 02_scripts/train_model.py

Levantar dashboard:

streamlit run 02_scripts/dashboard.py

Levantar API:

uvicorn api:app --app-dir 02_scripts --reload

Abrir documentacion de API:

http://127.0.0.1:8000/docs

## Salida del dataset maestro

Al ejecutar `build_dataset.py`, el proyecto genera:

01_datos_procesados/master_dataset.parquet

Salida actual:

Filas: 98,666
Columnas: 37
Pedidos tardios: 6,535
Pedidos a tiempo o antes: 92,131
Tasa de entregas tardias: 6.62%

## Entrenamiento y resultados

El script `02_scripts/train_model.py` compara dos modelos:

random_forest
gradient_boosting

El mejor modelo actual es:

gradient_boosting

Metricas actuales del mejor modelo:

precision: 0.1431
recall: 0.6236
f1: 0.2328
roc_auc: 0.7369

Interpretacion:

- El dataset esta desbalanceado: solo 6.62% de pedidos llegaron tarde.
- El modelo detecta una parte importante de los pedidos tardios.
- La precision es baja, por lo que puede generar falsas alertas.
- El resultado sirve como alerta temprana, no como verdad absoluta.

## Entregables generados

01_datos_procesados/master_dataset.parquet
04_resultados/delay_model.pkl
04_resultados/metrics.json
04_resultados/feature_importance.csv
04_resultados/category_risk.csv
02_scripts/api.py
02_scripts/dashboard.py

## Endpoints

GET /

Devuelve informacion basica del servicio.

POST /orders/delay_risk

Calcula la probabilidad de retraso para un pedido.

Ejemplo de entrada:

{
  "seller_state": "SP",
  "customer_state": "BA",
  "product_category_name_english": "furniture_decor"
}

GET /orders/top_risk_categories

Devuelve categorias con mayor tasa historica de retraso.

## Uso esperado del sistema

1. Cargar y preparar datos historicos.
2. Entrenar el modelo.
3. Revisar metricas y resultados.
4. Usar el dashboard para analisis visual.
5. Usar el simulador para probar pedidos nuevos.
6. Usar la API para consultar riesgo desde otros sistemas.

## Resumen

Este proyecto convierte datos historicos de OLIST en un sistema analitico para
predecir riesgo de retraso. El valor principal esta en anticipar problemas
logisticos antes de que afecten al cliente.
