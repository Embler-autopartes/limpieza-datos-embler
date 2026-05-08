"""
Auditoria de cruce: CSVs enriched vs carpetas de imagenes en R2 (referencia local).
Solo lectura. Genera reporte en C:\\embler\\auditoria_cruce.txt
"""
import os
import re
import sys
import io
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ENRICHED_DIR = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\output\enriched")
IMAGES_DIR = Path(r"C:\fotos_ml_2026-04-23_1641")
OUT_DIR = Path(r"C:\embler")
OUT_FILE = OUT_DIR / "auditoria_cruce.txt"
URL_BASE = "https://pub-7f4859912bd64708bc328970b6821976.r2.dev"
ID_COL = "Id_ML"
ID_PATTERN = re.compile(r"^MLM\d+(-\w+)?$")
FOLDER_PATTERN = re.compile(r"^MLM\d+(-\w+)?$")
IMG_FILE_PATTERN = re.compile(r"^MLM\d+(-\w+)?_img\d+\.(jpg|jpeg|webp|png)$", re.IGNORECASE)

OUT_DIR.mkdir(parents=True, exist_ok=True)

buf = io.StringIO()

def log(msg=""):
    print(msg)
    buf.write(msg + "\n")

# ----------------------------------------------------------------------
log("=" * 80)
log("AUDITORIA DE CRUCE: CSVs ENRICHED vs CARPETAS DE IMAGENES")
log("Fecha de ejecucion: 2026-04-27")
log("=" * 80)

# Anomalia inicial: el usuario pidio .xlsx pero los archivos son .csv
log("\n[NOTA] El usuario pidio archivos .xlsx, pero la carpeta enriched contiene")
log("       solo archivos .csv. Se procesan los .csv existentes (12 archivos).")

# ----------------------------------------------------------------------
# PASO 1 - Inventario de archivos
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 1 - INVENTARIO DE ARCHIVOS")
log("=" * 80)

csv_files = sorted([p for p in ENRICHED_DIR.glob("*.csv")])
log(f"\nTotal de archivos CSV en enriched/: {len(csv_files)}")

dfs = {}
for path in csv_files:
    try:
        df = pd.read_csv(path, dtype=str, low_memory=False)
    except Exception as e:
        log(f"\n[ERROR] No se pudo leer {path.name}: {e}")
        continue
    dfs[path.name] = df
    log(f"\n--- {path.name} ---")
    log(f"  Hojas: 1 (CSV plano, hoja virtual unica)")
    log(f"  Filas: {len(df)}")
    log(f"  Columnas ({len(df.columns)}):")
    for col in df.columns:
        log(f"    - {col}")
    has_id = ID_COL in df.columns
    log(f"  Columna '{ID_COL}' presente: {has_id}")

# ----------------------------------------------------------------------
# PASO 2 - Validacion de IDs
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 2 - VALIDACION DE IDs (columna 'Id_ML')")
log("=" * 80)

per_file_ids = {}  # filename -> list of ids (raw, kept order)
for fname, df in dfs.items():
    log(f"\n--- {fname} ---")
    if ID_COL not in df.columns:
        log(f"  [ALERTA] No existe columna '{ID_COL}'. Se omite.")
        continue
    series = df[ID_COL]
    total = len(series)
    non_empty_mask = series.notna() & (series.astype(str).str.strip() != "")
    non_empty = non_empty_mask.sum()
    empty = total - non_empty
    values = series[non_empty_mask].astype(str).str.strip().tolist()
    bad = [v for v in values if not ID_PATTERN.match(v)]
    log(f"  No vacios: {non_empty}")
    log(f"  Vacios/NaN: {empty}")
    log(f"  IDs que NO matchean ^MLM\\d+(-\\w+)?$: {len(bad)}")
    if bad:
        log(f"  Ejemplos (max 5): {bad[:5]}")
    per_file_ids[fname] = values

# ----------------------------------------------------------------------
# PASO 3 - Consolidacion global
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 3 - CONSOLIDACION GLOBAL DE IDs")
log("=" * 80)

total_rows = sum(len(v) for v in per_file_ids.values())
all_ids_flat = []
id_to_files = defaultdict(list)  # id -> [(fname, count_in_file)]
for fname, ids in per_file_ids.items():
    cnt = Counter(ids)
    for _id, c in cnt.items():
        id_to_files[_id].append((fname, c))
    all_ids_flat.extend(ids)

