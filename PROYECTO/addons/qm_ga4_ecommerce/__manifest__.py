{
    "name": "QuetzalMart · GA4 comercio electrónico",
    "version": "18.0.1.0.0",
    "summary": "Completa los eventos de comercio electrónico de GA4 que Odoo 18 no emite",
    "description": """
Odoo 18 ya envía view_item, add_to_cart y purchase a Google Analytics 4.
Este módulo agrega los eventos del carrito y del checkout, con items, value y currency:
view_cart, remove_from_cart, add_to_cart (al subir cantidades en el carrito),
begin_checkout, add_shipping_info y add_payment_info.
""",
    "category": "Website/Website",
    "author": "SOG2 Grupo 14",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": ["views/templates.xml"],
    "assets": {
        "web.assets_frontend": ["qm_ga4_ecommerce/static/src/js/qm_ga4_ecommerce.js"],
    },
    "installable": True,
}
