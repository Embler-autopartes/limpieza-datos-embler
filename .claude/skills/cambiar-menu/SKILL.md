---
name: cambiar-menu
description: |
  Modifica el Mega menu de Shopify de la tienda Embler (marca -> categoria -> subcategoria, ~300 items)
  usando Matrixify en dos pasos: primer pase importa con titles prefijados ("BMW - Motor - Poleas") para
  evitar errores de unicidad de Matrixify, segundo pase renombra a labels cortos ("Poleas") usando match
  por ID. Usa este skill siempre que el usuario quiera reconstruir el menu, agregar/quitar marcas,
  cambiar la cantidad de subcategorias visibles, modificar las collections enlazadas, ajustar la
  jerarquia del mega menu, o cualquier cambio masivo en el menu de navegacion. Se activa con frases como:
  "cambia el menu", "actualiza el mega menu", "regenera el menu", "agrega una marca al menu",
  "quita Sprinter del menu", "cambia el cap de subcategorias", "rehaz el menu en Shopify",
  "el menu de navegacion", "modificar el menu", "import el menu a Matrixify", "armar el menu nuevo",
  "agregar items al menu", "estructurar el menu", "ajustar el mega menu", o cualquier referencia a
  los archivos en `menu/`. Tambien cuando el usuario pegue un Export o Import_Result de Matrixify
  relacionado al menu.
---

# Cambiar Mega menu de Shopify

Este skill orquesta la modificacion del **Mega menu** de la tienda Embler en Shopify. El menu tiene
3 niveles (marca / categoria / subcategoria) y ~300 items totales — justo bajo el limite practico
de Shopify.

## Modelo mental: por qué dos pasos en vez de uno

Matrixify exige que `Menu Item: Title` sea **globalmente unico dentro del menu** para resolver
parent-matching de items nuevos (sin ID). Como nuestro menu tiene categorias con titles repetidos
entre marcas (12 marcas con "Accesorios", 13 con "Motor"), un solo pase con titles cortos
**falla con error de validacion** y rechaza el import entero.

Solucion confirmada por experimento (2026-05-13):

1. **Pase 1 — REPLACE con titles prefijados** (`BMW - Accesorios`, `Audi - Accesorios`, ...).
   Los titles son globalmente unicos, Matrixify acepta y asigna IDs.
2. **Pase 2 — MERGE con titles cortos referenciando por ID** (`Accesorios`, `Motor`, ...).
   Match por `Menu Item: ID`, no por Title. La unicidad ya no importa. Los labels quedan limpios.

Si intentas saltar el pase 1, Matrixify rechaza el archivo con:

```
REPLACE: Found by Handle | Multiple Menu Items found by value: [Accesorios].
```

## Archivos clave

| Archivo | Rol |
|---|---|
| `scripts/14_generar_mega_menu_matrixify.py` | Genera los archivos para el pase 1. |
| `scripts/15_generar_mega_menu_rename_corto.py` | Genera el archivo del pase 2 (rename). |
| `Procesamiento de Catálogo/outputs/collections-matrixify/source/Embler-Collections.xlsx` | Fuente: las 895 Smart Collections existentes. |
| `menu/PROCESO.md` | Documentacion completa del flujo + lessons learned. |
| `menu/Export_*.xlsx` | Exports de Matrixify (backups o para extraer IDs post-import). |

## Configuracion del menu

Edita estas constantes en `scripts/14_generar_mega_menu_matrixify.py`:

- `MENU_TITLE`, `MENU_HANDLE` — identidad del menu en Shopify.
- `SUB_PER_GROUP` — cap de subcategorias por categoria (default 3, orden alfabetico).
- `BRAND_LABELS` — lista `[(display_label, brand_metafield_value, brand_handle), ...]`.
  - Agrega o comenta entradas para agregar/quitar marcas.
  - El `display_label` es lo que ve el cliente; el `brand_metafield_value` es el valor exacto del
    metafield `global._brand` de las collections (debe matchear case-sensitive).

## Workflow completo

### 0. Entender el cambio

Pregunta al usuario que cambio quiere hacer:

- ¿Agregar/quitar marcas? → editar `BRAND_LABELS`.
- ¿Cambiar el cap de subcategorias? → editar `SUB_PER_GROUP`.
- ¿Cambiar criterio de seleccion (alfabetico vs popularidad)? → modificar la regla de sort en `build_hierarchy()`.
- ¿Agregar/quitar categorias o subcategorias especificas? → ese cambio se hace en las Smart Collections (no en el menu); el menu hereda automaticamente al regenerar.
- ¿Solo renombrar items existentes? → puede saltarse el pase 1 y usar solo el rename con match por ID. Requiere que ya existan los items en Shopify.

### 1. Backup del menu actual

Matrixify → Export → Menus → guarda `Export_<timestamp>.xlsx` en `menu/`.

Este es tu rollback. Avisa al usuario explicitamente que debe descargar este archivo antes de proceder.

### 2. Generar archivos del pase 1

```bash
python3 scripts/14_generar_mega_menu_matrixify.py
```

Produce en `menu/`:

