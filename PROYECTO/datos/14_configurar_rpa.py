"""Paso 14: prepara Odoo para que el robot de UiPath cargue clientes y productos con la pantalla Importar.

El auxiliar no permite usar la API de Odoo desde UiPath: el robot entra al sitio como una persona y usa
Importar registros. Este script solo deja lista esa pantalla (configuración, no carga datos):

1. Usuario "Robot RPA": así lo que carga el robot queda identificado (create_uid) en el sitio y en SQL.
   Permisos: contactos, ventas e inventario (administrador) y publicar en la tienda.
   La contraseña se genera al crearlo y se imprime una sola vez: guardarla en el Administrador de
   credenciales de Windows (ver PROYECTO/rpa/README.md). No se guarda en el repositorio.
2. Asignación guardada de la columna "website": los archivos consolidados usan los nombres técnicos de
   los campos como encabezados y Odoo los reconoce solos, salvo "website", que propone para el campo
   Sitio web (website_id) en lugar de Enlace del sitio web.

Idempotente. Uso: python -X utf8 14_configurar_rpa.py [--nueva-clave]
"""
import secrets
import sys

from odoo_cliente import Odoo

LOGIN = "robot.rpa@quetzalmart.com"
GRUPOS = [
    "base.group_user",
    "base.group_partner_manager",                # crear contactos
    "sales_team.group_sale_manager",             # crear productos
    "stock.group_stock_manager",                 # aplicar ajustes de inventario
    "website.group_website_restricted_editor",   # publicar productos en la tienda
]
# (modelo, encabezado en minúsculas, campo): Odoo busca las asignaciones guardadas en minúsculas.
ASIGNACIONES = [("res.partner", "website", "website")]


def configurar_usuario(odoo, nueva_clave):
    existente = odoo.ref("__qm__.usuario_robot_rpa")
    grupos = [odoo.ref(g) for g in GRUPOS]
    if None in grupos:
        faltan = [g for g, i in zip(GRUPOS, grupos) if i is None]
        raise SystemExit(f"No se encontraron los grupos {faltan}: instale Ventas, Inventario y Sitio web")
    valores = {
        "name": "Robot RPA",
        "login": LOGIN,
        "email": LOGIN,
        "lang": "es_419",
        "tz": "America/Guatemala",
        "groups_id": [(4, g) for g in grupos],
    }
    clave = None
    if not existente or nueva_clave:
        clave = secrets.token_urlsafe(12)
        valores["password"] = clave
    usuario = odoo.upsert("res.users", "usuario_robot_rpa", valores)
    print(f"Usuario Robot RPA listo (id {usuario}, login {LOGIN})")
    if clave:
        print(f"Contraseña (se muestra una sola vez): {clave}")
    else:
        print("La contraseña no cambió (use --nueva-clave para generar otra)")


def configurar_asignaciones(odoo):
    for modelo, columna, campo in ASIGNACIONES:
        odoo.upsert("base_import.mapping", f"rpa_asignacion_{modelo.replace('.', '_')}_{columna}", {
            "res_model": modelo, "column_name": columna, "field_name": campo,
        })
        print(f"Asignación guardada: {modelo} '{columna}' -> {campo}")


def main():
    odoo = Odoo()
    configurar_usuario(odoo, "--nueva-clave" in sys.argv)
    configurar_asignaciones(odoo)


if __name__ == "__main__":
    main()
