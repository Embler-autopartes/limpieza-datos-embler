# Mega menu — import a Shopify via Matrixify

## Archivos

- `Embler-Mega-Menu.xlsx` — **archivo principal a importar**. Labels cortos (`Motor`, `Poleas`, etc.).
- `Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx` — fallback con labels prefijados (`BMW - Motor`, `BMW - Motor - Poleas`). Usa este SI el principal rompe la jerarquia parent-child (ver caveat de "Parent matching" abajo).
- `MEGA-MENU-PROPUESTA.md` — preview de la estructura para validar antes del import.
- `Export_2026-05-13_173845.xlsx` — backup del menu actual (para revertir si algo sale mal).
- `ESTRUCTURA-MENU.md` — referencia completa de las 895 collections (no solo las del menu).

## Resumen

- Total items en el menu: **299**
- Niveles: marca (sin link) → categoria → max 3 subcategorias
- Menu target: `mega-menu` (Title: "Mega menu")

## Cómo importar

> **Importante:** el archivo usa `Command=REPLACE` a nivel del menu. Eso significa que Matrixify
> **borra completamente el menu "Mega menu" actual** y lo recrea solo con los items de este archivo.
> Resultado: Sprinter, Citroën, Peugeot, Renault, y cualquier hijo viejo de BMW desaparecen
> automaticamente. No es un MERGE.

1. **Backup recomendado:** en Shopify Admin → Apps → Matrixify → Export, exporta el menu actual ("Mega menu") por si quieres revertir.
2. Matrixify → Import → sube `Embler-Mega-Menu.xlsx`.
3. Run import. El menu se elimina y se recrea desde cero con los 299 items.
4. Verifica en `/admin/content/menus/` que el nuevo "Mega menu" aparezca con la estructura esperada.

**Nota sobre el ID del menu:** REPLACE borra el menu y crea uno nuevo, asi que el ID interno
(`313377915250` en la URL actual) puede cambiar. El handle (`mega-menu`) **se mantiene**, asi que
si tu theme referencia el menu por handle (lo normal), todo sigue funcionando. Si el theme
referencia por ID, hay que actualizarlo.

## Caveats

- **Parent matching por Title (riesgo manejable)**: Matrixify identifica el parent por Title exacto.
  El archivo principal usa labels cortos (`Motor`, `Suspensión`), lo que significa que **multiples
  marcas tienen una categoria llamada "Motor"**. Para que funcione, las filas estan agrupadas
  hierarquicamente por marca (BMW completo, luego Audi completo, ...) apostando a que Matrixify
  procesa en orden y asigna parent al match mas reciente.

  **Si después del import notas que subcategorias quedaron bajo la marca equivocada** (ej. ves
  "Poleas" bajo BMW cuando deberia estar bajo Audi), no funciono el matching posicional. En ese caso:
  1. Importa `Export_2026-05-13_173845.xlsx` para revertir al menu de antes.
  2. Importa `Embler-Mega-Menu-FALLBACK-con-prefijos.xlsx` que usa titulos globalmente unicos.
  3. Los labels en el menu apareceran con prefijo de marca (verbose), pero estructura correcta.

- **Marca sin link**: usamos Resource Type=HTTP + URL=`#`. Algunos themes tratan esto como hover-only (correcto para mega menus); otros pueden marcarlo como link roto. Si el theme se queja, cambia el `#` por la collection padre (`bmw`, `audi`, etc.) en el admin.
- **Subcategorias topadas a 3 alfabeticas**: muchas categorias tienen >3 (ej. BMW Motor tiene 30+ subs). El cap es para no rebasar el limite practico de Shopify. Si quieres priorizar otras subcategorias (las mas vendidas, las top), editalas en el admin o regenera el archivo cambiando `SUB_PER_GROUP` o la regla de orden en `scripts/14_generar_mega_menu_matrixify.py`.

## Para regenerar

```bash
python3 scripts/14_generar_mega_menu_matrixify.py
```
