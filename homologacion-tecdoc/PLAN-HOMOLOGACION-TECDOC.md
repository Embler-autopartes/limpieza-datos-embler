# Plan de homologación de categorías Embler ↔ TecDoc

> Objetivo: que **Grupo** y **Subgrupo** del catálogo Embler tengan **match perfecto con la
> taxonomía estándar de TecDoc/TecAlliance**, recategorizar lo necesario, y rehacer el
> mega menú vía Matrixify.

---

## 1. Punto de partida (inventario real)

### Taxonomía TecDoc (estándar de los armadores) — extraída de la API
- **17 sistemas** de nivel superior (`getShortCuts2`)
- **34 grupos raíz** + **811 nodos** totales en el árbol de assembly groups
- Guardado en `homologacion-tecdoc/categorias_tecdoc.json` (árbol completo con IDs y conteos)
- Naming formal, español de España: `Kit de freno`, `Suspensión / Amortiguación`,
  `Suspensión de eje/Guía de rueda/Ruedas`, `Transmisión por correas`, `Sistema de encendido/incandescencia`

### Taxonomía Embler actual
- **15 Grupos** (metafield `global.group`) · **310 Subgrupos** (metafield `global.sub_group`)
- **11,911 productos** · **896 Smart Collections** · **13 marcas** en el mega menú
- Naming MX/refaccionaria: `Balatas`, `Mazas de Ruedas`, `Marchas`, `Calaveras`, `Bandas de Accesorios`
- Árbol: `Procesamiento de Catálogo/outputs/_arbol_marca_grupo_subgrupo.json`
- Catálogo: `outputs/2026-06-02-shopify-remapeado/catalogo_completo.csv`

### El problema central
Las taxonomías **no coinciden** en:
1. **Nombres** — dialecto distinto (Balatas ≠ Freno de disco; Marchas ≠ Sistema de arranque).
2. **Estructura** — Embler pliega distinto. Ejemplos:
   - `Motor` (Embler) contiene Filtros, Encendido, Refrigeración, Bandas → TecDoc los separa en
     sistemas propios (`Filtro`, `Sistema de encendido`, `Refrigeración`, `Transmisión por correas`).
   - `Enfriamiento` (Embler) = `Refrigeración` + `Calefacción/Ventilación` + `Aire acondicionado` (TecDoc).
   - `Suspensión de aire` (749 prod) → `Suspensión/Amortiguación → Suspensión neumática` (id 101884).
   - `Chasis` (18 prod) es un duplicado de Frenos/Suspensión → consolidar.
3. **Cardinalidad** — N:M. Un grupo Embler explota en varios sistemas TecDoc; varios subgrupos
   Embler caen en un mismo nodo TecDoc.

---

## 2. Borrador de mapeo a nivel GRUPO (15 → TecDoc)

| Embler Grupo (prod) | Sistema(s)/grupo(s) raíz TecDoc destino |
|---|---|
| Motor (5,901) | `Motor` (100002) **+ reubicar** subgrupos a `Filtro`, `Sistema de encendido/incandescencia`, `Refrigeración`, `Transmisión por correas`, `Preparación de combustible` |
| Suspensión (2,240) | `Suspensión de eje/Guía de rueda/Ruedas` (100013) + `Suspensión / Amortiguación` (100011) |
| Colisión (973) | `Carrocería` (100001) + `Iluminación`(100014/electrico) + `Limpieza de vidrios` (100018) |
| Frenos (968) | `Kit de freno` (100006) |
| Suspensión de aire (749) | `Suspensión / Amortiguación → Suspensión neumática` (101884) |
| Accesorios (269) | `Accesorios` (100733) + `Equipamiento interior` (100341) + `Sistema de cierre` (100685) |
| Enfriamiento (261) | `Refrigeración` (100007) + `Calefacción/Ventilación` (100241) + `Aire acondicionado` (100243) |
| Transmisión (202) | `Transmisión` (100238) + `Clutch` (100050) + `Tracción a las ruedas` (100014) + `Transmisión por ejes` (100400) |
| Dirección (145) | `Dirección` (100012) |
| Otros (108) | caso por caso → reclasificar o `Servicio` (100019) |
| Tuning (34) | TecDoc no tiene "Tuning"; los spoilers/alerones → `Carrocería`. Decidir si se mantiene como etiqueta de uso. |
| Eléctrico (23) | `Sistema eléctrico` (100010) |
| Herramientas (18) | nodos `Herramientas` (103129/103148) o mantener fuera de TecDoc |
| Chasis (18) | consolidar en `Frenos` / `Suspensión de eje` (es duplicado) |
| Escape (2) | `Sistema de escape` (100004) |

