"""
04_etl_carga.py - ETL del CSV de ventas 2021 hacia PostgreSQL (Supabase).

Cubre el punto 1 del alcance:
  a. Extraer los datos del .csv
  b. Verificar valores faltantes o duplicados y decidir como manejarlos
  c. Asegurar que los tipos de datos sean correctos
  d. Cargar a la base SQL en la nube

Genera bitacora_etl.txt con todo lo que decida el script. Ese archivo
alimenta la seccion "Proceso de analisis" del informe: no lo borren.

Uso:  python 04_etl_carga.py ventas_2021.csv
"""

import sys
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2.extensions as _ext
from psycopg2.extras import execute_values

from db import get_engine

# ----------------------------------------------------------------
# psycopg2 solo entiende tipos nativos de Python. Pandas devuelve
# numpy.int64 / numpy.float64 / numpy.bool_, que el driver no sabe
# traducir a SQL y lanza "can't adapt type 'numpy.int64'".
# Estos adaptadores hacen la conversion automaticamente.
# ----------------------------------------------------------------
_ext.register_adapter(np.int64, lambda v: _ext.AsIs(int(v)))
_ext.register_adapter(np.int32, lambda v: _ext.AsIs(int(v)))
_ext.register_adapter(np.float64, lambda v: _ext.AsIs(float(v)))
_ext.register_adapter(np.float32, lambda v: _ext.AsIs(float(v)))
_ext.register_adapter(np.bool_, lambda v: _ext.AsIs(bool(v)))

RUTA = sys.argv[1] if len(sys.argv) > 1 else "ventas_2021.csv"
BITACORA = "bitacora_etl.txt"

_log_lineas = []


def log(msg=""):
    """Imprime en consola y guarda en la bitacora."""
    print(msg)
    _log_lineas.append(str(msg))


def seccion(titulo):
    log("\n" + "=" * 66)
    log(titulo)
    log("=" * 66)


# ================================================================
# 1. EXTRACCION
# ================================================================
seccion("1. EXTRACCION")
log(f"Archivo: {RUTA}")
log(f"Ejecutado: {datetime.now():%Y-%m-%d %H:%M:%S}")

