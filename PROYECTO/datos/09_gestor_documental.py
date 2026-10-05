"""Paso 9: gestor documental (módulo OCA dms) integrado al ERP.

- Instala dms (descargarlo antes con infra/obtener_addons.sh).
- Almacenamiento "Documentos QuetzalMart" con carpetas por tipo de documento y grupo de acceso.
- Etiquetas en 4 categorías para filtrar: tipo de documento, sucursal, área y estado.
- Carga los 15 PDF de PROYECTO/dms/documentos/ y además adjunta cada uno a su registro del ERP
  (visible en el historial del registro): factura de proveedor -> factura contable,
  contrato de outsourcing -> empresa proveedora del servicio, contrato laboral -> empleado.

Idempotente. Requiere 05_compras.py y 03_empleados.py.
Uso: python 09_gestor_documental.py
"""
import base64
from pathlib import Path

from catalogo import COMPRAS_CON_FACTURA_DIGITAL, CONTRATOS_LABORALES, OUTSOURCING, empleados
from odoo_cliente import Odoo

DOCUMENTOS = Path(__file__).resolve().parent.parent / "dms" / "documentos"

CARPETAS = {
    "facturas_proveedores": "Facturas de proveedores",
    "contratos_outsourcing": "Contratos de outsourcing",
    "contratos_empleados": "Contratos de empleados",
}

# categoría: [etiquetas]
ETIQUETAS = {
    "Tipo de documento": ["Factura de proveedor", "Contrato de outsourcing", "Contrato laboral"],
    "Sucursal": ["Guatemala", "México", "El Salvador"],
    "Área": ["Compras", "Operaciones", "Recursos Humanos"],
    "Estado": ["Pagada", "Pendiente de pago", "Vigente"],
}
SUCURSAL = {"GT": "Guatemala", "MX": "México", "SV": "El Salvador"}


def instalar_dms(odoo):
    odoo.call("ir.module.module", "update_list")
    modulo = odoo.search_read("ir.module.module", [("name", "=", "dms")], ["state"])
    if not modulo:
        raise SystemExit("No se encontró el módulo dms: ejecute PROYECTO/infra/obtener_addons.sh y reinicie Odoo")
    if modulo[0]["state"] != "installed":
        print("Instalando dms...")
        odoo.call("ir.module.module", "button_immediate_install", [modulo[0]["id"]])
    gestor = odoo.ref("dms.group_dms_manager")
    odoo.write("res.users", odoo.uid, {"groups_id": [(4, gestor)]})


def estructura(odoo):
    grupo = odoo.upsert("dms.access.group", "dms_grupo_administracion", {
        "name": "Administración QuetzalMart",
        "perm_create": True, "perm_write": True, "perm_unlink": True,
        "explicit_user_ids": [(4, odoo.uid)],
    })
    almacenamiento = odoo.upsert("dms.storage", "dms_almacenamiento", {"name": "Documentos QuetzalMart", "save_type": "file"})
    raiz = odoo.upsert("dms.directory", "dms_carpeta_raiz", {
        "name": "QuetzalMart",
        "is_root_directory": True,
        "storage_id": almacenamiento,
        "group_ids": [(6, 0, [grupo])],
    })
    carpetas = {
        clave: odoo.upsert("dms.directory", f"dms_carpeta_{clave}", {"name": nombre, "parent_id": raiz, "inherit_group_ids": True})
        for clave, nombre in CARPETAS.items()
    }
    categorias, etiquetas = {}, {}
    for i, (categoria, nombres) in enumerate(ETIQUETAS.items()):
        categorias[categoria] = odoo.upsert("dms.category", f"dms_categoria_{i}", {"name": categoria})
        for j, nombre in enumerate(nombres):
            etiquetas[nombre] = odoo.upsert("dms.tag", f"dms_etiqueta_{i}_{j}", {
                "name": nombre, "category_id": categorias[categoria], "color": i + 2,
            })
    return carpetas, categorias, etiquetas


def adjuntar(odoo, archivo, modelo, res_id):
    """Deja el PDF como adjunto del registro del ERP (visible en su chatter)."""
    if not odoo.search("ir.attachment", [("res_model", "=", modelo), ("res_id", "=", res_id), ("name", "=", archivo.name)]):
        odoo.create("ir.attachment", {
            "name": archivo.name, "res_model": modelo, "res_id": res_id, "mimetype": "application/pdf",
            "datas": base64.b64encode(archivo.read_bytes()).decode(),
        })


