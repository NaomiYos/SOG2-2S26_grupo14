"""Paso 1: módulos y configuración base de QuetzalMart.

- Compañía QuetzalMart (Guatemala, GTQ) antes de instalar contabilidad.
- Módulos: Contactos, CRM, Ventas, Compras, Inventario, Facturación, Empleados y localización GT.
- Plan contable de Guatemala con IVA 12 % como impuesto por defecto de ventas y compras.
- Multialmacén: sede Guatemala (GT) y sucursales México (MX) y El Salvador (SV).

Se puede ejecutar varias veces: solo instala o actualiza lo que falta.
Uso: python 01_configurar_erp.py
"""
from odoo_cliente import Odoo

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


def configurar_impuestos(odoo, compania):
    datos = odoo.search_read("res.company", [("id", "=", compania)], ["chart_template"])[0]
    if datos["chart_template"] != "gt":
        odoo.call("account.chart.template", "try_loading", "gt", compania, install_demo=False)
        print("Plan contable de Guatemala cargado")
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
    print("IVA 12 % por defecto en ventas y compras")

    # El plan contable crea los diarios en inglés; se traducen para facturas y reportes.
    for codigo, nombre in DIARIOS.items():
        odoo.write("account.journal", odoo.search("account.journal", [("code", "=", codigo), ("company_id", "=", compania)]), {"name": nombre})
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
    print(f"Almacenes: {', '.join(SUCURSALES)}")


def main():
    odoo = Odoo()
    compania = configurar_compania(odoo)
    instalar_modulos(odoo)
    configurar_impuestos(odoo, compania)
    configurar_almacenes(odoo, compania)
    print("Configuración base completa")


if __name__ == "__main__":
    main()
