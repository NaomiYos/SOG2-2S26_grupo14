# RPA · Carga de clientes y productos con UiPath

El robot recorre una carpeta con subcarpetas y archivos de Excel de nombres poco prácticos, toma **solo** las hojas
llamadas exactamente `clientes` y `productos`, consolida su contenido y lo carga en Odoo. El resultado se ve en el
sitio (Contactos, Productos y la tienda) y por SQL (sección 9 de `PROYECTO/sql/consultas_calificacion.sql`).
En la calificación se ejecuta en vivo con una carpeta que entrega el auxiliar.

## Reglas del auxiliar (foros *RPA*, *Datos RPA* y *dudas proyecto*)

| Regla | Cómo la cumple el robot |
|---|---|
| **No usar ninguna API de Odoo desde UiPath** | Carga con la pantalla **Importar registros** de Odoo, manejando Chrome como una persona |
| Las hojas se llaman exactamente `clientes` y `productos` | Compara el nombre de la hoja de forma exacta; ignora la carpeta y el nombre del archivo |
| Encabezados iguales a los archivos de ejemplo (`ejemplos/`): `External ID`, no `ID Externo` | Acepta los del ejemplo (con o sin `*`) y algunos alias en español |
| Obligatorias: `External ID`, `Name`, `Product Type` / `Name`, `Company Type` | Las filas sin ellas no se cargan y quedan en `rechazos.xlsx` con archivo, hoja, fila y motivo |
| `Related Company` y `Product Values` siempre vienen vacías | Se ignoran |

## Cómo funciona

```
Carpeta raíz (la del auxiliar)
  1. Listar todos los .xls/.xlsx de la carpeta y sus subcarpetas (sin los temporales "~$")
  2. Abrir cada libro y revisar el nombre de sus hojas
  3. Leer las hojas "clientes" y "productos" (valores sin formato) y marcar su origen  ── codigo/AgregarOrigen.cs
  4. Unir todas las hojas de cada tipo (Merge Data Table)
  5. Consolidar: validar, normalizar y quitar duplicados  ── codigo/Consolidar.cs
  6. Escribir salida/clientes.xlsx, productos.xlsx, existencias.xlsx y rechazos.xlsx
  7. Chrome: iniciar sesión en Odoo como "Robot RPA"
  8. Contactos > Importar registros > clientes.xlsx
  9. Inventario > Productos > Importar registros > productos.xlsx
 10. Inventario > Inventario físico > Importar registros > existencias.xlsx > Aplicar todo
```

Qué hace la consolidación (`codigo/Consolidar.cs`):

| Dato del Excel | Se convierte en | Por qué |
|---|---|---|
| Encabezados (`Name*`, `Sales Price`...) | Nombre técnico del campo (`name`, `list_price`...) | Odoo reconoce el nombre técnico en cualquier idioma, sin asignar columnas a mano |
| `Company Type`: Company / Person | `company` / `person` | Valores internos de Odoo |
| `Product Type`: Goods / Service / Combo | `consu` / `service` / `combo` | Ídem; los bienes se marcan con *Rastrear inventario* |
| Código postal y de barras guardados como número (`54398267125.00001`) | Texto sin decimales (`54398267125`) | Excel los guarda como número |
| `Está publicado`: True / False / vacío | `True` / `False` | Vacío = no publicado |
| `Cantidad a la mano` | Archivo aparte `existencias.xlsx` (solo bienes con cantidad) | Odoo no permite importarla junto con el producto; se carga como ajuste de inventario en `GT/Existencias` |
| Clientes repetidos (mismo nombre y correo) o productos con el mismo `External ID` | Una sola fila | Varios archivos traen los mismos registros |
| `External ID` | Identificador del producto en Odoo (`__import__.<External ID>`) | Si se vuelve a ejecutar, actualiza en lugar de duplicar |

## Preparación (una sola vez)

