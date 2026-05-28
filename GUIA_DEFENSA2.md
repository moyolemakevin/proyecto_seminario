# Guia de defensa - OLIST Delay Alert System

Este documento resume las preguntas y respuestas clave para defender el proyecto.
Esta pensado para estudiar rapido y responder con seguridad.

## 1. Idea general del proyecto

### Cual es el problema?

El problema principal es que Olist no sabe anticipadamente que pedidos tienen
mayor riesgo de llegar tarde.

Normalmente la empresa se entera del problema cuando el cliente reclama o
cuando el pedido ya se retraso. El proyecto busca anticiparse a ese problema.

Respuesta para defensa:

> El problema de negocio es que los retrasos logisticos afectan la satisfaccion
> del cliente. Si un pedido llega despues de la fecha estimada, el cliente puede
> reclamar, dejar una mala calificacion o perder confianza en la plataforma.
> Por eso necesitamos un sistema que permita anticipar que pedidos tienen mayor
> riesgo de retrasarse.

Pregunta central:

```text
Que pedidos tienen mayor riesgo de llegar tarde y requieren seguimiento
logistico prioritario?
```

### Cual es la solucion?

La solucion es un sistema de alerta temprana que usa datos historicos de Olist
para calcular la probabilidad de retraso de un pedido.

El sistema devuelve:

```text
- Probabilidad de retraso
- Nivel de riesgo: bajo, medio o alto
- Recomendacion operativa
- Acciones sugeridas
```

Frase clave:

> El sistema no reemplaza al equipo logistico, sino que ayuda a priorizar que
> pedidos deben revisarse primero.

## 2. Herramientas utilizadas

```text
Python
```

Lenguaje principal del proyecto. Se uso para procesar datos, entrenar el modelo,
crear la API y construir el dashboard.

```text
Pandas
```

Se uso para leer CSV, limpiar datos, unir tablas y construir el dataset maestro.

```text
NumPy
```

Se uso para calculos numericos, especialmente distancia Haversine y operaciones
matematicas.

```text
Scikit-learn
```

Se uso para machine learning: imputacion, codificacion de variables, pipelines,
entrenamiento de modelos y metricas.

```text
Joblib
```

Se uso para guardar y cargar el modelo entrenado en formato `.pkl`.

```text
FastAPI
```

Se uso para crear la API que recibe datos de un pedido y devuelve el riesgo de
retraso.

```text
Pydantic
```

Se uso para validar los datos de entrada de la API.

```text
Uvicorn
```

Se uso para levantar la API localmente.

```text
Streamlit
```

Se uso para crear el dashboard interactivo.

```text
Plotly
```

Se uso para crear graficos interactivos dentro del dashboard.

```text
CSV
```

Formato de los datos crudos originales de Olist.

```text
Parquet
```

Formato usado para guardar el dataset maestro procesado.

Respuesta para defensa:

> Las herramientas usadas fueron Python como lenguaje principal, Pandas y NumPy
> para procesamiento de datos, Scikit-learn para machine learning, FastAPI para
> publicar el modelo como API, Streamlit y Plotly para el dashboard interactivo,
> y Joblib para guardar el modelo entrenado.

## 3. Base de datos y archivos

### El proyecto tiene base de datos?

Si, pero no es una base de datos tradicional como MySQL o PostgreSQL.

El proyecto trabaja con archivos historicos:

```text
00_datos_crudos/
```

Archivos principales:

```text
olist_orders_dataset.csv
olist_customers_dataset.csv
olist_order_items_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_geolocation_dataset.csv
product_category_name_translation.csv
```

Luego el codigo genera:

```text
01_datos_procesados/master_dataset.parquet
```

Respuesta para defensa:

> El proyecto no usa una base de datos relacional como MySQL. Trabaja con
> archivos CSV historicos de Olist, y mediante programacion se construye un
> dataset maestro en formato Parquet. Ese archivo funciona como la base de datos
> procesada del sistema.

### Que es Parquet?

