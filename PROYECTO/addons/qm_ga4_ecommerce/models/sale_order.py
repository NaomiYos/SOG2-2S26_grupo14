from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _qm_ga4_datos(self):
        """Carrito en el formato de comercio electrónico de GA4.

        Los items usan las mismas claves que Odoo en su evento purchase
        (WebsiteSale.order_lines_2_google_api) para que GA4 los cruce.
        """
        self.ensure_one()
        productos = self.order_line.filtered(lambda linea: not linea.is_delivery and not linea.display_type)
        envio = self.order_line.filtered("is_delivery")
        return {
            "pedido": self.id,
            "currency": self.currency_id.name,
            "value": sum(productos.mapped("price_subtotal")),
            "shipping": sum(envio.mapped("price_unit")),
            "shipping_tier": self.carrier_id.name or "",
            "lineas": [
                {
                    "product_id": linea.product_id.id,
                    "item": {
                        "item_id": linea.product_id.barcode or linea.product_id.id,
                        "item_name": linea.product_id.name or "-",
                        "item_category": linea.product_id.categ_id.name or "-",
                        "price": linea.price_unit,
                        "quantity": linea.product_uom_qty,
                    },
                }
                for linea in productos
            ],
        }