def subir(odoo, xmlid, archivo, carpeta, categoria, nombres_etiqueta, etiquetas, modelo, res_id):
    adjuntar(odoo, archivo, modelo, res_id)
    return odoo.upsert("dms.file", xmlid, {
        "name": archivo.name,
        "directory_id": carpeta,
        "content": base64.b64encode(archivo.read_bytes()).decode(),
        "mimetype": "application/pdf",
        "category_id": categoria,
        "tag_ids": [(6, 0, [etiquetas[n] for n in nombres_etiqueta])],
    })


def main():
    odoo = Odoo()
    instalar_dms(odoo)
    carpetas, categorias, etiquetas = estructura(odoo)
    tipo = categorias["Tipo de documento"]

    # Facturas de proveedores: misma serie (ref) que la factura registrada en Odoo.
    for n, xmlid in enumerate(COMPRAS_CON_FACTURA_DIGITAL, start=1):
        compra = odoo.search_read("purchase.order", [("id", "=", odoo.ref(f"__qm__.{xmlid}"))], ["name", "partner_id", "picking_type_id"])[0]
        factura = odoo.search_read("account.move", [("invoice_origin", "=", compra["name"]), ("move_type", "=", "in_invoice")],
                                   ["ref", "payment_state"])[0]
        archivo = next((DOCUMENTOS / "facturas_proveedores").glob(f"Factura_*_{factura['ref']}.pdf"))
        sucursal = compra["picking_type_id"][1].split(":")[0].replace("QuetzalMart ", "")
        estado = "Pagada" if factura["payment_state"] in ("paid", "in_payment") else "Pendiente de pago"
        subir(odoo, f"dms_factura_{n}", archivo, carpetas["facturas_proveedores"], tipo,
              ["Factura de proveedor", sucursal, "Compras", estado], etiquetas, "account.move", factura["id"])

    # Contratos de outsourcing: la empresa de servicios queda como proveedor en Contactos.
    servicios = odoo.upsert("res.partner.category", "etiqueta_outsourcing", {"name": "Proveedor de servicios (outsourcing)"})
    for codigo, (nombre, pais, ciudad, calle, _servicio, _cuota, sucursal, _inicio) in OUTSOURCING.items():
        empresa = odoo.upsert("res.partner", f"outsourcing_{codigo.lower()}", {
            "name": nombre, "is_company": True, "street": calle, "city": ciudad, "country_id": odoo.ref(f"base.{pais}"),
            "email": f"contratos@{codigo.lower()}.servicios.example.com", "ref": codigo, "supplier_rank": 1,
            "category_id": [(6, 0, [servicios])], "lang": "es_419",
        })
        archivo = next((DOCUMENTOS / "contratos_outsourcing").glob(f"Contrato_outsourcing_{codigo}_*.pdf"))
        subir(odoo, f"dms_outsourcing_{codigo.lower()}", archivo, carpetas["contratos_outsourcing"], tipo,
              ["Contrato de outsourcing", SUCURSAL[sucursal], "Operaciones", "Vigente"], etiquetas, "res.partner", empresa)

    # Contratos laborales: vinculados al expediente del empleado.
    lista = empleados()
    for cargo in CONTRATOS_LABORALES:
        e = next(x for x in lista if x["cargo"] == cargo)
        empleado = odoo.ref(f"__qm__.empleado_{e['codigo'].lower()}")
        archivo = DOCUMENTOS / "contratos_empleados" / f"Contrato_laboral_{e['codigo']}_{cargo}.pdf"
        subir(odoo, f"dms_contrato_{e['codigo'].lower()}", archivo, carpetas["contratos_empleados"], tipo,
              ["Contrato laboral", SUCURSAL[e["sucursal"]], "Recursos Humanos", "Vigente"], etiquetas, "hr.employee", empleado)

    total = odoo.call("dms.file", "search_count", [("directory_id", "child_of", odoo.ref("__qm__.dms_carpeta_raiz"))])
    print(f"Gestor documental: {total} documentos en {len(CARPETAS)} carpetas, "
          f"{sum(len(v) for v in ETIQUETAS.values())} etiquetas en {len(ETIQUETAS)} categorías")


if __name__ == "__main__":
    main()
