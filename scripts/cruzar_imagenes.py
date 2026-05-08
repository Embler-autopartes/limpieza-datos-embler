"""
Cruza los enriched_resolved con las carpetas R2 para generar URLs de imagenes.
Excluye filas sin Id_ML.

Genera:
  output/with_images/{categoria}_with_images.csv   (con columnas de imagenes)
  C:\\embler\\reporte_cruce_imagenes.txt            (resumen)
"""
import sys
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler")
RESOLVED_DIR = ROOT / "output" / "enriched_resolved"
OUT_DIR = ROOT / "output" / "with_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = Path(r"C:\fotos_ml_2026-04-23_1641")
URL_BASE = "https://pub-7f4859912bd64708bc328970b6821976.r2.dev"
LOG = Path(r"C:\embler") / "reporte_cruce_imagenes.txt"

ID_COL = "Id_ML"
IMG_FILE_PATTERN = re.compile(r"^MLM\d+(-\w+)?_img\d+\.(jpg|jpeg|webp|png)$", re.IGNORECASE)

# ----------------------------------------------------------------------
# Indexar archivos por carpeta R2 (una sola pasada)
# ----------------------------------------------------------------------
print("Indexando carpetas R2...")
folder_files = {}  # carpeta -> [files ordenados]
for d in IMAGES_DIR.iterdir():
    if not d.is_dir():
        continue
    files = sorted([f.name for f in d.iterdir() if f.is_file() and IMG_FILE_PATTERN.match(f.name)])
    if files:
        folder_files[d.name] = files
print(f"  Carpetas con imagenes: {len(folder_files)}")

# ----------------------------------------------------------------------
# Procesar cada resolved
# ----------------------------------------------------------------------
log_lines = []
def log(m=""):
    print(m)
    log_lines.append(m)

log("=" * 70)
log("CRUCE DE IMAGENES")
log("=" * 70)

global_stats = defaultdict(int)

for path in sorted(RESOLVED_DIR.glob("*_resolved.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    n_in = len(df)

    # Excluir sin Id_ML
    mask_id = df[ID_COL].notna() & (df[ID_COL].astype(str).str.strip() != "")
    df = df[mask_id].copy()
    n_con_id = len(df)

    # Cruce con R2
    df["Id_ML"] = df["Id_ML"].astype(str).str.strip()
    df["imagenes_count"] = 0
    df["imagenes_urls"] = ""
    df["imagen_principal"] = ""

    con_imgs = 0
    sin_imgs = 0
    for idx, row in df.iterrows():
        _id = row["Id_ML"]
        files = folder_files.get(_id, [])
        if files:
            urls = [f"{URL_BASE}/{_id}/{fn}" for fn in files]
            df.at[idx, "imagenes_count"] = len(urls)
            df.at[idx, "imagenes_urls"] = ";".join(urls)
            df.at[idx, "imagen_principal"] = urls[0]
            # Tambien refrescar shopify_image_src si existe la columna
            if "shopify_image_src" in df.columns:
                df.at[idx, "shopify_image_src"] = urls[0]
            con_imgs += 1
        else:
            sin_imgs += 1

    out = OUT_DIR / path.name.replace("_resolved.csv", "_with_images.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")

    log(f"\n{path.name}")
    log(f"  Filas entrada:        {n_in}")
    log(f"  Excluidas (sin Id):   {n_in - n_con_id}")
    log(f"  Con Id_ML:            {n_con_id}")
    log(f"    Con imagenes en R2: {con_imgs}")
    log(f"    Sin imagenes en R2: {sin_imgs}")
    log(f"  -> {out.name}")

    global_stats["filas_entrada"] += n_in
    global_stats["excluidas_sin_id"] += (n_in - n_con_id)
    global_stats["con_id"] += n_con_id
    global_stats["con_imagenes"] += con_imgs
    global_stats["sin_imagenes"] += sin_imgs

# ----------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------
log("\n" + "=" * 70)
log("RESUMEN GLOBAL")
log("=" * 70)
log(f"Filas entrada totales:           {global_stats['filas_entrada']}")
log(f"  Excluidas (sin Id_ML):         {global_stats['excluidas_sin_id']}")
log(f"  Con Id_ML procesadas:          {global_stats['con_id']}")
log(f"    Con imagenes en R2:          {global_stats['con_imagenes']}")
log(f"    Sin imagenes en R2:          {global_stats['sin_imagenes']}")

LOG.write_text("\n".join(log_lines), encoding="utf-8")
print(f"\n[OK] Reporte: {LOG}")
print(f"[OK] Carpeta: {OUT_DIR}")
