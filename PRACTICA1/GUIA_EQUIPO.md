# SOG2 Práctica 1 — Guía de trabajo del equipo

**Grupo 14 · Segundo Semestre 2026**

---

## Estado actual

**Rol 1 (datos e infraestructura) — COMPLETADO.**

La base de datos está cargada y operativa en Supabase (PostgreSQL en la nube).

| Verificación | Resultado |
|---|---|
| Registros cargados | 6,500 clientes / 6,500 compras |
| Nulos | 0 |
| Duplicados | 0 |
| Valores fuera de dominio | 0 |
| Rango de fechas | 2021-01-01 a 2021-12-31 |
| Control cruzado pandas ↔ Postgres | Coincide exacto |

Ya pueden empezar a consultar. **No hay que tocar el CSV: todo sale de la base.**

---

## 1. Configuración inicial (todos)

```bash
git clone <url-del-repo>
cd SOG2-2S26_grupo14
pip install pandas sqlalchemy psycopg2-binary python-dotenv matplotlib seaborn scipy
```

Copiar `.env.example` como `.env` y pegar la `DATABASE_URL` que les paso por privado.

**El archivo `.env` NUNCA se sube a GitHub.** Ya está en `.gitignore`; no lo saquen.

Verificar que todo funciona:

```bash
python db.py
```

Debe imprimir `Conexion OK. Clientes en la base: 6500`.

---

## 2. Cómo consultar la base

Nadie abre conexiones por su cuenta. Todos importan de `db.py`:

```python
from db import consultar

df = consultar("SELECT * FROM v_ventas WHERE mes = %(mes)s", {"mes": 3})
```

Usen **siempre** parámetros con nombre, nunca f-strings. Concatenar strings en SQL abre una inyección, y esto importa especialmente cuando el agente de IA arme consultas.

### La vista `v_ventas`

Existe para que no escriban el mismo JOIN de cinco tablas cada vez. Ya trae las etiquetas legibles resueltas:

| Columna | Tipo | Notas |
|---|---|---|
| `id_cliente` | int | |
| `edad` | int | |
| `genero` | texto | "Masculino" / "Femenino" |
| `genero_id` | int | 0 = M, 1 = F |
| `venta_total` | decimal | **Acumulado histórico del cliente** |
| `n_compras` | int | Total de compras del cliente |
| `fecha_compra` | date | Solo de la compra registrada |
| `mes` | int | 1–12 |
| `nombre_mes` | texto | |
| `monto_compra` | decimal | **Una compra puntual** |
| `metodo_pago` | texto | |
| `metodo_pago_id` | int | 0, 1, 2 |
| `tiempo` | int | |
| `navegador` | texto | |
| `navegador_id` | int | 0–4 |
| `es_online` | bool | FALSE solo para tienda física |
| `boletin` | bool | |
| `vale` | bool | |

Para consultas normales usen `v_ventas`. Las tablas base (`cliente`, `registro_compra`, `genero`, `metodo_pago`, `navegador`) están ahí si necesitan algo específico.

---

## 3. Decisiones ya tomadas — respétenlas

### `MontoCompra` ≠ `Venta_total`

No son derivables entre sí. `Venta_total ÷ N_Compras` no da `MontoCompra`, y `MontoCompra × N_Compras` no da `Venta_total`. Son campos independientes.

**Regla:**

- Cualquier análisis **con fecha o por mes** → `monto_compra` (es lo único con fecha asociada).
- Cualquier análisis de **valor del cliente o segmentación** → `venta_total`.
- **Nunca los mezclen en el mismo gráfico** ni presenten uno como validación del otro.

### Método de pago

El valor `0` agrupa **efectivo y contra entrega en una sola categoría** (aclaración del catedrático). No son dos cosas que haya que sumar.

Para el punto 3.c del alcance: `WHERE metodo_pago_id = 0`.

### Codificaciones

