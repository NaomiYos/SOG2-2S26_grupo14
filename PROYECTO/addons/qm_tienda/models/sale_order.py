from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _send_payment_succeeded_for_order_mail(self):
        """Sin correo "Orden pendiente" en los pedidos de la tienda."""
        return super(SaleOrder, self.filtered(lambda pedido: not pedido.website_id))._send_payment_succeeded_for_order_mail()

    def _send_order_confirmation_mail(self):
        """La confirmación de los pedidos de la tienda la envía la regla, con la factura adjunta."""
        return super(SaleOrder, self.filtered(lambda pedido: not pedido.website_id))._send_order_confirmation_mail()
