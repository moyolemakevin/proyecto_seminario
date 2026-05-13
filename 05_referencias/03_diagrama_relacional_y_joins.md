# Diagrama relacional y justificacion de joins

Este documento deja explicito el diseno relacional usado para construir el
DataFrame analitico maestro del Caso 09 antes de modelar.

## Esquema relacional

```text
orders
  |-- customer_id
  v
customers
  |-- customer_zip_code_prefix
  v
geolocation  -> coordenadas cliente

orders
  |-- order_id
  v
items
  |-- product_id
  v
products
  |-- product_category_name
  v
product_category_name_translation

items
  |-- seller_id
  v
sellers
  |-- seller_zip_code_prefix
  v
geolocation  -> coordenadas vendedor

orders
  |-- order_id
  |-- reviews
  v
payments
```

## Cadena principal

```text
orders -> customers
orders -> items -> products -> category_translation
items -> sellers
orders -> reviews
orders -> payments
customers -> geolocation
sellers -> geolocation
```

## Justificacion de joins

| Paso | Join | Justificacion |
|---|---|---|
| `orders -> customers` | left | Conserva pedidos aunque falte algun dato del cliente. |
| `orders -> items` | inner | El modelo necesita productos/items para explicar riesgo logistico. |
| `items -> products` | left | No descarta items si faltan metadatos del producto. |
| `products -> translation` | left | La traduccion mejora lectura de categorias sin eliminar productos. |
| `items -> sellers` | left | Agrega origen logistico del vendedor sin descartar items incompletos. |
| `orders -> reviews` | left | No todos los pedidos tienen resena. |
| `orders -> payments` | left | El pago aporta senales comerciales sin eliminar pedidos. |
| `customers -> geolocation` | left | Algunas coordenadas de cliente pueden faltar. |
| `sellers -> geolocation` | left | Algunas coordenadas de vendedor pueden faltar. |

## Variables requeridas por el caso

```python
dias_retraso = (
    order_delivered_customer_date - order_estimated_delivery_date
).dt.days

entrego_tarde = 1 si dias_retraso > 0, caso contrario 0

distancia_aprox = sqrt(
    (seller_lat - customer_lat) ** 2
    + (seller_lng - customer_lng) ** 2
)
```

## Mejora adicional del proyecto

Ademas de `distancia_aprox`, el proyecto conserva `distancia_km_haversine` para
visualizaciones y explicaciones de negocio en kilometros. La variable requerida
por la rubrica sigue disponible con su definicion original.
