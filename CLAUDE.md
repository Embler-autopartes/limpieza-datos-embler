# Limpieza de Datos Embler - Instrucciones para Claude

## Contexto del Proyecto

Este proyecto procesa un catalogo de autopartes europeas (BMW, Mercedes-Benz, Audi, VW, etc.) para generar contenido de ecommerce. El input vigente (`CRUCE_ML_MC.xlsx`, abril 2026) cruza productos de MercadoLibre con Microsip (ERP) y los reparte en 4 hojas segun el resultado del match.

## Estructura de Carpetas

```
input/             -> Archivo fuente (CRUCE_ML_MC.xlsx)
new-output/        -> Salida vigente. Subcarpeta por hoja (alcance acotado a 2 hojas).
  ml_con_match/         -> 13,960 productos ML con match unico en Microsip (PRINCIPAL)
  ml_sin_match/         -> 847 productos ML publicados sin match en Microsip
output/            -> Salida del input anterior (INPUT.xlsx). Conservada como historico.
scripts/           -> Scripts de Python para extraccion y procesamiento
ANALISIS.md        -> Documentacion del analisis de datos
```

Nota: las hojas `ML_ambiguos_revisar` (7,251 filas) y `MC_sin_match` (3,812 filas) del Excel
existen pero no se procesan en este flujo. El script `01_extraer_categorias_v2.py` solo
genera CSVs para `ml_con_match` y `ml_sin_match`.

## Archivo Input

**`input/CRUCE_ML_MC.xlsx`** - 4 hojas, schema nuevo de 34 columnas (las hojas ML_*).

### Hojas (solo se procesan las 2 primeras)
- **`ML_con_match`** (13,961 filas): productos ML con match unico Microsip - fuente principal de procesamiento.
- **`ML_sin_match`** (848 filas): productos ML sin match Microsip - se enriquecen pero quedan sin SKU ERP.
- ~~`ML_ambiguos_revisar`~~ (7,252 filas) - fuera de alcance.
- ~~`MC_sin_match`~~ (3,813 filas) - fuera de alcance.

### Columnas clave (hojas ML_*) — indices nuevos
- `Categoria` (col 2): Categoria jerarquica de ML
- `Titulo` (col 3): Titulo de ML, punto de partida para nombre comercial
- `Descripcion` (col 4): Descripcion existente (incluye bloque "APLICA PARA LOS SIGUIENTES MODELOS:")
- `Precio` (col 5)
- `SKU` (col 6)
- `Garantia` (col 10)
- `Compatibilidades` (col 13): catalogo completo de vehiculos compatibles
- `Compatibilidades Restricciones` (col 14)
- `Atributo Marca` (col 15)
- `Atributo Numero de parte` (col 16)
- `Atributo Tipo de vehiculo` (col 18)
- `Atributo Origen` (col 19)
- `Atributo Codigo OEM` (col 20)
- `Atributo Modelo` (col 21)
- `Atributo Lado` (col 22)
- `MC_SKU_match` / `MC_ARTICULO_ID_match` / `MC_NOMBRE_match` / `MC_ESTATUS_match` (cols 24-27): datos del match Microsip
- `TIENE_MATCH` (col 32) / `AMBIGUO` (col 33): flags de matching

### Columnas agregadas por el script de extraccion
- `marca_normalizada` (col 34): Marca del producto normalizada (Original Frey, Embler, etc.)
- `subcategoria_limpia` (col 35): Tercer nivel del path de categoria ML
- `categoria_archivo` (col 36): Bucket usado para nombrar el CSV (refacciones_motor, etc.)

## Estrategia de Procesamiento

### Procesamiento por Chunks

Los datos se procesan en chunks para evitar exceder limites de contexto y mantener calidad:

1. **Extraer por categoria** usando Python -> CSVs por categoria en `output/`
2. **Procesar cada CSV** con Claude para generar columnas nuevas
3. **Consolidar** outputs en archivos finales

### Categorias para chunking:
- `refacciones_autos` (~12,914 filas) - subdividir por subcategoria
- `accesorios` (~80 filas)
- `tuning` (~83 filas)
- `motos` (~58 filas)
- `linea_pesada` (~56 filas)
- `otros` (~172 filas)

Para refacciones_autos (muy grande), subdividir por subcategoria extraida del path de Categoria_ML:
- Motor, Suspension, Frenos, Transmision, Electrico, Carroceria, etc.

## Columnas de Output a Generar

Para cada producto, generar estas columnas nuevas organizadas en dos grupos:

### Caracteristicas (columnas individuales)

- `caract_marca` — Marca normalizada del producto (Original Frey, Embler, Mahle, etc.)
- `caract_origen` — Origen del producto (Importado, Nacional). Vacio si no hay dato.
- `caract_tipo_vehiculo` — Tipo de vehiculo (Carro/Camioneta, Moto, Linea Pesada)
- `caract_compatibilidad` — Texto en parrafo con vehiculos compatibles, legible para el cliente

### Secciones de contenido

- `seccion_descripcion` — Descripcion comercial (100-250 palabras, tono tecnico-comercial)
- `seccion_antes_de_comprar` — Texto fijo: pedir VIN, verificar numero de parte/OEM
- `seccion_envio` — Texto fijo: stock disponible, envio mismo dia, DHL/FedEx
- `seccion_devoluciones` — Texto fijo: politica de devoluciones (30 dias, sin uso, validacion VIN)
- `seccion_faq` — 3-5 preguntas frecuentes en JSON array
- `productos_relacionados` — Hasta 5 SKUs relacionados del mismo catalogo

### Columnas Shopify (para importacion CSV)

