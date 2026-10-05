"""
analisis_segmentacion.py - Rol 3: Segmentacion de clientes y correlacion.
Cubre los puntos 4 y 5 del alcance de la practica.

Nota metodologica (ver GUIA_EQUIPO.md seccion ROL 3):
  - Genero y metodo de pago son categoricas: se usa chi-cuadrado de
    independencia + Cramer's V, nunca Pearson.
  - Edad y venta_total son continuas: Pearson si aplica, reportando
    tambien el p-valor y comentando el tamano del efecto.

Contrato (ver GUIA_EQUIPO.md seccion 5): las funciones de datos
devuelven dict serializable a JSON, nunca imprimen. Los graficos van
en funciones separadas con sufijo _grafico.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency, pearsonr

from db import consultar

DIR_GRAFICAS = "graficas"
os.makedirs(DIR_GRAFICAS, exist_ok=True)

RANGOS_EDAD_DEFECTO = [(18, 25), (26, 35), (36, 45), (46, 55), (56, 120)]


def _etiquetar_rango_edad(edad: int, rangos: list) -> str:
    for lo, hi in rangos:
        if lo <= edad <= hi:
            etiqueta = f"{lo}-{hi}" if hi < 120 else f"{lo}+"
            return etiqueta
    return "otro"


def _interpretar_cramers_v(v: float) -> str:
    if v < 0.10:
        return "despreciable"
    if v < 0.30:
        return "debil"
    if v < 0.50:
        return "moderada"
    return "fuerte"


def cramers_v(tabla: pd.DataFrame) -> float:
    """Calcula Cramer's V a partir de una tabla de contingencia."""
    chi2 = chi2_contingency(tabla)[0]
    n = tabla.values.sum()
    return float(np.sqrt(chi2 / (n * (min(tabla.shape) - 1))))


# ================================================================
# FUNCIONES DE DATOS
# ================================================================

def segmentar_por_edad(rangos: list = None) -> dict:
    """
    Agrupa a los clientes en rangos etarios y analiza sus patrones de
    compra (venta total promedio, monto promedio por compra, numero de
    compras promedio).

    Args:
        rangos: lista de tuplas (edad_min, edad_max) que define los
            rangos etarios. Si es None, usa 18-25, 26-35, 36-45, 46-55, 56+.

    Returns:
        dict con estadisticas de venta_total, monto_compra y n_compras
        por rango de edad, mas el rango con mayor venta_total promedio.
    """
    rangos = rangos or RANGOS_EDAD_DEFECTO

    df = consultar("SELECT edad, venta_total, monto_compra, n_compras FROM v_ventas")
    df["rango_edad"] = df["edad"].apply(lambda e: _etiquetar_rango_edad(e, rangos))

    agrupado = df.groupby("rango_edad").agg(
        clientes=("edad", "count"),
        venta_total_promedio=("venta_total", "mean"),
        monto_compra_promedio=("monto_compra", "mean"),
        n_compras_promedio=("n_compras", "mean"),
    ).reset_index()

    orden = [_etiquetar_rango_edad(lo, rangos) for lo, hi in rangos]
    agrupado["orden"] = agrupado["rango_edad"].apply(
        lambda r: orden.index(r) if r in orden else len(orden)
    )
    agrupado = agrupado.sort_values("orden")

    datos = [
        {
            "rango_edad": str(r.rango_edad),
            "clientes": int(r.clientes),
            "venta_total_promedio": round(float(r.venta_total_promedio), 2),
            "monto_compra_promedio": round(float(r.monto_compra_promedio), 2),
            "n_compras_promedio": round(float(r.n_compras_promedio), 2),
        }
        for r in agrupado.itertuples()
    ]

    mayor_venta = max(datos, key=lambda d: d["venta_total_promedio"])

    return {"rangos": datos, "rango_mayor_venta_promedio": mayor_venta}


