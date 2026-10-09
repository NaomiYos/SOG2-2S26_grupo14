"""Paso 1: módulos y configuración base de QuetzalMart.

- Compañía QuetzalMart (Guatemala, GTQ) antes de instalar contabilidad.
- Módulos: Contactos, CRM, Ventas, Compras, Inventario, Facturación, Empleados y localización GT.
- Plan contable de Guatemala con IVA 12 % como impuesto por defecto de ventas y compras
  (y la compañía y la lista de precios de vuelta en GTQ si el plan genérico las dejó en USD).
- Multialmacén: sede Guatemala (GT) y sucursales México (MX) y El Salvador (SV).
- Logo, colores corporativos y diseño de facturas y demás documentos.

Se puede ejecutar varias veces: solo instala o actualiza lo que falta.
Uso: python 01_configurar_erp.py
"""
import base64
from pathlib import Path

from odoo_cliente import Odoo

LOGO = Path(__file__).with_name("imagenes") / "logo_quetzalmart.png"

MODULOS = ["contacts", "crm", "sale_management", "purchase", "stock", "account", "hr", "l10n_gt"]

COMPANIA = {
    "name": "QuetzalMart, S.A.",
    "street": "6a. Avenida 10-25, Zona 1",
    "city": "Ciudad de Guatemala",
    "zip": "01001",
    "phone": "+502 2200 1400",
    "email": "info@quetzalmart.com",
    "website": "https://quetzalmart.com",
    "vat": "12345678",
}

DIARIOS = {
    "INV": "Facturas de cliente",
    "FACTU": "Facturas de proveedor",
    "BNK1": "Banco",
    "CSH1": "Efectivo",
    "MISCE": "Operaciones varias",
    "CABA": "Impuestos base de efectivo",
    "CAMBI": "Diferencia cambiaria",
    "STJ": "Valoración de inventario",
}

# código: (nombre del almacén, país, ciudad, dirección)
SUCURSALES = {
    "GT": ("QuetzalMart Guatemala", "gt", "Ciudad de Guatemala", "6a. Avenida 10-25, Zona 1"),
    "MX": ("QuetzalMart México", "mx", "Ciudad de México", "Av. Insurgentes Sur 1458, Col. Actipan"),
    "SV": ("QuetzalMart El Salvador", "sv", "San Salvador", "Blvd. de Los Héroes 1120, Col. Miramonte"),
}


def configurar_compania(odoo):
    gt = odoo.ref("base.gt")
    gtq = odoo.ref("base.GTQ")
    odoo.write("res.currency", gtq, {"active": True})
    compania = odoo.search("res.company", [])[0]
    actual = odoo.search_read("res.company", [("id", "=", compania)], ["currency_id"])[0]
    valores = dict(COMPANIA, country_id=gt)
    # La moneda solo se puede cambiar antes de que existan asientos contables.
    if actual["currency_id"][0] != gtq and not odoo.search("ir.model", [("model", "=", "account.move.line")]):
        valores["currency_id"] = gtq
    odoo.write("res.company", compania, valores)
    odoo.write("res.users", odoo.uid, {"lang": "es_419", "tz": "America/Guatemala"})
    print(f"Compañía configurada: {COMPANIA['name']}")
    return compania


def configurar_marca(odoo, compania):
    """Logo, colores y diseño de documentos (facturas, pedidos, cotizaciones)."""
    odoo.write("res.company", compania, {
        "logo": base64.b64encode(LOGO.read_bytes()).decode(),
        "primary_color": "#0B7A4B",
        "secondary_color": "#C8102E",
        "external_report_layout_id": odoo.ref("web.external_layout_bold"),
        "report_header": "Calidad a precios accesibles",
        "report_footer": "QuetzalMart, S.A. · 6a. Avenida 10-25, Zona 1, Ciudad de Guatemala · +502 2200 1400 · info@quetzalmart.com",
    })
    # wkhtmltopdf corre dentro del contenedor de Odoo: debe pedir los estilos a sí mismo,
    # no al dominio público, o los PDF salen sin formato.
    odoo.call("ir.config_parameter", "set_param", "report.url", "http://127.0.0.1:8069")
    print("Logo, colores y diseño de documentos")


def instalar_modulos(odoo):
    pendientes = odoo.search_read(
        "ir.module.module", [("name", "in", MODULOS), ("state", "!=", "installed")], ["name"]
    )
    if not pendientes:
        print("Módulos: todos instalados")
        return
    print(f"Instalando: {', '.join(m['name'] for m in pendientes)} (puede tardar varios minutos)...")
    odoo.call("ir.module.module", "button_immediate_install", [m["id"] for m in pendientes])
    print("Módulos instalados")