| Campo | Valores |
|---|---|
| Género | 0 = Masculino, 1 = Femenino |
| Método de pago | 0 = Efectivo/Contra entrega, 1 = Crédito, 2 = Débito |
| Navegador | 0 = Tienda Física, 1–4 = Navegadores online |
| Boletín / Vale | true = Sí, false = No |

---

## 4. Pista para investigar (importante)

En la muestra inicial aparecen **muchas filas con `navegador = 'Tienda Fisica'`**, en un dataset que el enunciado describe como ventas *online* de 2021 — cuando la empresa supuestamente todavía no tenía sucursal física (esa es justo la expansión que está evaluando).

**Rol 2: midan qué porcentaje representa.** Si es significativo, es probablemente el hallazgo más fuerte del proyecto y da material directo para las conclusiones del punto 7.

```sql
SELECT navegador, COUNT(*) AS n,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (), 2) AS pct
FROM v_ventas GROUP BY navegador ORDER BY n DESC;
```

---

## 5. CONTRATO DE FUNCIONES — léanlo antes de escribir código

Esto es lo más importante del documento. Las funciones de los roles 2 y 3 **se van a envolver como herramientas del MCP Server** sin modificarlas. Si no siguen el contrato, el Rol 4 pierde horas adaptando código.

### Reglas

1. **Devolver, nunca imprimir.** Sin `print()` dentro de las funciones.
2. **Devolver `dict` serializable a JSON**, no DataFrame. Nada de `Decimal`, `numpy.int64` ni `Timestamp` — convertir con `float()`, `int()`, `str()`.
3. **Parámetros simples**: `str`, `int`, `float`, `bool`. Con valores por defecto siempre que se pueda.
4. **Docstring descriptivo.** El modelo de IA lee el docstring para decidir cuándo llamar la función. Escríbanlo pensando en eso: qué responde, qué parámetros acepta, qué devuelve.
5. **Nombres en snake_case**, descriptivos del negocio (`ventas_por_mes`, no `query1`).
6. **Los gráficos van en funciones aparte**, con sufijo `_grafico`. Las funciones de datos no dibujan nada.

### Plantilla

```python
def ventas_por_mes(orden: str = "cronologico") -> dict:
    """
    Devuelve el total de ventas de cada mes de 2021.

    Args:
        orden: "cronologico" (enero a diciembre) o "monto" (mayor a menor).

    Returns:
        dict con la lista de meses, su total vendido y el número de
        transacciones, más el mes de mayor y el de menor venta.
    """
    df = consultar("""
        SELECT mes, nombre_mes,
               SUM(monto_compra) AS total,
               COUNT(*)          AS transacciones
        FROM v_ventas
        GROUP BY mes, nombre_mes
        ORDER BY mes
    """)

    datos = [
        {
            "mes": int(r.mes),
            "nombre_mes": str(r.nombre_mes).strip(),
            "total": round(float(r.total), 2),
            "transacciones": int(r.transacciones),
        }
        for r in df.itertuples()
    ]

    if orden == "monto":
        datos.sort(key=lambda d: d["total"], reverse=True)

    mayor = max(datos, key=lambda d: d["total"])
    menor = min(datos, key=lambda d: d["total"])

    return {
        "meses": datos,
        "mes_mayor_venta": mayor,
        "mes_menor_venta": menor,
        "total_anual": round(sum(d["total"] for d in datos), 2),
    }
```

Ojo con un detalle: PostgreSQL devuelve `NUMERIC` como `Decimal`, que **no es serializable a JSON**. Siempre `float()`.

### Archivos

- Rol 2 → `analisis_exploratorio.py`
- Rol 3 → `analisis_segmentacion.py`
- Rol 4 → `mcp_server.py` y `agente/`

---

## ROL 2 — Análisis exploratorio y tendencias

Cubre los puntos **2 y 3** del alcance.

### Funciones a entregar

