// Invoke Code (C#) · se ejecuta después de leer cada hoja "clientes" o "productos".
// Agrega a cada fila de dónde salió, para el registro de rechazos.
// Argumentos:
//   dtHoja   DataTable  In/Out   tabla que devolvió Read Range
//   archivo  String     In       ruta del libro de Excel
//   hoja     String     In       nombre de la hoja
dtHoja.Columns.Add("__archivo", typeof(string));
dtHoja.Columns.Add("__hoja", typeof(string));
dtHoja.Columns.Add("__fila", typeof(string));
for (int i = 0; i < dtHoja.Rows.Count; i++)
{
    dtHoja.Rows[i]["__archivo"] = System.IO.Path.GetFileName(archivo);
    dtHoja.Rows[i]["__hoja"] = hoja;
    dtHoja.Rows[i]["__fila"] = (i + 2).ToString();  // la fila 1 es el encabezado
}
