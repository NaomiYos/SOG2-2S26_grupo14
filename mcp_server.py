"""
mcp_server.py - Rol 4: MCP Server.

Expone las funciones de analisis del Rol 2 (analisis_exploratorio.py) y
del Rol 3 (analisis_segmentacion.py) como herramientas MCP, sin
modificarlas: cada funcion ya devuelve un dict serializable a JSON y
trae su propio docstring, que es lo que el modelo de IA lee para saber
cuando usarla (ver GUIA_EQUIPO.md seccion 5, contrato de funciones).

Deliberadamente NO se expone una herramienta generica tipo
ejecutar_sql(query): el catedratico lo marca como error de diseno
porque abre una inyeccion SQL y el modelo genera consultas
inconsistentes. En su lugar se exponen las 13 funciones de negocio ya
construidas por los roles 2 y 3, una por pregunta del alcance.

Uso:
    python mcp_server.py            # corre el server en stdio
"""

from mcp.server.fastmcp import FastMCP

import analisis_exploratorio as rol2
import analisis_segmentacion as rol3

mcp = FastMCP("ventas-2021")

# ---- Rol 2: analisis exploratorio y tendencias (puntos 2 y 3) ----
mcp.tool()(rol2.estadisticas_basicas)
mcp.tool()(rol2.ventas_por_mes)
mcp.tool()(rol2.distribucion_metodo_pago)
mcp.tool()(rol2.distribucion_navegador)
mcp.tool()(rol2.distribucion_boletin_vale)
mcp.tool()(rol2.ventas_contra_entrega)
mcp.tool()(rol2.promociones_por_mes)

# ---- Rol 3: segmentacion y correlacion (puntos 4 y 5) ----
mcp.tool()(rol3.segmentar_por_edad)
mcp.tool()(rol3.comparar_generos)
mcp.tool()(rol3.patrones_boletin_vale)
mcp.tool()(rol3.correlacion_edad_venta)
mcp.tool()(rol3.correlacion_genero_metodo_pago)
mcp.tool()(rol3.correlacion_boletin_vale)


if __name__ == "__main__":
    mcp.run()