1. **Odoo**: ejecutar `PROYECTO/datos/14_configurar_rpa.py`. Crea el usuario **Robot RPA**
   (`robot.rpa@quetzalmart.com`) e imprime su contraseña una sola vez, y guarda la asignación de la columna `website`
   (Odoo la propone para el campo equivocado).
2. **Contraseña en Windows**: Panel de control > Administrador de credenciales > Credenciales de Windows >
   *Agregar una credencial genérica*: dirección `QuetzalMartRobotRPA`, usuario `robot.rpa@quetzalmart.com` y la contraseña
   (o en una terminal: `cmdkey /generic:QuetzalMartRobotRPA /user:robot.rpa@quetzalmart.com /pass:<contraseña>`).
   El robot la lee de ahí; nunca va en el proyecto.
3. **UiPath Studio Community** (gratis): crear cuenta en https://www.uipath.com/community > *Try UiPath free*; en el
   portal (Automation Cloud) > *Download Studio*. Instalar, iniciar sesión y elegir el perfil **UiPath Studio**.
   Instalar la extensión de Chrome: Studio > Home > Tools > UI Automation > *Chrome*.
   En `chrome://extensions` > *UiPath Browser Automation* > *Detalles*, activar **Permitir el acceso a las URL de
   archivo**: sin eso *Browser File Picker Scope* no puede subir el Excel a Odoo.
   En Chrome > Configuración > Contraseñas, desactivar *Ofrecer guardar contraseñas* (el aviso tapa la pantalla).
4. **Excel** instalado (lo usa *Use Excel File* para abrir los `.xls`).

## Construcción en UiPath Studio, paso a paso

Proyecto nuevo: *Process*, nombre `QuetzalMartRPA`, ubicación `PROYECTO/rpa/`, compatibilidad **Windows**, lenguaje **C#**.
Paquetes (Manage Packages): `UiPath.Excel.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.System.Activities`
(vienen por defecto) y `UiPath.Credentials.Activities`.

Tomar una captura de cada paso para la sección 4 del Manual 1 (lista al final).

### Variables de `Main.xaml`

| Variable | Tipo | Valor inicial |
|---|---|---|
| `urlOdoo` | String | `"https://<ip-con-guiones>.sslip.io"` |
| `ubicacionExistencias` | String | `"GT/Existencias"` |
| `carpetaRaiz` | String | |
| `carpetaSalida` | String | `System.IO.Path.GetFullPath("salida")` |
| `archivos` | String[] | |
| `dtHoja`, `dtClientesCrudo`, `dtProductosCrudo` | DataTable | `null` |
| `dtClientes`, `dtProductos`, `dtExistencias`, `dtRechazos` | DataTable | |
| `resumen` | String | |
| `usuarioOdoo` | String | |
| `claveOdoo` | SecureString | |

### Parte 1: leer y consolidar

1. **Select Folder** → salida `carpetaRaiz` (el auxiliar elige la carpeta al ejecutar).
2. **Get Secure Credential**: Target `"QuetzalMartRobotRPA"`, tipo *Generic* → `usuarioOdoo`, `claveOdoo`.
3. **Assign** `archivos` =
   `System.IO.Directory.GetFiles(carpetaRaiz, "*.xls*", System.IO.SearchOption.AllDirectories).Where(f => !System.IO.Path.GetFileName(f).StartsWith("~$")).ToArray()`
