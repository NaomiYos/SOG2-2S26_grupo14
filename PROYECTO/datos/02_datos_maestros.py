"""Paso 2: datos maestros.

- Etiquetas de contacto y categorías de producto.
- 14 proveedores (10 de mercadería y 4 de materiales de operación).
- 60 productos de venta con imagen, código interno, código de barras EAN-13, precio, costo y peso,
  cada uno con su proveedor y precio de compra.
- 80 clientes (60 personas y 20 empresas) en Guatemala, México y El Salvador.

Idempotente: re-ejecutarlo actualiza los registros en lugar de duplicarlos.
Uso: python 02_datos_maestros.py
"""
import base64
import random
from pathlib import Path

from catalogo import CATEGORIAS, ETIQUETAS_CLIENTE, PRODUCTOS, PROVEEDORES, clientes, codigo_producto, ean13
from odoo_cliente import Odoo

IMAGENES = Path(__file__).with_name("imagenes") / "productos"


def etiquetas(odoo):
    nombres = ETIQUETAS_CLIENTE + sorted({p[4] for p in PROVEEDORES.values()})
    ids = {}
    for i, nombre in enumerate(nombres):
        ids[nombre] = odoo.upsert("res.partner.category", f"etiqueta_{i:02d}", {"name": nombre})
    return ids


def categorias(odoo):
    todos = odoo.ref("product.product_category_all")
    return {
        codigo: odoo.upsert("product.category", f"categoria_{codigo.lower()}", {"name": nombre, "parent_id": todos})
        for codigo, (nombre, _fondo, _proveedor) in CATEGORIAS.items()
    }


def proveedores(odoo, ids_etiqueta):
    rnd = random.Random(2026)
    ids = {}
    for codigo, (nombre, pais, ciudad, calle, etiqueta) in PROVEEDORES.items():
        ids[codigo] = odoo.upsert("res.partner", f"proveedor_{codigo.lower()}", {
            "name": nombre,
            "is_company": True,
            "street": calle,
            "city": ciudad,
            "country_id": odoo.ref(f"base.{pais}"),
            "vat": f"{rnd.randint(1000000, 9999999)}-{rnd.randint(0, 9)}",
            "email": f"ventas@{codigo.lower()}.proveedores.example.com",
            "phone": f"+502 2{rnd.randint(100, 999)} {rnd.randint(1000, 9999)}",
            "ref": codigo,
            "supplier_rank": 1,
            "category_id": [(6, 0, [ids_etiqueta[etiqueta]])],
            "lang": "es_419",
        })
    print(f"Proveedores: {len(ids)}")
    return ids


def productos(odoo, ids_categoria, ids_proveedor):
    iva_venta, iva_compra = (
        odoo.search_read("res.company", [], ["account_sale_tax_id", "account_purchase_tax_id"])[0][campo][0]
        for campo in ("account_sale_tax_id", "account_purchase_tax_id")
    )
    for i, (categoria, nombre, _emoji, precio, costo, peso, descripcion) in enumerate(PRODUCTOS):
        codigo = codigo_producto(i)
        imagen = IMAGENES / f"{codigo}.jpg"
        plantilla = odoo.upsert("product.template", f"producto_{codigo.lower().replace('-', '_')}", {
            "name": nombre,
            "type": "consu",
            "is_storable": True,
            "categ_id": ids_categoria[categoria],
            "default_code": codigo,
            "barcode": ean13(i),
            "list_price": precio,
            "standard_price": costo,
            "weight": peso,
            "description_sale": descripcion,
            "sale_ok": True,
            "purchase_ok": True,
            "taxes_id": [(6, 0, [iva_venta])],
            "supplier_taxes_id": [(6, 0, [iva_compra])],
            "image_1920": base64.b64encode(imagen.read_bytes()).decode() if imagen.exists() else False,
        })
        odoo.upsert("product.supplierinfo", f"tarifa_proveedor_{codigo.lower().replace('-', '_')}", {
            "partner_id": ids_proveedor[CATEGORIAS[categoria][2]],
            "product_tmpl_id": plantilla,
            "price": costo,
            "min_qty": 1,
            "delay": 3,
        })
    print(f"Productos: {len(PRODUCTOS)} (con imagen, proveedor y precio de compra)")


def cargar_clientes(odoo, ids_etiqueta):
    estados = {}
    for pais in ("gt", "mx", "sv"):
        for estado in odoo.search_read("res.country.state", [("country_id", "=", odoo.ref(f"base.{pais}"))], ["name"]):
            estados[(pais, estado["name"])] = estado["id"]
    lista = clientes()
    for c in lista:
        odoo.upsert("res.partner", f"cliente_{c['codigo'].lower()}", {
            "name": c["nombre"],
            "is_company": c["empresa"],
            "email": c["correo"],
            "phone": c["telefono"],
            "street": c["calle"],
            "city": c["ciudad"],
            "zip": c["cp"],
            "state_id": estados.get((c["pais"], c["estado"]), False),
            "country_id": odoo.ref(f"base.{c['pais']}"),
            "ref": c["codigo"],
            "customer_rank": 1,
            "category_id": [(6, 0, [ids_etiqueta[c["etiqueta"]]])],
            "lang": "es_419",
        })
    print(f"Clientes: {len(lista)} ({sum(c['empresa'] for c in lista)} empresas)")


def main():
    odoo = Odoo()
    ids_etiqueta = etiquetas(odoo)
    ids_categoria = categorias(odoo)
    ids_proveedor = proveedores(odoo, ids_etiqueta)
    productos(odoo, ids_categoria, ids_proveedor)
    cargar_clientes(odoo, ids_etiqueta)
    print("Datos maestros cargados")


if __name__ == "__main__":
    main()