`.parquet` es un formato de archivo para guardar datos tabulares, parecido a CSV,
pero mas eficiente.

Comparacion:

```text
CSV:
- Texto plano
- Facil de abrir
- Mas pesado
- Mas lento con muchos datos

Parquet:
- Optimizado para analisis
- Mas liviano
- Mas rapido
- Conserva mejor los tipos de datos
```

Respuesta para defensa:

> Parquet es como nuestro CSV final optimizado. Contiene todos los datos ya
> limpios, unidos y listos para el modelo.

## 4. Comandos para iniciar el sistema

Abrir PowerShell en el proyecto:

```powershell
cd C:\xampp\htdocs\proyecto_seminario
```

Instalar dependencias:

```powershell
pip install -r 02_scripts/requirements.txt
```

Construir dataset:

```powershell
python 02_scripts/build_dataset.py
```

Entrenar modelo:

```powershell
python 02_scripts/train_model.py
```

Levantar API:

```powershell
uvicorn api:app --app-dir 02_scripts --reload
```

Abrir documentacion de la API:

```text
http://127.0.0.1:8000/docs
```

Levantar dashboard:

```powershell
streamlit run 02_scripts/dashboard.py
```

Abrir dashboard:

```text
http://localhost:8501
```

Frase para exposicion:

> Primero levanto la API con Uvicorn para publicar el modelo, y luego levanto el
> dashboard con Streamlit para visualizar los resultados.

## 4.1 Metodologia utilizada

### Que metodologia se usa en el proyecto?

El proyecto usa una metodologia analitica basada en el ciclo de vida de ciencia
de datos. Tambien puede explicarse como una version practica de CRISP-DM.

CRISP-DM significa:

```text
Cross Industry Standard Process for Data Mining
```

Es una metodologia comun para proyectos de analisis de datos y machine learning.

### Fases aplicadas en el proyecto

```text
1. Comprension del negocio
2. Comprension de los datos
3. Preparacion de los datos
4. Modelado
5. Evaluacion
6. Despliegue
```

### 1. Comprension del negocio

Se identifico el problema:

```text
Los retrasos logisticos afectan la satisfaccion del cliente.
```

Pregunta de negocio:

```text
Que pedidos tienen mayor riesgo de llegar tarde?
```

Respuesta para defensa:

> Primero se definio el problema de negocio: anticipar retrasos logisticos en
> pedidos de e-commerce para priorizar seguimiento operativo.

### 2. Comprension de los datos

Se revisaron los CSV de Olist:

```text
Pedidos
Clientes
Vendedores
Productos
Pagos
Resenas
Geolocalizacion
```

Respuesta:

> En esta fase se identifico que informacion tenia cada archivo y como podia
> aportar al analisis del retraso.

### 3. Preparacion de los datos

Se implemento en:

```text
02_scripts/build_dataset.py
```

Procesos:

```text
Leer CSV
Convertir fechas
Filtrar pedidos entregados
Unir tablas
Calcular dias de retraso
Crear variable entrego_tarde
Calcular distancia, precio, flete, peso y volumen
Guardar master_dataset.parquet
```

Respuesta:

> La preparacion de datos fue la fase mas importante, porque ahi se construyo el
> dataset maestro que luego alimenta el modelo.

### 4. Modelado

Se implemento en:

```text
02_scripts/train_model.py
```

Modelos probados:

```text
Random Forest
Gradient Boosting
```

Respuesta:

> En la fase de modelado se entrenaron dos algoritmos y se selecciono el mejor
> segun el F1 con umbral operativo.

### 5. Evaluacion

Metricas usadas:

```text
Precision
Recall
F1
ROC AUC
Average Precision
Matriz de confusion
```

Respuesta:

> La evaluacion se hizo con metricas adecuadas para datos desbalanceados, porque
> solo 6.77% de los pedidos llegaron tarde.

### 6. Despliegue

Se implemento con:

```text
FastAPI
Streamlit
```

Archivos:

```text
02_scripts/api.py
02_scripts/dashboard.py
```

