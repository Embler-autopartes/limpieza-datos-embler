# Limpieza de Datos Embler - Instrucciones para Claude

## Contexto del Proyecto

Este proyecto procesa un catalogo de autopartes europeas (BMW, Mercedes-Benz, Audi, VW, etc.) para generar contenido de ecommerce. El archivo input contiene 13,363 productos cruzados entre Microsip (ERP) y MercadoLibre (marketplace).

## Estructura de Carpetas

```
input/          -> Archivo fuente (CRUCE_MICROSIP_MERCADOLIBRE (2).xlsx)
output/         -> Archivos procesados por categoria
scripts/        -> Scripts de Python para extraccion y procesamiento
ANALISIS.md     -> Documentacion del analisis de datos
```

## Archivo Input

**`input/CRUCE_MICROSIP_MERCADOLIBRE (2).xlsx`** - Hoja "Sheet1", 13,363 filas, 36 columnas.

### Columnas clave para generar contenido:
- `Titulo_ML` (col 14): Titulo de ML, punto de partida para nombre comercial
- `Descripcion_ML` (col 15): Descripcion existente (99.5% completa)
- `NOMBRE_ARTICULO_MC` (col 3): Nombre tecnico del ERP
- `Categoria_ML` (col 13): Categoria jerarquica de ML
- `Compatibilidades_ML` (col 24): Vehiculos compatibles (51.1% completa)
- `Marca_ML` (col 26): Marca del producto (99.1%)
- `Numero de parte_ML` (col 27): Part number (99%)
- `Garantia_ML` (col 21): Info de garantia (100%)
- `Tipo de vehiculo_ML` (col 29): Carro/Moto/Linea Pesada (95.6%)
- `Codigo OEM_ML` (col 31): Codigo original (64.6%)
- `Precio_ML` (col 16): Precio (100%)

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
- `seccion_faq` — 3-5 preguntas frecuentes en JSON array
- `productos_relacionados` — Hasta 5 SKUs relacionados del mismo catalogo
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

Cada archivo de output en `output/` sera un CSV con las columnas originales MAS las nuevas columnas generadas. Nombre de archivos:
```
output/refacciones_motor.csv
output/refacciones_suspension.csv
output/refacciones_frenos.csv
output/accesorios.csv
output/tuning.csv
output/motos.csv
output/linea_pesada.csv
output/otros.csv
```

## Flujo de Trabajo

1. Ejecutar `scripts/01_extraer_categorias.py` -> genera CSVs por categoria en output/
2. Para cada CSV, procesar con Claude en batches de ~50-100 filas
3. Claude genera las 5 columnas nuevas para cada batch
4. Consolidar batches en el CSV final de cada categoria
5. Validacion: verificar que no hay campos inventados donde no deberia

## Notas Importantes

- **Idioma**: Todo el contenido generado debe ser en espanol
- **Autopartes europeas**: El nicho es BMW, Mercedes-Benz, Audi, VW, Porsche, Mini, etc.
- **Tono**: Tecnico-comercial. El cliente es mecanico o conocedor de autos europeos.
- **No inventar datos tecnicos**: Mejor dejar vacio que poner datos incorrectos de compatibilidad o especificaciones.
- **Marcas de vehiculo vs marca de producto**: No confundir. BMW es la marca del vehiculo, Original Frey/Embler es la marca del producto (refaccion).