# El archivo usa ';' como separador y '.' como decimal.
try:
    df = pd.read_csv(RUTA, sep=";", encoding="utf-8")
    log("Encoding: utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(RUTA, sep=";", encoding="latin-1")
    log("Encoding: latin-1 (utf-8 fallo)")

df.columns = [c.strip() for c in df.columns]
df = df.rename(columns={"Boletín": "Boletin"})

log(f"Filas leidas: {len(df)}")
log(f"Columnas: {list(df.columns)}")

filas_iniciales = len(df)

COLUMNAS_ESPERADAS = [
    "Id_cliente", "Edad", "Genero", "Venta_total", "N_Compras",
    "FechaCompra", "MontoCompra", "MetodoPago", "Tiempo",
    "Navegador", "Boletin", "Vale",
]
faltantes = set(COLUMNAS_ESPERADAS) - set(df.columns)
if faltantes:
    log(f"ERROR: faltan columnas {faltantes}")
    sys.exit(1)


# ================================================================
# 2. CALIDAD: NULOS Y DUPLICADOS
# ================================================================
seccion("2. CALIDAD DE DATOS")

nulos = df.isna().sum()
nulos = nulos[nulos > 0]
if len(nulos) == 0:
    log("Nulos: ninguno.")
else:
    log("Nulos detectados:")
    for col, n in nulos.items():
        log(f"   {col}: {n} ({n / len(df) * 100:.2f}%)")
    # DECISION: se eliminan las filas con nulos. Con 6500 registros y una
    # proporcion baja, imputar introduciria sesgo en un analisis descriptivo.
    antes = len(df)
    df = df.dropna()
    log(f"DECISION: eliminar filas con nulos -> {antes - len(df)} filas fuera")

dup_completos = df.duplicated().sum()
log(f"Filas identicas duplicadas: {dup_completos}")
if dup_completos > 0:
    df = df.drop_duplicates()
    log(f"DECISION: eliminadas. Quedan {len(df)} filas")

dup_id = df["Id_cliente"].duplicated().sum()
log(f"Id_cliente duplicados: {dup_id}")
if dup_id > 0:
    # DECISION: Id_cliente es la PK. Se conserva la primera aparicion.
    df = df.drop_duplicates(subset=["Id_cliente"], keep="first")
    log(f"DECISION: conservar primera aparicion -> quedan {len(df)} filas")


# ================================================================
# 3. TIPOS Y TRANSFORMACION
# ================================================================
seccion("3. TIPOS DE DATOS")

# --- Fecha: formato DD.MM.YY, hay que forzarlo. dateutil no lo infiere. ---
df["FechaCompra"] = pd.to_datetime(
    df["FechaCompra"], format="%d.%m.%y", errors="coerce"
)
malas = df["FechaCompra"].isna().sum()
log(f"Fechas no parseables con formato DD.MM.YY: {malas}")
if malas > 0:
    df = df[df["FechaCompra"].notna()]
    log(f"DECISION: descartadas -> quedan {len(df)} filas")

fuera_2021 = (df["FechaCompra"].dt.year != 2021).sum()
log(f"Fechas fuera de 2021: {fuera_2021}")
if fuera_2021 > 0:
    log("   (se conservan; el enunciado dice 2021 pero no obliga a filtrar)")
log(f"Rango de fechas: {df['FechaCompra'].min():%Y-%m-%d} a {df['FechaCompra'].max():%Y-%m-%d}")

# --- Numericos ---
enteros = ["Id_cliente", "Edad", "N_Compras", "Tiempo"]
decimales = ["Venta_total", "MontoCompra"]

for c in enteros:
    df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
for c in decimales:
    df[c] = pd.to_numeric(df[c], errors="coerce")

no_num = df[enteros + decimales].isna().sum().sum()
if no_num > 0:
    log(f"Valores no numericos encontrados: {no_num}")
    df = df.dropna(subset=enteros + decimales)
    log(f"DECISION: descartados -> quedan {len(df)} filas")
else:
    log("Conversion numerica: sin errores.")

# --- Validacion de dominios contra el enunciado ---
log("\nValidacion de dominios:")
DOMINIOS = {
    "Genero": {0, 1},
    "MetodoPago": {0, 1, 2},
    "Navegador": {0, 1, 2, 3, 4},
    "Boletin": {0, 1},
    "Vale": {0, 1},
}
hay_violacion = False
for col, dom in DOMINIOS.items():
    reales = set(df[col].dropna().unique())
    extra = reales - dom
    if extra:
        hay_violacion = True
        n = df[col].isin(extra).sum()
        log(f"   {col}: FUERA DE DOMINIO {extra} en {n} filas")
        df = df[df[col].isin(dom)]
    else:
        log(f"   {col}: OK {sorted(reales)}")

if hay_violacion:
    log(f"DECISION: filas fuera de dominio eliminadas -> quedan {len(df)}")

# --- Coherencia logica ---
log("\nCoherencia logica:")
neg_edad = ((df["Edad"] < 0) | (df["Edad"] > 120)).sum()
neg_monto = (df["MontoCompra"] < 0).sum()
neg_venta = (df["Venta_total"] < 0).sum()
log(f"   Edad fuera de [0,120]:   {neg_edad}")
log(f"   MontoCompra negativo:    {neg_monto}")
log(f"   Venta_total negativo:    {neg_venta}")
if neg_edad or neg_monto or neg_venta:
    df = df[
        (df["Edad"].between(0, 120))
        & (df["MontoCompra"] >= 0)
        & (df["Venta_total"] >= 0)
    ]
    log(f"DECISION: filas incoherentes eliminadas -> quedan {len(df)}")

# --- Banderas a booleano ---
df["Boletin"] = df["Boletin"].astype(int).astype(bool)
df["Vale"] = df["Vale"].astype(int).astype(bool)
log("\nBoletin y Vale convertidos a booleano.")

log(f"\nFilas iniciales: {filas_iniciales}")
log(f"Filas finales:   {len(df)}")
log(f"Descartadas:     {filas_iniciales - len(df)} ({(filas_iniciales - len(df)) / filas_iniciales * 100:.2f}%)")


# ================================================================
# 4. CARGA
# ================================================================
seccion("4. CARGA A POSTGRESQL")

engine = get_engine()
raw = engine.raw_connection()
try:
    cur = raw.cursor()

    # Orden importa: cliente primero (es el padre de la FK).
    log("Limpiando tablas de datos (los catalogos no se tocan)...")
    cur.execute("TRUNCATE TABLE registro_compra, cliente RESTART IDENTITY CASCADE;")

    # --- Conversion explicita a tipos nativos de Python ---
    # No dependemos de los adaptadores de numpy: en Windows con NumPy 2.x
    # el registro de np.int64 no siempre captura el tipo que produce pandas.
    # Convertir valor por valor es infalible y con 6500 filas ni se nota.
    def _py(v):
        """Convierte cualquier escalar de numpy/pandas a su equivalente Python."""
        if v is None or v is pd.NA:
            return None
        if hasattr(v, "item"):      # np.int64, np.float64, np.bool_
            return v.item()
        return v

    def _filas(dframe):
        return [tuple(_py(v) for v in fila)
                for fila in dframe.itertuples(index=False, name=None)]

    # --- cliente ---
    df_cli = df[["Id_cliente", "Edad", "Genero", "Venta_total", "N_Compras"]].copy()
    filas_cliente = _filas(df_cli)

    # verificacion: si algo sigue siendo numpy, avisar antes de fallar en SQL
    tipos = {type(v).__name__ for fila in filas_cliente[:5] for v in fila}
    log(f"Tipos Python en las filas de cliente: {tipos}")
    execute_values(
        cur,
        """INSERT INTO cliente
           (id_cliente, edad, genero_id, venta_total, n_compras)
           VALUES %s""",
        filas_cliente,
        page_size=1000,
    )
    log(f"cliente: {len(filas_cliente)} filas insertadas")

    # --- registro_compra ---
    df_rc = df[["Id_cliente", "FechaCompra", "MontoCompra", "MetodoPago",
                "Tiempo", "Navegador", "Boletin", "Vale"]].copy()
    df_rc["FechaCompra"] = df_rc["FechaCompra"].dt.date  # date, no Timestamp
    filas_rc = _filas(df_rc)

    tipos = {type(v).__name__ for fila in filas_rc[:5] for v in fila}
    log(f"Tipos Python en las filas de registro_compra: {tipos}")

    execute_values(
        cur,
        """INSERT INTO registro_compra
           (id_cliente, fecha_compra, monto_compra, metodo_pago_id,
            tiempo, navegador_id, boletin, vale)
           VALUES %s""",
        filas_rc,
        page_size=1000,
    )
    log(f"registro_compra: {len(filas_rc)} filas insertadas")

    raw.commit()
    log("COMMIT realizado.")

except Exception as e:
    raw.rollback()
    log(f"ERROR durante la carga, se hizo ROLLBACK: {e}")
    raise
finally:
    raw.close()


# ================================================================
# 5. VERIFICACION POST-CARGA
# ================================================================
seccion("5. VERIFICACION")

from db import consultar  # noqa: E402  (se importa aqui para usar el engine ya vivo)

v = consultar("""
    SELECT
      (SELECT COUNT(*) FROM cliente)          AS clientes,
      (SELECT COUNT(*) FROM registro_compra)  AS compras,
      (SELECT COUNT(*) FROM v_ventas)         AS vista
""")
log(v.to_string(index=False))

if int(v["clientes"].iloc[0]) == len(df) == int(v["vista"].iloc[0]):
    log("\nOK: los conteos cuadran con el DataFrame y la vista no pierde filas.")
else:
    log("\nATENCION: los conteos NO cuadran. Revisar los JOIN de la vista.")

log("\nMuestra desde la base:")
log(consultar("SELECT * FROM v_ventas LIMIT 5").to_string(index=False))

log("\nControl cruzado de totales:")
log(consultar("""
    SELECT
      ROUND(SUM(monto_compra), 2) AS suma_monto_compra,
      ROUND(SUM(venta_total), 2)  AS suma_venta_total,
      ROUND(AVG(edad), 2)         AS edad_promedio
    FROM v_ventas
""").to_string(index=False))
log(f"   pandas -> monto_compra: {df['MontoCompra'].sum():.2f}")
log(f"   pandas -> venta_total:  {df['Venta_total'].sum():.2f}")
log(f"   pandas -> edad prom:    {df['Edad'].mean():.2f}")
log("   (si no coinciden, algo se perdio o duplico en la carga)")

with open(BITACORA, "w", encoding="utf-8") as f:
    f.write("\n".join(_log_lineas))
print(f"\nBitacora guardada en {BITACORA}")
