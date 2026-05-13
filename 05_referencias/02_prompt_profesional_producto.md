# Prompt profesional ejecutado

Actua como un consultor senior de analitica, machine learning y producto de
datos para ecommerce logistico. Convierte el proyecto OLIST Delay Alert System
en una demo profesional que un cliente de negocio pueda entender, probar y usar
para tomar decisiones.

## Objetivo del cliente

El cliente quiere saber:

- Que pedidos tienen mayor riesgo de llegar tarde.
- Que rutas, estados, categorias y metodos de pago concentran retrasos.
- Que acciones operativas debe tomar segun el nivel de riesgo.
- Como consumir el modelo desde una API.
- Como explicar el resultado a negocio sin tecnicismos innecesarios.

## Requisitos funcionales

1. Mostrar estados usando abreviatura y nombre completo, por ejemplo
   `SP - Sao Paulo`.
2. Mantener codigos de estado compatibles con el modelo y la API.
3. Agregar catalogos simples para que un consumidor de API sepa que valores
   puede usar.
4. Mostrar una cola operativa de pedidos con mayor riesgo.
5. Agregar recomendaciones concretas por nivel de riesgo.
6. Mejorar el dashboard para que funcione como herramienta de monitoreo, no
   solo como reporte.
7. Evitar sobreingenieria, nuevas dependencias innecesarias o cambios de rutas.
8. Mantener el proyecto facil de ejecutar con los scripts actuales.

## Criterios de aceptacion

- La API devuelve probabilidad, nivel de riesgo, modelo, umbrales, estado con
  codigo y nombre, recomendacion y acciones.
- El dashboard permite filtrar por estados con codigo y nombre.
- El dashboard incluye rutas criticas y una cola operativa de pedidos en riesgo.
- La documentacion explica los nuevos endpoints y el uso esperado.
- El codigo compila y los endpoints basicos responden correctamente.
