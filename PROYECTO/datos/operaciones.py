"""Operaciones comunes de inventario y contabilidad para los scripts de compras y ventas."""


def validar_movimientos(odoo, dominio, fecha):
    """Valida completas las recepciones/entregas pendientes y les asigna la fecha histórica.

    Odoo registra la fecha actual al validar; se reemplaza por `fecha` (datetime en texto)
    para que recepciones, entregas y la "fecha de entrega" de las facturas sean coherentes.
    """
    pickings = odoo.search_read("stock.picking", dominio + [("state", "not in", ["done", "cancel"])], ["move_ids"])
    for picking in pickings:
        # La fecha programada solo se puede cambiar antes de validar.
        odoo.write("stock.picking", picking["id"], {"scheduled_date": fecha})
        for move in odoo.search_read("stock.move", [("id", "in", picking["move_ids"])], ["product_uom_qty"]):
            odoo.write("stock.move", move["id"], {"quantity": move["product_uom_qty"], "picked": True})
        resultado = odoo.call("stock.picking", "button_validate", [picking["id"]])
        if isinstance(resultado, dict):
            raise SystemExit(f"El movimiento {picking['id']} pidió un asistente inesperado: {resultado.get('res_model')}")

    # Fecha de realizado histórica en todos los movimientos terminados (también los de ejecuciones previas).
    for picking in odoo.search_read("stock.picking", dominio + [("state", "=", "done")], ["move_ids", "date_done"]):
        if picking["date_done"] == fecha:
            continue
        odoo.write("stock.picking", picking["id"], {"date_done": fecha})
        odoo.write("stock.move", picking["move_ids"], {"date": fecha})
        lineas = odoo.search("stock.move.line", [("move_id", "in", picking["move_ids"])])
        if lineas:
            odoo.write("stock.move.line", lineas, {"date": fecha})


def publicar_factura(odoo, factura, valores):
    """Completa y publica una factura en borrador. No hace nada si ya está publicada."""
    if odoo.search_read("account.move", [("id", "=", factura)], ["state"])[0]["state"] == "draft":
        odoo.write("account.move", factura, valores)
        odoo.call("account.move", "action_post", [factura])


def pagar_factura(odoo, factura, fecha, codigo_diario):
    """Registra el pago total de una factura publicada si aún no está pagada."""
    if odoo.search_read("account.move", [("id", "=", factura)], ["payment_state"])[0]["payment_state"] != "not_paid":
        return
    contexto = {"active_model": "account.move", "active_ids": [factura]}
    asistente = odoo.call("account.payment.register", "create", {
        "payment_date": fecha.isoformat(),
        "journal_id": odoo.search("account.journal", [("code", "=", codigo_diario)])[0],
    }, context=contexto)
    odoo.call("account.payment.register", "action_create_payments", [asistente], context=contexto)
