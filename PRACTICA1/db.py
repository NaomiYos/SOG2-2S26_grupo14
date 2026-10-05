"""
db.py - Capa unica de acceso a la base de datos.

TODO el equipo importa de aqui. Nadie mas abre conexiones sueltas:
Supabase free tier limita las conexiones concurrentes y el pooler
se satura rapido si cada script abre la suya.

Uso tipico:
    from db import consultar
    df = consultar("SELECT * FROM v_ventas WHERE mes = %(mes)s", {"mes": 3})
"""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Falta DATABASE_URL. Crea un archivo .env con la cadena de conexion "
        "de Supabase (Project Settings > Database > Connection string > Session)."
    )

# pool_pre_ping evita el error 'server closed the connection unexpectedly'
# cuando Supabase corta conexiones ociosas (pasa seguido en el tier gratuito).
_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
)


def get_engine():
    """Devuelve el engine de SQLAlchemy. Para pandas.to_sql o uso avanzado."""
    return _engine


def consultar(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Ejecuta un SELECT y devuelve un DataFrame.

    Usa SIEMPRE parametros con nombre, nunca concatenacion de strings:
        BIEN:  consultar("SELECT * FROM cliente WHERE edad > %(e)s", {"e": 30})
        MAL:   consultar(f"SELECT * FROM cliente WHERE edad > {edad}")

    Esto importa especialmente para el Rol 4: si el agente de IA arma
    parte de la consulta, la concatenacion abre una inyeccion SQL.
    """
    return pd.read_sql_query(sql, _engine, params=params)


def ejecutar(sql: str, params: dict | None = None) -> None:
    """Ejecuta una sentencia que no devuelve filas (INSERT, UPDATE, DDL)."""
    with _engine.begin() as conn:
        conn.execute(text(sql), params or {})


def probar_conexion() -> bool:
    """Verifica que la base responde. Util como primer paso de cualquier script."""
    try:
        df = consultar("SELECT COUNT(*) AS n FROM cliente")
        print(f"Conexion OK. Clientes en la base: {df['n'].iloc[0]}")
        return True
    except Exception as e:
        print(f"Fallo la conexion: {e}")
        return False


if __name__ == "__main__":
    probar_conexion()