def fijar_gtq(odoo, compania):
    """Al instalar account, Odoo carga primero el plan genérico, que deja la compañía y la lista
    de precios en USD. Se vuelven a GTQ mientras no haya asientos ni pedidos que las usen."""
    gtq = odoo.ref("base.GTQ")
    actual = odoo.search_read("res.company", [("id", "=", compania)], ["currency_id"])[0]["currency_id"][0]
    if actual != gtq and not odoo.search("account.move.line", [("company_id", "=", compania)], limit=1):
        odoo.write("res.company", compania, {"currency_id": gtq})
        print("Moneda de la compañía: GTQ")
    for lista in odoo.search("product.pricelist", [("currency_id", "!=", gtq)], context={"active_test": False}):
        if not odoo.search("sale.order", [("pricelist_id", "=", lista)], limit=1):
            odoo.write("product.pricelist", lista, {"currency_id": gtq})
            print(f"Lista de precios {lista} en GTQ")


def configurar_impuestos(odoo, compania):
    datos = odoo.search_read("res.company", [("id", "=", compania)], ["chart_template"])[0]
    if datos["chart_template"] != "gt":
        # try_loading no es @api.model en Odoo 18: por XML-RPC necesita una lista de ids vacía primero.
        odoo.accion("account.chart.template", "try_loading", [], "gt", compania, install_demo=False)
        print("Plan contable de Guatemala cargado")
    fijar_gtq(odoo, compania)
    iva = {}
    for uso in ("sale", "purchase"):
        ids = odoo.search(
            "account.tax",
            [("company_id", "=", compania), ("type_tax_use", "=", uso), ("amount", "=", 12), ("amount_type", "=", "percent")],
            limit=1,
        )
        if not ids:
            raise SystemExit(f"No se encontró IVA 12 % de {uso}; revise la localización l10n_gt")
        iva[uso] = ids[0]
    odoo.write("res.company", compania, {"account_sale_tax_id": iva["sale"], "account_purchase_tax_id": iva["purchase"]})
    # El plan GT trae etiquetas contables ("VAT Payable"); en facturas debe leerse "IVA 12%".
    # Son campos traducibles: se escriben en inglés (base) y en español (lo que imprimen las facturas).
    for uso, nombre in (("sale", "IVA 12% ventas"), ("purchase", "IVA 12% compras")):
        for idioma in ("en_US", "es_419"):
            odoo.call("account.tax", "write", [iva[uso]], {"name": nombre, "invoice_label": "IVA 12%", "description": "IVA 12%"},
                      context={"lang": idioma})
    print("IVA 12 % por defecto en ventas y compras")

    # El plan contable crea los diarios en inglés; se traducen para facturas y reportes.
    for codigo, nombre in DIARIOS.items():
        diario = odoo.search("account.journal", [("code", "=", codigo), ("company_id", "=", compania)])
        for idioma in ("en_US", "es_419"):
            odoo.call("account.journal", "write", diario, {"name": nombre}, context={"lang": idioma})
    print("Diarios contables en español")


def configurar_almacenes(odoo, compania):
    ajustes = odoo.create("res.config.settings", {"group_stock_multi_locations": True})
    odoo.call("res.config.settings", "execute", [ajustes])

    contacto_compania = odoo.search_read("res.company", [("id", "=", compania)], ["partner_id"])[0]["partner_id"][0]
    for codigo, (nombre, pais, ciudad, calle) in SUCURSALES.items():
        direccion = odoo.upsert("res.partner", f"sucursal_{codigo.lower()}", {
            "name": nombre,
            "type": "other",
            "parent_id": contacto_compania,
            "street": calle,
            "city": ciudad,
            "country_id": odoo.ref(f"base.{pais}"),
        })
        valores = {"name": nombre, "code": codigo, "partner_id": direccion}
        if codigo == "GT":
            # El almacén creado por defecto pasa a ser la sede de Guatemala.
            principal = odoo.ref("stock.warehouse0")
            odoo.write("stock.warehouse", principal, valores)
        else:
            existente = odoo.search("stock.warehouse", [("code", "=", codigo), ("company_id", "=", compania)])
            if existente:
                odoo.write("stock.warehouse", existente, valores)
            else:
                odoo.create("stock.warehouse", dict(valores, company_id=compania))
    # stock_sms (se instala solo con CRM) abre un asistente de SMS al validar entregas.
    if odoo.search("ir.module.module", [("name", "=", "stock_sms"), ("state", "=", "installed")]):
        odoo.write("res.company", compania, {"stock_move_sms_validation": False, "has_received_warning_stock_sms": True})
    print(f"Almacenes: {', '.join(SUCURSALES)}")


def main():
    odoo = Odoo()
    compania = configurar_compania(odoo)
    instalar_modulos(odoo)
    configurar_impuestos(odoo, compania)
    configurar_almacenes(odoo, compania)
    configurar_marca(odoo, compania)
    print("Configuración base completa")


if __name__ == "__main__":
    main()
