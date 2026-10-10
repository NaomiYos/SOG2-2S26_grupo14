// Inject Js Script · pantalla "Importar" de Odoo, después de presionar "Probar".
// Si una etiqueta, un país o un departamento del archivo no existe en Odoo, la columna muestra la lista
// "Cuando un valor no puede coincidir:". Las etiquetas se crean ("Crear nuevos valores") y lo demás se deja
// vacío ("Establecer valor como vacío"), para no detener la carga por un dato opcional.
// Devuelve cuántas listas ajustó: si es más de 0 hay que presionar "Probar" otra vez.
function (element, input) {
    var listas = document.querySelectorAll("select.o_import_create_option");
    listas.forEach(function (lista) {
        var opciones = Array.prototype.map.call(lista.options, function (o) { return o.value; });
        if (lista.getAttribute("type") === "many2many" && opciones.indexOf("name_create_enabled_fields") >= 0) {
            lista.value = "name_create_enabled_fields";
        } else if (opciones.indexOf("import_set_empty_fields") >= 0) {
            lista.value = "import_set_empty_fields";
        }
        lista.dispatchEvent(new Event("change", { bubbles: true }));
    });
    return String(listas.length);
}
