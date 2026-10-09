"""Paso 7: 40 cotizaciones (sin confirmar).

- 20 cotizaciones de venta a clientes (presupuestos), con 30 días de validez.
- 20 solicitudes de presupuesto a proveedores.
El auxiliar aclaró en el foro que son 20 de venta y 20 de compra, no 20 en total.
La mitad de cada grupo queda marcada como enviada y el resto en borrador.
Fechas entre el 1 de septiembre y el 4 de octubre de 2026. Idempotente.
Requiere 02_datos_maestros.py y 04_materiales.py.
Uso: python 07_cotizaciones.py
"""
import random
from datetime import date, timedelta

from catalogo import CATEGORIAS, CATEGORIAS_MATERIAL, MATERIALES, PRODUCTOS, clientes, codigo_material, codigo_producto
from odoo_cliente import Odoo

A_CLIENTES = 20
A_PROVEEDORES = 20
# Las primeras 12 y 8 se generaron con una sola semilla (clientes y luego proveedores). Se conservan
# en ese orden y las nuevas usan otra semilla, para que volver a cargar no cambie las ya existentes.
ORIGINALES_CLIENTES = 12
ORIGINALES_PROVEEDORES = 8
INICIO = date(2026, 9, 1)
DIAS = 34


class Cotizaciones:
    def __init__(self, odoo):
        self.odoo = odoo
        self.almacenes = {w["code"]: (w["id"], w["in_type_id"][0]) for w in odoo.search_read("stock.warehouse", [], ["code", "in_type_id"])}
        codigos = [codigo_producto(i) for i in range(len(PRODUCTOS))] + [codigo_material(i) for i in range(len(MATERIALES))]
        self.variantes = {f["default_code"]: (f["id"], f["standard_price"])
                          for f in odoo.search_read("product.product", [("default_code", "in", codigos)], ["default_code", "standard_price"])}
        # Cotizaciones a clientes: empresas que piden precio por volumen.
        self.empresas = [c for c in clientes() if c["empresa"]]
        # Solicitudes a proveedores: cada uno cotiza lo que surte (mercadería o materiales).
        self.por_proveedor = {}
        for i, (categoria, *_resto) in enumerate(PRODUCTOS):
            self.por_proveedor.setdefault(CATEGORIAS[categoria][2], []).append(codigo_producto(i))
        for i, (categoria, *_resto) in enumerate(MATERIALES):
            self.por_proveedor.setdefault(CATEGORIAS_MATERIAL[categoria][2], []).append(codigo_material(i))

    def a_cliente(self, n, rnd):
        cliente = rnd.choice(self.empresas)
        fecha = INICIO + timedelta(days=rnd.randrange(DIAS))
        productos = rnd.sample([codigo_producto(i) for i in range(len(PRODUCTOS))], rnd.randint(3, 7))
        cotizacion = self.odoo.upsert("sale.order", f"cotizacion_cliente_{n:02d}", {
            "partner_id": self.odoo.ref(f"__qm__.cliente_{cliente['codigo'].lower()}"),
            "warehouse_id": self.almacenes[cliente["pais"].upper()][0],
            "date_order": f"{fecha.isoformat()} 11:00:00",
            "validity_date": (fecha + timedelta(days=30)).isoformat(),
            "note": "Precios sujetos a existencias. Entrega a domicilio sin costo en pedidos mayores a Q 500.00.",
            "order_line": [(5, 0, 0)] + [(0, 0, {"product_id": self.variantes[c][0], "product_uom_qty": rnd.randint(10, 60)}) for c in productos],
        })
        if n % 2 == 0:
            self.odoo.write("sale.order", cotizacion, {"state": "sent"})

    def a_proveedor(self, n, rnd):
        proveedor = rnd.choice(sorted(self.por_proveedor))
        sucursal = rnd.choice(["GT", "MX", "SV"])
        fecha = INICIO + timedelta(days=rnd.randrange(DIAS))
        disponibles = self.por_proveedor[proveedor]
        productos = rnd.sample(disponibles, rnd.randint(2, min(5, len(disponibles))))
        solicitud = self.odoo.upsert("purchase.order", f"cotizacion_proveedor_{n:02d}", {
            "partner_id": self.odoo.ref(f"__qm__.proveedor_{proveedor.lower()}"),
            "picking_type_id": self.almacenes[sucursal][1],
            "date_order": f"{fecha.isoformat()} 09:00:00",
            "date_planned": f"{(fecha + timedelta(days=10)).isoformat()} 09:00:00",
            "notes": "Favor de cotizar precio unitario, tiempo de entrega y condiciones de pago.",
            "order_line": [(5, 0, 0)] + [(0, 0, {
                "product_id": self.variantes[c][0],
                "product_qty": rnd.randint(20, 150) if c.startswith("QM") else rnd.randint(2, 15),
                "price_unit": self.variantes[c][1],
            }) for c in productos],
        })
        if n % 2 == 0:
            self.odoo.write("purchase.order", solicitud, {"state": "sent"})


def main():
    cotizaciones = Cotizaciones(Odoo())

    originales = random.Random(20)
    for n in range(1, ORIGINALES_CLIENTES + 1):
        cotizaciones.a_cliente(n, originales)
    for n in range(1, ORIGINALES_PROVEEDORES + 1):
        cotizaciones.a_proveedor(n, originales)

    nuevas = random.Random(2020)
    for n in range(ORIGINALES_CLIENTES + 1, A_CLIENTES + 1):
        cotizaciones.a_cliente(n, nuevas)
    for n in range(ORIGINALES_PROVEEDORES + 1, A_PROVEEDORES + 1):
        cotizaciones.a_proveedor(n, nuevas)

    print(f"Cotizaciones: {A_CLIENTES} a clientes y {A_PROVEEDORES} a proveedores (la mitad enviadas)")


if __name__ == "__main__":
    main()
