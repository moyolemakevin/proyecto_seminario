# Contexto de negocio

## Que es OLIST

OLIST es un marketplace de e-commerce de Brasil. Un marketplace es una
plataforma donde muchos vendedores ofrecen productos y muchos clientes hacen
compras.

En este tipo de negocio, OLIST no siempre es quien vende directamente el
producto. OLIST conecta al vendedor con el cliente y ayuda a gestionar la venta,
el pedido, el pago y la experiencia del comprador.

## Como funciona el negocio

El flujo basico de una compra es:

1. Un cliente compra un producto en la plataforma.
2. El pedido queda registrado con una fecha de compra.
3. El pago se aprueba.
4. El vendedor prepara el producto.
5. El producto pasa al proceso logistico.
6. El pedido llega al cliente.
7. El cliente puede dejar una calificacion o comentario.

El punto critico del negocio es que el cliente espera recibir el producto antes
o en la fecha estimada de entrega. Si el pedido llega despues, la experiencia
del cliente puede empeorar.

## Quienes participan

 actores:

Cliente:
Persona que compra el producto. Tiene ciudad, estado y codigo postal.

Vendedor:
Persona o empresa que vende el producto. Tambien tiene ciudad, estado y codigo
postal.

Pedido:
Compra realizada por un cliente. Tiene fechas importantes como compra,
aprobacion, entrega real y entrega estimada.

Producto:
Articulo comprado. Tiene categoria, peso y dimensiones.

Pago:
Informacion sobre el tipo de pago, valor pagado y numero de cuotas.

Review:
Calificacion que deja el cliente despues de la compra.

Logistica:
Proceso de mover el producto desde el vendedor hasta el cliente.

## Problema principal

El problema que queremos resolver es:

Saber con anticipacion si un pedido tiene riesgo de llegar tarde.

Esto es importante porque no todos los pedidos tienen el mismo nivel de riesgo.
Por ejemplo, no es lo mismo:

Pedido A:
Vendedor en Sao Paulo.
Cliente en Sao Paulo.
Ruta mas cercana.

Pedido B:
Vendedor en Bahia.
Cliente en Acre.
Ruta mas larga o mas compleja.

El segundo pedido puede tener mas riesgo logistico que el primero.

## Que significa entrega tardia

El dataset tiene dos fechas importantes:

order_delivered_customer_date
Fecha real en que el cliente recibio el pedido.

order_estimated_delivery_date
Fecha estimada o prometida de entrega.

Con esas fechas se calcula:

dias_retraso = fecha real de entrega - fecha estimada de entrega

Si `dias_retraso` es mayor que 0, el pedido llego tarde.

La variable final se llama:

entrego_tarde

Significado:

entrego_tarde = 1
El pedido llego despues de la fecha estimada.

entrego_tarde = 0
El pedido llego el mismo dia o antes de la fecha estimada.

## Que estamos construyendo

Estamos construyendo un sistema de alerta temprana.

El sistema usa datos historicos para aprender patrones de pedidos que llegaron
tarde y pedidos que llegaron a tiempo.

Luego, cuando se ingresa un pedido nuevo o simulado, el sistema calcula una
probabilidad de retraso.

Ejemplo:

Probabilidad de retraso: 42%
Nivel de riesgo: medio

Eso significa que, segun los datos historicos, ese pedido se parece a otros
casos que tuvieron cierto riesgo de llegar tarde.

## Para que sirve al negocio

El sistema puede ayudar a OLIST a:

1. Detectar pedidos con riesgo antes de que el cliente reclame.
2. Priorizar seguimiento logistico en pedidos complicados.
3. Avisar al cliente si existe riesgo de demora.
4. Identificar rutas entre estados con mas retrasos.
5. Identificar categorias de producto con mas problemas.
6. Revisar vendedores que puedan estar generando demoras.
7. Mejorar la promesa de fecha estimada.
8. Reducir malas calificaciones por retraso.

## Datos importantes del negocio

seller_state
Estado de Brasil donde esta ubicado el vendedor.

customer_state
Estado de Brasil donde esta ubicado el cliente.

product_category_name_english
Categoria del producto comprado.

payment_type
Tipo de pago usado por el cliente.

total_price
Precio total de los productos del pedido.

total_freight
Valor total del flete.

payment_installments
Numero de cuotas del pago.

review_score
Calificacion que dejo el cliente.

distancia_aprox
Distancia aproximada entre vendedor y cliente, calculada con coordenadas.

## Por que importan vendedor y cliente

En OLIST, el vendedor y el cliente pueden estar en estados distintos de Brasil.
Eso afecta la logistica.

Si vendedor y cliente estan cerca, el pedido puede ser mas facil de entregar.
Si estan lejos, la ruta puede ser mas costosa, mas lenta o mas propensa a
retrasos.

Por eso el modelo usa:

seller_state
customer_state
distancia_aprox

Estas variables ayudan a representar la ruta del pedido.

## Como se usa el modelo

El modelo recibe datos de un pedido, por ejemplo:

Estado del vendedor: SP
Estado del cliente: BA
Categoria: furniture_decor
Tipo de pago: boleto
Precio total: 100
Flete total: 20
Cuotas: 1

Con eso calcula:

Probabilidad de retraso.
Nivel de riesgo.

Los niveles usados son:

Bajo:
Probabilidad menor a 31%.

Medio:
Probabilidad desde 31% hasta menos de 61%.

Alto:
Probabilidad de 61% o mas.

## Que significa la tasa historica de retraso

La tasa historica actual es 6.62%.

Eso quiere decir que, en el dataset maestro, aproximadamente 6 de cada 100
pedidos llegaron tarde.

Pero esa tasa es general. No significa que todos los pedidos tengan siempre
6.62% de riesgo.

El modelo calcula un riesgo especifico para cada pedido, segun sus
caracteristicas.

Ejemplo:

Pedido simple:
Vendedor y cliente en el mismo estado.
Producto comun.
Flete bajo.
Puede tener riesgo bajo.

Pedido mas complejo:
Vendedor y cliente en estados lejanos.
Flete alto.
Categoria con retrasos historicos.
Puede tener riesgo medio o alto.

## Que decisiones permite tomar

Si el riesgo es bajo:
El pedido puede seguir el flujo normal.

Si el riesgo es medio:
Se puede monitorear con mas atencion.

Si el riesgo es alto:
Se puede priorizar revision logistica, contactar al vendedor o avisar al
cliente.

## Resumen sencillo

Este proyecto busca responder una pregunta de negocio:

Este pedido podria llegar tarde?

Para responderla, usamos datos historicos de OLIST, unimos varias tablas,
calculamos si cada pedido llego tarde o no, entrenamos un modelo y lo usamos en
un dashboard y una API.

El valor para el negocio esta en anticiparse al problema antes de que el cliente
tenga una mala experiencia.
