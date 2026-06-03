# Limpieza de Datos Embler - Instrucciones para Claude

## Estado actual del proyecto (junio 2026)

El catálogo de **12,744 productos** ya fue importado a Shopify (mayo 2026). El trabajo
actual es mantenimiento, correcciones de datos y nuevas importaciones de actualizaciones.

## Estructura de Carpetas

```
Procesamiento de Catálogo/
  input/             -> CRUCE_ML_MC.xlsx (fuente original, abril 2026)
  scripts/           -> Todos los scripts Python del pipeline
  outputs/           -> ÚNICA carpeta de outputs activos
    2026-05-09-USAR-shopify-import/   -> 12 CSVs YA_*.csv — el import real a Shopify
    2026-06-02-shopify-remapeado/     -> catalogo_completo.csv + partes — VERSIÓN ACTIVA
      generar_catalogo.py             -> script que genera los CSVs desde los YA_*
      catalogo_completo.csv           -> 12,744 productos, 51,593 filas, 37 cols, 22 MB
      catalogo_parte1.csv             -> 6,374 productos (para importar en 2 tandas)
      catalogo_parte2.csv             -> 6,375 productos
    collections-matrixify/            -> Colecciones del mega menú (tipo distinto)
    README.md
    _arbol_marca_grupo_subgrupo.json
```

### Regla obligatoria para outputs

Todo CSV final va en `outputs/YYYY-MM-DD-descripcion-corta/`.
Prefijo `USAR-` marca la versión activa de importación.

**NO hay `output/`, `new-output/` ni `new-output_v2/`** — fueron limpiados en junio 2026
por ser pasos intermedios ya superados.

## Schema del CSV de Shopify (37 columnas)

El archivo activo (`catalogo_completo.csv`) usa exactamente este orden de columnas,
alineado al export real de Shopify:

```
Handle, Title, Body (HTML), Vendor, Published,
Option1 Name, Option1 Value,
Variant SKU, Variant Grams, Variant Inventory Tracker, Variant Inventory Qty,
Variant Inventory Policy, Variant Fulfillment Service, Variant Price,
Variant Requires Shipping, Variant Taxable,
Image Src, Image Position, Image Alt Text, Gift Card,
SEO Title, SEO Description,
Filtros - Refacción (product.metafields.filters.detail_1),
Filtros - Año (product.metafields.filters.detail_2),
Filtros - Marca de la refacción (product.metafields.filters.detail_3),
Marca del auto (product.metafields.global.brand),
Grupo (product.metafields.global.group),
Información de envio (product.metafields.global.shipping),
Sub grupo (product.metafields.global.sub_group),
Marca (product.metafields.global._brand),
Listado - Número de parte (product.metafields.list.detail_1),
Descripción larga (product.metafields.page.descripcion_larga),
Características - Marca (product.metafields.page_info.detail_1),
Características - Tipo de vehículo (product.metafields.page_info.detail_2),
Características - Origen (product.metafields.page_info.detail_3),
Variant Weight Unit, Status
```

### Valores fijos en todos los productos

| Campo | Valor |
|-------|-------|
| Vendor | `Embler Autopartes` |
| Published | `true` |
| Option1 Name | `Title` |
| Option1 Value | `Default Title` |
| Variant Grams | `0` |
| Variant Inventory Tracker | `shopify` |
| Variant Inventory Qty | `1` |
| Variant Inventory Policy | `deny` |
| Variant Fulfillment Service | `manual` |
| Variant Requires Shipping | `true` |
| Variant Taxable | `true` |
| Gift Card | `false` |
| Información de envio | `entregamos-hoy` |
| Variant Weight Unit | `kg` |
| Status | `draft` (el humano activa después de revisar) |

### Mapeo de `Filtros - Refacción` por categoría

Este campo es el filtro de nivel superior en la tienda, NO el Grupo:

| Archivo fuente | Valor correcto |
|----------------|----------------|
| `refacciones_*` | `Refacciones` |
| `accesorios` | `Accesorios` |
| `tuning` | `Tuning` |
| `herramientas` | `Herramientas` |
| `otros` | `Otros` |

### Formato de filas (multi-row por producto)

Shopify usa múltiples filas por producto para las imágenes extra:
- **Fila principal**: todos los campos poblados + primera imagen
- **Filas de continuación**: solo `Handle` + `Image Src` + `Image Position`, todo lo demás vacío

## Script de generación: `generar_catalogo.py`

Consolida los 12 archivos `YA_*.csv` de `2026-05-09-USAR-shopify-import/` en un solo
`catalogo_completo.csv`. Para regenerar después de cambios en los YA_*:

```bash
cd "Procesamiento de Catálogo/outputs/2026-06-02-shopify-remapeado"
python3 generar_catalogo.py
```

Luego dividir en 2 partes si se necesita (Shopify tiene límite de tamaño):

```python
# El script de split está inline en el historial — lógica: agrupar por producto completo
# para que filas de imagen no queden partidas entre partes
```

## Datos con gaps conocidos (junio 2026)

Campos que tienen valores faltantes en algunos productos — **no inventar, dejar vacíos**:

| Campo | Productos vacíos | Razón |
|-------|-----------------|-------|
| `Filtros - Año` | ~985 | No había datos de año en compatibilidades fuente |
| `Marca del auto` + `Marca` | ~763 | Marca del vehículo no determinada (mayormente suspensión de aire) |
| `Características - Tipo de vehículo` | ~614 | No estaba en datos fuente |
| `Listado - Número de parte` | ~230 | Sin código OEM disponible |
| `Características - Marca` | ~115 | Marca del producto no determinada |

## Estado de la importación a Shopify (junio 2026)

- **11,929 productos existentes** se actualizan con el import actual
- **815 productos nuevos** se crearán al importar `catalogo_completo.csv`
- **1 producto en Shopify sin match**: kit de afinación creado manualmente, no tocarlo
  - Handle: `kit-afinacion-bmw-serie-3-e90-n52-325i-2007-al-2012-5w40-7-l-rjo8ml-...`

## Archivo fuente original

**`input/CRUCE_ML_MC.xlsx`** — 4 hojas, solo se procesaron las 2 primeras:
- `ML_con_match` (13,961 filas): productos con match único en Microsip — **fuente principal**
- `ML_sin_match` (848 filas): productos sin match ERP

Las hojas `ML_ambiguos_revisar` y `MC_sin_match` están fuera de alcance.

## Normalizacion de Marcas de producto

```
"ORIGINAL FREY GERMAN TECHNOLOGY QUALITY"  -> "Original Frey"
"ORIGINAL FREY GERMAN TECHNOLOGY GERMAN Q"  -> "Original Frey"
"ORIGINAL FREY GERMAN TECNHLOGY QUALITY"    -> "Original Frey"
"ORIGINAL FREY GERMAN TECHNOLOGY"           -> "Original Frey"
"EMBLER AUTOPARTES EUROPEAS"                -> "Embler"
"EMBLER"                                    -> "Embler"
```

## Notas importantes

- **Idioma**: Todo el contenido en español
- **Nicho**: Autopartes europeas — BMW, Mercedes-Benz, Audi, VW, Porsche, Mini, etc.
- **Tono**: Técnico-comercial. El cliente es mecánico o conocedor de autos europeos.
- **No inventar datos técnicos**: Mejor vacío que incorrecto en compatibilidad/OEM.
- **Marca del vehículo ≠ marca del producto**: BMW es la marca del vehículo;
  Original Frey / Embler es la marca de la refacción.
- **Handle = identificador único**: Shopify actualiza si el handle coincide, crea si no.
  Nunca cambiar handles de productos ya publicados.
