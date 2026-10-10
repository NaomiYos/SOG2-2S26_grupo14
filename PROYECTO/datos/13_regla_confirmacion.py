"""Paso 13: reglas de automatización de la tienda (pedidos web y registro de clientes).

Crea o actualiza tres reglas (Ajustes > Técnico > Automatización > Reglas de automatización):

1. "Confirmar pedidos de la tienda" (Pedido de venta, el estado pasa a "Cotización enviada", con sitio web).
   Con pago por transferencia el pedido queda en "Cotización enviada": la regla lo confirma.
2. "Facturar y notificar pedidos de la tienda" (Pedido de venta, el estado pasa a "Orden de venta",
   con sitio web). Sirve igual para transferencia (lo confirma la regla 1) y para tarjeta (lo confirma
   el pago). Para cada pedido:
   - crea y publica la factura; si el pago ya está hecho, la liga a la transacción para que quede pagada;
   - guarda el PDF de la factura en la carpeta "Facturas de clientes" del gestor documental;
   - registra en el CRM una oportunidad ganada del cliente (la de su registro o una nueva);
   - envía el correo de la compra con la factura en PDF adjunta;
   - programa el correo de campaña unos 3 minutos después.
3. "Oportunidad al registrarse en la tienda" (Usuario, al crear un usuario del portal):
   crea una oportunidad en el CRM con el cliente que se registró.

Los correos estándar de Odoo para estos pedidos ("Orden pendiente" y la confirmación sin factura)
los omite el módulo qm_tienda, así el cliente recibe solo el de la compra y el de campaña.

Idempotente: se puede ejecutar varias veces. Antes de reemplazar código imprime el anterior.
Requiere 12_plantillas_correo.py y 15_tienda_crm_pagos.py (carpeta y etiqueta del gestor documental).
Uso: python -X utf8 13_regla_confirmacion.py
"""
from odoo_cliente import Odoo

CODIGO_CONFIRMAR = """\
records.action_confirm()
"""

CODIGO_FACTURAR = """\
plantilla_compra = env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
plantilla_campana = env.ref('__qm__.plantilla_correo_campana', raise_if_not_found=False) or env['mail.template'].search([('name', 'ilike', 'Campaña posterior')], limit=1)
carpeta = env.ref('__qm__.dms_carpeta_facturas_clientes', raise_if_not_found=False)
etiqueta = env.ref('__qm__.dms_etiqueta_factura_cliente', raise_if_not_found=False)
fecha = (datetime.datetime.utcnow() + datetime.timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S')
for pedido in records:
    # Con transferencia, Odoo evalúa esta regla dos veces (borrador -> enviada -> orden de venta):
    # un pedido ya facturado y ya ligado a su oportunidad no se vuelve a procesar.
    if pedido.invoice_status != 'to invoice' and pedido.opportunity_id:
        continue
    adjuntos = []
    if pedido.invoice_status == 'to invoice':
        facturas = pedido._create_invoices()
        facturas.action_post()
        pagos = pedido.transaction_ids.filtered_domain([('state', '=', 'done')])
        if pagos:
            pagos.write({'invoice_ids': [(4, factura.id) for factura in facturas]})
        pdf = env['ir.actions.report']._render_qweb_pdf('account.account_invoices', facturas.ids)[0]
        nombre = 'Factura %s.pdf' % facturas[0].name.replace('/', '-')
        adjunto = env['ir.attachment'].create({
            'name': nombre,
            'type': 'binary',
            'datas': b64encode(pdf),
            'res_model': 'account.move',
            'res_id': facturas[0].id,
            'mimetype': 'application/pdf',
        })
        adjuntos = [adjunto.id]
        if carpeta:
            env['dms.file'].create({
                'name': nombre,
                'directory_id': carpeta.id,
                'content': b64encode(pdf),
                'tag_ids': [(6, 0, etiqueta.ids)],
            })
    if not pedido.opportunity_id:
        cliente = pedido.partner_id.commercial_partner_id
        oportunidad = env['crm.lead'].search([('partner_id', 'child_of', cliente.id), ('type', '=', 'opportunity'), ('stage_id.is_won', '=', False)], limit=1)
        if not oportunidad:
            oportunidad = env['crm.lead'].create({
                'name': 'Compra en la tienda %s' % pedido.name,
                'type': 'opportunity',
                'partner_id': pedido.partner_id.id,
                'team_id': pedido.team_id.id,
            })
        oportunidad.write({'expected_revenue': pedido.amount_untaxed})
        oportunidad.action_set_won()
        pedido.write({'opportunity_id': oportunidad.id})
    if plantilla_compra:
        plantilla_compra.send_mail(pedido.id, force_send=True, email_values={'attachment_ids': adjuntos} if adjuntos else None)
    if plantilla_campana:
        plantilla_campana.send_mail(pedido.id, force_send=False, email_values={'scheduled_date': fecha})
"""

