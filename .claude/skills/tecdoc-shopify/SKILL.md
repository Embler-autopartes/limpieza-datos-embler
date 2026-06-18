---
name: tecdoc-shopify
description: |
  Modifica la tienda Embler en Shopify (productos, collections, menú) usando Matrixify, con la
  estructura de categorías homologada a la taxonomía estándar de TecDoc/TecAlliance (3 niveles:
  Sistema TecDoc → Grupo → Subgrupo; metafields `tecdoc.sistema/subgrupo/node_id`). Conoce la
  homologación de los 310 subgrupos MX a los 811 nodos TecDoc, la restricción de NO cambiar
  `global.group`/`global.sub_group`, y el flujo exacto para modificar el sitio con Matrixify
  (imports de metafields, reglas de Smart Collections, menú en 2 pasos). Úsalo SIEMPRE que el
  usuario quiera: continuar/retomar la migración TecDoc; importar o actualizar productos,
  collections o el menú vía Matrixify; reclasificar productos a un sistema/grupo/subgrupo TecDoc;
  crear o modificar Smart Collections; reconstruir o ajustar el mega menú alineado a TecDoc;
  agregar metafields a productos; o cualquier cambio masivo en el catálogo/navegación de Embler.
  Se activa con frases como: "continúa la migración tecdoc", "retoma lo de tecalliance",
  "actualiza los productos con matrixify", "importa las collections de sistema", "rehaz el menú
  tecdoc", "agrega el metafield X a los productos", "modifica el sitio con matrixify",
  "reclasifica estos productos al sistema Y", "crea una collection por sistema", o cualquier
  referencia a la estructura TecDoc / los archivos en `homologacion-tecdoc/` de homologación.
---

# Modificar Shopify de Embler con estructura TecDoc (vía Matrixify)

Este skill da (1) el **contexto de la estructura TecDoc** que definimos, y (2) el **playbook para
modificar el sitio con Matrixify** (productos, collections, menú). Sirve para retomar la migración
inicial y para cualquier cambio futuro.

## 0. Primero: cargar el contexto

1. **Lee `MIGRACION-TECDOC.md`** (en esta carpeta de skill) — estado de la migración, qué está
   hecho, qué falta, runbook de imports.
2. **Lee los datos fuente** según necesites:
   - `homologacion-tecdoc/homologacion.csv` — 310 subgrupos MX → (sistema, subgrupo, node_id) TecDoc. La fuente de verdad del mapeo.
   - `homologacion-tecdoc/categorias_tecdoc.json` — árbol TecDoc completo (17 sistemas / 811 nodos, con IDs).
   - `homologacion-tecdoc/PLAN-HOMOLOGACION-TECDOC.md` — el plan completo y decisiones.
3. Pregunta al usuario si el cambio es: continuar la migración, o un cambio nuevo (productos / collections / menú).

## 1. La estructura TecDoc (cómo está organizado el catálogo)

**3 niveles**, de mayor a menor:
- **Sistema** (TecDoc) — los grupos raíz del árbol TecDoc (ej. Motor, Kit de freno, Suspensión / Amortiguación,
  Refrigeración, Dirección…). Es el nivel nuevo y el organizador del menú.
- **Grupo** (MX) — los 15 grupos originales (Motor, Frenos, Suspensión, Colisión…). **NO se tocan.**
- **Subgrupo** (MX) — los 310 subgrupos originales (Balatas, Bombas de Agua, Amortiguadores…). **NO se tocan.**

**Metafields (namespace.key):**
| Metafield | Qué guarda | ¿Se toca? |
|---|---|---|
| `global._brand` | Marca del auto (BMW, Audi…) | no |
| `global.group` | Grupo MX | **NUNCA** (lo usa la plantilla) |
| `global.sub_group` | Subgrupo MX | **NUNCA** (lo usa la plantilla) |
| `tecdoc.sistema` | Sistema TecDoc (nivel 1 nuevo) | sí, lo escribimos |
| `tecdoc.subgrupo` | Nombre oficial del nodo TecDoc | sí |
| `tecdoc.node_id` | assemblyGroupNodeId TecDoc (llave de match perfecto) | sí |

> ⚠️ **Restricción dura:** `global.group` y `global.sub_group` son inmutables — la plantilla de
> Shopify depende de esos strings. Toda alineación a TecDoc se hace con los metafields `tecdoc.*`.

Las **Smart Collections** de Embler se definen por reglas de metafield (match exacto). Tipos:
- Hoja (existentes): `_brand` + `global.group` + `global.sub_group` → ~895 collections.
- Sistema (nuevas, esta migración): `_brand` + `tecdoc.sistema` → handles `{marca}-sis-{sistema-slug}`.
Cambiar el valor de un metafield reasigna el producto a las collections automáticamente (no hay que tocar la collection).

