# Plan de 2 pasos: import + rename a labels cortos

## Paso 1 — Import del FALLBACK (en curso)

Archivo: `Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx`

Esto crea el menu con titles únicos verbosos como `BMW - Motor - Poleas`.
La jerarquía queda correcta porque los titles son globalmente únicos.

**Verifica después del import:** que el resultado en Matrixify diga `OK: 299, Failed: 0`.

---

## Paso 2 — Rename a labels cortos por ID

Una vez que el paso 1 está OK:

### 2a. Exportar el menu para obtener los IDs nuevos

En Shopify Admin → Apps → Matrixify → Export:

1. Selecciona **Menus**
2. Filtra por handle `mega-menu` (o exporta todos los menus, no importa).
3. Descarga el archivo.
4. Guárdalo en `menu/` (cualquier nombre `Export_*.xlsx` funciona; el más reciente se usa automáticamente, excepto el backup `Export_2026-05-13_173845.xlsx`).

### 2b. Generar el archivo de rename

```bash
python3 scripts/15_generar_mega_menu_rename_corto.py
```

Esto produce:
- `menu/Embler-Mega-Menu-RENAME-corto.xlsx` — archivo a importar (~286 renames)
- `menu/RENAME-PREVIEW.md` — preview de cómo quedará cada item antes/después

### 2c. Validar la preview

Abre `RENAME-PREVIEW.md` y verifica que la columna "Después" se vea limpia:

| ID | Antes | Después |
|----|-------|---------|
| `123` | `BMW - Motor` | `Motor` |
| `124` | `BMW - Motor - Poleas` | `Poleas` |
| `125` | `Audi - Motor` | `Motor` |
| `126` | `Audi - Motor - Bujias` | `Bujias` |

### 2d. Importar el rename

Matrixify → Import → sube `Embler-Mega-Menu-RENAME-corto.xlsx`.

Este import usa **`Command=MERGE`** + **`Menu Item: ID`** como llave de match:
- NO crea items nuevos.
- NO toca la jerarquía (Parent ID no cambia).
- Solo actualiza el campo `Title` de cada item.
- Como matchea por ID (no por Title), NO hay problema de duplicados.

Resultado esperado: el mismo menu, misma jerarquía, pero con labels limpios
(`Motor`, `Poleas`, `Accesorios`) en lugar de los verbosos.

---

## Por qué dos pasos en vez de uno

El primer import necesita Titles únicos (sin ID asignado, Matrixify resuelve
parent matching por Title). Una vez creados, cada item tiene ID, y el segundo
import puede usar ID como llave — eso libera la restricción de unicidad de
Title y permite labels cortos repetidos sin ambigüedad.

## Si algo sale mal

- **Paso 1 falla:** revisa el Import_Result, manda el archivo.
- **Paso 2 falla:** el menu queda con los labels verbosos del paso 1, totalmente
  funcional. Puedes vivir con eso mientras debuggeamos.
- **Quieres revertir todo:** importa `Export_2026-05-13_173845.xlsx` con
  Command=REPLACE en cada fila (es tu backup pre-cambios).