CODIGO_OPORTUNIDAD = """\
equipo = env['website'].search([], limit=1).salesteam_id
for usuario in records:
    cliente = usuario.partner_id
    if not env['crm.lead'].search_count([('partner_id', '=', cliente.id)]):
        env['crm.lead'].create({
            'name': 'Nuevo cliente de la tienda: %s' % cliente.name,
            'type': 'opportunity',
            'partner_id': cliente.id,
            'email_from': cliente.email,
            'team_id': equipo.id,
            'description': 'Se registró en la tienda en línea.',
        })
"""

# xmlid, nombre, modelo, disparador, (campo, valor) del estado o None, filtro, código
REGLAS = [
    ("regla_confirmar_pedidos_tienda", "Confirmar pedidos de la tienda", "sale.order", "on_state_set",
     ("state", "sent"), '[("state", "=", "sent"), ("website_id", "!=", False)]', CODIGO_CONFIRMAR),
    ("regla_facturar_pedidos_tienda", "Facturar y notificar pedidos de la tienda", "sale.order", "on_state_set",
     ("state", "sale"), '[("state", "=", "sale"), ("website_id", "!=", False)]', CODIGO_FACTURAR),
    ("regla_oportunidad_registro", "Oportunidad al registrarse en la tienda", "res.users", "on_create",
     None, '[("share", "=", True)]', CODIGO_OPORTUNIDAD),
]


def buscar_regla(odoo, xmlid, nombre):
    res_id = odoo.ref(f"__qm__.{xmlid}")
    if res_id and odoo.search("base.automation", [("id", "=", res_id)], context={"active_test": False}):
        return res_id
    encontradas = odoo.search("base.automation", [("name", "=", nombre)], context={"active_test": False})
    if encontradas:
        if not res_id:
            odoo.create("ir.model.data", {"module": "__qm__", "name": xmlid, "model": "base.automation",
                                          "res_id": encontradas[0], "noupdate": True})
        return encontradas[0]
    return None


def main():
    odoo = Odoo()
    for xmlid, nombre, modelo, disparador, estado, filtro, codigo in REGLAS:
        modelo_id = odoo.search("ir.model", [("model", "=", modelo)])[0]
        valores = {"name": nombre, "model_id": modelo_id, "trigger": disparador, "filter_domain": filtro, "active": True}
        if estado:
            campo = odoo.search("ir.model.fields", [("model", "=", modelo), ("name", "=", estado[0])])[0]
            opcion = odoo.search("ir.model.fields.selection", [("field_id", "=", campo), ("value", "=", estado[1])])[0]
            valores.update({"trigger_field_ids": [(6, 0, [campo])], "trg_selection_field_id": opcion})

        regla = buscar_regla(odoo, xmlid, nombre)
        if not regla:
            valores["action_server_ids"] = [(0, 0, {"name": nombre, "model_id": modelo_id, "state": "code", "code": codigo})]
            regla = odoo.create("base.automation", valores)
            odoo.create("ir.model.data", {"module": "__qm__", "name": xmlid, "model": "base.automation",
                                          "res_id": regla, "noupdate": True})
            print(f'Regla "{nombre}" creada.')
            continue

        odoo.write("base.automation", regla, valores)
        acciones = odoo.search_read("base.automation", [("id", "=", regla)], ["action_server_ids"])[0]["action_server_ids"]
        if len(acciones) != 1:
            raise SystemExit(f'La regla "{nombre}" debe tener exactamente una acción y tiene {len(acciones)}.')
        anterior = odoo.search_read("ir.actions.server", [("id", "=", acciones[0])], ["code"])[0]["code"]
        if anterior != codigo:
            print(f'--- Código anterior de "{nombre}" (guárdelo por si necesita restaurarlo) ---')
            print(anterior)
            print("--- Fin del código anterior ---")
            odoo.write("ir.actions.server", acciones[0], {"code": codigo})
        print(f'Regla "{nombre}" actualizada.')


if __name__ == "__main__":
    main()
