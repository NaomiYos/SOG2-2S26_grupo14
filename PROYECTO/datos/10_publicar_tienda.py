"""Publica en la tienda en línea los productos que se venden (no los materiales de operación)."""
from odoo_cliente import Odoo


def main():
    odoo = Odoo()
    pendientes = odoo.search("product.template", [("sale_ok", "=", True), ("is_published", "=", False)])
    if pendientes:
        odoo.write("product.template", pendientes, {"is_published": True})
    total = len(odoo.search("product.template", [("is_published", "=", True)]))
    print(f"Publicados ahora: {len(pendientes)} | Total publicados: {total}")


if __name__ == "__main__":
    main()