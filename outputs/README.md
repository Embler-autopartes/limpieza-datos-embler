# Outputs — catálogo Embler

Esta carpeta concentra todas las salidas finales del pipeline. Los archivos
intermedios siguen en `new-output/`, `new-output_v2/` y `output/` en la raíz.

## Cuál usar AHORA

**`2026-05-09-USAR-shopify-import/`** — CSVs listos para importar a Shopify.
Schema oficial Shopify (Handle, Title, Body HTML, metafields…), 12,749 productos,
51,593 imágenes, URLs limpias de R2 (sin las genéricas de MercadoLibre).

## Otras carpetas vigentes

- **`2026-05-09-delta-productos-nuevos/`** — 58 productos que aparecieron en el
  catálogo actualizado (cruce con `mercado libre db.xlsx`) y NO estaban en el
  mayo. Schema interno, sin adaptar. Para trabajar aparte e integrarlos después.

- **`2026-05-08-catalogo-schema-interno/`** — Catálogo completo en schema
  interno (`Id`, `Categoría`, `Título`, `caract_*`, `seccion_*`, `shopify_*`,
  `img1..imgN`). 13,436 productos. Es la fuente de verdad post-cruce con
  `mercado libre db.xlsx`. Útil para regenerar/auditar.

## Histórico (`historico/`)

Versiones anteriores conservadas como referencia. **No usar para importar.**

- `2026-05-07-shopify-mayo-imgs-genericas/` — Versión mayo 7 con imágenes
  genéricas de ML (~111k imgs, promedio 8.35/prod). Reemplazada por la versión
  del 2026-05-09 cuando se filtraron las genéricas.
- `2026-05-04-shopify-estructura-sitio/` — Schema Shopify intermedio antes de
  agregar metafields `custom.marca/grupo/sub_grupo`.
- `2026-04-final-con-imagenes/` y `2026-04-final/` — Outputs originales del
  primer pipeline (input anterior `INPUT.xlsx`, antes del schema `CRUCE_ML_MC`).

## Nomenclatura

`YYYY-MM-DD-descripcion-corta/`

- Fecha = día en que se generó el output (no la fecha del input).
- Descripción = qué hace única a esa versión (ej. `imgs-genericas`,
  `imgs-actualizadas`, `delta-productos-nuevos`).
- Prefijo `USAR-` opcional para marcar la versión activa de importación.
- Versiones superadas se mueven a `historico/` (no se borran).
