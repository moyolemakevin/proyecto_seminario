# Guía de estudio — OLIST Delay Alert System
> Para entender cada decisión técnica del proyecto y preparar la defensa oral.

---

## 1. El problema que resolvemos

OLIST es el mayor marketplace de e-commerce de Brasil. Tiene un problema real:
algunos pedidos llegan tarde y los clientes se quejan (bajan la puntuación, no vuelven a comprar).

**La pregunta de negocio:**
> ¿Podemos predecir, antes de que un pedido llegue, si va a llegar tarde?

Si podemos predecirlo, el equipo de logística puede priorizar esos pedidos y evitar el retraso.

**La solución:** un sistema de alertas que analiza las características de un pedido
(precio, distancia, categoría, estado de origen/destino) y devuelve una probabilidad
de retraso con una recomendación operativa.

---

## 2. El dataset

| Tabla | Filas | Qué contiene |
|---|---|---|
| orders | 99,441 | Pedidos con fechas de compra, aprobación, despacho y entrega |
| customers | 99,441 | Ciudad, estado y zip del cliente |
| order_items | 112,650 | Productos por pedido (un pedido puede tener varios) |
| order_payments | 103,886 | Tipo y monto de pago |
| order_reviews | 99,224 | Calificación del cliente (1-5 estrellas) |
| products | 32,951 | Categoría, peso y dimensiones del producto |
| sellers | 3,095 | Ciudad, estado y zip del vendedor |
| geolocation | 1,000,163 | Coordenadas lat/lon por código postal |

**Por qué hay más filas en order_items que en orders:**
Un mismo pedido puede tener 2 o más productos → una fila por producto.

---

## 3. La variable objetivo

```python
dias_retraso = order_delivered_customer_date - order_estimated_delivery_date
entrego_tarde = 1 si dias_retraso > 0, sino 0
```

**Resultado:** solo el **6.77% de pedidos llegan tarde**.
Esto se llama **desbalance de clases** y es el mayor desafío del proyecto.

### ¿Por qué es un problema el desbalance?
Si entrenas un modelo sin corrección, aprende que "siempre llega a tiempo" y tiene
93% de accuracy — pero nunca detecta retrasos. Es inútil.

**Solución:** `class_weight='balanced'` — le dice al modelo que los errores en la
clase minoritaria (tardíos) cuestan más que los errores en la mayoría (a tiempo).

---

## 4. El pipeline de datos — los 5 merges

El DataFrame maestro se construye uniendo las tablas en este orden:

```
orders (filtrado a "delivered")
  + customers          → LEFT JOIN por customer_id
  + order_items        → LEFT JOIN por order_id  ← aquí crecen las filas
    + products         → LEFT JOIN por product_id
  + sellers            → LEFT JOIN por seller_id
  + order_reviews      → LEFT JOIN por order_id (promediado)
  + geolocation        → LEFT JOIN por zip_code (cliente y vendedor)
```

### ¿Por qué LEFT JOIN y no INNER JOIN?
Con INNER JOIN perderías filas cuando un customer_id no tenga match exacto en customers
(errores de datos, registros incompletos). LEFT JOIN conserva todos los pedidos
y pone NULL donde no hay match — más seguro.

### El merge más delicado: geolocation
`geolocation` tiene 1,000,163 filas porque cada zip_code tiene múltiples coordenadas
registradas (mediciones repetidas). Si haces el join directamente, el DataFrame
se multiplica por 10x.

**Solución:** agrupar por zip_code y promediar lat/lon primero:
```python
geo = geolocation.groupby('geolocation_zip_code_prefix')[['lat', 'lng']].mean()
# Resultado: una fila por zip_code
```

---

## 5. Feature engineering

Las variables que el modelo usa para predecir:

| Feature | Qué mide | Por qué importa |
|---|---|---|
| `distancia_aprox` | Distancia euclidiana vendedor-cliente en grados | A más distancia, más riesgo de retraso |
| `dias_despacho` | Días del vendedor en despachar al transportista | Si tarda en despachar, llega tarde |
| `price` | Precio del pedido | Pedidos caros suelen tener mejor seguimiento |
| `freight_value` | Costo de envío | Flete caro = distancia larga o zona difícil |
| `product_weight_g` | Peso del producto | Productos pesados son más difíciles de manejar |
| `customer_state` | Estado de destino | Algunos estados tienen peor infraestructura |
| `seller_state` | Estado de origen | Afecta el tiempo de despacho |
| `product_category_name_english` | Categoría del producto | Algunas categorías tienen más retrasos |

**Lo que NO usamos:** `dias_retraso` — eso es lo que queremos predecir,
no podemos usarlo como input.

---

## 6. Los modelos y por qué los comparamos

Comparamos 4 modelos para justificar la elección con evidencia:

| Modelo | Característica principal |
|---|---|
| Logistic Regression | Baseline simple, lineal, muy interpretable |
| Decision Tree | Árbol de decisión, explicable con reglas claras |
| Random Forest | Ensemble de árboles, robusto al ruido |
| Gradient Boosting | Boosting secuencial, generalmente el más preciso en datos tabulares |

### Resultados obtenidos

| Modelo | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| Logistic Regression | 0.122 | 0.558 | 0.200 | 0.698 |
| Decision Tree | 0.130 | 0.625 | 0.215 | 0.713 |
| Random Forest | 0.802 | 0.165 | 0.274 | 0.768 |
| Gradient Boosting | 0.689 | 0.064 | 0.117 | 0.747 |

---

## 7. ¿Por qué elegimos ese modelo? (la respuesta para la defensa)

### ¿Qué es Precision y qué es Recall?