Respuesta:

> Finalmente el modelo se desplego como una API para recibir pedidos nuevos y
> como un dashboard para visualizar indicadores y simular escenarios.

### Respuesta corta si preguntan metodologia

> La metodologia usada fue un flujo de ciencia de datos basado en CRISP-DM:
> primero se entendio el problema de negocio, luego se analizaron y prepararon
> los datos, despues se entreno y evaluo el modelo, y finalmente se desplego en
> una API y un dashboard.

## 4.2 Arquitectura del sistema

### Que arquitectura tiene el proyecto?

El proyecto tiene una arquitectura por capas.

```text
Capa de datos
Capa de procesamiento
Capa de machine learning
Capa de servicios API
Capa de visualizacion
Capa de reglas de negocio
```

### Diagrama simple

```text
CSV originales
      |
      v
build_dataset.py
      |
      v
master_dataset.parquet
      |
      v
train_model.py
      |
      v
delay_model.pkl + metrics.json
      |
      +-------------> api.py
      |
      +-------------> dashboard.py
```

### 1. Capa de datos

Carpetas:

```text
00_datos_crudos/
01_datos_procesados/
```

Funcion:

> Almacenar los datos originales y el dataset maestro procesado.

Archivos principales:

```text
CSV originales
master_dataset.parquet
```

### 2. Capa de procesamiento

Archivo:

```text
02_scripts/build_dataset.py
```

Funcion:

> Limpia, transforma y une los datos para crear el dataset maestro.

### 3. Capa de machine learning

Archivo:

```text
02_scripts/train_model.py
```

Salidas:

```text
04_resultados/delay_model.pkl
04_resultados/metrics.json
04_resultados/feature_importance.csv
04_resultados/category_risk.csv
```

Funcion:

> Entrena modelos, selecciona el mejor y guarda los artefactos necesarios para
> prediccion y evaluacion.

### 4. Capa de API

Archivo:

```text
02_scripts/api.py
```

Tecnologia:

```text
FastAPI
```

Funcion:

> Exponer el modelo como servicio para recibir datos de pedidos nuevos y
> devolver probabilidad, riesgo y acciones recomendadas.

Endpoint principal:

```text
POST /orders/delay_risk
```

### 5. Capa de visualizacion

Archivo:

```text
02_scripts/dashboard.py
```

Tecnologia:

```text
Streamlit + Plotly
```

Funcion:

> Mostrar indicadores, graficos, filtros, cola operativa y simulador de riesgo.

### 6. Capa de reglas de negocio

Archivo:

```text
02_scripts/business_rules.py
```

Funcion:

> Traducir el resultado del modelo a recomendaciones operativas segun riesgo
> bajo, medio o alto.

Ejemplo:

```text
Riesgo alto:
- Priorizar seguimiento logistico
- Validar despacho con vendedor y transportista
- Preparar comunicacion proactiva al cliente
```

### Por que se dice que es arquitectura por capas?

Porque cada parte tiene una responsabilidad diferente:

```text
Datos: almacenar informacion
Procesamiento: limpiar y unir
Modelo: aprender patrones
API: publicar predicciones
Dashboard: visualizar resultados
Reglas: convertir riesgo en acciones
```

Respuesta para defensa:

> La arquitectura esta separada por capas. Una capa gestiona los datos, otra
> prepara el dataset, otra entrena el modelo, otra publica la API y otra muestra
> el dashboard. Esta separacion ayuda a mantener el proyecto ordenado y facil de
> explicar.

### Arquitectura en una frase

> Es una arquitectura analitica por capas: datos historicos, procesamiento ETL,
> modelo predictivo, API de consulta y dashboard operativo.

## 5. Explicacion del archivo build_dataset.py

### Para que sirve build_dataset.py?

Sirve para construir el dataset maestro. Lee los CSV originales, limpia fechas,
une tablas, crea variables nuevas y guarda el resultado en Parquet.

Respuesta:

> Este archivo hace el proceso ETL: extrae los CSV, transforma los datos y carga
> el resultado en un dataset maestro.

