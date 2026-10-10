// Invoke Code (C#) · consolida lo leído de todas las hojas "clientes" y "productos".
// Deja los encabezados con el nombre técnico del campo de Odoo, para que la pantalla Importar los reconozca sola.
// Argumentos:
//   dtClientesCrudo       DataTable  In    todas las hojas "clientes" unidas con Merge Data Table
//   dtProductosCrudo      DataTable  In    todas las hojas "productos" unidas con Merge Data Table
//   ubicacionExistencias  String     In    ubicación de Odoo para "Cantidad a la mano", por ejemplo "GT/Existencias"
//   dtClientes            DataTable  Out   para Contactos > Importar
//   dtProductos           DataTable  Out   para Inventario > Productos > Importar
//   dtExistencias         DataTable  Out   para Inventario > Inventario físico > Importar
//   dtRechazos            DataTable  Out   filas que no se cargan y por qué
//   resumen               String     Out   conteos para el registro y el mensaje final
var cultura = System.Globalization.CultureInfo.InvariantCulture;
var numeros = System.Globalization.NumberStyles.Float;

// Encabezado normalizado: sin asterisco, sin espacios extra y en minúsculas ("Name*" -> "name").
Func<string, string> clave = s => System.Text.RegularExpressions.Regex.Replace((s ?? "").Replace("*", "").Trim().ToLowerInvariant(), @"\s+", " ");

Func<DataTable, Dictionary<string, List<string>>> columnas = t =>
{
    var mapa = new Dictionary<string, List<string>>();
    if (t != null)
        foreach (DataColumn c in t.Columns)
        {
            string k = clave(c.ColumnName);
            if (!mapa.ContainsKey(k)) mapa[k] = new List<string>();
            mapa[k].Add(c.ColumnName);
        }
    return mapa;
};

// Primer valor no vacío entre los encabezados aceptados (alias) de una fila.
Func<DataRow, Dictionary<string, List<string>>, string[], string> leer = (fila, mapa, alias) =>
{
    foreach (string a in alias)
    {
        List<string> nombres;
        if (!mapa.TryGetValue(a, out nombres)) continue;
        foreach (string nombre in nombres)
        {
            object v = fila[nombre];
            if (v == null || v == DBNull.Value) continue;
            string s = Convert.ToString(v, cultura).Trim();
            if (s != "") return s;
        }
    }
    return "";
};

// Excel guarda códigos postales y de barras como números: 10407.0 -> "10407", 54398267125.00001 -> "54398267125".
Func<string, bool, string> sinDecimales = (s, siempre) =>
{
    double d;
    if (s == "" || !double.TryParse(s, numeros, cultura, out d)) return s;
    if (!siempre && Math.Abs(d - Math.Round(d)) > 1e-9) return s;
    return Math.Round(d).ToString("0", cultura);
};

Func<string, string> numero = s =>
{
    double d;
    return s != "" && double.TryParse(s, numeros, cultura, out d) ? d.ToString(cultura) : s;
};

var tiposCliente = new Dictionary<string, string> {
    { "company", "company" }, { "empresa", "company" }, { "compañía", "company" }, { "compania", "company" },
    { "person", "person" }, { "individual", "person" }, { "persona", "person" } };
var tiposProducto = new Dictionary<string, string> {
    { "goods", "consu" }, { "consu", "consu" }, { "consumable", "consu" }, { "storable product", "consu" },
    { "product", "consu" }, { "bienes", "consu" }, { "producto", "consu" },
    { "service", "service" }, { "servicio", "service" }, { "combo", "combo" } };
var verdadero = new HashSet<string> { "true", "1", "yes", "sí", "si", "verdadero", "x" };