| Función | Qué responde |
|---|---|
| `estadisticas_basicas(variable=None)` | Media, mediana, moda, desv. estándar, min, max de `edad`, `venta_total`, `monto_compra`, `n_compras`, `tiempo`. Si `variable` es `None`, todas. |
| `ventas_por_mes(orden="cronologico")` | Total por mes + mes mayor y menor (punto 3.a) |
| `distribucion_metodo_pago()` | Conteo, monto y porcentaje por método |
| `distribucion_navegador()` | Conteo, monto y porcentaje por navegador + más y menos usado (punto 3.b) |
| `distribucion_boletin_vale()` | Distribución cruzada de ambas banderas |
| `ventas_contra_entrega()` | Total y porcentaje con `metodo_pago_id = 0` (punto 3.c) |
| `promociones_por_mes()` | Meses con más boletines y más vales (punto 3.d) |

### Gráficos (4 de los 7 mínimos)

1. Líneas — ventas por mes
2. Barras — ventas por método de pago
3. Barras — distribución por navegador
4. Barras agrupadas — boletín y vale por mes

Guardar en `graficas/` como PNG a 150 dpi mínimo. Títulos y ejes en español, con unidades.

### Del informe

Ninguna sección propia. Aportan una conclusión, dos acciones concretas y una pregunta del punto 8.

---

## ROL 3 — Segmentación y correlación

Cubre los puntos **4 y 5** del alcance.

### Funciones a entregar

| Función | Qué responde |
|---|---|
| `segmentar_por_edad(rangos=None)` | Agrupar por rango etario y analizar patrones (punto 4.a) |
| `comparar_generos()` | Comportamiento de compra M vs F (punto 4.b) |
| `patrones_boletin_vale()` | Patrones de compra según uso de promociones (punto 4.c) |
| `correlacion_edad_venta()` | Relación entre edad y venta total (punto 5.a) |
| `correlacion_genero_metodo_pago()` | Relación género ↔ método de pago (punto 5.b) |
| `correlacion_boletin_vale()` | Relación entre uso de boletines y vales (punto 5.c) |

### Nota estadística importante

**Género y método de pago son variables categóricas.** Aplicarles Pearson es un error metodológico. Usen **chi-cuadrado de independencia** y reporten **Cramér's V** como medida de fuerza:

```python
from scipy.stats import chi2_contingency
import numpy as np

def cramers_v(tabla):
    chi2 = chi2_contingency(tabla)[0]
    n = tabla.values.sum()
    return np.sqrt(chi2 / (n * (min(tabla.shape) - 1)))
```

Interpretación: <0.10 despreciable · 0.10–0.30 débil · 0.30–0.50 moderada · >0.50 fuerte.

Para edad ↔ venta_total, que son ambas continuas, Pearson sí aplica. Reporten también el p-valor: con 6500 registros una correlación de 0.03 puede salir "significativa" y no significar nada. **Comenten el tamaño del efecto, no solo la significancia.**

Rangos etarios sugeridos: 18–25, 26–35, 36–45, 46–55, 56+. Ajusten según la distribución real.

### Gráficos (3 de los 7 mínimos)

5. Dispersión — edad vs venta_total, con línea de tendencia
6. Barras agrupadas — comportamiento por rango etario y género
7. Mapa de calor — matriz de correlación

### Del informe

Sección **Metodología**: por qué eligieron cada tipo de visualización para cada hallazgo. Más una conclusión, dos acciones y una pregunta del punto 8.

---

## ROL 4 — Agente conversacional

Cubre el requisito de que **los puntos 2 al 6 sean consultables por chat**. Son 30 de los 100 puntos de la rúbrica.

### Entregables

**1. MCP Server** (`mcp_server.py`) que expone las funciones de los roles 2 y 3 como herramientas.

**2. Agente en Google ADK** conectado al MCP. Usar **Gemini Flash o Flash-lite** (gratuitos con límite de tokens, según recomienda el enunciado).