unique_ids = set(all_ids_flat)
log(f"\nTotal de IDs no vacios sumados (todos los archivos): {total_rows}")
log(f"Total de IDs unicos: {len(unique_ids)}")

# Duplicados entre archivos diferentes
cross_dupes = {i: locs for i, locs in id_to_files.items() if len(locs) > 1}
log(f"\nIDs duplicados entre archivos diferentes: {len(cross_dupes)}")
if cross_dupes:
    log("  Primeros 20:")
    for _id, locs in list(cross_dupes.items())[:20]:
        loc_str = ", ".join(f"{f}({c})" for f, c in locs)
        log(f"    {_id}  ->  {loc_str}")

# Duplicados dentro del mismo archivo
log("\nIDs duplicados dentro del mismo archivo:")
for fname, ids in per_file_ids.items():
    cnt = Counter(ids)
    dups_in_file = [(i, c) for i, c in cnt.items() if c > 1]
    log(f"  {fname}: {len(dups_in_file)} IDs con duplicados")
    if dups_in_file:
        sample = dups_in_file[:5]
        log(f"    Ejemplos: {sample}")

# ----------------------------------------------------------------------
# PASO 4 - Comparacion de columnas entre archivos
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 4 - COMPARACION DE COLUMNAS ENTRE ARCHIVOS")
log("=" * 80)

cols_by_file = {fname: list(df.columns) for fname, df in dfs.items()}
all_cols = set()
for cols in cols_by_file.values():
    all_cols.update(cols)

# Columnas presentes en TODOS
common = set.intersection(*[set(c) for c in cols_by_file.values()]) if cols_by_file else set()
log(f"\nColumnas presentes en TODOS los archivos ({len(common)}):")
for c in sorted(common):
    log(f"  - {c}")

# Columnas que estan solo en algunos
partial = sorted(all_cols - common)
log(f"\nColumnas que estan solo en algunos archivos ({len(partial)}):")
for c in partial:
    files_with = [f for f, cols in cols_by_file.items() if c in cols]
    log(f"  - '{c}' en {len(files_with)}/{len(cols_by_file)}: {files_with}")

# ----------------------------------------------------------------------
# PASO 5 - Cruce con carpetas de imagenes
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 5 - CRUCE CON CARPETAS DE IMAGENES")
log("=" * 80)

# Listar solo CARPETAS que matchean MLM\d+ o MLM\d+-\w+
all_entries = list(IMAGES_DIR.iterdir())
img_folders = []
non_matching = []
for p in all_entries:
    if p.is_dir() and FOLDER_PATTERN.match(p.name):
        img_folders.append(p.name)
    elif p.is_dir():
        non_matching.append(p.name)

img_folder_set = set(img_folders)
log(f"\nTotal de carpetas en {IMAGES_DIR}: {sum(1 for p in all_entries if p.is_dir())}")
log(f"Carpetas con patron MLM<id> o MLM<id>-<var>: {len(img_folder_set)}")
log(f"Carpetas que NO matchean patron (ignoradas): {len(non_matching)}")
if non_matching[:5]:
    log(f"  Ejemplos ignoradas: {non_matching[:5]}")

# Variaciones (con guion)
variation_folders = {f for f in img_folder_set if "-" in f}
plain_folders = img_folder_set - variation_folders
log(f"\nCarpetas tipo MLM<id> (sin variacion): {len(plain_folders)}")
log(f"Carpetas tipo MLM<id>-<var> (con variacion): {len(variation_folders)}")

# Cruces
ids_with_folder = unique_ids & img_folder_set
ids_without_folder = unique_ids - img_folder_set
orphans = img_folder_set - unique_ids

log(f"\nIDs en CSV CON carpeta de imagenes (match exacto): {len(ids_with_folder)}")
log(f"IDs en CSV SIN carpeta de imagenes: {len(ids_without_folder)}")
log("  Primeros 20 IDs sin carpeta:")
for i, _id in enumerate(sorted(ids_without_folder)[:20]):
    log(f"    {_id}")

log(f"\nCarpetas huerfanas (sin producto en ningun CSV): {len(orphans)}")
log("  Primeros 20:")
for i, name in enumerate(sorted(orphans)[:20]):
    log(f"    {name}")

