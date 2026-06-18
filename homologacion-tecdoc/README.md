# Homologación de categorías Embler ↔ TecDoc (pipeline de migración a Shopify)

> Pipeline para que **Grupo/Subgrupo** del catálogo Embler tengan match con la taxonomía
> estándar TecDoc y rehacer collections + mega menú vía Matrixify. Se separó de
> `../evaluacion-api-tecdoc/` (la evaluación del API para el buscador, que es otro tema).
>
> **Lo usa el skill `tecdoc-shopify`** — si mueves o renombras estos archivos, actualiza
> las rutas en `.claude/skills/tecdoc-shopify/SKILL.md` y `MIGRACION-TECDOC.md`.

## Archivos

| Archivo | Qué es |
|---|---|
| `PLAN-HOMOLOGACION-TECDOC.md` | Plan y decisiones completas |
| `homologacion.csv` | **Fuente de verdad**: 310 subgrupos MX → (sistema, subgrupo, node_id) TecDoc |
| `categorias_tecdoc.json` | Árbol TecDoc completo (17 sistemas / 811 nodos, con IDs) |
| `catalogo_tecdoc_metafields.csv` | CSV de metafields de producto generado |
| `homologar.py` | Genera la homologación (incluye overrides manuales) |
| `extraer_categorias.py` | Extrae el árbol TecDoc del API → `categorias_tecdoc.json` |
| `generar_metafields_tecdoc.py` | Genera el CSV de metafields de productos |
| `generar_import_tecdoc.py` | Genera collections de sistema + menú pase 1 |
| `preview_menu_tecdoc.py`, `preview_menu_lean.py` | Previews del mega menú |
| `menu_pase1.xlsx`, `collections_sistema.xlsx` | Archivos de import para Matrixify |
