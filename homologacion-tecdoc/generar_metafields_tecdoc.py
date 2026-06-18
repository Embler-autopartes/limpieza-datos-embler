#!/usr/bin/env python3
"""
FASE 2: genera CSV listo para Matrixify que AGREGA los metafields TecDoc a cada producto.
NO toca global.group ni global.sub_group (la plantilla de Shopify depende de esos strings).
Solo agrega 3 metafields nuevos por Handle: tecdoc.sistema, tecdoc.grupo, tecdoc.node_id.

Salida: catalogo_tecdoc_metafields.csv  (Handle + 3 columnas metafield, una fila por producto)
"""
import csv, sys
csv.field_size_limit(sys.maxsize)

CAT = "../Procesamiento de Catálogo/outputs/2026-06-02-shopify-remapeado/catalogo_completo.csv"
COL_HANDLE = "Handle"
COL_GRUPO = "Grupo (product.metafields.global.group)"
COL_SUB = "Sub grupo (product.metafields.global.sub_group)"

# cargar homologacion -> dict (grupo, subgrupo) -> (sistema, subgrupo_tecdoc, node_id)
H = {}
for r in csv.DictReader(open("homologacion.csv", encoding="utf-8")):
    H[(r["grupo_embler"], r["subgrupo_embler"])] = (r["tecdoc_sistema"], r["tecdoc_subgrupo"], r["tecdoc_node_id"])

# fallback para combos del catalogo que no estaban en el arbol (snapshot mas viejo)
FALLBACK_ESPECIFICO = {
    ("Enfriamiento", "Soportes de Compresor"): ("Aire acondicionado", "Compresor/piezas", "100354"),
    ("Motor", "Cojinetes"): ("Motor", "Bloque motor", "100514"),
    ("Accesorios", "De Limpiaparabrisas"): ("Limpieza de vidrios", "Limpieza de vidrios", "100018"),
    ("Accesorios", "Sensores"): ("Sistemas de seguridad", "Sistema de asistencia de manejo", "706455"),
}
FALLBACK_GRUPO = {  # grupo -> (sistema, subgrupo_tecdoc, node_id) = raiz del sistema
    "Motor": ("Motor", "Motor", "100002"),
    "Suspensión": ("Suspensión / Amortiguación", "Suspensión / Amortiguación", "100011"),
    "Suspensión de aire": ("Suspensión / Amortiguación", "Suspensión neumática", "101884"),
    "Frenos": ("Kit de freno", "Kit de freno", "100006"),
    "Chasis": ("Kit de freno", "Kit de freno", "100006"),
    "Colisión": ("Carrocería", "Carrocería", "100001"),
    "Tuning": ("Carrocería", "Carrocería", "100001"),
    "Accesorios": ("Accesorios", "Accesorios", "100733"),
    "Enfriamiento": ("Refrigeración", "Refrigeración", "100007"),
    "Transmisión": ("Transmisión", "Transmisión", "100238"),
    "Dirección": ("Dirección", "Dirección", "100012"),
    "Eléctrico": ("Sistema eléctrico", "Sistema eléctrico", "100010"),
    "Escape": ("Sistema de escape", "Sistema de escape", "100004"),
    "Herramientas": ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento", "100019"),
    "Otros": ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento", "100019"),
}

OUT_COLS = [
    "Handle",
    "Metafield: tecdoc.sistema [single_line_text_field]",
    "Metafield: tecdoc.subgrupo [single_line_text_field]",
    "Metafield: tecdoc.node_id [single_line_text_field]",
]

written, sin_match, vacios = 0, 0, 0
seen = set()
with open(CAT, encoding="utf-8") as f, open("catalogo_tecdoc_metafields.csv", "w", newline="", encoding="utf-8") as out:
    rd = csv.DictReader(f)
    wr = csv.DictWriter(out, fieldnames=OUT_COLS)
    wr.writeheader()
    for row in rd:
        h = row[COL_HANDLE].strip()
        g = (row.get(COL_GRUPO) or "").strip()
        s = (row.get(COL_SUB) or "").strip()
        if not h or h in seen:
            continue  # solo fila principal por producto (las de imagen repiten handle vacio en grupo)
        if not g:
            vacios += 1
            continue
        seen.add(h)
        key = (g, s if s else "(sin sub)") if (g == "Otros" and not s) else (g, s)
        tec = H.get((g, s)) or H.get(key) or FALLBACK_ESPECIFICO.get((g, s)) or FALLBACK_GRUPO.get(g)
        if not tec:
            sin_match += 1
            continue
        wr.writerow({
            OUT_COLS[0]: h,
            OUT_COLS[1]: tec[0],
            OUT_COLS[2]: tec[1],
            OUT_COLS[3]: tec[2],
        })
        written += 1

print(f"Productos con metafields TecDoc escritos: {written}")
print(f"Filas sin grupo (continuacion/imagen): {vacios}")
print(f"Productos sin match en homologacion: {sin_match}")
print("Salida: catalogo_tecdoc_metafields.csv")
