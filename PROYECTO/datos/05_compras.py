"""Paso 5: 100 compras a proveedores con su recepción y factura.

Cada compra se confirma, se recibe completa en el almacén de su sucursal y genera la factura
del proveedor (publicada). Cerca del 85 % de las facturas queda pagada y el resto pendiente.

- 30 compras de cobertura: cada proveedor de mercadería surte todos sus productos a GT, MX y SV,
  para que todas las sucursales tengan inventario de los 60 productos.
- 40 compras de reposición de mercadería al azar.
- 30 compras de materiales de operación (15 de cobertura proveedor x sucursal + 15 al azar).

Fechas entre abril y septiembre de 2026. Idempotente: las compras ya procesadas se omiten.
Requiere 02_datos_maestros.py y 04_materiales.py.
Uso: python 05_compras.py
"""
import random
from datetime import date, timedelta

from catalogo import CATEGORIAS, CATEGORIAS_MATERIAL, MATERIALES, PRODUCTOS, codigo_material, codigo_producto
from odoo_cliente import Odoo

INICIO = date(2026, 4, 1)
DIAS = 182
SUCURSALES = ["GT", "MX", "SV"]
PESO_SUCURSAL = [0.5, 0.25, 0.25]
PORCENTAJE_PAGADO = 0.85


def variantes(odoo, codigos):
    filas = odoo.search_read("product.product", [("default_code", "in", codigos)], ["default_code", "standard_price"])
    return {f["default_code"]: (f["id"], f["standard_price"]) for f in filas}


def plan_de_compras():
    """Lista determinista de compras: (proveedor, sucursal, [(código, cantidad)], fecha)."""
    rnd = random.Random(100)
    por_proveedor = {}
    for i, (categoria, *_resto) in enumerate(PRODUCTOS):
        por_proveedor.setdefault(CATEGORIAS[categoria][2], []).append(codigo_producto(i))
    materiales = {}
    for i, (categoria, *_resto) in enumerate(MATERIALES):
        materiales.setdefault(CATEGORIAS_MATERIAL[categoria][2], []).append(codigo_material(i))

    def fecha():
        return INICIO + timedelta(days=rnd.randrange(DIAS))

    plan = []
    # Cobertura de mercadería: los 60 productos llegan a las 3 sucursales.
    for proveedor, codigos in por_proveedor.items():
        for sucursal in SUCURSALES:
            plan.append((proveedor, sucursal, [(c, rnd.randint(60, 150)) for c in codigos], fecha()))
    # Reposición de mercadería al azar.
    for _ in range(40):
        proveedor = rnd.choice(list(por_proveedor))
        codigos = rnd.sample(por_proveedor[proveedor], rnd.randint(2, len(por_proveedor[proveedor])))
        sucursal = rnd.choices(SUCURSALES, PESO_SUCURSAL)[0]
        plan.append((proveedor, sucursal, [(c, rnd.randint(24, 120)) for c in codigos], fecha()))
    # Materiales: cobertura proveedor x sucursal y después al azar.
    for proveedor, codigos in materiales.items():
        for sucursal in SUCURSALES:
            plan.append((proveedor, sucursal, [(c, rnd.randint(2, 12)) for c in rnd.sample(codigos, 6)], fecha()))
    for _ in range(15):
        proveedor = rnd.choice(list(materiales))
        codigos = rnd.sample(materiales[proveedor], rnd.randint(2, 5))
        sucursal = rnd.choices(SUCURSALES, PESO_SUCURSAL)[0]
        plan.append((proveedor, sucursal, [(c, rnd.randint(1, 10)) for c in codigos], fecha()))
    # Orden cronológico para que la numeración P0000x siga las fechas.
    plan.sort(key=lambda compra: compra[3])
    pagos = [rnd.random() < PORCENTAJE_PAGADO for _ in plan]
    return list(zip(plan, pagos))


