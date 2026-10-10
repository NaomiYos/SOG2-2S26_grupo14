"""Paso 15: ajustes de la tienda, del correo, del pago, del gestor documental y del CRM.

1. Instala qm_tienda (omite los correos estándar de los pedidos web) y payment_demo.
2. Tienda: precios con IVA incluido (el IVA del 12 % ya está incluido en el precio de venta).
3. Correo: el remitente de las plantillas de la compra y la campaña, y el correo de la compañía,
   pasan a ser el remitente verificado en Brevo. Desactiva el resumen periódico de Odoo
   (se enviaba a admin@example.com y fallaba).
4. Pago con tarjeta en modo de prueba (proveedor "Demostración" de Odoo): el pago queda hecho,
   el pedido se confirma y GA4 registra el purchase. La transferencia bancaria se mantiene.
5. Gestor documental: carpeta "Facturas de clientes" con la etiqueta "Factura de cliente".
   Factura los pedidos web confirmados que quedaron "por facturar", exporta los PDF nuevos
   (08_exportar_facturas.py) y los sube a esa carpeta. Las facturas de la tienda que se generen
   después las agrega la regla de 13_regla_confirmacion.py.
6. CRM: oportunidades de ejemplo con clientes empresa, en distintas etapas.

Idempotente: usa External IDs y nombres de archivo. Ejecutar 13_regla_confirmacion.py después.
Uso: python -X utf8 15_tienda_crm_pagos.py "QuetzalMart <ventas@su-dominio.com>"
El remitente debe ser exactamente el verificado en Brevo (no se guarda en el repo).
"""
import base64
import importlib
import re
import sys
from pathlib import Path

from odoo_cliente import Odoo

FACTURAS_PDF = Path(__file__).resolve().parent.parent / "facturas_pdf"
PLANTILLAS = ["sale.mail_template_sale_confirmation", "__qm__.plantilla_correo_compra", "__qm__.plantilla_correo_campana"]

# (necesidad del cliente, etapa, ingreso esperado en Q, probabilidad)
OPORTUNIDADES = [
    ("Abastecimiento mensual de abarrotes", "New", 18500, 10),
    ("Línea de productos frescos para cafetería", "New", 7200, 15),
    ("Canastas navideñas para colaboradores", "Qualified", 45000, 40),
    ("Contrato anual de bebidas", "Qualified", 32000, 35),
    ("Insumos de limpieza para sucursales", "Proposition", 12800, 60),
    ("Pedido mayorista de granos básicos", "Proposition", 26400, 70),
    ("Productos para evento corporativo", "Proposition", 9600, 55),
    ("Suministro de lácteos semanal", "Won", 15300, 100),
    ("Despensa para comedor de empleados", "Won", 21700, 100),
    ("Café y snacks para oficinas", "Won", 6900, 100),
    ("Abarrotes para tienda de barrio", "New", 4800, 20),
    ("Productos importados para temporada", "Qualified", 13900, 30),
]


def instalar(odoo, nombres):
    odoo.call("ir.module.module", "update_list")
    for nombre in nombres:
        modulo = odoo.search_read("ir.module.module", [("name", "=", nombre)], ["state"])
        if not modulo:
            raise SystemExit(f"No se encontró el módulo {nombre}: revise PROYECTO/addons y reinicie Odoo")
        if modulo[0]["state"] != "installed":
            print(f"Instalando {nombre}...")
            odoo.accion("ir.module.module", "button_immediate_install", [modulo[0]["id"]])


def tienda_con_iva(odoo):
    odoo.write("website", odoo.search("website", []), {"show_line_subtotals_tax_selection": "tax_included"})
    print("Tienda: precios con IVA incluido.")


def correo(odoo, remitente):
    direccion = re.search(r"<([^>]+)>", remitente)
    direccion = direccion.group(1) if direccion else remitente.strip()
    for xmlid in PLANTILLAS:
        plantilla = odoo.ref(xmlid)
        if plantilla:
            odoo.write("mail.template", plantilla, {"email_from": remitente})
    compania = odoo.search_read("res.company", [], ["partner_id"], limit=1)[0]
    odoo.write("res.partner", compania["partner_id"][0], {"email": direccion})
    for resumen in odoo.search_read("digest.digest", [("state", "=", "activated")], ["id"]):
        odoo.accion("digest.digest", "action_deactivate", [resumen["id"]])
    print(f"Correo: remitente {remitente}; correo de la compañía {direccion}; resumen periódico desactivado.")


def pago_de_prueba(odoo):
    proveedor = odoo.search("payment.provider", [("code", "=", "demo")], context={"active_test": False})
    if not proveedor:
        raise SystemExit("No existe el proveedor de pago Demostración: revise la instalación de payment_demo")
    odoo.write("payment.provider", proveedor, {"state": "test", "is_published": True})
    # Nombre traducible: se escribe en inglés y en el español de la tienda. La tienda muestra el del
    # método de pago y, debajo, "Asegurado por <proveedor>".
    metodo = odoo.search("payment.method", [("code", "=", "demo")], context={"active_test": False})
    for idioma in ("en_US", "es_419"):
        odoo.call("payment.provider", "write", proveedor, {"name": "Pago en modo de prueba"}, context={"lang": idioma})
        odoo.call("payment.method", "write", metodo, {"name": "Tarjeta de crédito o débito (modo de prueba)"}, context={"lang": idioma})
    print("Pago: tarjeta en modo de prueba publicada.")


