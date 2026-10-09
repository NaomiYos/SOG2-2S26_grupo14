"""Paso 13: actualiza el código de la regla "Confirmar pedidos de la tienda".

La regla debe existir antes (se crea en Ajustes > Técnico > Automatización > Reglas de automatización,
con el disparador "El estado está establecido como: Cotización enviada" y el filtro de pedidos con sitio web).
Este script solo reemplaza el código de su acción, para que al comprar en la tienda ocurra todo esto:

1. Se confirma el pedido (sin enviar aún el correo).
2. Se crea y publica la factura de cliente.
3. Se envía el correo de la compra con la factura en PDF adjunta.
4. Se programa el correo de campaña unos 3 minutos después.

Es idempotente: se puede ejecutar varias veces. Antes de reemplazar, imprime el código anterior
para poder restaurarlo si algo falla.
Uso: python -X utf8 13_regla_confirmacion.py
"""
from odoo_cliente import Odoo

NOMBRE_REGLA = "Confirmar pedidos de la tienda"

CODIGO = """\
plantilla_compra = env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
plantilla_campana = env.ref('__qm__.plantilla_correo_campana', raise_if_not_found=False) or env['mail.template'].search([('name', 'ilike', 'Campaña posterior')], limit=1)
records.action_confirm()
fecha = (datetime.datetime.utcnow() + datetime.timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S')
for pedido in records:
    adjuntos = []
    if pedido.invoice_status == 'to invoice':
        facturas = pedido._create_invoices()
        facturas.action_post()
        pdf = env['ir.actions.report']._render_qweb_pdf('account.account_invoices', facturas.ids)[0]
        adjunto = env['ir.attachment'].create({
            'name': 'Factura %s.pdf' % facturas[0].name.replace('/', '-'),
            'type': 'binary',
            'datas': b64encode(pdf),
            'res_model': 'account.move',
            'res_id': facturas[0].id,
            'mimetype': 'application/pdf',
        })
        adjuntos = [adjunto.id]
    if plantilla_compra:
        plantilla_compra.send_mail(pedido.id, force_send=True, email_values={'attachment_ids': adjuntos} if adjuntos else None)
    if plantilla_campana:
        plantilla_campana.send_mail(pedido.id, force_send=False, email_values={'scheduled_date': fecha})
"""


def main():
    odoo = Odoo()
    reglas = odoo.search_read("base.automation", [("name", "=", NOMBRE_REGLA)], ["name", "action_server_ids"])
    if not reglas:
        raise SystemExit(f'No existe la regla "{NOMBRE_REGLA}". Créala primero en Ajustes > Técnico > Automatización.')
    acciones = reglas[0]["action_server_ids"]
    if len(acciones) != 1:
        raise SystemExit(f"La regla debe tener exactamente una acción y tiene {len(acciones)}.")

    anterior = odoo.search_read("ir.actions.server", [("id", "=", acciones[0])], ["code"])[0]["code"]
    print("--- Código anterior (guárdelo por si necesita restaurarlo) ---")
    print(anterior)
    print("--- Fin del código anterior ---")

    odoo.write("ir.actions.server", acciones[0], {"code": CODIGO})
    print(f'Regla "{NOMBRE_REGLA}" actualizada.')


if __name__ == "__main__":
    main()
