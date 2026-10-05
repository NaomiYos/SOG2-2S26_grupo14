"""Paso 7: 20 cotizaciones (sin confirmar).

- 12 cotizaciones de venta a clientes (presupuestos), con 30 días de validez.
- 8 solicitudes de presupuesto a proveedores.
La mitad de cada grupo queda marcada como enviada y el resto en borrador.
Fechas entre el 1 de septiembre y el 4 de octubre de 2026. Idempotente.
Requiere 02_datos_maestros.py y 04_materiales.py.
Uso: python 07_cotizaciones.py
"""
import random
from datetime import date, timedelta

from catalogo import CATEGORIAS, CATEGORIAS_MATERIAL, MATERIALES, PRODUCTOS, clientes, codigo_material, codigo_producto
from odoo_cliente import Odoo

A_CLIENTES = 12
A_PROVEEDORES = 8
INICIO = date(2026, 9, 1)
DIAS = 34


def main():
    odoo = Odoo()
    rnd = random.Random(20)
    almacenes = {w["code"]: (w["id"], w["in_type_id"][0]) for w in odoo.search_read("stock.warehouse", [], ["code", "in_type_id"])}
    codigos = [codigo_producto(i) for i in range(len(PRODUCTOS))] + [codigo_material(i) for i in range(len(MATERIALES))]
    variantes = {f["default_code"]: (f["id"], f["standard_price"])
                 for f in odoo.search_read("product.product", [("default_code", "in", codigos)], ["default_code", "standard_price"])}

    # Cotizaciones a clientes: empresas que piden precio por volumen.
    empresas = [c for c in clientes() if c["empresa"]]
    for n in range(1, A_CLIENTES + 1):
        cliente = rnd.choice(empresas)
        fecha = INICIO + timedelta(days=rnd.randrange(DIAS))
        productos = rnd.sample([codigo_producto(i) for i in range(len(PRODUCTOS))], rnd.randint(3, 7))
        cotizacion = odoo.upsert("sale.order", f"cotizacion_cliente_{n:02d}", {
            "partner_id": odoo.ref(f"__qm__.cliente_{cliente['codigo'].lower()}"),
            "warehouse_id": almacenes[cliente["pais"].upper()][0],
            "date_order": f"{fecha.isoformat()} 11:00:00",
            "validity_date": (fecha + timedelta(days=30)).isoformat(),
            "note": "Precios sujetos a existencias. Entrega a domicilio sin costo en pedidos mayores a Q 500.00.",
            "order_line": [(5, 0, 0)] + [(0, 0, {"product_id": variantes[c][0], "product_uom_qty": rnd.randint(10, 60)}) for c in productos],
        })
        if n % 2 == 0:
            odoo.write("sale.order", cotizacion, {"state": "sent"})

    # Solicitudes de presupuesto a proveedores (mercadería y materiales).
    por_proveedor = {}
    for i, (categoria, *_resto) in enumerate(PRODUCTOS):
        por_proveedor.setdefault(CATEGORIAS[categoria][2], []).append(codigo_producto(i))
    for i, (categoria, *_resto) in enumerate(MATERIALES):
        por_proveedor.setdefault(CATEGORIAS_MATERIAL[categoria][2], []).append(codigo_material(i))
    for n in range(1, A_PROVEEDORES + 1):
        proveedor = rnd.choice(sorted(por_proveedor))
        sucursal = rnd.choice(["GT", "MX", "SV"])
        fecha = INICIO + timedelta(days=rnd.randrange(DIAS))
        productos = rnd.sample(por_proveedor[proveedor], rnd.randint(2, min(5, len(por_proveedor[proveedor]))))
        solicitud = odoo.upsert("purchase.order", f"cotizacion_proveedor_{n:02d}", {
            "partner_id": odoo.ref(f"__qm__.proveedor_{proveedor.lower()}"),
            "picking_type_id": almacenes[sucursal][1],
            "date_order": f"{fecha.isoformat()} 09:00:00",
            "date_planned": f"{(fecha + timedelta(days=10)).isoformat()} 09:00:00",
            "notes": "Favor de cotizar precio unitario, tiempo de entrega y condiciones de pago.",
            "order_line": [(5, 0, 0)] + [(0, 0, {
                "product_id": variantes[c][0],
                "product_qty": rnd.randint(20, 150) if c.startswith("QM") else rnd.randint(2, 15),
                "price_unit": variantes[c][1],
            }) for c in productos],
        })
        if n % 2 == 0:
            odoo.write("purchase.order", solicitud, {"state": "sent"})

    print(f"Cotizaciones: {A_CLIENTES} a clientes y {A_PROVEEDORES} a proveedores (la mitad enviadas)")


if __name__ == "__main__":
    main()