def comparar_generos() -> dict:
    """
    Compara el comportamiento de compra entre clientes masculinos y
    femeninos: venta total promedio, monto promedio por compra y numero
    de compras promedio, mas una prueba t de diferencia de medias sobre
    venta_total.

    Returns:
        dict con las metricas promedio por genero y el resultado
        (estadistico t, p-valor, si la diferencia es significativa al 5%)
        de la comparacion de venta_total entre generos.
    """
    from scipy.stats import ttest_ind

    df = consultar("SELECT genero, venta_total, monto_compra, n_compras FROM v_ventas")

    agrupado = df.groupby("genero").agg(
        clientes=("genero", "count"),
        venta_total_promedio=("venta_total", "mean"),
        monto_compra_promedio=("monto_compra", "mean"),
        n_compras_promedio=("n_compras", "mean"),
    ).reset_index()

    por_genero = [
        {
            "genero": str(r.genero),
            "clientes": int(r.clientes),
            "venta_total_promedio": round(float(r.venta_total_promedio), 2),
            "monto_compra_promedio": round(float(r.monto_compra_promedio), 2),
            "n_compras_promedio": round(float(r.n_compras_promedio), 2),
        }
        for r in agrupado.itertuples()
    ]

    generos = df["genero"].unique()
    grupo_a = df[df["genero"] == generos[0]]["venta_total"]
    grupo_b = df[df["genero"] == generos[1]]["venta_total"]
    t_stat, p_valor = ttest_ind(grupo_a, grupo_b, equal_var=False)

    return {
        "por_genero": por_genero,
        "prueba_t_venta_total": {
            "estadistico_t": round(float(t_stat), 4),
            "p_valor": round(float(p_valor), 4),
            "diferencia_significativa_95": bool(p_valor < 0.05),
        },
    }


def patrones_boletin_vale() -> dict:
    """
    Agrupa a los clientes segun si reciben boletin y/o usan vale, y
    analiza su patron de compra (venta total promedio, monto promedio
    por compra, numero de compras promedio) en cada combinacion.

    Returns:
        dict con las cuatro combinaciones (boletin, vale) y sus
        metricas promedio, mas la combinacion con mayor venta_total
        promedio.
    """
    df = consultar("SELECT boletin, vale, venta_total, monto_compra, n_compras FROM v_ventas")

    agrupado = df.groupby(["boletin", "vale"]).agg(
        clientes=("boletin", "count"),
        venta_total_promedio=("venta_total", "mean"),
        monto_compra_promedio=("monto_compra", "mean"),
        n_compras_promedio=("n_compras", "mean"),
    ).reset_index()

    datos = [
        {
            "boletin": bool(r.boletin),
            "vale": bool(r.vale),
            "clientes": int(r.clientes),
            "venta_total_promedio": round(float(r.venta_total_promedio), 2),
            "monto_compra_promedio": round(float(r.monto_compra_promedio), 2),
            "n_compras_promedio": round(float(r.n_compras_promedio), 2),
        }
        for r in agrupado.itertuples()
    ]

    mayor_venta = max(datos, key=lambda d: d["venta_total_promedio"])

    return {"combinaciones": datos, "combinacion_mayor_venta_promedio": mayor_venta}


def correlacion_edad_venta() -> dict:
    """
    Investiga si existe relacion entre la edad del cliente y su venta
    total, usando el coeficiente de correlacion de Pearson (ambas son
    variables continuas).

    Returns:
        dict con el coeficiente r, el p-valor, si es estadisticamente
        significativo al 5%, y una interpretacion del tamano del efecto
        (no solo de la significancia).
    """
    df = consultar("SELECT edad, venta_total FROM v_ventas")
    r, p_valor = pearsonr(df["edad"], df["venta_total"])

    abs_r = abs(r)
    if abs_r < 0.10:
        efecto = "despreciable"
    elif abs_r < 0.30:
        efecto = "debil"
    elif abs_r < 0.50:
        efecto = "moderado"
    else:
        efecto = "fuerte"

    return {
        "coeficiente_r": round(float(r), 4),
        "p_valor": round(float(p_valor), 6),
        "significativo_95": bool(p_valor < 0.05),
        "tamano_efecto": efecto,
        "n_observaciones": int(len(df)),
        "nota": "Con muestras grandes un p-valor bajo no implica que el "
                "efecto sea relevante; el tamano del efecto (r) es lo que "
                "importa para decidir si la relacion es fuerte.",
    }


def correlacion_genero_metodo_pago() -> dict:
    """
    Examina si existe asociacion entre el genero del cliente y el
    metodo de pago preferido, usando chi-cuadrado de independencia y
    Cramer's V como medida de fuerza (ambas son variables categoricas,
    Pearson no aplica).

    Returns:
        dict con la tabla de contingencia, el estadistico chi-cuadrado,
        el p-valor, Cramer's V y su interpretacion (despreciable / debil
        / moderada / fuerte).
    """
    df = consultar("SELECT genero, metodo_pago FROM v_ventas")
    tabla = pd.crosstab(df["genero"], df["metodo_pago"])

    chi2, p_valor, gl, _ = chi2_contingency(tabla)
    v = cramers_v(tabla)

    return {
        "tabla_contingencia": {
            genero: {metodo: int(tabla.loc[genero, metodo]) for metodo in tabla.columns}
            for genero in tabla.index
        },
        "chi_cuadrado": round(float(chi2), 4),
        "grados_libertad": int(gl),
        "p_valor": round(float(p_valor), 6),
        "significativo_95": bool(p_valor < 0.05),
        "cramers_v": round(v, 4),
        "fuerza_asociacion": _interpretar_cramers_v(v),
    }


