"""Paso 4: 60 materiales de operación para las sucursales.

Productos almacenables que no se venden (empaque, oficina, limpieza, equipo, uniformes),
agrupados en la categoría "Materiales de operación", con imagen, costo y proveedor.
Las compras del paso siguiente los reparten entre los almacenes GT, MX y SV.

Idempotente. Requiere haber corrido 02_datos_maestros.py (proveedores).
Uso: python 04_materiales.py
"""
import base64
from pathlib import Path

from catalogo import CATEGORIAS_MATERIAL, MATERIALES, codigo_material
from odoo_cliente import Odoo

IMAGENES = Path(__file__).with_name("imagenes") / "productos"


def main():
    odoo = Odoo()
    padre = odoo.upsert("product.category", "categoria_materiales", {
        "name": "Materiales de operación",
        "parent_id": odoo.ref("product.product_category_all"),
    })
    ids_categoria = {
        codigo: odoo.upsert("product.category", f"categoria_mat_{codigo.lower()}", {"name": nombre, "parent_id": padre})
        for codigo, (nombre, _fondo, _proveedor) in CATEGORIAS_MATERIAL.items()
    }
    iva_compra = odoo.search_read("res.company", [], ["account_purchase_tax_id"])[0]["account_purchase_tax_id"][0]

    for i, (categoria, nombre, _emoji, costo, peso) in enumerate(MATERIALES):
        codigo = codigo_material(i)
        sufijo = codigo.lower().replace("-", "_")
        imagen = IMAGENES / f"{codigo}.jpg"
        plantilla = odoo.upsert("product.template", f"material_{sufijo}", {
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "categ_id": ids_categoria[categoria],
            "default_code": codigo,
            "standard_price": costo,
            "list_price": 0,
            "weight": peso,
            "sale_ok": False,
            "purchase_ok": True,
            "taxes_id": [(5, 0, 0)],
            "supplier_taxes_id": [(6, 0, [iva_compra])],
            "description_purchase": f"Material de operación para sucursales: {CATEGORIAS_MATERIAL[categoria][0].lower()}.",
            "image_1920": base64.b64encode(imagen.read_bytes()).decode() if imagen.exists() else False,
        })
        odoo.upsert("product.supplierinfo", f"tarifa_proveedor_{sufijo}", {
            "partner_id": odoo.ref(f"__qm__.proveedor_{CATEGORIAS_MATERIAL[categoria][2].lower()}"),
            "product_tmpl_id": plantilla,
            "price": costo,
            "min_qty": 1,
            "delay": 5,
        })
    print(f"Materiales: {len(MATERIALES)} en {len(ids_categoria)} subcategorías")


if __name__ == "__main__":
    main()