→ El mapeo a nivel **Subgrupo (310)** se construye en la Fase 1 con apoyo de la API
(`getAutoCompleteSuggestions` + facets de `getArticles` por categoría) y revisión humana.

---

## 3. Decisiones tomadas (✅ confirmadas con el cliente)

| Tema | Decisión |
|---|---|
| **Naming** | Mantener nombres MX visibles + guardar ID/nombre TecDoc en **metafields nuevos**. UX y SEO intactos, match estructural a TecDoc por ID. |
| **Niveles** | **3 niveles**: Sistema (TecDoc) → Grupo → Subgrupo. |
| **Match** | Por nombre (tabla de homologación determinista). |

### ⚠️ Restricción dura (cliente, jun-2026)
Los valores de `global.group` y `global.sub_group` **NO se cambian** — la plantilla de Shopify
depende de esos strings a nivel programación. La homologación TecDoc se **agrega** como metafields
nuevos en paralelo:
- `tecdoc.sistema` — uno de los 17 sistemas / 28 grupos raíz (nuevo nivel 1)
- `tecdoc.subgrupo` — nombre oficial del nodo TecDoc
- `tecdoc.node_id` — assemblyGroupNodeId (la llave de match perfecto)

---

## 4. Fases de ejecución

### ✅ Fase 1 — Tabla de homologación  (COMPLETADA)
- `homologacion.csv`: los **310 subgrupos** mapeados a su nodo TecDoc (sistema + nombre + node_id).
- Método: matcher determinista (sinónimos MX→TecDoc + sesgo por sistema) + **84 overrides manuales**
  decididos por criterio de autopartes. **Cobertura 100%** (11,911 prod), auto-auditado.
- Generado por `homologar.py` desde `categorias_tecdoc.json` + `_arbol_marca_grupo_subgrupo.json`.

### ✅ Fase 2 — Metafields TecDoc en el catálogo  (COMPLETADA — pendiente importar)
- `catalogo_tecdoc_metafields.csv`: **12,705 productos** × (Handle + 3 metafields TecDoc). 0 sin match.
- Generado por `generar_metafields_tecdoc.py`. NO toca group/sub_group.
- **Pendiente:** crear las definiciones de metafield `tecdoc.*` en Shopify e importar este CSV por
  Matrixify (match por Handle, modo update). Productos en `draft` hasta validar.

### ⏳ Fase 3 — Smart Collections por sistema (siguiente)
- Las 896 collections actuales (por grupo/sub_group) **se conservan** (no cambia su regla).
- Opcional: crear collections nuevas a nivel **Sistema TecDoc** (regla: `tecdoc.sistema` = X) para el
  nuevo nivel 1 del menú. ~28 collections nuevas (una por sistema, o por marca×sistema).

### ⏳ Fase 4 — Rehacer el mega menú (siguiente, vía Matrixify)
- Nueva jerarquía: **Marca → Sistema (TecDoc) → Grupo/Subgrupo**.
- Usar el skill `cambiar-menu` (import Matrixify en 2 pasos: prefijo único → rename a label corto).

### ⏳ Fase 5 — Validación
- Conteos por sistema (ver tabla abajo), productos huérfanos, collections vacías, muestreo manual.

## 6. Distribución resultante por Sistema TecDoc (nivel 1 del nuevo menú)
Top sistemas por volumen: Motor (2,920) · Suspensión/Amortiguación (1,791) · Refrigeración (1,644) ·
Suspensión de eje/Ruedas (1,131) · Carrocería (1,018) · Kit de freno (982) · Filtro (417) ·
Encendido (388) · … (28 sistemas en total, 11,911 prod). Detalle reproducible con `homologar.py`.

## 7. Archivos generados
| Archivo | Contenido |
|---|---|
| `categorias_tecdoc.json` | Árbol completo TecDoc (17 sistemas / 811 nodos) |
| `homologacion.csv` | Tabla 310 subgrupos Embler → nodo TecDoc (la fuente de verdad) |
| `catalogo_tecdoc_metafields.csv` | 12,705 productos listos para Matrixify (metafields TecDoc) |
| `homologar.py` · `generar_metafields_tecdoc.py` · `extraer_categorias.py` | Scripts reproducibles |

---

## 5. Riesgos / notas
- **Alto impacto y difícil de revertir**: toca 11,911 productos + 896 collections + menú. Hacer en `draft`/staging y validar antes de publicar.
- **Nunca cambiar handles** (Shopify actualiza por handle).
- **SEO**: si se renombran categorías (A1), planear redirects de las URLs de colección viejas.
- **"Tuning"/"Herramientas"/"Accesorios"** no tienen equivalente limpio en TecDoc → política explícita.
