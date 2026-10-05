"""Paso 3: recursos humanos.

- 3 lugares de trabajo (sede Guatemala, sucursales México y El Salvador).
- 5 departamentos y 6 cargos.
- 35 empleados con cargo, departamento, sucursal, jefe directo y datos personales.
  Los empleados de cada sucursal reportan a su gerente; los gerentes de MX y SV al de GT.

Idempotente: re-ejecutarlo actualiza los registros en lugar de duplicarlos.
Uso: python 03_empleados.py
"""
from catalogo import CARGOS, DEPARTAMENTOS, empleados
from odoo_cliente import Odoo

SUCURSALES = {"GT": "Sede Guatemala", "MX": "Sucursal México", "SV": "Sucursal El Salvador"}


def lugares_de_trabajo(odoo):
    return {
        codigo: odoo.upsert("hr.work.location", f"lugar_{codigo.lower()}", {
            "name": nombre,
            "location_type": "office",
            "address_id": odoo.ref(f"__qm__.sucursal_{codigo.lower()}"),
        })
        for codigo, nombre in SUCURSALES.items()
    }


def departamentos(odoo):
    ids = {}
    for codigo, nombre in DEPARTAMENTOS.items():
        if codigo == "ADM":
            ids[codigo] = odoo.ref("hr.dep_administration")
            odoo.write("hr.department", ids[codigo], {"name": nombre})
        else:
            ids[codigo] = odoo.upsert("hr.department", f"departamento_{codigo.lower()}", {"name": nombre})
    print(f"Departamentos: {len(ids)}")
    return ids


def cargos(odoo, ids_departamento):
    ids = {
        codigo: odoo.upsert("hr.job", f"cargo_{codigo.lower()}", {
            "name": nombre,
            "department_id": ids_departamento[departamento],
        })
        for codigo, (nombre, departamento, _plazas) in CARGOS.items()
    }
    print(f"Cargos: {len(ids)}")
    return ids


def main():
    odoo = Odoo()
    ids_lugar = lugares_de_trabajo(odoo)
    ids_departamento = departamentos(odoo)
    ids_cargo = cargos(odoo, ids_departamento)

    lista = empleados()
    ids_empleado = {}
    # Primero los gerentes, para poder asignarlos como jefes del resto.
    for e in sorted(lista, key=lambda x: x["cargo"] != "GER"):
        if e["cargo"] == "GER":
            jefe = ids_empleado.get("GER_GT") if e["sucursal"] != "GT" else False
        else:
            jefe = ids_empleado[f"GER_{e['sucursal']}"]
        ids_empleado[e["codigo"]] = odoo.upsert("hr.employee", f"empleado_{e['codigo'].lower()}", {
            "name": e["nombre"],
            "job_id": ids_cargo[e["cargo"]],
            "job_title": CARGOS[e["cargo"]][0],
            "department_id": ids_departamento[e["departamento"]],
            "parent_id": jefe,
            "work_location_id": ids_lugar[e["sucursal"]],
            "address_id": odoo.ref(f"__qm__.sucursal_{e['sucursal'].lower()}"),
            "work_email": e["correo"],
            "mobile_phone": e["movil"],
            "gender": e["genero"],
            "birthday": e["nacimiento"],
            "identification_id": e["identificacion"],
            "private_country_id": odoo.ref(f"base.{e['sucursal'].lower()}"),
            "marital": e["estado_civil"],
            "employee_type": "employee",
        })
        if e["cargo"] == "GER":
            ids_empleado[f"GER_{e['sucursal']}"] = ids_empleado[e["codigo"]]

    # Jefe de cada departamento: el primer empleado de la sede Guatemala en ese departamento.
    for codigo, id_departamento in ids_departamento.items():
        jefe = next(e for e in lista if e["departamento"] == codigo and e["sucursal"] == "GT")
        odoo.write("hr.department", id_departamento, {"manager_id": ids_empleado[jefe["codigo"]]})

    print(f"Empleados: {len(lista)}")


if __name__ == "__main__":
    main()
