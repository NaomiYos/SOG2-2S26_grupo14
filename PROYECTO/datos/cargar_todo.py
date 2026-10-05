"""Ejecuta en orden todos los pasos de configuración y carga (01 a 08).

Cada paso es idempotente, así que se puede volver a correr si alguno falla a medias.
Uso: python cargar_todo.py
"""
import importlib
import time
from pathlib import Path

PASOS = sorted(p.stem for p in Path(__file__).parent.glob("0[0-9]_*.py"))


def main():
    inicio = time.time()
    for paso in PASOS:
        print(f"\n=== {paso} ===")
        importlib.import_module(paso).main()
    print(f"\nCarga completa en {(time.time() - inicio) / 60:.1f} minutos")


if __name__ == "__main__":
    main()
