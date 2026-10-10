{
    "name": "QuetzalMart · Correos de los pedidos de la tienda",
    "version": "18.0.1.0.0",
    "summary": "Deja que la regla de la tienda envíe el único correo de la compra (con la factura)",
    "description": """
En los pedidos de la tienda en línea, Odoo enviaría por su cuenta dos correos más:
"Orden pendiente" al registrar un pago por transferencia y la confirmación estándar al pagar con
tarjeta. Los dos salen sin la factura y, el primero, desde odoobot@example.com.
Este módulo los omite solo para los pedidos con sitio web: el correo de la compra (con la factura
en PDF) y el de campaña los envía la regla "Facturar y notificar pedidos de la tienda"
(PROYECTO/datos/13_regla_confirmacion.py). Los pedidos creados en el backend no cambian.
""",
    "category": "Website/Website",
    "author": "SOG2 Grupo 14",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "installable": True,
}
