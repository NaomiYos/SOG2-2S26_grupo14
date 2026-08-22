"""
Perfilado del CSV de ventas 2021.
Se ejecuta ANTES de definir el esquema. No modifica nada, solo reporta.

Uso:  python 01_perfilado.py ruta/al/ventas.csv
"""

import sys
import pandas as pd

RUTA = sys.argv[1] if len(sys.argv) > 1 else "Venta_online_c.csv"

# encoding: los CSV de esta practica suelen venir en latin-1 por la "i" de Boletin.
# Si utf-8 falla, cae a latin-1 automaticamente.
try:
    df = pd.read_csv(RUTA, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(RUTA, encoding="latin-1")
    print(">> Archivo leido como latin-1 (no era utf-8)\n")

print("=" * 70)
print("1. FORMA Y COLUMNAS")
print("=" * 70)
print(f"Filas: {len(df)}   Columnas: {len(df.columns)}")
print("\nNombres reales de columna (ojo con tildes y espacios):")
for c in df.columns:
    print(f"  [{c}]  ->  dtype: {df[c].dtype}")

print("\n" + "=" * 70)
print("2. LA PREGUNTA CLAVE: se repite Id_cliente?")
print("=" * 70)
col_id = [c for c in df.columns if "cliente" in c.lower()][0]
n_unicos = df[col_id].nunique()
print(f"Filas totales:      {len(df)}")
print(f"Id_cliente unicos:  {n_unicos}")
if n_unicos == len(df):
    print(">> UNA fila por cliente. N_Compras es un contador agregado.")
    print(">> El CSV NO trae el detalle transaccional.")
else:
    print(">> Id_cliente SE REPITE. Cada fila es una transaccion.")
    print(">> Se puede normalizar en clientes + compras.")
    # verificar si los atributos de cliente son consistentes entre filas
    for attr in ["Edad", "Genero", "Venta_total", "N_Compras"]:
        if attr in df.columns:
            inconsistentes = df.groupby(col_id)[attr].nunique()
            n_malos = (inconsistentes > 1).sum()
            estado = "OK" if n_malos == 0 else f"{n_malos} clientes INCONSISTENTES"
            print(f"   {attr}: {estado}")

print("\n" + "=" * 70)
print("3. NULOS")
print("=" * 70)
nulos = df.isna().sum()
nulos = nulos[nulos > 0]
if len(nulos) == 0:
    print("Sin valores nulos.")
else:
    for col, n in nulos.items():
        print(f"  {col}: {n} ({n / len(df) * 100:.2f}%)")

print("\n" + "=" * 70)
print("4. DUPLICADOS DE FILA COMPLETA")
print("=" * 70)
print(f"Filas identicas duplicadas: {df.duplicated().sum()}")

print("\n" + "=" * 70)
print("5. DOMINIOS DE LAS CATEGORICAS (validar contra el enunciado)")
print("=" * 70)
esperado = {
    "Genero": {0, 1},
    "MetodoPago": {0, 1, 2},
    "Navegador": {0, 1, 2, 3, 4},
    "Boletin": {0, 1},
    "Boletín": {0, 1},
    "Vale": {0, 1},
}
for col, dom in esperado.items():
    if col in df.columns:
        reales = set(df[col].dropna().unique())
        extra = reales - dom
        marca = "OK" if not extra else f"VALORES FUERA DE DOMINIO: {extra}"
        print(f"  {col}: {sorted(reales)}  -> {marca}")
        print(f"     conteo:\n{df[col].value_counts().to_string()}")

print("\n" + "=" * 70)
print("6. NUMERICAS: rangos y valores imposibles")
print("=" * 70)
for col in ["Edad", "Venta_total", "MontoCompra", "N_Compras", "Tiempo"]:
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce")
        n_negativos = (s < 0).sum()
        n_ceros = (s == 0).sum()
        print(f"  {col}: min={s.min()}  max={s.max()}  media={s.mean():.2f}")
        print(f"     negativos={n_negativos}  ceros={n_ceros}  no-numericos={s.isna().sum() - df[col].isna().sum()}")

print("\n" + "=" * 70)
print("7. FECHAS")
print("=" * 70)
col_fecha = [c for c in df.columns if "fecha" in c.lower()]
if col_fecha:
    c = col_fecha[0]
    print(f"Muestra cruda: {df[c].dropna().head(5).tolist()}")
    f = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    print(f"No parseables: {f.isna().sum() - df[c].isna().sum()}")
    print(f"Rango: {f.min()} -> {f.max()}")
    fuera_2021 = ((f.dt.year != 2021) & f.notna()).sum()
    print(f"Fuera del anio 2021: {fuera_2021}")
    print("\nFilas por mes:")
    print(f.dt.month.value_counts().sort_index().to_string())

print("\n" + "=" * 70)
print("8. MUESTRA")
print("=" * 70)
print(df.head(10).to_string())