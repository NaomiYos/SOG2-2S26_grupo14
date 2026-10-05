"""Conexión XML-RPC a Odoo compartida por todos los scripts de carga.

Lee ODOO_URL, ODOO_DB, ODOO_USER y ODOO_PASSWORD de datos/.env o del entorno.
Solo usa la librería estándar para que corra igual en local y contra el servidor.
"""
import os
import sys
import xmlrpc.client
from pathlib import Path


def _cargar_env():
    archivo = Path(__file__).with_name(".env")
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


class Odoo:
    def __init__(self):
        _cargar_env()
        faltan = [v for v in ("ODOO_URL", "ODOO_DB", "ODOO_USER", "ODOO_PASSWORD") if not os.environ.get(v)]
        if faltan:
            sys.exit(f"Faltan variables: {', '.join(faltan)}. Copie datos/.env.example como datos/.env")
        self.url = os.environ["ODOO_URL"].rstrip("/")
        self.db = os.environ["ODOO_DB"]
        self.password = os.environ["ODOO_PASSWORD"]
        comun = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = comun.authenticate(self.db, os.environ["ODOO_USER"], self.password, {})
        if not self.uid:
            sys.exit("Usuario o contraseña de Odoo incorrectos")
        self._modelos = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)

    def call(self, modelo, metodo, *args, **kwargs):
        return self._modelos.execute_kw(self.db, self.uid, self.password, modelo, metodo, list(args), kwargs)

    def search(self, modelo, dominio, **kwargs):
        return self.call(modelo, "search", dominio, **kwargs)

    def search_read(self, modelo, dominio, campos, **kwargs):
        return self.call(modelo, "search_read", dominio, fields=campos, **kwargs)

    def create(self, modelo, valores):
        return self.call(modelo, "create", valores)

    def write(self, modelo, ids, valores):
        return self.call(modelo, "write", ids if isinstance(ids, list) else [ids], valores)

    def ref(self, xmlid):
        """Id de un registro por su External ID, o None si no existe."""
        modulo, nombre = xmlid.split(".", 1)
        res = self.search_read("ir.model.data", [("module", "=", modulo), ("name", "=", nombre)], ["res_id"])
        return res[0]["res_id"] if res else None

    def upsert(self, modelo, xmlid, valores):
        """Crea o actualiza un registro identificado por External ID (__qm__.<nombre>).

        Permite re-ejecutar cualquier script sin duplicar datos.
        """
        nombre = xmlid.split(".", 1)[1] if "." in xmlid else xmlid
        res_id = self.ref(f"__qm__.{nombre}")
        if res_id and self.search(modelo, [("id", "=", res_id)], context={"active_test": False}):
            self.write(modelo, res_id, valores)
            return res_id
        res_id = self.create(modelo, valores)
        self.create("ir.model.data", {"module": "__qm__", "name": nombre, "model": modelo, "res_id": res_id, "noupdate": True})
        return res_id
