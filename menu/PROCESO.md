# Proceso completo: armar/actualizar el Mega menu de Shopify

Documentación del proceso que hicimos el 2026-05-13 para reconstruir el "Mega menu" de la tienda Embler basado en las 895 Smart Collections importadas previamente. Sirve de referencia para repetir o adaptar el flujo en el futuro.

---

## Resumen ejecutivo

Construir el Mega menu de Shopify (con jerarquía marca → categoría → subcategoría, ~300 items) requiere **dos imports a Matrixify**:

1. **Import #1 — REPLACE con titles prefijados** (`BMW - Motor - Poleas`). Crea la estructura completa con jerarquía correcta.
2. **Import #2 — MERGE por ID con titles cortos** (`Poleas`). Renombra los items sin tocar la jerarquía.

El motivo del doble paso está en la sección "Por qué dos pasos" más abajo.

---

## Pre-requisitos

1. **Smart Collections existentes en Shopify** con metafields `global._brand`, `global.group`, `global.sub_group`. El proceso lee la lista de collections desde `Procesamiento de Catálogo/outputs/collections-matrixify/source/Embler-Collections.xlsx`.
2. **App Matrixify instalada** en la tienda Shopify.
3. **Python 3** con `openpyxl` (`pip install openpyxl` si falta).

---

## Paso 0 — Backup del menu actual

Antes de cualquier cambio, exporta el menu actual desde Matrixify:

1. Admin Shopify → Apps → Matrixify → Export.
2. Selecciona **Menus**, exporta.
3. Guarda el `.xlsx` en `menu/` con un nombre que indique fecha (ej. `Export_2026-05-13_173845.xlsx`).

Este archivo es tu opción de rollback. Si todo sale mal: importas el backup con `Command=REPLACE` y vuelve al estado previo.

---

## Paso 1 — Generar los archivos de import

```bash
python3 scripts/14_generar_mega_menu_matrixify.py
```

Produce en `menu/`:

| Archivo | Uso |
|---|---|
| `Embler-Mega-Menu.xlsx` | Versión "corta" (labels limpios). **NO funciona en primer pase** — Matrixify rechaza por duplicados. Solo histórico/referencia. |
| `Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx` | **Archivo de PASO 1**. Labels prefijados (`BMW - Motor`) globalmente únicos. |
| `MEGA-MENU-PROPUESTA.md` | Preview de la estructura para validar antes de importar. |
| `README.md` | Instrucciones para el equipo. |

### Configuración del script (variables al inicio)

- `MENU_TITLE = "Mega menu"` — nombre del menu en Shopify.
- `MENU_HANDLE = "mega-menu"` — handle.
- `SUB_PER_GROUP = 3` — cap de subcategorías por categoría (orden alfabético).
- `BRAND_LABELS` — lista de tuplas `(display_label, brand_metafield_value, brand_handle)`. Edita aquí para:
  - Agregar/quitar marcas del menu.
  - Conservar labels visibles distintos al brand metafield (ej. "Mercedes Benz" como display pero collection `mercedes-benz`).

---

## Paso 2 — Import #1: estructura con prefijos

1. Matrixify → Import → sube `menu/Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx`.
2. Espera a que termine. Resultado esperado: `OK: 299, Failed: 0`.
3. Descarga el `Import_Result_*.xlsx` que Matrixify ofrece. Guárdalo en `menu/` para auditoría.

**Lo que pasa internamente:**
- `Command=REPLACE` borra completamente el menu actual.
- El menu se recrea con un ID nuevo (el handle `mega-menu` se mantiene).
- Como los titles son únicos (`BMW - Motor`, `Audi - Motor`, etc.), Matrixify no tiene ambigüedad de parent-matching.

**Verifica en el admin:**
- URL nueva: `/admin/content/menus/<NUEVO_ID>` (el ID cambió porque REPLACE recrea).
- La jerarquía visible: BMW → BMW - Motor → BMW - Motor - Anillos de motor, etc.
- Los links de categorías y subcategorías apuntan a `/collections/<handle>`.

---

## Paso 3 — Export del menu post-import #1

Para el segundo import necesitamos los IDs que Shopify acaba de asignar a cada item:

1. Matrixify → Export → Menus.
2. Guarda en `menu/` (cualquier nombre `Export_*.xlsx`).

---

## Paso 4 — Generar el archivo de rename

```bash
python3 scripts/15_generar_mega_menu_rename_corto.py
# o pasando el path:
python3 scripts/15_generar_mega_menu_rename_corto.py menu/Export_<timestamp>.xlsx
```

Si no pasas argumento, el script toma el `Export_*.xlsx` más reciente en `menu/` (excluye el backup `Export_2026-05-13_173845.xlsx` si está hardcoded).

Produce:

| Archivo | Uso |
|---|---|
| `Embler-Mega-Menu-RENAME-corto.xlsx` | **Archivo de PASO 2.** ~286 filas con `Command=MERGE` matchea por `Menu Item: ID`. Solo actualiza el campo `Title`. |
| `RENAME-PREVIEW.md` | Tabla antes/después para validar visualmente. |