def correlacion_boletin_vale() -> dict:
    """
    Investiga si existe asociacion entre recibir boletin y usar vale,
    usando chi-cuadrado de independencia y Cramer's V (ambas son
    variables categoricas binarias).

    Returns:
        dict con la tabla de contingencia, el estadistico chi-cuadrado,
        el p-valor, Cramer's V y su interpretacion.
    """
    df = consultar("SELECT boletin, vale FROM v_ventas")
    tabla = pd.crosstab(df["boletin"], df["vale"])

    chi2, p_valor, gl, _ = chi2_contingency(tabla)
    v = cramers_v(tabla)

    return {
        "tabla_contingencia": {
            str(boletin): {str(vale): int(tabla.loc[boletin, vale]) for vale in tabla.columns}
            for boletin in tabla.index
        },
        "chi_cuadrado": round(float(chi2), 4),
        "grados_libertad": int(gl),
        "p_valor": round(float(p_valor), 6),
        "significativo_95": bool(p_valor < 0.05),
        "cramers_v": round(v, 4),
        "fuerza_asociacion": _interpretar_cramers_v(v),
    }


# ================================================================
# GRAFICOS
# ================================================================

def edad_venta_grafico(ruta: str = None) -> str:
    """Genera un grafico de dispersion de edad vs venta_total con linea de tendencia."""
    df = consultar("SELECT edad, venta_total FROM v_ventas")

    plt.figure(figsize=(8, 6))
    plt.scatter(df["edad"], df["venta_total"], alpha=0.3, color="#2563eb", s=15)

    m, b = np.polyfit(df["edad"], df["venta_total"], 1)
    x_linea = np.array([df["edad"].min(), df["edad"].max()])
    plt.plot(x_linea, m * x_linea + b, color="#dc2626", linewidth=2, label="Tendencia lineal")

    plt.title("Edad vs. venta total del cliente")
    plt.xlabel("Edad (anios)")
    plt.ylabel("Venta total (Q)")
    plt.legend()
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "edad_vs_venta_total.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


def comportamiento_edad_genero_grafico(rangos: list = None, ruta: str = None) -> str:
    """Genera un grafico de barras agrupadas de venta_total promedio por rango de edad y genero."""
    rangos = rangos or RANGOS_EDAD_DEFECTO

    df = consultar("SELECT edad, genero, venta_total FROM v_ventas")
    df["rango_edad"] = df["edad"].apply(lambda e: _etiquetar_rango_edad(e, rangos))

    orden = [_etiquetar_rango_edad(lo, rangos) for lo, hi in rangos]
    agrupado = df.groupby(["rango_edad", "genero"])["venta_total"].mean().unstack()
    agrupado = agrupado.reindex(orden)

    agrupado.plot(kind="bar", figsize=(10, 6), color=["#2563eb", "#db2777"])
    plt.title("Venta total promedio por rango de edad y genero")
    plt.xlabel("Rango de edad")
    plt.ylabel("Venta total promedio (Q)")
    plt.xticks(rotation=0)
    plt.legend(title="Genero")
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "comportamiento_edad_genero.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


def matriz_correlacion_grafico(ruta: str = None) -> str:
    """Genera un mapa de calor con la matriz de correlacion de las variables numericas."""
    df = consultar("SELECT edad, venta_total, monto_compra, n_compras, tiempo FROM v_ventas")
    corr = df.corr(numeric_only=True)

    plt.figure(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, square=True)
    plt.title("Matriz de correlacion - variables numericas")
    plt.tight_layout()

    ruta = ruta or os.path.join(DIR_GRAFICAS, "matriz_correlacion.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    return ruta


if __name__ == "__main__":
    print("segmentar_por_edad:", segmentar_por_edad())
    print("comparar_generos:", comparar_generos())
    print("patrones_boletin_vale:", patrones_boletin_vale())
    print("correlacion_edad_venta:", correlacion_edad_venta())
    print("correlacion_genero_metodo_pago:", correlacion_genero_metodo_pago())
    print("correlacion_boletin_vale:", correlacion_boletin_vale())

    print("\nGenerando graficos en", DIR_GRAFICAS)
    print(edad_venta_grafico())
    print(comportamiento_edad_genero_grafico())
    print(matriz_correlacion_grafico())
