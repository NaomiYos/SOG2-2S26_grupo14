"""Paso 6: 150 ventas entregadas y facturadas.

Cada venta se confirma, se entrega desde el almacén de la sucursal del país del cliente
y genera su factura de cliente (publicada). Personas pagan de contado y empresas a 30 días.
Cerca del 80 % queda cobrada: personas en efectivo y empresas por banco. Las empresas compran más volumen que las personas.

Solo se venden cantidades con existencia en la sucursal, así el inventario nunca queda negativo.
Fechas entre mediados de abril y el 4 de octubre de 2026. Idempotente.
Requiere 02_datos_maestros.py y 05_compras.py.
Uso: python 06_ventas.py
"""
import random
from datetime import date, timedelta

from catalogo import PRODUCTOS, clientes, codigo_producto
from odoo_cliente import Odoo
from operaciones import pagar_factura, publicar_factura, validar_movimientos

CANTIDAD = 150
INICIO = date(2026, 4, 15)
DIAS = 173
PORCENTAJE_COBRADO = 0.8
FECHA_CORTE = date(2026, 10, 5)


def existencias_previas(odoo, ids_variante):
    """{(sucursal, código): cantidad} disponible antes de las ventas de este script.

    A las existencias actuales se les suma lo ya entregado a clientes, para que el plan
    sea idéntico en cada ejecución aunque las ventas ya estén cargadas.
    """
    codigo_por_id = {v: k for k, v in ids_variante.items()}
    stock = {}
    for almacen in odoo.search_read("stock.warehouse", [], ["code", "view_location_id"]):
        ubicaciones = ("location_id", "child_of", almacen["view_location_id"][0])
        for quant in odoo.search_read("stock.quant", [ubicaciones, ("location_id.usage", "=", "internal"),
                                                      ("product_id", "in", list(codigo_por_id))], ["product_id", "quantity"]):
            clave = (almacen["code"], codigo_por_id[quant["product_id"][0]])
            stock[clave] = stock.get(clave, 0) + quant["quantity"]
        for move in odoo.search_read("stock.move", [ubicaciones, ("state", "=", "done"), ("location_dest_id.usage", "=", "customer"),
                                                    ("product_id", "in", list(codigo_por_id))], ["product_id", "quantity"]):
            clave = (almacen["code"], codigo_por_id[move["product_id"][0]])
            stock[clave] = stock.get(clave, 0) + move["quantity"]
    return stock


def plan_de_ventas(stock):
    """Lista determinista de ventas: (cliente, sucursal, [(código, cantidad)], fecha, cobrada)."""
    rnd = random.Random(150)
    lista_clientes = clientes()
    codigos = [codigo_producto(i) for i in range(len(PRODUCTOS))]
    plan = []
    for n in range(CANTIDAD):
        # Los primeros 80 pedidos recorren a todos los clientes; el resto se reparte al azar.
        cliente = lista_clientes[n] if n < len(lista_clientes) else rnd.choice(lista_clientes)
        sucursal = cliente["pais"].upper()
        if cliente["empresa"]:
            productos, rango = rnd.sample(codigos, rnd.randint(3, 8)), (6, 24)
        else:
            productos, rango = rnd.sample(codigos, rnd.randint(1, 5)), (1, 6)
        lineas = []
        for codigo in productos:
            cantidad = min(rnd.randint(*rango), int(stock.get((sucursal, codigo), 0)))
            if cantidad > 0:
                stock[(sucursal, codigo)] -= cantidad
                lineas.append((codigo, cantidad))
        if lineas:
            plan.append((cliente, sucursal, lineas, INICIO + timedelta(days=rnd.randrange(DIAS)), rnd.random() < PORCENTAJE_COBRADO))
    plan.sort(key=lambda venta: venta[3])
    return plan


def facturar(odoo, venta, fecha, referencia, cobrada, empresa):
    dominio = [("invoice_origin", "=", referencia), ("move_type", "=", "out_invoice")]
    if not odoo.search("account.move", dominio):
        contexto = {"active_model": "sale.order", "active_ids": [venta]}
        asistente = odoo.call("sale.advance.payment.inv", "create", {"advance_payment_method": "delivered"}, context=contexto)
        odoo.accion("sale.advance.payment.inv", "create_invoices", [asistente], context=contexto)
    factura = odoo.search("account.move", dominio)[0]
    publicar_factura(odoo, factura, {
        "invoice_date": fecha.isoformat(),
        "invoice_date_due": (fecha + timedelta(days=30 if empresa else 0)).isoformat(),
    })
    if cobrada:
        # Cobro entre el mismo día y 20 días después, reproducible por número de pedido.
        dias = random.Random(referencia).randint(0, 20)
        pagar_factura(odoo, factura, min(fecha + timedelta(days=dias), FECHA_CORTE), "BNK1" if empresa else "CSH1")


def main():
    odoo = Odoo()
    almacenes = {w["code"]: w["id"] for w in odoo.search_read("stock.warehouse", [], ["code"])}
    codigos = [codigo_producto(i) for i in range(len(PRODUCTOS))]
    ids_variante = {f["default_code"]: f["id"] for f in odoo.search_read("product.product", [("default_code", "in", codigos)], ["default_code"])}

    stock = existencias_previas(odoo, ids_variante)
    plan = plan_de_ventas(stock)
    for n, (cliente, sucursal, lineas, fecha, cobrada) in enumerate(plan, start=1):
        xmlid = f"venta_{n:03d}"
        venta = odoo.ref(f"__qm__.{xmlid}")
        momento = f"{fecha.isoformat()} 15:00:00"
        if not venta:
            venta = odoo.upsert("sale.order", xmlid, {
                "partner_id": odoo.ref(f"__qm__.cliente_{cliente['codigo'].lower()}"),
                "warehouse_id": almacenes[sucursal],
                "date_order": momento,
                "client_order_ref": f"OC-{cliente['codigo']}-{n:03d}" if cliente["empresa"] else False,
                "order_line": [(0, 0, {"product_id": ids_variante[codigo], "product_uom_qty": cantidad}) for codigo, cantidad in lineas],
            })
        estado = odoo.search_read("sale.order", [("id", "=", venta)], ["state", "name"])[0]
        if estado["state"] in ("draft", "sent"):
            odoo.call("sale.order", "action_confirm", [venta])
            # Confirmar usa la fecha actual; se devuelve la fecha histórica de la venta.
            odoo.write("sale.order", venta, {"date_order": momento})
        validar_movimientos(odoo, [("sale_id", "=", venta)], f"{fecha.isoformat()} 17:00:00")
        facturar(odoo, venta, fecha, estado["name"], cobrada, cliente["empresa"])
        if n % 25 == 0:
            print(f"  {n}/{len(plan)} ventas procesadas")

    print(f"Ventas: {len(plan)} confirmadas, entregadas y facturadas ({sum(v[4] for v in plan)} cobradas)")


if __name__ == "__main__":
    main()