### Que significa ETL?

```text
E = Extract: extraer datos desde archivos CSV
T = Transform: limpiar, unir y crear variables
L = Load: guardar el dataset procesado
```

### Que hace RAW_FILES?

Es un diccionario con los nombres de los archivos CSV requeridos.

```python
RAW_FILES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "items": "olist_order_items_dataset.csv",
}
```

Respuesta:

> RAW_FILES centraliza los nombres de los archivos para que el codigo sea mas
> ordenado y facil de mantener.

### Que hace read_csv()?

```python
def read_csv(name: str) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(...)
    return pd.read_csv(path)
```

Lee un archivo CSV y lo devuelve como DataFrame. Primero valida que el archivo
exista.

Respuesta:

> La funcion verifica que el archivo exista y luego lo carga con Pandas. Si falta
> un archivo, muestra un error claro.

### Que es un DataFrame?

Un DataFrame es una tabla de datos en Python, parecida a una hoja de Excel o una
tabla de base de datos.

### Por que se convierten las fechas?

El codigo convierte columnas de texto a fechas:

```python
orders[col] = pd.to_datetime(orders[col], errors="coerce")
```

Respuesta:

> Se convierten a fecha porque necesitamos restarlas para calcular dias de
> retraso y tiempo de aprobacion.

### Que hace errors="coerce"?

Si una fecha esta mal escrita o no se puede convertir, Pandas la deja como valor
nulo en vez de romper el programa.

### Por que se filtran solo pedidos delivered?

```python
orders["order_status"].eq("delivered")
```

Respuesta:

> Porque solo en pedidos entregados conocemos la fecha real de entrega. Sin esa
> fecha no podemos saber si el pedido llego tarde.

### Como se calcula el retraso?

```python
dias_retraso = fecha_real_entrega - fecha_estimada_entrega
```

En el codigo:

```python
supervised_orders["dias_retraso"] = (
    supervised_orders["order_delivered_customer_date"]
    - supervised_orders["order_estimated_delivery_date"]
).dt.days
```

Interpretacion:

```text
Si dias_retraso > 0: llego tarde
Si dias_retraso <= 0: llego a tiempo o antes
```

### Que es entrego_tarde?

Es la variable objetivo del modelo.

```python
supervised_orders["entrego_tarde"] = (
    supervised_orders["dias_retraso"] > 0
).astype(int)
```

Respuesta:

> `entrego_tarde` convierte el retraso en una etiqueta de machine learning. Vale
> 1 si el pedido llego tarde y 0 si llego a tiempo o antes.

### Que variables temporales se crean?

```text
approval_time_hours
purchase_month
purchase_dayofweek
purchase_hour
is_weekend
```

Explicacion:

```text
approval_time_hours: horas entre compra y aprobacion del pago
purchase_month: mes de compra
purchase_dayofweek: dia de la semana, 0 lunes y 6 domingo
purchase_hour: hora de compra
is_weekend: 1 si fue fin de semana, 0 si no
```

### Que hace prepare_products()?

Une productos con la tabla de traduccion y calcula volumen.

```python
product_volume_cm3 = length * height * width
```

Respuesta:

> Esta funcion traduce categorias de producto y calcula el volumen en centimetros
> cubicos.

### Que hace aggregate_items()?

Agrupa los productos por pedido y calcula:

```text
item_count
total_price
avg_price
total_freight
avg_freight
total_product_weight_g
avg_product_weight_g
max_product_volume_cm3
avg_product_volume_cm3
```

Respuesta:

> Esta funcion resume todos los items de un pedido en una sola fila, para que el
> modelo pueda trabajar a nivel de pedido.

### Por que se usa groupby("order_id")?

Porque un pedido puede tener varios productos. Se agrupan por `order_id` para
tener una sola fila por pedido.

### Por que se usa drop_duplicates("order_id")?

Se usa para elegir un registro principal por pedido, tomando el producto de mayor
precio como referencia principal.