- `shopify_handle` — URL slug unico (minusculas, guiones, sin acentos)
- `shopify_title` — Titulo limpio del producto
- `shopify_body_html` — Descripcion completa en HTML (combina todas las secciones)
- `shopify_product_category` — Siempre "Vehicles & Parts > Vehicle Parts & Accessories"
- `shopify_type` — Tipo para collections (Motor, Frenos, Suspensión, Sistema Eléctrico, Carrocería, Filtros, etc.)
- `shopify_tags` — Marcas de VEHICULO compatibles (BMW, Audi, Mercedes-Benz, etc.)
- `shopify_published` — TRUE
- `shopify_option1_name` / `shopify_option1_value` — "Title" / "Default Title" (sin variantes)
- `shopify_variant_sku` — Directo de SKU_ML
- `shopify_variant_price` — Directo de Precio_ML
- `shopify_variant_compare_price` — Vacio (sin dato)
- `shopify_variant_weight` / `shopify_variant_weight_unit` — Vacio / "kg"
- `shopify_image_src` — Vacio (sin imagenes)
- `shopify_image_alt_text` — Texto alt generado
- `shopify_seo_title` — Titulo SEO (max 60 chars, con "| Embler")
- `shopify_seo_description` — Meta description (max 155 chars)
- `shopify_status` — "draft" (el humano activa despues de revisar)

### Revision humana

- `revision_humana` — Lista de acciones pendientes para el humano ([BUSCAR], [VERIFICAR], [INCLUIR], [REVISAR], [ANALIZAR]). Vacio si todo esta completo.

## Reglas de Inferencia

### SE PUEDE inferir:
| Campo | Desde | Confianza |
|-------|-------|-----------|
| Descripcion comercial | Titulo + Descripcion + Nombre tecnico | Alta |
| FAQs genericas | Categoria + Garantia + Marca | Alta |
| Productos relacionados | Misma categoria/marca vehiculo | Media |
| Marca normalizada | Variaciones de nombres de marca | Alta |
| Subcategoria | Path de categoria ML | Alta |
| Keywords SEO | Titulo + Nombre + Compatibilidad | Alta |
| Tipo de empaque | Categoria del producto | Media |
| Handle (URL slug) | Titulo del producto | Alta |
| Titulo limpio | Titulo_ML (quitar "&", capitalizar) | Alta |
| Body HTML | Secciones de contenido generadas | Alta |
| Product Type (Shopify) | Subcategoria del path ML | Alta |
| Tags vehiculo | Compatibilidades + Titulo | Alta |
| SEO Title/Description | Titulo + marca + vehiculo | Alta |
| Image Alt Text | Titulo + marca producto + vehiculo | Alta |

### NO se puede inferir (no inventar):
| Campo | Razon |
|-------|-------|
| Peso y dimensiones | No hay datos fuente |
| Imagenes | No hay URLs |
| Especificaciones tecnicas | Material, tolerancias no disponibles |
| Precio de envio | Depende de logistica |
| Compatibilidad vehicular (si no hay datos) | Riesgo alto de error |
| Lado de instalacion (si no esta) | Critico, no se puede adivinar |
| Codigo OEM (si no esta) | Dato tecnico preciso |

## Normalizacion de Marcas

Aplicar estas reglas al procesar:
```
"ORIGINAL FREY GERMAN TECHNOLOGY QUALITY" -> "Original Frey"
"ORIGINAL FREY GERMAN TECHNOLOGY GERMAN Q" -> "Original Frey"
"ORIGINAL FREY GERMAN TECNHLOGY QUALITY" -> "Original Frey"
"ORIGINAL FREY GERMAN TECHNOLOGY" -> "Original Frey"
"EMBLER AUTOPARTES EUROPEAS" -> "Embler"
"EMBLER" -> "Embler"
```

## Formato de Output

Cada CSV en `new-output/<hoja>/` tiene las 34 columnas originales del input MAS las 3 columnas agregadas por el script (`marca_normalizada`, `subcategoria_limpia`, `categoria_archivo`). El procesamiento posterior con Claude agrega las columnas de contenido (`caract_*`, `seccion_*`, `shopify_*`, `revision_humana`).

Categorias generadas por hoja:
```
new-output/ml_con_match/
  refacciones_motor.csv         (4,743)
  refacciones_suspension.csv    (4,385)
  refacciones_otros.csv         (1,868)
  refacciones_frenos.csv        (1,000)
  refacciones_carroceria.csv      (597)
  accesorios.csv                  (465)
  refacciones_electrico.csv       (378)
  refacciones_transmision.csv     (192)
  refacciones_clima.csv           (131)
  tuning.csv                      (110)
  otros.csv                        (73)
  herramientas.csv                 (18)
new-output/ml_sin_match/        (mismas categorias, 847 filas total)
```

## Flujo de Trabajo

1. Ejecutar `scripts/01_extraer_categorias_v2.py` -> genera CSVs por categoria en `new-output/<hoja>/`
2. Para cada CSV de `ml_con_match/`, procesar con Claude en batches de ~50-100 filas
3. Claude genera las columnas de contenido para cada batch
4. Consolidar batches en el CSV final de cada categoria
5. Validacion: verificar que no hay campos inventados donde no deberia

## Notas Importantes

- **Idioma**: Todo el contenido generado debe ser en espanol
- **Autopartes europeas**: El nicho es BMW, Mercedes-Benz, Audi, VW, Porsche, Mini, etc.
- **Tono**: Tecnico-comercial. El cliente es mecanico o conocedor de autos europeos.
- **No inventar datos tecnicos**: Mejor dejar vacio que poner datos incorrectos de compatibilidad o especificaciones.
- **Marcas de vehiculo vs marca de producto**: No confundir. BMW es la marca del vehiculo, Original Frey/Embler es la marca del producto (refaccion).
