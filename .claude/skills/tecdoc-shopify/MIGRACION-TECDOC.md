# Migración TecDoc — contexto y estado (para retomar)

> Documento de estado de la migración que homologa el catálogo Embler con la taxonomía
> estándar de TecDoc/TecAlliance y reorganiza menú + collections en Shopify.
> **Estado al 2026-06-11: PAUSADA esperando licencia de Matrixify.** Lo de Claude (metafield
> definitions) está hecho; los imports a Matrixify quedan pendientes.

---

## 1. Qué es esta migración

El catálogo (≈12,700 productos) usa una taxonomía MX propia (15 Grupos / 310 Subgrupos).
La homologamos con la taxonomía estándar de TecDoc (17 sistemas / 811 nodos) para alinear
la tienda al estándar de los armadores, sin romper la plantilla de Shopify.

### Decisiones tomadas (confirmadas con el cliente)
1. **Naming**: se mantienen los nombres MX visibles; la homologación TecDoc se guarda en
   **metafields nuevos** (`tecdoc.*`). UX y SEO intactos.
2. **Niveles**: 3 niveles → **Sistema (TecDoc) → Grupo → Subgrupo**.
3. **Match**: por nombre (tabla de homologación determinista, no por dato de API).
4. **Menú**: jerarquía **Marca → Sistema (TecDoc) → Subgrupo**, versión **LEAN**
   (top 8 sistemas/marca + top 3 subgrupos/sistema, por volumen) = **286 items** (cabe en Shopify ~300).
5. **Encabezado "Sistema" del menú = CON link** → requiere collections nuevas (marca × sistema).

### ⚠️ Restricción dura (cliente)
**NO cambiar** los valores de `global.group` ni `global.sub_group` — la plantilla de Shopify
depende de esos strings a nivel programación. La homologación TecDoc se **agrega** aparte.

---

## 2. Qué YA está hecho

- ✅ **Taxonomía TecDoc extraída** de la API → `base-pruebas/categorias_tecdoc.json` (17 sistemas / 811 nodos).
- ✅ **Tabla de homologación** → `base-pruebas/homologacion.csv`: 310 subgrupos → nodo TecDoc, **100%**
  (matcher determinista + ~86 overrides manuales decididos por Claude, auto-auditado).
- ✅ **Metafield definitions creadas en Shopify** (Settings → Custom data → Products):
  - `tecdoc.sistema` (TecDoc Sistema) — single line text — **"Use as a condition in smart collections" ACTIVADO**.
  - `tecdoc.subgrupo` (TecDoc Subgrupo) — single line text.
  - `tecdoc.node_id` (TecDoc Node ID) — single line text.
- ✅ **Archivos de import generados** (en `base-pruebas/`):
  - `catalogo_tecdoc_metafields.csv` — 12,705 productos × (Handle + 3 metafields tecdoc.*). NO toca group/sub_group.
  - `collections_sistema.xlsx` — 81 Smart Collections nuevas (marca × sistema), regla `_brand` + `tecdoc.sistema`.
  - `menu_pase1.xlsx` — 286 items, Marca → Sistema → Subgrupo, títulos prefijados (REPLACE).

---

## 3. Qué FALTA (runbook de imports — BLOQUEADO por licencia Matrixify)

**Orden estricto.** Claude NO puede subir archivos a Matrixify (el botón abre el selector
nativo del SO y el contenido vive en un iframe cerrado). El **usuario arrastra** cada archivo;
**Claude verifica** el resultado en el admin nativo.

1. **Productos** — importar `catalogo_tecdoc_metafields.csv` (match por Handle, MERGE).
   - Verificar: en la definición `tecdoc.sistema`, "Used in" debe mostrar ~12,705 productos.
2. **Collections** — importar `collections_sistema.xlsx` (81 collections, se llenan solas con el paso 1).
   - Verificar: Products → Collections, buscar `*-sis-*` (ej. `bmw-sis-motor`) y que tengan productos.
3. **Backup + Menú pase 1** — Export → Menus (backup), luego importar `menu_pase1.xlsx` (REPLACE).
   - Verificar: Content → Menus → "Mega menu" con Marca → Sistema → Subgrupo.
4. **Menú pase 2 (rename)** — Export → Menus → compartir ese export con Claude → Claude genera
   el archivo de rename (títulos cortos: "BMW - Motor" → "Motor", match por ID) → usuario lo importa.
   - Mecánica de 2 pasos documentada en el skill [[cambiar-menu]] (PROCESO.md).

---

## 4. Cómo regenerar los archivos (si cambian los datos fuente)

```bash
cd base-pruebas
python3 extraer_categorias.py          # -> categorias_tecdoc.json (necesita API TecDoc activa)
python3 homologar.py                   # -> homologacion.csv (310 subgrupos -> nodo TecDoc)
python3 generar_metafields_tecdoc.py   # -> catalogo_tecdoc_metafields.csv
python3 generar_import_tecdoc.py       # -> collections_sistema.xlsx + menu_pase1.xlsx
python3 preview_menu_lean.py           # -> menu/MENU-TECDOC-LEAN.md (preview)
```

Caps del menú lean: `CAP_SIS=8`, `CAP_SUB=3` en `generar_import_tecdoc.py` y `preview_menu_lean.py`.

---

## 5. Distribución por Sistema TecDoc (resultado de la homologación)
Motor 2920 · Suspensión/Amortiguación 1791 · Refrigeración 1644 · Suspensión de eje/Ruedas 1131 ·
Carrocería 1018 · Kit de freno 982 · Filtro 417 · Encendido 388 · … (28 sistemas, 11,911 prod).

Detalle completo: `base-pruebas/PLAN-HOMOLOGACION-TECDOC.md` y `homologacion.csv`.
