# Proyecto Seminario: Caso 09 - E-Commerce OLIST Brasil

## Descripción

Proyecto de titulación desarrollado durante el Seminario EDA 2026. Se construye un **sistema predictivo de alertas de entrega** sobre el dataset público de OLIST, aplicando integración multi-tabla, análisis exploratorio, modelado con scikit-learn y despliegue como producto analítico (API + dashboard).

---

## Contexto del problema

**OLIST** es el mayor marketplace de e-commerce de Brasil. Su dataset público contiene 100 000 pedidos realizados entre 2016 y 2018, distribuidos en **8 tablas relacionales**: pedidos, clientes, productos, vendedores, reseñas, pagos, ítems y geolocalización.

Las entregas tardías generan dos costos críticos para la plataforma:
- **Reputacional**: reseñas negativas y pérdida de confianza del cliente.
- **Operativo**: atención al cliente reactiva y posibles compensaciones.

La distancia aproximada entre vendedor y cliente, calculada a partir de coordenadas geográficas, resulta ser uno de los predictores más importantes del retraso en la entrega.

---

## Objetivo del proyecto

Construir un sistema predictivo de alertas de entrega que determine si un pedido llegará tarde a su destino, para que la plataforma emita **alertas proactivas al cliente** antes de que el retraso ocurra, analizando qué factores operativos y geográficos aumentan más el riesgo de demora.

---

## Pregunta de negocio

> **¿Es posible predecir, en el momento en que se confirma un pedido, si éste llegará tarde — y qué factores del vendedor, el cliente y el producto aumentan más ese riesgo?**

Variables clave construidas:
- `dias_retraso` = `order_delivered_customer_date` − `order_estimated_delivery_date`
- `entrego_tarde` = 1 si `dias_retraso` > 0 (variable objetivo de clasificación)
- `distancia_aprox` = distancia euclidiana en grados entre coordenadas del vendedor y del cliente

---

## Historias de usuario

### HU-01 · Alerta proactiva al cliente
**Como** cliente de OLIST que acaba de realizar un pedido,  
**quiero** recibir una alerta cuando exista alta probabilidad de que mi entrega se retrase,  
**para** poder reorganizar mis planes con anticipación y no quedar esperando sin información.

**Criterios de aceptación:**
- El sistema evalúa el riesgo de retraso en el momento de confirmación del pedido.
- Si la probabilidad supera el umbral definido, se emite una alerta antes de la fecha estimada.
- La alerta incluye los principales factores de riesgo identificados por el modelo.

---

### HU-02 · Análisis de riesgo por categoría y estado
**Como** analista de logística de OLIST,  
**quiero** visualizar en un dashboard qué categorías de producto y qué estados del Brasil presentan mayor tasa histórica de retrasos,  
**para** priorizar acciones de mejora con los vendedores de esas zonas y categorías.

**Criterios de aceptación:**
- El dashboard muestra un mapa coroplético de Brasil con tasa de retraso por estado del cliente.
- Existe un gráfico de barras de satisfacción promedio (score de reseña) por categoría de producto.
- Los datos son filtrables por período de tiempo.

---

### HU-03 · Predicción bajo demanda para el equipo de logística
**Como** coordinador de logística de OLIST,  
**quiero** ingresar los datos de un nuevo pedido (estado del vendedor, estado del cliente, categoría del producto) y obtener la probabilidad de retraso,  
**para** tomar decisiones operativas proactivas — como reasignar al vendedor o alertar al transportista — antes de que el problema ocurra.

**Criterios de aceptación:**
- El formulario en el dashboard acepta: estado vendedor, estado cliente, categoría de producto.
- El sistema devuelve la probabilidad de retraso (0–100%) y las 3 variables de mayor riesgo.
- La API `POST /orders/delay_risk` devuelve el mismo resultado en formato JSON.

---

## Ficha del dataset

| Campo | Detalle |
|---|---|
| **Nombre** | Brazilian E-Commerce Public Dataset by Olist |
| **Fuente** | [Kaggle · olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |
| **Licencia** | CC BY-NC-SA 4.0 |
| **Período** | Septiembre 2016 – Agosto 2018 |
| **Volumen** | ~100 000 pedidos · 8 tablas CSV |
| **Tamaño total** | ~43 MB descomprimido |
| **Idioma original** | Portugués (Brasil) |

### Tablas del dataset

| Tabla | Filas aprox. | Descripción |
|---|---|---|
| `olist_orders_dataset` | 99 441 | Pedidos con fechas y estado |
| `olist_order_items_dataset` | 112 650 | Ítems por pedido, precio, flete |
| `olist_customers_dataset` | 99 441 | Clientes con ubicación |
| `olist_products_dataset` | 32 951 | Productos con categoría y dimensiones |
| `olist_sellers_dataset` | 3 095 | Vendedores con ubicación |
| `olist_order_reviews_dataset` | 100 000 | Reseñas y scores de satisfacción |
| `olist_order_payments_dataset` | 103 886 | Métodos y valores de pago |
| `olist_geolocation_dataset` | 1 000 163 | Coordenadas lat/lon por código postal |