- `Embler-Mega-Menu.xlsx` — version "corta" (NO USAR como primer pase, falla).
- `Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx` — **este es el del pase 1**.
- `MEGA-MENU-PROPUESTA.md` — preview de la estructura.
- `README.md` — guia rapida.

Pide al usuario revisar `MEGA-MENU-PROPUESTA.md` antes de importar.

### 3. Pase 1 — Import a Matrixify

Indica al usuario:

> "Matrixify → Import → sube `menu/Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx`."

Resultado esperado: `OK: 299, Failed: 0` (numero exacto depende del cap y marcas).

**Importante:** REPLACE cambia el ID del menu (Shopify lo borra y recrea). El handle `mega-menu`
se mantiene, asi que el theme no se ve afectado si referencia por handle. Si referencia por ID,
el usuario debe actualizarlo.

Si el import falla:
- Revisa el Import_Result que descarga Matrixify.
- Causa mas comun: duplicados de Title (significa que las collections fuente tienen problemas — no
  todas las marcas tienen sus collections brand-group creadas). Verifica con `ESTRUCTURA-MENU.md`.

### 4. Pase 2 — Export para capturar IDs

Despues del pase 1, en Matrixify → Export → Menus → guarda otro `Export_*.xlsx` en `menu/`.

Este export contiene las columnas `Menu Item: ID` y `Menu Item: Parent ID` que necesita el rename.

### 5. Generar el archivo de rename

```bash
python3 scripts/15_generar_mega_menu_rename_corto.py
# o explicitamente:
python3 scripts/15_generar_mega_menu_rename_corto.py menu/Export_<timestamp>.xlsx
```

Sin argumento, toma el `Export_*.xlsx` mas reciente en `menu/`.

Produce:

- `menu/Embler-Mega-Menu-RENAME-corto.xlsx` — archivo del pase 2.
- `menu/RENAME-PREVIEW.md` — tabla antes/despues para validar.

### 6. Pase 2 — Import del rename

Pide al usuario revisar `RENAME-PREVIEW.md`, luego:

> "Matrixify → Import → sube `menu/Embler-Mega-Menu-RENAME-corto.xlsx`."

Resultado esperado: `OK: <total_no_marca>, Failed: 0` (las marcas no se renombran).

El menu en el admin ahora muestra labels cortos manteniendo la jerarquia y los links.

## Casos especiales

### El usuario quiere agregar UNA sola marca

Editar `BRAND_LABELS` para agregar la marca, regenerar y hacer los dos pases completos. No hay
forma mas elegante porque REPLACE borra todo y recrea — el incremento de una marca implica regenerar
el menu completo.

Alternativa: hacer el cambio manualmente en el admin de Shopify (una sola marca son ~25 clicks,
manejable).

### El usuario solo quiere renombrar algunos items

Si ya existen en Shopify y solo quieres cambiar Titles, NO necesitas el pase 1. Genera manualmente
un archivo con columnas `Handle, Command=MERGE, Title, Menu Item: ID, Menu Item: Command=MERGE,
Menu Item: Title` con las filas a renombrar. Sube ese archivo. Mucho mas seguro que regenerar.

### El usuario quiere cambiar links (target de collection)

Mismo patron que rename: archivo con `Menu Item: ID` + nuevas columnas
`Menu Item: Resource Type, Menu Item: Resource Handle`. Command=MERGE.

### El usuario quiere borrar items especificos

Archivo con `Menu Item: ID` + `Menu Item: Command=DELETE`. Command del menu = MERGE
(no REPLACE — REPLACE borraria todo).

### Algo salio mal y hay que revertir

Importa el `Export_<backup>.xlsx` previo con `Command=REPLACE` en cada fila. El menu vuelve al
estado anterior. La unica perdida son los IDs internos (cambiaran de nuevo).

## Tools requeridos

- **Python 3** con `openpyxl`.
- **Matrixify** instalado en la tienda Shopify (NO se puede hacer via el MCP de Shopify — no expone
  tools de menus).
- Acceso al admin de Shopify para descargar/subir archivos a Matrixify.

## Verificacion final

Despues del pase 2, abre el menu en el admin (`/admin/content/menus/<menu_id>`) y verifica:

1. **Cuenta de marcas** coincide con `BRAND_LABELS`.
2. **Algunas categorias al azar** linkean a la collection correcta (click en el item, ver el Link target).
3. **Algunas subcategorias** estan donde deben (Audi Motor tiene subcategorias de Audi, no de BMW).
4. **No hay duplicados de items** ni items huerfanos sin parent.
5. **El storefront refleja el cambio** (carga la tienda y abre el mega menu).

Si todo OK, archiva los archivos generados en `menu/` para auditoria. Si necesitas hacer rollback,
el backup esta disponible.

## Referencias

- `menu/PROCESO.md` — documento completo del proceso con cronologia real, lessons learned, y
  variantes operativas.
- `menu/ESTRUCTURA-MENU.md` — catalogo completo de las 895 Smart Collections (referencia, no se
  usa directamente en el menu).
- Skill relacionado: [[mover-producto-collection]] para ajustar metafields de productos individuales
  (no afecta el menu pero si la membresia de productos en collections).