## 2. Cómo modificar el sitio con Matrixify

Matrixify importa/exporta vía Excel/CSV. **El match es por `Handle`** (productos, collections, menús).
Usar `Command: MERGE` para actualizar sin borrar; `REPLACE` solo cuando se quiera recrear (ej. menú completo).

### A) Productos — agregar/actualizar metafields
CSV con `Handle` + columnas `Metafield: <namespace>.<key> [<tipo>]`. Ej:
`Handle,Metafield: tecdoc.sistema [single_line_text_field],…` — una fila por producto. NO incluir
columnas de group/sub_group si no se quieren tocar. Ver `generar_metafields_tecdoc.py`.

### B) Smart Collections — crear/modificar
Hoja "Smart Collections". Columnas: `Handle, Command, Title, Published, Must Match,
Rule: Product Column, Rule: Relation, Rule: Condition`. **Multi-regla = repetir el Handle por fila**
(1ª fila lleva Title/Command/Must Match=`all conditions`; filas siguientes solo Handle + columnas Rule).
⚠️ Matrixify NO acepta `all` en "Must Match" — usa exactamente `all conditions` (o `any condition`), si no falla todo el import.
Para reglas sobre un metafield: `Rule: Product Column = "Metafield: tecdoc.sistema"`, `Relation = Equals`,
`Condition = <valor>`. **Requisito:** la metafield definition debe existir y tener
**"Use as a condition in smart collections" ACTIVADO** (si no, la regla no funciona). Ver `generar_import_tecdoc.py`.

### C) Menú (mega menu) — 2 pasos
El menú se reconstruye con el método de 2 pasos documentado en el skill **`cambiar-menu`** (PROCESO.md):
- **Pase 1 (REPLACE)** con títulos prefijados únicos ("BMW - Motor - Balatas") para que Matrixify resuelva el parent matching.
- **Pase 2 (MERGE)** renombra a títulos cortos ("Balatas") por `Menu Item: ID` (de un Export intermedio).
Estructura TecDoc del menú: **Marca → Sistema (link a collection `{marca}-sis-{sistema}`) → Subgrupo
(link a la collection hoja existente)**. Ver `generar_import_tecdoc.py` (genera el pase 1).

### Metafield definitions (prerequisito de B)
Se crean en **Settings → Custom data → Products → Add definition**. Para usarlas en collections,
activar **"Use as a condition in smart collections"**. **Claude SÍ puede crear definitions por el navegador** (admin nativo).

## 3. Limitación de automatización (importante)

**Claude NO puede subir archivos a Matrixify por el navegador**: el botón "Add file" abre el
selector de archivos nativo del SO (no operable) y el contenido de la app vive en un **iframe cerrado**
(el input no aparece en el árbol accesible). Por lo tanto:
- **El usuario arrastra** cada archivo a Matrixify → Import y le da Import.
- **Claude verifica** el resultado en el admin nativo de Shopify (sí accesible):
  - Productos/metafields: Settings → Custom data → la definición muestra "Used in: N products".
  - Collections: Products → Collections (filtrar por handle).
  - Menú: Content → Menus → "Mega menu".
- **Claude SÍ puede**: crear metafield definitions, leer/verificar productos, collections y menús en el admin,
  generar todos los archivos de import, y guiar paso a paso.

## 4. Para ESTE primer caso (continuar la migración)

Sigue el **runbook de la sección 3 de `MIGRACION-TECDOC.md`**: imports en orden
(productos → collections → menú pase 1 → export → menú pase 2). Antes de cada paso, regenera el
archivo si los datos fuente cambiaron (sección 4 de ese doc). Verifica cada import en el admin antes del siguiente.

## 5. Archivos clave
| Archivo | Rol |
|---|---|
| `.claude/skills/tecdoc-shopify/MIGRACION-TECDOC.md` | Estado y runbook de la migración |
| `homologacion-tecdoc/homologacion.csv` | Mapeo 310 subgrupos → nodo TecDoc (fuente de verdad) |
| `homologacion-tecdoc/categorias_tecdoc.json` | Árbol TecDoc (17 sistemas / 811 nodos) |
| `homologacion-tecdoc/homologar.py` | Genera la homologación (incluye overrides manuales) |
| `homologacion-tecdoc/generar_metafields_tecdoc.py` | Genera CSV de metafields de productos |
| `homologacion-tecdoc/generar_import_tecdoc.py` | Genera collections de sistema + menú pase 1 |
| `homologacion-tecdoc/PLAN-HOMOLOGACION-TECDOC.md` | Plan y decisiones completas |

## Skills relacionados
- `cambiar-menu` — mecánica detallada del menú en 2 pasos (úsala para el pase 1/2).
- `mover-producto-collection` — reclasificar pocos productos cambiando metafields (uno a uno).