# Variaciones: cuantas aparecen como Id_ML completo
var_in_csv = variation_folders & unique_ids
var_not_in_csv = variation_folders - unique_ids
log(f"\nDe las {len(variation_folders)} carpetas con variacion (MLM<id>-<var>):")
log(f"  Aparecen como Id_ML EXACTO (con sufijo) en algun CSV: {len(var_in_csv)}")
log(f"  NO aparecen como Id_ML exacto: {len(var_not_in_csv)}")

# Tambien: el id base (sin sufijo) de las carpetas variacion - cuantos coinciden con un Id_ML del CSV
var_base_in_csv = 0
for f in variation_folders:
    base = f.split("-", 1)[0]
    if base in unique_ids:
        var_base_in_csv += 1
log(f"  Su parte base (antes del guion) coincide con un Id_ML del CSV: {var_base_in_csv}")

# ----------------------------------------------------------------------
# PASO 6 - Muestra de URLs generadas
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 6 - MUESTRA DE URLs GENERADAS")
log("=" * 80)

def list_imgs_in_folder(folder_name):
    folder = IMAGES_DIR / folder_name
    if not folder.is_dir():
        return []
    files = []
    for f in folder.iterdir():
        if f.is_file() and IMG_FILE_PATTERN.match(f.name):
            files.append(f.name)
    files.sort()
    return files

for fname, df in dfs.items():
    log(f"\n--- {fname} ---")
    if ID_COL not in df.columns:
        continue
    ids = df[ID_COL].dropna().astype(str).str.strip().tolist()
    shown = 0
    for _id in ids:
        if shown >= 3:
            break
        if _id in img_folder_set:
            files = list_imgs_in_folder(_id)
            log(f"  Id_ML: {_id}")
            log(f"    Imagenes en carpeta: {len(files)}")
            log(f"    Primeras 3 URLs:")
            for fn in files[:3]:
                log(f"      {URL_BASE}/{_id}/{fn}")
            shown += 1
    if shown == 0:
        log("  (Ningun ID con carpeta de imagenes encontrado en este archivo)")

# ----------------------------------------------------------------------
# PASO 7 - Resumen ejecutivo
# ----------------------------------------------------------------------
log("\n" + "=" * 80)
log("PASO 7 - RESUMEN EJECUTIVO")
log("=" * 80)

log(f"\nArchivos procesados (CSV): {len(dfs)}")
for fname in dfs:
    log(f"  - {fname}: {len(dfs[fname])} filas")

log(f"\nTotal filas sumadas: {sum(len(d) for d in dfs.values())}")
log(f"Total IDs unicos: {len(unique_ids)}")
log(f"  Con carpeta de imagenes: {len(ids_with_folder)}")
log(f"  Sin carpeta de imagenes: {len(ids_without_folder)}")
log(f"Carpetas huerfanas (sin producto): {len(orphans)}")

# Alertas
alerts = []
if any(len(per_file_ids.get(f, [])) != len(set(per_file_ids.get(f, []))) for f in per_file_ids):
    alerts.append("Hay IDs duplicados dentro de archivos individuales (ver Paso 3).")
if cross_dupes:
    alerts.append(f"{len(cross_dupes)} IDs aparecen en mas de un archivo (ver Paso 3).")
if partial:
    alerts.append(f"{len(partial)} columnas no estan en TODOS los archivos -> requiere mapeo si se concatenan.")
if len(ids_without_folder) > 0:
    alerts.append(f"{len(ids_without_folder)} productos NO tienen carpeta de imagenes asociada.")
if len(orphans) > 0:
    alerts.append(f"{len(orphans)} carpetas de imagenes son huerfanas (sin producto).")
if any(any(not ID_PATTERN.match(v) for v in vs) for vs in per_file_ids.values()):
    alerts.append("Hay IDs con formato fuera del patron MLM\\d+(-\\w+)?.")

log(f"\nAlertas / anomalias detectadas ({len(alerts)}):")
if alerts:
    for a in alerts:
        log(f"  [!] {a}")
else:
    log("  (ninguna)")

log("\n" + "=" * 80)
log("FIN DE AUDITORIA")
log("=" * 80)

# Guardar
OUT_FILE.write_text(buf.getvalue(), encoding="utf-8")
print(f"\n[OK] Reporte guardado en: {OUT_FILE}")