// Tabla local: C# no deja usar argumentos Out dentro de una lambda (UiPath los declara como out).
var rechazos = new DataTable("rechazos");
foreach (string c in new[] { "Tipo", "Archivo", "Hoja", "Fila", "Nombre", "Motivo" }) rechazos.Columns.Add(c);
Action<string, DataRow, string, string> rechazar = (tipo, fila, nombre, motivo) =>
{
    Func<string, string> origen = col => fila.Table.Columns.Contains(col) ? Convert.ToString(fila[col]) : "";
    rechazos.Rows.Add(tipo, origen("__archivo"), origen("__hoja"), origen("__fila"), nombre, motivo);
};

// ---- Clientes ------------------------------------------------------------------------------
string[] camposCliente = { "name", "company_type", "parent_id", "email", "phone", "street", "street2", "city",
                           "state_id", "zip", "country_id", "vat", "website", "category_id", "ref", "comment" };
// Alias aceptados por campo (el primero es el encabezado del archivo de ejemplo del foro).
var aliasCliente = new Dictionary<string, string[]> {
    { "name", new[] { "name", "nombre" } },
    { "company_type", new[] { "company type", "tipo de compañía", "tipo" } },
    { "parent_id", new[] { "related company", "empresa relacionada" } },
    { "email", new[] { "email", "correo", "correo electrónico" } },
    { "phone", new[] { "phone", "teléfono", "telefono" } },
    { "street", new[] { "street", "calle" } },
    { "street2", new[] { "street2", "calle 2" } },
    { "city", new[] { "city", "ciudad" } },
    { "state_id", new[] { "state", "estado", "departamento" } },
    { "zip", new[] { "zip", "código postal", "codigo postal" } },
    { "country_id", new[] { "country", "país", "pais" } },
    { "vat", new[] { "tax id", "nit", "número de identificación fiscal" } },
    { "website", new[] { "website", "sitio web" } },
    { "category_id", new[] { "tags", "etiquetas" } },
    { "ref", new[] { "reference", "referencia" } },
    { "comment", new[] { "notes", "notas" } } };

dtClientes = new DataTable("clientes");
foreach (string c in camposCliente) dtClientes.Columns.Add(c);
var vistosCliente = new HashSet<string>();
int clientesDuplicados = 0;
var mapaCli = columnas(dtClientesCrudo);
if (dtClientesCrudo != null)
    foreach (DataRow fila in dtClientesCrudo.Rows)
    {
        var v = new Dictionary<string, string>();
        bool vacia = true;
        foreach (string campo in camposCliente)
        {
            v[campo] = leer(fila, mapaCli, aliasCliente[campo]);
            if (v[campo] != "") vacia = false;
        }
        if (vacia) continue;  // filas con formato pero sin datos
        if (v["name"] == "") { rechazar("Cliente", fila, "", "Falta Name"); continue; }
        string tipo;
        if (v["company_type"] == "") { rechazar("Cliente", fila, v["name"], "Falta Company Type"); continue; }
        if (!tiposCliente.TryGetValue(v["company_type"].ToLowerInvariant(), out tipo))
        { rechazar("Cliente", fila, v["name"], "Company Type no válido: " + v["company_type"]); continue; }
        v["company_type"] = tipo;
        v["zip"] = sinDecimales(v["zip"], false);
        v["phone"] = sinDecimales(v["phone"], false);
        v["vat"] = sinDecimales(v["vat"], false);
        string k = v["name"].ToLowerInvariant() + "|" + v["email"].ToLowerInvariant();
        if (!vistosCliente.Add(k)) { clientesDuplicados++; continue; }
        var nueva = dtClientes.NewRow();
        foreach (string campo in camposCliente) nueva[campo] = v[campo];
        dtClientes.Rows.Add(nueva);
    }

// ---- Productos y existencias -----------------------------------------------------------------
string[] camposProducto = { "id", "name", "type", "default_code", "barcode", "list_price", "standard_price",
                            "weight", "description_sale", "is_published", "is_storable" };
