"""Crea las categorías de la tienda en línea a partir de las categorías internas y las asigna a los productos vendibles."""
from odoo_cliente import Odoo


def main():
    odoo = Odoo()
    productos = odoo.search_read("product.template", [("sale_ok", "=", True)], ["categ_id"])
    por_categoria = {}
    for p in productos:
        if p["categ_id"]:
            por_categoria.setdefault(p["categ_id"][0], []).append(p["id"])

    nombres = {c["id"]: c["name"] for c in odoo.search_read(
        "product.category", [("id", "in", list(por_categoria))], ["name"])}

    for categ_id, ids in por_categoria.items():
        publica = odoo.upsert("product.public.category", f"tienda_categ_{categ_id}", {"name": nombres[categ_id]})
        odoo.write("product.template", ids, {"public_categ_ids": [(4, publica)]})
        print(f"{nombres[categ_id]}: {len(ids)} productos")


if __name__ == "__main__":
    main()