### Que hace aggregate_reviews()?

Agrupa resenas por pedido:

```text
review_score: promedio de calificacion
review_count: cantidad de resenas
```

### Que hace aggregate_payments()?

Agrupa pagos por pedido:

```text
payment_installments: maximo numero de cuotas
payment_value: valor total pagado
payment_count: cantidad de pagos
payment_type: tipo de pago principal
```

### Que hace aggregate_geolocation()?

Agrupa coordenadas por codigo postal y crea dos tablas:

```text
customer_geo: coordenadas del cliente
seller_geo: coordenadas del vendedor
```

### Como se calcula la distancia?

El proyecto calcula dos distancias.

Distancia euclidiana:

```python
sqrt((lat1 - lat2)^2 + (lng1 - lng2)^2)
```

Distancia Haversine en kilometros:

```python
distancia_km_haversine
```

Respuesta:

> Haversine calcula una distancia aproximada en kilometros entre dos puntos de la
> Tierra usando latitud y longitud.

### Que significa radius_km = 6371.0?

Es el radio promedio de la Tierra en kilometros.

### Que hace build_master_dataset()?

Construye el dataset final.

Une:

```text
orders
customers
items
reviews
payments
customer_geo
seller_geo
```

Respuesta:

> Esta funcion integra todas las fuentes de datos en una sola tabla maestra.

### Que hace main()?

Ejecuta todo el proceso:

```text
1. Crea carpeta de salida
2. Construye dataset maestro
3. Guarda master_dataset.parquet
4. Imprime resumen de filas, columnas y tasa de retraso
```

## 6. Explicacion del entrenamiento del modelo

### Que hace train_model.py?

Carga el dataset maestro, valida columnas, prepara variables, entrena modelos,
evalua metricas y guarda el mejor modelo.

### Que modelos se probaron?

```text
Random Forest
Gradient Boosting
```

### Cual fue el mejor modelo?

```text
Gradient Boosting
```

Respuesta:

> El mejor modelo fue Gradient Boosting porque obtuvo mejor F1 con el umbral
> operativo.

### Que es Gradient Boosting?

Es un modelo basado en varios arboles de decision. Los arboles se construyen de
forma secuencial y cada uno intenta corregir los errores del anterior.

Respuesta:

> Gradient Boosting es util para datos tabulares porque puede aprender relaciones
> entre variables logisticas, comerciales y geograficas.

### Que variables usa el modelo?

Categoricas:

```text
seller_state
customer_state
product_category_name_english
payment_type
```

Numericas:

```text
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

### Que variables NO se deben usar para predecir?

```text
dias_retraso
entrego_tarde
order_delivered_customer_date
```

Respuesta:

> No se usan porque en la vida real no se conocen al momento de hacer la
> prediccion. Usarlas seria fuga de informacion.

### Que es fuga de informacion?

Es usar una variable que contiene informacion del futuro o de la respuesta real.

Ejemplo:

> Si uso la fecha real de entrega para predecir si llego tarde, ya estoy usando
> informacion que no existe antes de entregar el pedido.

### Que es OneHotEncoder?

Convierte variables categoricas en columnas numericas.

Ejemplo:

```text
payment_type = boleto
payment_type = credit_card
```

Se transforman en columnas con 0 y 1 para que el modelo pueda entenderlas.

### Que es SimpleImputer?

Sirve para rellenar datos faltantes.

En el proyecto:

```text
Categoricas: se rellenan con "unknown"
Numericas: se rellenan con la mediana
```

### Que es un Pipeline?

Es una cadena ordenada de pasos.

En este proyecto:

```text
Imputar datos -> codificar categorias -> entrenar modelo
```

Respuesta:

> El pipeline asegura que el preprocesamiento y el modelo se ejecuten siempre de
> la misma manera.

## 7. Metricas del modelo

Datos del proyecto:

```text
Total de pedidos: 96,470
Pedidos tardios: 6,534
Pedidos a tiempo: 89,936
Tasa historica de retraso: 6.77%
```

### Por que el problema esta desbalanceado?

Porque solo 6.77% de los pedidos llegan tarde y mas del 93% llegan a tiempo.

### Por que no se usa accuracy como metrica principal?

Porque si el modelo dijera "todo llega a tiempo", tendria una accuracy alta,
pero no serviria para detectar retrasos.

Respuesta:

> En problemas desbalanceados, accuracy puede enganar. Por eso usamos precision,
> recall, F1 y ROC AUC.

### Precision

Resultado:

```text
Precision = 23.15%
```

Significado:

> De todos los pedidos que el modelo marco como alerta, 23.15% realmente llegaron
> tarde.

Ejemplo:

```text
De cada 100 alertas, aproximadamente 23 son retrasos reales.
```

Frase:

> La precision mide que tan limpia es la cola de alertas.

### Recall

Resultado:

```text
Recall = 37.11%
```

Significado:

> De todos los pedidos que realmente llegaron tarde, el modelo logro detectar
> 37.11%.

Ejemplo:

```text
De cada 100 retrasos reales, el modelo detecta aproximadamente 37.
```

Frase:

> El recall mide cuantos retrasos reales logra capturar el modelo.

### F1

Resultado:

```text
F1 = 0.285
```

F1 combina precision y recall.

Formula:

```text
F1 = 2 * (precision * recall) / (precision + recall)
```

Respuesta:

> F1 es el balance entre precision y recall. En este proyecto se usa porque el
> dataset esta desbalanceado y necesitamos equilibrar alertas correctas con
> retrasos capturados.

### ROC AUC

Resultado:

```text
ROC AUC = 0.742
```

Interpretacion:

```text
0.5 = modelo casi al azar
1.0 = modelo perfecto
0.742 = capacidad aceptable de separacion
```

Respuesta:

> ROC AUC mide que tan bien el modelo separa pedidos de mayor riesgo y menor
> riesgo. Un valor de 0.742 indica que el modelo aprendio patrones utiles.

### Umbrales de riesgo

```text
Riesgo bajo: menor a 64.18%
Riesgo medio: desde 64.18% hasta menos de 69.18%
Riesgo alto: desde 69.18% en adelante
```

Respuesta:

> El modelo devuelve una probabilidad. Luego esa probabilidad se transforma en
> nivel de riesgo usando umbrales operativos.

### Matriz de confusion

Resultados:

```text
True Negative: 16,377
False Positive: 1,610
False Negative: 822
True Positive: 485
```

Explicacion:

```text
True Negative:
Pedido llego a tiempo y el modelo dijo a tiempo.

False Positive:
Pedido llego a tiempo, pero el modelo genero alerta.

False Negative:
Pedido llego tarde, pero el modelo no lo detecto.