def carpeta_facturas(odoo):
    raiz = odoo.ref("__qm__.dms_carpeta_raiz")
    categoria = odoo.ref("__qm__.dms_categoria_0")
    if not raiz or not categoria:
        raise SystemExit("Falta la estructura del gestor documental: ejecute 09_gestor_documental.py")
    carpeta = odoo.upsert("dms.directory", "dms_carpeta_facturas_clientes",
                          {"name": "Facturas de clientes", "parent_id": raiz, "inherit_group_ids": True})
    etiqueta = odoo.upsert("dms.tag", "dms_etiqueta_factura_cliente",
                           {"name": "Factura de cliente", "category_id": categoria, "color": 2})
    return carpeta, etiqueta


def facturar_pedidos_web(odoo):
    pedidos = odoo.search("sale.order", [("website_id", "!=", False), ("state", "=", "sale"), ("invoice_status", "=", "to invoice")])
    if not pedidos:
        return
    asistente = odoo.call("sale.advance.payment.inv", "create", {"advance_payment_method": "delivered"},
                          context={"active_model": "sale.order", "active_ids": pedidos})
    odoo.accion("sale.advance.payment.inv", "create_invoices", [asistente],
                context={"active_model": "sale.order", "active_ids": pedidos})
    borradores = odoo.search("account.move", [("line_ids.sale_line_ids.order_id", "in", pedidos), ("state", "=", "draft")])
    if borradores:
        odoo.accion("account.move", "action_post", borradores)
    print(f"Facturados {len(pedidos)} pedidos web pendientes ({len(borradores)} facturas publicadas).")


def subir_facturas(odoo, carpeta, etiqueta):
    sys.argv = sys.argv[:1]
    importlib.import_module("08_exportar_facturas").main()  # deja en facturas_pdf/ los PDF que falten
    existentes = {f["name"] for f in odoo.search_read("dms.file", [("directory_id", "=", carpeta)], ["name"])}
    nuevas = 0
    for archivo in sorted(FACTURAS_PDF.glob("*.pdf")):
        nombre = f"Factura {archivo.stem.replace('_', '-')}.pdf"
        if nombre in existentes:
            continue
        odoo.create("dms.file", {
            "name": nombre,
            "directory_id": carpeta,
            "content": base64.b64encode(archivo.read_bytes()).decode(),
            "tag_ids": [(6, 0, [etiqueta])],
        })
        nuevas += 1
    print(f"Gestor documental: {nuevas} facturas de cliente nuevas en la carpeta ({len(existentes) + nuevas} en total).")


def crm(odoo):
    etapas = {e["name"]: e["id"] for e in odoo.search_read("crm.stage", [], ["name"], context={"lang": "en_US"})}
    equipo = odoo.search("crm.team", [], limit=1, order="id")[0]
    clientes = odoo.search_read("res.partner", [("is_company", "=", True), ("customer_rank", ">", 0)],
                                ["name", "email", "phone"], order="id", limit=len(OPORTUNIDADES))
    if not clientes:
        raise SystemExit("No hay clientes empresa: ejecute 02_datos_maestros.py")
    for i, (necesidad, etapa, ingreso, probabilidad) in enumerate(OPORTUNIDADES):
        cliente = clientes[i % len(clientes)]
        oportunidad = odoo.upsert("crm.lead", f"crm_oportunidad_{i + 1:02d}", {
            "name": f"{necesidad} - {cliente['name']}",
            "type": "opportunity",
            "partner_id": cliente["id"],
            "email_from": cliente["email"] or False,
            "phone": cliente["phone"] or False,
            "team_id": equipo,
            "user_id": odoo.uid,
            "stage_id": etapas[etapa],
            "expected_revenue": ingreso,
            "probability": probabilidad,
        })
        if etapa == "Won":
            odoo.accion("crm.lead", "action_set_won", [oportunidad])
    print(f"CRM: {len(OPORTUNIDADES)} oportunidades de ejemplo.")


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Falta el remitente. Uso: python -X utf8 15_tienda_crm_pagos.py "QuetzalMart <ventas@su-dominio.com>"')
    remitente = sys.argv[1]
    odoo = Odoo()
    instalar(odoo, ["qm_tienda", "payment_demo"])
    tienda_con_iva(odoo)
    correo(odoo, remitente)
    pago_de_prueba(odoo)
    carpeta, etiqueta = carpeta_facturas(odoo)
    facturar_pedidos_web(odoo)
    subir_facturas(odoo, carpeta, etiqueta)
    crm(odoo)


if __name__ == "__main__":
    main()