def recibir(odoo, compra):
    pickings = odoo.search_read("stock.picking", [("purchase_id", "=", compra), ("state", "not in", ["done", "cancel"])], ["move_ids"])
    for picking in pickings:
        for move in odoo.search_read("stock.move", [("id", "in", picking["move_ids"])], ["product_uom_qty"]):
            odoo.write("stock.move", move["id"], {"quantity": move["product_uom_qty"], "picked": True})
        resultado = odoo.call("stock.picking", "button_validate", [picking["id"]])
        if isinstance(resultado, dict):
            raise SystemExit(f"La recepción {picking['id']} pidió un asistente inesperado: {resultado.get('res_model')}")


def facturar(odoo, compra, fecha, referencia, pagada):
    factura = odoo.search("account.move", [("invoice_origin", "=", referencia), ("move_type", "=", "in_invoice")])
    if not factura:
        odoo.call("purchase.order", "action_create_invoice", [compra])
        factura = odoo.search("account.move", [("invoice_origin", "=", referencia), ("move_type", "=", "in_invoice")])
    factura = factura[0]
    datos = odoo.search_read("account.move", [("id", "=", factura)], ["state", "payment_state"])[0]
    fecha_factura = fecha + timedelta(days=2)
    if datos["state"] == "draft":
        odoo.write("account.move", factura, {
            "invoice_date": fecha_factura.isoformat(),
            "ref": f"FAC-{referencia.replace('P', '')}-{fecha_factura:%m%d}",
        })
        odoo.call("account.move", "action_post", [factura])
    if pagada and datos["payment_state"] in ("not_paid", False):
        contexto = {"active_model": "account.move", "active_ids": [factura]}
        asistente = odoo.call("account.payment.register", "create", {
            "payment_date": (fecha_factura + timedelta(days=15)).isoformat(),
            "journal_id": odoo.search("account.journal", [("code", "=", "BNK1")])[0],
        }, context=contexto)
        odoo.call("account.payment.register", "action_create_payments", [asistente], context=contexto)


def main():
    odoo = Odoo()
    almacenes = {w["code"]: w["in_type_id"][0] for w in odoo.search_read("stock.warehouse", [], ["code", "in_type_id"])}
    codigos = [codigo_producto(i) for i in range(len(PRODUCTOS))] + [codigo_material(i) for i in range(len(MATERIALES))]
    ids_variante = variantes(odoo, codigos)

    plan = plan_de_compras()
    for n, ((proveedor, sucursal, lineas, fecha), pagada) in enumerate(plan, start=1):
        valores = {
            "partner_id": odoo.ref(f"__qm__.proveedor_{proveedor.lower()}"),
            "partner_ref": f"PED-{proveedor}-{n:03d}",
            "picking_type_id": almacenes[sucursal],
            "date_order": f"{fecha.isoformat()} 10:00:00",
            "date_planned": f"{(fecha + timedelta(days=3)).isoformat()} 10:00:00",
            "order_line": [(0, 0, {
                "product_id": ids_variante[codigo][0],
                "product_qty": cantidad,
                "price_unit": ids_variante[codigo][1],
            }) for codigo, cantidad in lineas],
        }
        xmlid = f"compra_{n:03d}"
        compra = odoo.ref(f"__qm__.{xmlid}")
        if not compra:
            compra = odoo.upsert("purchase.order", xmlid, valores)
        estado = odoo.search_read("purchase.order", [("id", "=", compra)], ["state", "name"])[0]
        if estado["state"] in ("draft", "sent"):
            odoo.call("purchase.order", "button_confirm", [compra])
            # Confirmar usa la fecha actual; se devuelve la fecha histórica de la compra.
            odoo.write("purchase.order", compra, {"date_approve": valores["date_order"], "date_order": valores["date_order"]})
        recibir(odoo, compra)
        facturar(odoo, compra, fecha, estado["name"], pagada)
        if n % 10 == 0:
            print(f"  {n}/{len(plan)} compras procesadas")

    print(f"Compras: {len(plan)} confirmadas, recibidas y facturadas ({sum(p for _c, p in plan)} pagadas)")


if __name__ == "__main__":
    main()