True Positive:
Pedido llego tarde y el modelo si genero alerta.
```

Frase:

> Un falso positivo representa revisar un pedido que al final llega bien. Un falso
> negativo es mas delicado porque representa un retraso no anticipado.

## 8. Variables mas influyentes

Variables importantes del modelo:

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

Respuesta:

> El modelo encontro que el mes de compra, la distancia, el estado del cliente,
> el estado del vendedor, el flete y el tiempo de aprobacion influyen en el
> riesgo de retraso.

### Por que febrero y marzo suben el riesgo?

En el dataset:

```text
Mes 2: 11.88% de retraso
Mes 3: 15.12% de retraso
Promedio general: 6.77%
```

Respuesta:

> El riesgo sube en los meses 2 y 3 porque historicamente esos meses tuvieron
> mas retrasos que el promedio general. El modelo aprende ese patron temporal.

Importante:

> No significa que todos los pedidos de febrero o marzo lleguen tarde. Solo
> significa que el mes aumenta el riesgo cuando se combina con otras variables.

## 9. API

### Para que sirve la API?

La API permite consultar el modelo con datos de un pedido nuevo.

Respuesta:

> La API convierte el modelo entrenado en un servicio que puede recibir datos de
> un pedido y devolver una prediccion.

### Tecnologia usada

```text
FastAPI
```

### Endpoint principal

```text
POST /orders/delay_risk
```

### Entrada de ejemplo

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

### Respuesta de ejemplo

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

### Que pasa si falta una variable?

El sistema usa valores base historicos o medianas para completar datos faltantes.

Respuesta:

> La API construye una fila completa para el modelo. Si el usuario no envia todas
> las variables, se completan con valores base calculados del dataset historico.

## 10. Dashboard

### Para que sirve el dashboard?

Sirve para visualizar KPIs, alertas, rutas criticas, categorias, mapa, cola
operativa y simulador.

Respuesta:

> El dashboard permite que el equipo logistico analice los resultados sin entrar
> al codigo.

### Filtros del lado izquierdo

Sirven para segmentar el analisis.

Filtros:

```text
Rango de compra
Estado del cliente
Estado del vendedor
Tipo de pago
Riesgo estimado
Categorias
Minimo de pedidos por grupo
```

Respuesta:

> Los filtros permiten analizar una parte especifica del dataset. Cada vez que
> se cambia un filtro, los indicadores, graficos y tablas se actualizan
> automaticamente.

### Resumen ejecutivo

Muestra:

```text
Pedidos filtrados
Tasa de retraso real
Alertas del modelo
Pedidos de riesgo alto
Dias promedio de retraso
```

Respuesta:

> Esta vista da una lectura rapida del estado general de la operacion logistica.

### Operacion

Incluye la cola operativa.

Respuesta:

> La cola operativa lista los pedidos con riesgo medio o alto, ordenados por
> probabilidad. Sirve como lista diaria de seguimiento logistico.

### Drivers logisticos

Muestra factores que explican el riesgo:

```text
Mapa por estado
Riesgo por estado destino
Riesgo por categoria
Satisfaccion por categoria
Riesgo por distancia
Retraso por tipo de pago
```

### Simulador

Permite ingresar un pedido nuevo y calcular su riesgo.

Respuesta:

> El simulador convierte el modelo en una herramienta practica. Permite probar
> escenarios y ver como cambia el riesgo si cambia la ruta, categoria, precio,
> flete, distancia, peso o mes de compra.

### Pestaña Modelo

Muestra:

```text
Modelo seleccionado
Precision
Recall
F1
ROC AUC
Variables importantes
Matriz de confusion
```

Respuesta:

> Esta pestana sirve para explicar el rendimiento del modelo y entender que
> variables influyen mas en la prediccion.

## 11. Distancia en el simulador

### La distancia que aparece por defecto sale del dataset?

Si.

El sistema calcula una tabla interna:

```python
df.groupby(["seller_state", "customer_state"])["distancia_km_haversine"].median()
```

Respuesta:

> La distancia por defecto no se escribe manualmente. Sale del dataset historico.
> Para cada ruta vendedor-cliente, el sistema usa la mediana historica de
> distancia.

### Es distancia real por carretera?

No. Es una distancia aproximada usando coordenadas geograficas.

Respuesta:

> No es distancia exacta por carretera. Es una aproximacion en kilometros usando
> latitud y longitud.

## 12. Ejemplo para obtener riesgo alto

Usar estos valores en el simulador:

```text
Estado vendedor: SP - Sao Paulo
Estado cliente: RJ - Rio de Janeiro
Categoria: health_beauty
Tipo de pago: boleto
Precio total: 550.00
Flete total: 145.99
Cantidad de items: 1
Cuotas: 1
Distancia estimada km: 544.91
```

Variables logisticas avanzadas:

```text
Peso total g: 30000
Peso promedio g: 30000
Volumen maximo cm3: 210000
Volumen promedio cm3: 210000
Mes de compra: 2
Dia semana 0-6: 2
```

Resultado esperado:

```text
Probabilidad aproximada: 86%
Riesgo: Alto
```

### Por que genera riesgo alto si la distancia no es tan grande?

Porque el modelo no decide solo por distancia.

En ese caso se combinan:

```text
- Producto muy pesado: 30 kg
- Volumen alto
- Flete alto
- Categoria health_beauty
- Pago por boleto
- Mes 2, que historicamente tuvo mas retrasos
- Ruta SP -> RJ
```

Respuesta:

> No es una regla manual de mas distancia igual mas riesgo. Es una prediccion
> basada en patrones historicos combinados.

### Por que una distancia enorme no siempre da riesgo alto?

Porque si se ingresa un valor demasiado extremo o poco parecido a los datos
historicos, el modelo no necesariamente lo interpreta como un caso de alto riesgo.

Respuesta:

> El modelo responde mejor con combinaciones parecidas a casos reales del dataset.
> La distancia es importante, pero no es la unica variable.

## 13. Warning de scikit-learn

Mensaje:

```text
InconsistentVersionWarning
Trying to unpickle estimator from version 1.8.0 when using version 1.7.2
```

Significado:

> El modelo fue guardado con una version de scikit-learn y se esta cargando con
> otra version.

Respuesta para defensa:

> Esta advertencia aparece porque el modelo fue entrenado y guardado con una
> version de scikit-learn diferente a la version instalada actualmente. No
> impide ejecutar el dashboard, pero en produccion lo ideal seria usar la misma
> version con la que se entreno el modelo.

Solucion posible:

```powershell
python -m pip install scikit-learn==1.8.0
```

O reentrenar el modelo con la version actual:

```powershell
python 02_scripts/train_model.py
```

## 14. Preguntas rapidas de codigo

### Para que sirve pandas?

Para leer, limpiar, unir y transformar tablas.

### Para que sirve numpy?

Para calculos numericos y matematicos.

### Para que sirve Path?

Para manejar rutas de archivos de forma ordenada.

### Que hace pd.read_csv?

Lee un CSV y lo convierte en DataFrame.

### Que hace pd.to_datetime?

Convierte texto a fechas.

### Que hace fillna?

Rellena valores faltantes.

### Que hace merge?

Une tablas usando una columna en comun.

### Que hace groupby?

Agrupa registros para calcular resumenes.

### Que hace agg?

Permite calcular varias agregaciones, como suma, promedio y conteo.

### Que hace sort_values?

Ordena los datos.

### Que hace drop_duplicates?

Elimina duplicados y conserva un registro por clave.

### Que hace to_parquet?

Guarda un DataFrame en formato Parquet.

### Que hace if __name__ == "__main__"?

Permite ejecutar el archivo directamente desde la terminal.

## 15. Preguntas rapidas de defensa

### El modelo predice con 100% de seguridad?

No. Estima una probabilidad basada en patrones historicos.

### El sistema toma decisiones automaticamente?

No. Genera alertas y recomendaciones para que el equipo logistico priorice.

### Por que la precision no es tan alta?

Porque el problema es dificil y desbalanceado: solo 6.77% de pedidos llegan
tarde. Aun asi, la precision de 23.15% mejora mucho la seleccion frente a
elegir pedidos al azar.

### Que es un falso positivo?

Un pedido que el modelo alerta, pero finalmente llega a tiempo.

### Que es un falso negativo?

Un pedido que llega tarde, pero el modelo no alerto.

### Cual error es mas grave?

El falso negativo, porque representa un retraso que no fue anticipado.

### Cual es la principal limitacion?

La distancia es aproximada y no incluye datos reales de carretera, clima,
trafico o transportistas.

### Como se podria mejorar?

Agregando:

```text
- Datos de transportistas
- Clima
- Trafico
- Rutas reales
- Capacidad logistica
- Reentrenamiento periodico
```

## 16. Cierre recomendado

> En conclusion, este proyecto convierte datos historicos de e-commerce en una
> herramienta practica de decision logistica. No solo calcula una probabilidad,
> sino que transforma esa prediccion en acciones concretas para reducir retrasos
> y mejorar la experiencia del cliente.

Frase final corta:

> El valor principal del sistema es anticiparse al problema antes de que el
> cliente reclame.