**3. System prompt** que instruya al agente a:
- Responder siempre con datos de las herramientas, nunca inventar cifras
- Usar las etiquetas legibles ("Tarjeta de Crédito", no "1")
- Decir explícitamente cuando no tenga una herramienta para lo que le preguntan

**4. Batería de pruebas**: 15–20 preguntas con capturas para el informe.

### Regla de diseño crítica

**No expongan una herramienta genérica de tipo `ejecutar_sql(query)`.** Es tentador y es un error: el modelo genera SQL inconsistente y abre un hueco de inyección.

Expongan **8–12 herramientas específicas**, una por pregunta de negocio. El docstring de cada una es lo que el modelo lee para decidir cuándo usarla — inviertan tiempo ahí.

### Preguntas de prueba sugeridas

- ¿Cuál fue el mes con más ventas?
- ¿Qué navegador es el menos popular?
- ¿Cuánto se vendió contra entrega?
- Compará el gasto promedio entre hombres y mujeres
- ¿Hay relación entre la edad y cuánto gasta un cliente?
- ¿Los clientes que reciben el boletín compran más?
- ¿Qué porcentaje de las ventas fue en tienda física?
- Dame las estadísticas básicas de la edad
- ¿En qué meses se usaron más vales?

### Del informe

Sección **Planificación** (división de tareas, tecnologías elegidas y por qué, plazos) + armado y maquetado del PDF final.

---

## 6. Trabajo compartido

Cada quien aporta:

- **Una conclusión** del punto 7.a — **mínimo 20 líneas cada una**. No es negociable, lo pide el enunciado.
- **Dos acciones concretas** del punto 7.b (son 8 en total entre los cuatro).
- **Una o dos preguntas** del punto 8 (son 5 en total; dos personas toman dos).

Reparto sugerido del punto 8:

| Pregunta | Responsable |
|---|---|
| a. Diferenciación de la competencia | Rol 3 |
| b. Decisiones estratégicas | Rol 2 |
| c. Ahorro de costos / eficiencia | Rol 1 |
| d. Datos adicionales recomendados | Rol 1 |
| e. Impacto del chat de IA a futuro | Rol 4 |

---

## 7. Entregable final

**Archivo:** `SOG2-2S26_grupo14.pdf` — nombre exacto, se entrega en UEDI.

Debe contener: presentación, planificación, proceso de análisis, metodología, conclusiones, recomendaciones, respuestas, diagrama de la BD y código.

### Penalizaciones a evitar

| Penalización | Estado |
|---|---|
| No usar BD relacional (−20%) | Cubierto: PostgreSQL, 5 tablas normalizadas |
| BD no en la nube (−20%) | Cubierto: Supabase |
| **Entrega tarde (−100%)** | **Ojo con esto** |
| Copias | Nota 0 y reporte a la escuela |

---

## 8. Cronograma sugerido (20 h estimadas)

| Fase | Horas | Quién |
|---|---|---|
| BD y ETL | 1–5 | Rol 1 ✅ hecho |
| Funciones de análisis | 5–12 | Roles 2 y 3 en paralelo |
| MCP + agente | 8–15 | Rol 4 (arranca con funciones parciales) |
| Integración y pruebas | 15–18 | Todos |
| Redacción y PDF | 18–20 | Todos, maqueta Rol 4 |

**Punto de sincronización clave:** el Rol 4 no puede esperar a que los roles 2 y 3 terminen todo. En cuanto tengan **dos o tres funciones listas**, súbanlas al repo para que empiece a envolver el MCP. Trabajar en serie no cabe en 20 horas.

---

## 9. Convenciones de Git

Rama por rol: `rol2-exploratorio`, `rol3-segmentacion`, `rol4-agente`. Merge a `main` cuando esté probado.

**Nunca commitear:** `.env`, `__pycache__/`, checkpoints de notebooks. Ya está en `.gitignore`.

Antes de cada push, verifiquen que no hay credenciales:

```bash
git diff --cached | grep -i -E "password|supabase|postgresql://"
```
