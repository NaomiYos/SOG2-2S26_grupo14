"""
analisis_exploratorio.py - Rol 2: Analisis exploratorio y tendencias.
Cubre los puntos 2 y 3 del alcance de la practica.

Contrato (ver GUIA_EQUIPO.md seccion 5):
  - Las funciones de datos devuelven dict serializable a JSON, nunca imprimen.
  - Los graficos van en funciones separadas con sufijo _grafico.
  - Se consulta siempre via db.consultar(), nunca abriendo conexiones sueltas.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import consultar

DIR_GRAFICAS = "graficas"
os.makedirs(DIR_GRAFICAS, exist_ok=True)

VARIABLES_NUMERICAS = ["edad", "venta_total", "monto_compra", "n_compras", "tiempo"]

# La vista v_ventas devuelve nombre_mes en ingles (TO_CHAR usa el locale
# del servidor de Supabase, que no es es_ES). La practica exige titulos
# y ejes en espanol, asi que el nombre de mes se traduce aqui en vez de
# depender del locale de la base.
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


# ================================================================
# FUNCIONES DE DATOS
# ================================================================

def estadisticas_basicas(variable: str = None) -> dict:
    """
    Calcula estadisticas descriptivas (media, mediana, moda, desviacion
    estandar, minimo, maximo) para las variables numericas del dataset.

    Args:
        variable: nombre de la variable a analizar. Debe ser una de
            "edad", "venta_total", "monto_compra", "n_compras", "tiempo".
            Si es None, se calculan todas.

    Returns:
        dict con una entrada por variable calculada, cada una con
        media, mediana, moda, desviacion_estandar, minimo y maximo.
    """
    variables = [variable] if variable else VARIABLES_NUMERICAS
    invalidas = [v for v in variables if v not in VARIABLES_NUMERICAS]
    if invalidas:
        return {"error": f"Variable(s) invalida(s): {invalidas}. "
                          f"Validas: {VARIABLES_NUMERICAS}"}

    cols = ", ".join(f"{v}" for v in variables)
    # una sola fila por cliente evita contar venta_total/n_compras/edad
    # repetidos por cada compra (aqui no afecta, hay 1 compra por cliente,
    # pero se deja explicito por si el detalle transaccional crece a futuro)
    df = consultar(f"SELECT {cols} FROM v_ventas")

    resultado = {}
    for v in variables:
        serie = df[v]
        moda = serie.mode()
        resultado[v] = {
            "media": round(float(serie.mean()), 2),
            "mediana": round(float(serie.median()), 2),
            "moda": round(float(moda.iloc[0]), 2) if not moda.empty else None,
            "desviacion_estandar": round(float(serie.std()), 2),
            "minimo": round(float(serie.min()), 2),
            "maximo": round(float(serie.max()), 2),
        }

    return {"variables": resultado}


def ventas_por_mes(orden: str = "cronologico") -> dict:
    """
    Devuelve el total de ventas de cada mes de 2021.

    Args:
        orden: "cronologico" (enero a diciembre) o "monto" (mayor a menor).

    Returns:
        dict con la lista de meses, su total vendido y el numero de
        transacciones, mas el mes de mayor y el de menor venta.
    """
    df = consultar("""
        SELECT mes,
               SUM(monto_compra) AS total,
               COUNT(*)          AS transacciones
        FROM v_ventas
        GROUP BY mes
        ORDER BY mes
    """)

    datos = [
        {
            "mes": int(r.mes),
            "nombre_mes": MESES_ES[int(r.mes)],
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


def distribucion_metodo_pago() -> dict:
    """
    Devuelve cuantas compras y cuanto monto corresponde a cada metodo de
    pago (Efectivo/Contra entrega, Tarjeta de Credito, Tarjeta de Debito),
    junto con el porcentaje de transacciones de cada uno.

    Returns:
        dict con la lista de metodos de pago (nombre, transacciones,
        monto total, porcentaje) y el metodo mas usado.
    """
    df = consultar("""
        SELECT metodo_pago, metodo_pago_id,
               COUNT(*)          AS transacciones,
               SUM(monto_compra) AS monto_total
        FROM v_ventas
        GROUP BY metodo_pago, metodo_pago_id
        ORDER BY metodo_pago_id
    """)

    total_transacciones = int(df["transacciones"].sum())
    datos = [
        {
            "metodo_pago": str(r.metodo_pago),
            "metodo_pago_id": int(r.metodo_pago_id),
            "transacciones": int(r.transacciones),
            "monto_total": round(float(r.monto_total), 2),
            "porcentaje": round(100 * r.transacciones / total_transacciones, 2),
        }
        for r in df.itertuples()
    ]

    mas_usado = max(datos, key=lambda d: d["transacciones"])

    return {"metodos": datos, "metodo_mas_usado": mas_usado}


def distribucion_navegador() -> dict:
    """
    Devuelve cuantas compras y cuanto monto corresponde a cada navegador
    (incluye "Tienda Fisica" como una categoria mas), junto con el
    porcentaje de transacciones de cada uno.

    Returns:
        dict con la lista de navegadores (nombre, transacciones, monto
        total, porcentaje), el mas y el menos utilizado, y el porcentaje
        de ventas hechas en tienda fisica frente al total online.
    """
    df = consultar("""
        SELECT navegador, navegador_id, es_online,
               COUNT(*)          AS transacciones,
               SUM(monto_compra) AS monto_total
        FROM v_ventas
        GROUP BY navegador, navegador_id, es_online
        ORDER BY navegador_id
    """)

    total_transacciones = int(df["transacciones"].sum())
    datos = [
        {
            "navegador": str(r.navegador),
            "navegador_id": int(r.navegador_id),
            "es_online": bool(r.es_online),
            "transacciones": int(r.transacciones),
            "monto_total": round(float(r.monto_total), 2),
            "porcentaje": round(100 * r.transacciones / total_transacciones, 2),
        }
        for r in df.itertuples()
    ]

    mas_usado = max(datos, key=lambda d: d["transacciones"])
    menos_usado = min(datos, key=lambda d: d["transacciones"])
    tienda_fisica = next((d for d in datos if not d["es_online"]), None)

    return {
        "navegadores": datos,
        "navegador_mas_usado": mas_usado,
        "navegador_menos_usado": menos_usado,
        "porcentaje_tienda_fisica": tienda_fisica["porcentaje"] if tienda_fisica else 0.0,
    }


def distribucion_boletin_vale() -> dict:
    """
    Cruza el uso de boletin y vale entre los clientes: cuantas compras
    tuvieron ambos, solo boletin, solo vale, o ninguno.

    Returns:
        dict con las cuatro combinaciones (boletin, vale, transacciones,
        porcentaje) y los totales de boletin=True y vale=True por separado.
    """
    df = consultar("""
        SELECT boletin, vale, COUNT(*) AS transacciones
        FROM v_ventas
        GROUP BY boletin, vale
        ORDER BY boletin DESC, vale DESC
    """)

    total = int(df["transacciones"].sum())
    combinaciones = [
        {
            "boletin": bool(r.boletin),
            "vale": bool(r.vale),
            "transacciones": int(r.transacciones),
            "porcentaje": round(100 * r.transacciones / total, 2),
        }
        for r in df.itertuples()
    ]

    total_boletin = sum(c["transacciones"] for c in combinaciones if c["boletin"])
    total_vale = sum(c["transacciones"] for c in combinaciones if c["vale"])

    return {
        "combinaciones": combinaciones,
        "total_con_boletin": total_boletin,
        "total_con_vale": total_vale,
        "porcentaje_con_boletin": round(100 * total_boletin / total, 2),
        "porcentaje_con_vale": round(100 * total_vale / total, 2),
    }


def ventas_contra_entrega() -> dict:
    """
    Calcula el total vendido y el porcentaje de transacciones pagadas en
    efectivo o contra entrega (metodo_pago_id = 0), frente al resto de
    metodos de pago.

    Returns:
        dict con transacciones y monto de contra entrega/efectivo,
        el total general, y el porcentaje que representa.
    """
    df = consultar("""
        SELECT
            COUNT(*) FILTER (WHERE metodo_pago_id = 0) AS transacciones_contra_entrega,
            SUM(monto_compra) FILTER (WHERE metodo_pago_id = 0) AS monto_contra_entrega,
            COUNT(*)          AS transacciones_totales,
            SUM(monto_compra) AS monto_total
        FROM v_ventas
    """)
    r = df.iloc[0]

    transacciones_ce = int(r["transacciones_contra_entrega"])
    monto_ce = float(r["monto_contra_entrega"] or 0)
    total_transacciones = int(r["transacciones_totales"])
    monto_total = float(r["monto_total"])

    return {
        "transacciones_contra_entrega": transacciones_ce,
        "monto_contra_entrega": round(monto_ce, 2),
        "porcentaje_transacciones": round(100 * transacciones_ce / total_transacciones, 2),
        "porcentaje_monto": round(100 * monto_ce / monto_total, 2),
        "transacciones_totales": total_transacciones,
        "monto_total": round(monto_total, 2),
    }


def promociones_por_mes() -> dict:
    """
    Identifica en que meses de 2021 se usaron mas boletines y mas vales.

    Returns:
        dict con el detalle mensual de boletines y vales usados, y el
        mes con mas boletines y el mes con mas vales.
    """
    df = consultar("""
        SELECT mes,
               COUNT(*) FILTER (WHERE boletin) AS boletines,
               COUNT(*) FILTER (WHERE vale)    AS vales
        FROM v_ventas
        GROUP BY mes
        ORDER BY mes
    """)

    datos = [
        {
            "mes": int(r.mes),
            "nombre_mes": MESES_ES[int(r.mes)],
            "boletines": int(r.boletines),
            "vales": int(r.vales),
        }
        for r in df.itertuples()
    ]

    mes_mas_boletines = max(datos, key=lambda d: d["boletines"])
    mes_mas_vales = max(datos, key=lambda d: d["vales"])

    return {
        "meses": datos,
        "mes_mas_boletines": mes_mas_boletines,
        "mes_mas_vales": mes_mas_vales,
    }


# ================================================================
# GRAFICOS
# ================================================================

def ventas_por_mes_grafico(ruta: str = None) -> str:
    """Genera un grafico de lineas con el total de ventas por mes de 2021."""
    datos = ventas_por_mes()["meses"]
    meses = [d["nombre_mes"] for d in datos]
    totales = [d["total"] for d in datos]

    plt.figure(figsize=(10, 5))
    plt.plot(meses, totales, marker="o", color="#2563eb")
    plt.title("Ventas totales por mes (2021)")
    plt.xlabel("Mes")
    plt.ylabel("Monto vendido (Q)")
    plt.xticks(rotation=45, ha="right")
    plt.grid(alpha=0.3)
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "ventas_por_mes.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


def distribucion_metodo_pago_grafico(ruta: str = None) -> str:
    """Genera un grafico de barras con las transacciones por metodo de pago."""
    datos = distribucion_metodo_pago()["metodos"]
    nombres = [d["metodo_pago"] for d in datos]
    transacciones = [d["transacciones"] for d in datos]

    plt.figure(figsize=(8, 5))
    plt.bar(nombres, transacciones, color="#16a34a")
    plt.title("Transacciones por metodo de pago")
    plt.xlabel("Metodo de pago")
    plt.ylabel("Numero de transacciones")
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "distribucion_metodo_pago.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


def distribucion_navegador_grafico(ruta: str = None) -> str:
    """Genera un grafico de barras con las transacciones por navegador."""
    datos = distribucion_navegador()["navegadores"]
    nombres = [d["navegador"] for d in datos]
    transacciones = [d["transacciones"] for d in datos]

    plt.figure(figsize=(8, 5))
    plt.bar(nombres, transacciones, color="#d97706")
    plt.title("Transacciones por navegador")
    plt.xlabel("Navegador")
    plt.ylabel("Numero de transacciones")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "distribucion_navegador.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


def boletin_vale_por_mes_grafico(ruta: str = None) -> str:
    """Genera un grafico de barras agrupadas con boletines y vales usados por mes."""
    datos = promociones_por_mes()["meses"]
    meses = [d["nombre_mes"] for d in datos]
    boletines = [d["boletines"] for d in datos]
    vales = [d["vales"] for d in datos]

    x = range(len(meses))
    ancho = 0.35

    plt.figure(figsize=(11, 5))
    plt.bar([i - ancho / 2 for i in x], boletines, width=ancho, label="Boletin", color="#7c3aed")
    plt.bar([i + ancho / 2 for i in x], vales, width=ancho, label="Vale", color="#db2777")
    plt.xticks(list(x), meses, rotation=45, ha="right")
    plt.title("Boletines y vales usados por mes (2021)")
    plt.xlabel("Mes")
    plt.ylabel("Cantidad de compras")
    plt.legend()
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "boletin_vale_por_mes.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


if __name__ == "__main__":
    print("estadisticas_basicas:", estadisticas_basicas())
    print("ventas_por_mes:", ventas_por_mes())
    print("distribucion_metodo_pago:", distribucion_metodo_pago())
    print("distribucion_navegador:", distribucion_navegador())
    print("distribucion_boletin_vale:", distribucion_boletin_vale())
    print("ventas_contra_entrega:", ventas_contra_entrega())
    print("promociones_por_mes:", promociones_por_mes())

    print("\nGenerando graficos en", DIR_GRAFICAS)
    print(ventas_por_mes_grafico())
    print(distribucion_metodo_pago_grafico())
    print(distribucion_navegador_grafico())
    print(boletin_vale_por_mes_grafico())