4. **Log Message**: `"Archivos de Excel encontrados: " + archivos.Length`.
5. **For Each** `archivo` in `archivos` (TypeArgument String), dentro un **Try Catch**:
   - **Use Excel File**: ruta `archivo`, *Read only* activado, *Save changes* desactivado. Nombre de referencia `Excel`.
     - **For Each Excel Sheet** (`CurrentSheet`) en `Excel`:
       - **If** `CurrentSheet.Name == "clientes" || CurrentSheet.Name == "productos"`:
         1. **Read Range**: rango `CurrentSheet`, *Has headers* activado, leer **valores sin formato**
            (propiedad *Read formatting* = *Raw value*, si la versión la tiene) → `dtHoja`.
         2. **Invoke Code** (C#) con el contenido de `codigo/AgregarOrigen.cs`. Argumentos: `dtHoja` (In/Out, DataTable),
            `archivo` (In, String), `hoja` (In, String) = `CurrentSheet.Name`.
         3. **If** `CurrentSheet.Name == "clientes"`:
            - **If** `dtClientesCrudo == null` → **Assign** `dtClientesCrudo = dtHoja`;
              si no → **Merge Data Table**: origen `dtHoja`, destino `dtClientesCrudo`, *MissingSchemaAction* = `Add`.
            - En el *Else*, lo mismo con `dtProductosCrudo`.
         4. **Log Message**: `"Hoja " + CurrentSheet.Name + " leída de " + archivo + " (" + dtHoja.Rows.Count + " filas)"`.
   - **Catch** `System.Exception`: **Log Message** nivel *Warn*: `"No se pudo leer " + archivo + ": " + exception.Message`.
6. **Invoke Code** (C#) con el contenido de `codigo/Consolidar.cs`. Argumentos: `dtClientesCrudo`, `dtProductosCrudo`
   (In, DataTable), `ubicacionExistencias` (In, String), `dtClientes`, `dtProductos`, `dtExistencias`, `dtRechazos`
   (Out, DataTable) y `resumen` (Out, String).
7. **Log Message** `resumen`.
8. **Create Folder** `carpetaSalida`. Para cada tabla, **Write Range Workbook** (categoría *Workbook*, no necesita Excel)
   con *Add headers* activado: `carpetaSalida + "\clientes.xlsx"` hoja `clientes`, y lo mismo con `productos`,
   `existencias` y `rechazos`. Antes, **Delete File** de cada uno para no mezclar con una ejecución anterior.

### Parte 2: cargar en Odoo con la pantalla Importar

9. **Use Application/Browser**: Chrome, URL `urlOdoo + "/web/login"`.
   - **Check App State** ¿aparece el campo *Correo electrónico*? Si aparece: **Type Into** `usuarioOdoo`,
     **Type Secure Text** `claveOdoo`, **Click** *Iniciar sesión*.
10. Crear el flujo **`ImportarArchivo.xaml`** (argumentos `in_url` y `in_archivo`, String) e invocarlo 3 veces con
    **Invoke Workflow File**:

    | Paso | `in_url` | `in_archivo` |
    |---|---|---|
    | Clientes | `urlOdoo + "/odoo/contacts?view_type=list"` | `carpetaSalida + "\clientes.xlsx"` |
    | Productos | `urlOdoo + "/odoo/action-stock.product_template_action_product?view_type=list"` | `carpetaSalida + "\productos.xlsx"` |
    | Existencias | `urlOdoo + "/odoo/physical-inventory"` | `carpetaSalida + "\existencias.xlsx"` |

    Si una tabla viene vacía (`dtX.Rows.Count == 0`), saltar su importación con un **If**.

    Contenido de `ImportarArchivo.xaml` (todo dentro de **Use Application/Browser** con la misma ventana de Chrome):
    1. **Go To URL** `in_url`.
    2. **Click** en el engrane (⚙ *Acciones*) junto al título de la lista → **Click** *Importar registros*.
    3. **Click** *Subir archivo de datos* → en la ventana de Windows, **Type Into** el campo *Nombre* con `in_archivo`
       y la tecla Enter.
    4. **Click** *Probar*.
    5. **Inject Js Script** (si una etiqueta, un país o un departamento no existe, Odoo muestra una lista
       "Cuando un valor no puede coincidir:" en esa columna; este script elige *Crear nuevos valores* para las
       etiquetas y *Establecer valor como vacío* para lo demás):

       ```js
       function(e) {
         var listas = document.querySelectorAll("select.o_import_create_option");
         listas.forEach(function (s) {
           var opciones = Array.prototype.map.call(s.options, function (o) { return o.value; });
           if (s.getAttribute("type") === "many2many" && opciones.indexOf("name_create_enabled_fields") >= 0) s.value = "name_create_enabled_fields";
           else if (opciones.indexOf("import_set_empty_fields") >= 0) s.value = "import_set_empty_fields";
           s.dispatchEvent(new Event("change", { bubbles: true }));
         });
         return String(listas.length);
       }
       ```
    6. Si el script devolvió más de 0 → **Click** *Probar* otra vez.
    7. **Check App State**: ¿aparece *Todo parece correcto.*? Si no, **Take Screenshot**, **Log Message** con el
       error que muestra Odoo y **Throw** (el error queda en el registro).
    8. **Click** *Importar* y esperar a que vuelva la lista (**Check App State** sobre la lista).
11. En *Inventario físico*, después de importar: **Click** *Aplicar todo* y, en la ventana que aparece, **Click** *Aplicar*.
12. **Message Box** con `resumen` (y la ruta de `rechazos.xlsx` si tiene filas).

Al indicar cada elemento en pantalla, preferir selectores por texto (*Importar registros*, *Probar*, *Importar*)
o por clase (`o_import_file`, `o_import_create_option`) y quitar los atributos que cambian (ids numéricos).

## Probar sin Odoo

```bash
pip install openpyxl xlwt xlrd
python generador/generar_carpetas.py               # crea carpeta_prueba/ con trampas
python codigo/probar_consolidacion.py carpeta_prueba
```

`probar_consolidacion.py` emula la parte 1 y ejecuta el mismo C# que el robot (compilado con el .NET de Windows).
Con `carpeta_prueba` debe dar **10 clientes, 8 productos, 5 existencias y 2 + 2 rechazados**; con `ejemplos/`
(archivos del foro), 4 clientes, 7 productos y 5 existencias. Si el auxiliar entrega la carpeta antes de ejecutar el
robot, este comando dice qué se va a cargar.

**Ensayos contra Odoo**: lo que carga el robot es real. Los datos de `carpeta_prueba` usan referencias `RPA-...`
y External ID `RPA_PRUEBA_...` para poder encontrarlos y archivarlos después del ensayo.

## Día de la calificación

1. Copiar la carpeta del auxiliar a la PC y abrir el proyecto en UiPath Studio.
2. (Opcional) `python codigo/probar_consolidacion.py "<carpeta del auxiliar>"` para anticipar los conteos.
3. Ejecutar `Main.xaml` y elegir la carpeta.
4. Mostrar en Odoo: Contactos (filtrar por *Creado por: Robot RPA*), Productos, la tienda `/shop` (los publicados) y el
   inventario.
5. Mostrar en SQL la sección 9 de `consultas_calificacion.sql`.

## Capturas para el Manual 1, sección 4 (`PROYECTO/evidencias/rpa/`)

| # | Captura |
|---|---|
| 01 | Carpeta del auxiliar o `carpeta_prueba` abierta en el Explorador (nombres poco prácticos) |
| 02 | Proyecto en Studio: paquetes instalados |
| 03 | Variables de `Main.xaml` |
| 04 | Select Folder, Get Secure Credential y el Assign de `archivos` |
| 05 | For Each con Use Excel File, For Each Excel Sheet y el If del nombre de la hoja |
| 06 | Invoke Code de `AgregarOrigen` y el Merge Data Table |
| 07 | Invoke Code de `Consolidar` con sus argumentos |
| 08 | Write Range de los 4 archivos |
| 09 | Inicio de sesión en Odoo |
| 10 | `ImportarArchivo.xaml` completo |
| 11 | Ejecución: panel *Output* con los mensajes del robot |
| 12 | `salida/` con los 4 archivos y `rechazos.xlsx` abierto |
| 13 | Odoo: pantalla de importación con *Todo parece correcto.* |
| 14 | Odoo: clientes cargados (filtro *Creado por: Robot RPA*) |
| 15 | Odoo: productos cargados y uno publicado en la tienda |
| 16 | Odoo: inventario con la cantidad a la mano |
| 17 | Consulta SQL de la sección 9 |