var aliasProducto = new Dictionary<string, string[]> {
    { "id", new[] { "external id", "id externo" } },
    { "name", new[] { "name", "nombre" } },
    { "type", new[] { "product type", "tipo de producto" } },
    { "default_code", new[] { "internal reference", "referencia interna" } },
    { "barcode", new[] { "barcode", "código de barras", "codigo de barras" } },
    { "list_price", new[] { "sales price", "precio de venta" } },
    { "standard_price", new[] { "cost", "costo" } },
    { "weight", new[] { "weight", "peso" } },
    { "description_sale", new[] { "sales description", "descripción de venta", "descripcion de venta" } },
    { "is_published", new[] { "está publicado", "esta publicado", "is published", "published" } } };
string[] aliasCantidad = { "cantidad a la mano", "quantity on hand", "on hand" };

dtProductos = new DataTable("productos");
foreach (string c in camposProducto) dtProductos.Columns.Add(c);
dtExistencias = new DataTable("existencias");
foreach (string c in new[] { "product_id", "location_id", "inventory_quantity" }) dtExistencias.Columns.Add(c);
var vistosProducto = new HashSet<string>();
int productosDuplicados = 0;
var mapaProd = columnas(dtProductosCrudo);
if (dtProductosCrudo != null)
    foreach (DataRow fila in dtProductosCrudo.Rows)
    {
        var v = new Dictionary<string, string>();
        bool vacia = true;
        foreach (string campo in aliasProducto.Keys)
        {
            v[campo] = leer(fila, mapaProd, aliasProducto[campo]);
            if (v[campo] != "") vacia = false;
        }
        string cantidad = leer(fila, mapaProd, aliasCantidad);
        if (vacia && cantidad == "") continue;
        if (v["id"] == "") { rechazar("Producto", fila, v["name"], "Falta External ID"); continue; }
        if (v["name"] == "") { rechazar("Producto", fila, v["id"], "Falta Name"); continue; }
        string tipo;
        if (v["type"] == "") { rechazar("Producto", fila, v["name"], "Falta Product Type"); continue; }
        if (!tiposProducto.TryGetValue(v["type"].ToLowerInvariant(), out tipo))
        { rechazar("Producto", fila, v["name"], "Product Type no válido: " + v["type"]); continue; }
        v["type"] = tipo;
        v["barcode"] = sinDecimales(v["barcode"], true);
        v["default_code"] = sinDecimales(v["default_code"], false);
        v["list_price"] = numero(v["list_price"]);
        v["standard_price"] = numero(v["standard_price"]);
        v["weight"] = numero(v["weight"]);
        v["is_published"] = verdadero.Contains(v["is_published"].ToLowerInvariant()) ? "True" : "False";
        // Solo los bienes llevan inventario; "Cantidad a la mano" se carga aparte (no se puede importar con el producto).
        v["is_storable"] = tipo == "consu" ? "True" : "False";
        if (!vistosProducto.Add(v["id"].ToLowerInvariant())) { productosDuplicados++; continue; }
        var nueva = dtProductos.NewRow();
        foreach (string campo in camposProducto) nueva[campo] = v[campo];
        dtProductos.Rows.Add(nueva);

        double unidades;
        if (tipo == "consu" && double.TryParse(cantidad, numeros, cultura, out unidades) && unidades > 0)
            // El producto se busca por su referencia interna o, si no tiene, por su nombre.
            dtExistencias.Rows.Add(v["default_code"] != "" ? v["default_code"] : v["name"], ubicacionExistencias,
                                   unidades.ToString(cultura));
    }

dtRechazos = rechazos;
int rechazosCliente = rechazos.Select("Tipo = 'Cliente'").Length;
int rechazosProducto = rechazos.Select("Tipo = 'Producto'").Length;
resumen = string.Format(
    "Clientes: {0} para cargar, {1} duplicados, {2} rechazados. Productos: {3} para cargar, {4} duplicados, {5} rechazados. Existencias: {6}.",
    dtClientes.Rows.Count, clientesDuplicados, rechazosCliente,
    dtProductos.Rows.Count, productosDuplicados, rechazosProducto, dtExistencias.Rows.Count);
