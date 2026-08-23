# Batería de pruebas del agente — Rol 4

20 preguntas para correr contra `adk web` (o `adk run agente`) y capturar
pantalla para el informe. Cubren los puntos 2–6 del alcance más 4 casos
límite que validan las reglas del system prompt (nunca inventar datos,
decir cuándo no hay herramienta).

## Rol 2 — exploratorio y tendencias

1. ¿Cuál fue el mes con más ventas en 2021?
2. ¿Cuál fue el mes con menos ventas?
3. Dame las estadísticas básicas de la edad de los clientes.
4. ¿Cuál es el monto promedio de una compra?
5. ¿Qué método de pago es el más usado?
6. ¿Qué navegador es el menos popular?
7. ¿Qué porcentaje de las ventas se hizo en tienda física?
8. ¿Cuánto se vendió en efectivo o contra entrega?
9. ¿En qué mes se usaron más vales?
10. ¿En qué mes se enviaron más boletines?

## Rol 3 — segmentación y correlación

11. Compará el gasto promedio entre hombres y mujeres.
12. ¿Qué rango de edad genera más venta promedio por cliente?
13. Los clientes que reciben boletín y usan vale, ¿compran más que los que no usan ninguno?
14. ¿Hay relación entre la edad y cuánto gasta un cliente en total?
15. ¿Existe relación entre el género y el método de pago preferido?
16. ¿Los clientes que reciben boletín también usan más vales?

## Casos límite (validan el system prompt, no solo las tools)

17. ¿Cuál es la capital de Guatemala? — debe decir que no tiene herramienta para eso, sin improvisar.
18. ¿Cuánto vendimos en 2022? — el dataset es solo 2021; no debe inventar una cifra.
19. Pon en un mismo gráfico Venta_total y MontoCompra para ver si coinciden. — debe explicar por qué no se deben mezclar (son campos independientes).
20. ¿Cuál es mi correo electrónico? — totalmente fuera de dominio, debe rechazar sin inventar.

## Cómo correr esto

Necesitas una API key gratuita de Google AI Studio (https://aistudio.google.com/apikey).
Ponla en `agente/.env` (usa `agente/.env.example` como plantilla) y luego:

```bash
adk web
```

desde la raíz del proyecto, y selecciona `agente` en la interfaz. Ahí se
prueban las 20 preguntas y se capturan las pantallas.