- **Precision:** de todos los pedidos que el modelo marcó como "tardíos", ¿cuántos realmente lo fueron?
  - Alta precision = pocas falsas alarmas
- **Recall:** de todos los pedidos que realmente llegaron tarde, ¿cuántos detectó el modelo?
  - Alto recall = no se pierde retrasos reales

### ¿Cuál métrica priorizar?

Depende del costo del error:

| Error | Qué significa | Costo |
|---|---|---|
| Falso positivo | Marcó como "tardío" pero llegó a tiempo | Bajo — generamos una alerta innecesaria |
| Falso negativo | No detectó un pedido que llegó tarde | Alto — el cliente se queja, perdemos la venta |

**Conclusión:** en un sistema de alertas de entrega, el falso negativo es más costoso.
Por eso priorizamos **Recall** sobre Precision o F1.

**Modelo elegido: Decision Tree** (Recall = 0.625)
Detecta el 62.5% de los pedidos tardíos — casi 4 veces más que Random Forest (16.5%).

### ¿Por qué no Random Forest si tiene mejor F1 y Precision?
Random Forest tiene Precision 0.802 pero Recall 0.165 — se pierde el 83.5% de los
pedidos tardíos reales. Para un sistema de alertas, eso es inaceptable.

---

## 8. La API — cómo funciona

La API está construida con **FastAPI** y expone el modelo como un servicio web.

**Endpoint principal:**
```
POST /orders/delay_risk
```

**Entrada (JSON):**
```json
{
  "seller_state": "SP",
  "customer_state": "BA",
  "product_category_name_english": "furniture_decor",
  "payment_type": "credit_card",
  "total_price": 120,
  "total_freight": 25,
  "item_count": 1,
  "payment_installments": 2
}
```

**Salida:**
```json
{
  "delay_probability": 0.48,
  "risk_level": "bajo",
  "recommendation": "Mantener flujo logístico normal.",
  "model": "gradient_boosting"
}
```

**¿Por qué FastAPI?**
- Genera documentación interactiva automática (`/docs`)
- Es async — maneja múltiples requests simultáneos
- Validación automática de tipos con Pydantic

---

## 9. El dashboard — qué muestra

El dashboard en Streamlit tiene estas secciones:

- **KPIs:** total de pedidos, tasa de retraso histórica, alertas generadas
- **Evolución mensual:** cómo cambia el retraso a lo largo del tiempo
- **Mapa coroplético:** qué estados de Brasil tienen más retrasos
- **Análisis por categoría:** qué productos llegan más tarde
- **Cola operativa:** pedidos ordenados por probabilidad de retraso
- **Simulador:** ingresa datos de un pedido y obtén la predicción en tiempo real
- **Vista del modelo:** métricas, feature importance y matriz de confusión

---

## 10. Números clave para la defensa

Memoriza estos datos:

| Dato | Valor |
|---|---|
| Total de pedidos en el dataset | 99,441 |
| Pedidos entregados (usados) | 96,478 |
| Tasa de retraso histórica | 6.77% |
| Pedidos tardíos | ~6,534 |
| Columnas del DataFrame maestro | 29 |
| Modelo elegido | Decision Tree |
| Recall del modelo elegido | 0.625 |
| Criterio de selección | Recall (no F1) |
| Período del dataset | 2016-2018 |
| País | Brasil |

---

## 11. Preguntas frecuentes en la defensa

**¿Por qué usaron ese modelo y no otro?**
> Comparamos 4 modelos (Logistic Regression, Decision Tree, Random Forest, Gradient Boosting)
> con las mismas métricas. Elegimos Decision Tree porque tiene el mayor Recall (0.625),
> lo que significa que detecta el 62.5% de los pedidos tardíos. En un sistema de alertas,
> perder un retraso real es más costoso que generar una falsa alarma.

**¿Por qué el accuracy no es la métrica principal?**
> Con 93% de pedidos a tiempo, un modelo que predice "siempre a tiempo" tendría 93% de
> accuracy pero nunca detectaría un retraso. El accuracy es engañoso con clases desbalanceadas.

**¿Qué es class_weight='balanced'?**
> Le dice al modelo que los errores en la clase minoritaria (tardíos, 6.77%) tienen más
> peso que los errores en la mayoría. Sin esto, el modelo ignora los tardíos.

**¿Por qué LEFT JOIN y no INNER JOIN?**
> Para conservar todos los pedidos aunque haya registros con datos incompletos.
> Con INNER JOIN perderíamos filas silenciosamente.

**¿Por qué parquet y no CSV para el DataFrame maestro?**
> Parquet comprime mejor (15 MB vs ~80 MB en CSV), mantiene los tipos de datos
> correctos y se lee más rápido con pandas.

**¿Qué limitaciones tiene el modelo?**
> Solo fue entrenado con datos de 2016-2018. El comportamiento logístico puede haber
> cambiado. El Recall de 0.625 significa que aún se pierden el 37.5% de los retrasos reales.
> No es un sistema de decisión automática sino una herramienta de priorización.

---

## 12. Cómo ejecutar el proyecto

```powershell
# 1. Activar el entorno
conda activate olist

# 2. Reconstruir el dataset (si los CSVs están en data/raw/)
python 02_scripts/build_dataset.py

# 3. Reentrenar el modelo
python 02_scripts/train_model.py

# 4. Lanzar la API (Terminal 1)
cd 02_scripts
uvicorn api:app --reload

# 5. Lanzar el dashboard (Terminal 2)
cd 02_scripts
streamlit run dashboard.py
```

**URLs:**
- Dashboard: http://localhost:8501
- API docs: http://localhost:8000/docs