**Lógica del rename:**
- Brand level (sin parent): no se toca. "BMW" → "BMW".
- Categoría (parent = brand): quita el prefijo del parent. `BMW - Motor` → `Motor`.
- Subcategoría (parent = categoría): quita el prefijo del parent. `BMW - Motor - Poleas` → `Poleas`.

---

## Paso 5 — Import #2: rename a labels cortos

1. Revisa `menu/RENAME-PREVIEW.md` para confirmar que los renames se ven bien.
2. Matrixify → Import → sube `menu/Embler-Mega-Menu-RENAME-corto.xlsx`.
3. Resultado esperado: `OK: 286, Failed: 0`.

**Lo que pasa internamente:**
- Matrixify matchea cada fila por `Menu Item: ID` (no por Title).
- Como los IDs son únicos por construcción, no hay ambigüedad aunque varios items terminen con el mismo Title (`Motor` aparece 12 veces — una por marca — y eso está OK).
- `Command=MERGE` solo actualiza el campo `Title`, deja todo lo demás intacto.

**Verifica en el admin:** los items ahora muestran labels cortos (`Motor`, `Accesorios`, `Poleas`) y la jerarquía sigue intacta.

---

## Por qué dos pasos en vez de uno

**Restricción que encontramos:** Matrixify exige que `Menu Item: Title` sea globalmente único dentro del menu para resolver parent-matching cuando los items son nuevos (sin ID).

Cuando intentamos un solo pase con titles cortos (`Motor`, `Suspensión`), Matrixify rechazó **toda la importación** en validación previa con error:

```
REPLACE: Found by Handle | Multiple Menu Items found by value: [Accesorios].
```

Esto pasa porque 12 marcas tendrían una categoría llamada "Accesorios" — Matrixify no sabe distinguirlas sin IDs.

**Solución:**
1. Primer pase con titles prefijados → garantiza unicidad → Matrixify asigna IDs.
2. Segundo pase referenciando por ID → ya no necesita titles únicos → renombramos a labels cortos.

---

## Cambios comunes y cómo aplicarlos

### Agregar/quitar una marca del menu

Edita `BRAND_LABELS` en `scripts/14_generar_mega_menu_matrixify.py`:

```python
BRAND_LABELS = [
    ("BMW", "BMW", "bmw"),
    # ("Citroen", "Citroen", "citroen"),  # comentar para sacar del menu
    ("Nueva Marca", "Nueva-Marca", "nueva-marca"),  # agregar
    ...
]
```

Vuelve a correr ambos scripts (paso 1, import #1, paso 3 export, paso 4, import #2).

### Cambiar el cap de subcategorías

Edita `SUB_PER_GROUP = 3` en `scripts/14_generar_mega_menu_matrixify.py` y vuelve a generar.

### Cambiar el criterio de selección de subcategorías

Actualmente es alfabético (`sorted(brand_group_subs[b][g], key=lambda x: x[0].lower())`). Para priorizar por ventas, popularidad, etc., reemplaza el sort por un lookup contra esa fuente de datos.

### Renombrar una marca específica

Edita el primer elemento de la tupla en `BRAND_LABELS` (display label). Esto solo afecta el label visible; la collection real sigue igual.

---

## Lessons learned (no repetir)

1. **No intentes un solo pase con titles cortos.** Matrixify rechaza globalmente. Siempre dos pasos.
2. **Backup antes de cada import.** El backup se hace via Export de Matrixify. Sin backup, no hay rollback rápido.
3. **REPLACE cambia el menu ID.** Si tu theme referencia el menu por ID, hay que actualizarlo. Si lo referencia por handle (`mega-menu`), todo sigue funcionando.
4. **Resource Type=COLLECTION + Resource Handle** es la forma limpia de linkear a una collection. NO uses URLs construidas a mano (`/collections/all?filter=...`) — esas son workarounds del menu viejo, antes de tener las Smart Collections reales.
5. **Marca sin link:** `Resource Type=HTTP, URL=#`. Algunos themes lo tratan como hover-only para mega menu trigger. Si el theme rompe, cámbialo al handle de la brand collection (`bmw`, `audi`) — el usuario clickeará la marca y caerá en la collection padre, lo cual no es terrible.

---

## Archivos relacionados

- `scripts/14_generar_mega_menu_matrixify.py` — genera los archivos del paso 1.
- `scripts/15_generar_mega_menu_rename_corto.py` — genera el archivo del paso 4 (rename).
- `scripts/13_generar_estructura_menu.py` — genera `ESTRUCTURA-MENU.md` con las 895 collections completas (referencia, no para el menu).
- `menu/ESTRUCTURA-MENU.md` — referencia completa de collections.
- `menu/MEGA-MENU-PROPUESTA.md` — preview de la estructura del menu antes de importar.

---

## Cronología real (2026-05-13)

| Hora | Evento | Resultado |
|---|---|---|
| 17:38 | Backup del menu actual (Export_*.xlsx) | OK |
| 18:19 | Primer intento con titles cortos | 299 Failed (duplicados) |
| 18:31 | Segundo intento con FALLBACK (titles prefijados) | 299 OK ✓ |
| 18:36 | Export del menu post-import #1 | OK |
| 18:40 | Generación del rename file (286 filas) | OK |
| _pendiente_ | Import #2 (rename) | _pendiente_ |
