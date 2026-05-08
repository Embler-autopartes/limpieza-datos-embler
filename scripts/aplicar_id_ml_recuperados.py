"""
Aplica los Id_ML recuperados (unicos + desambiguados por cascada) a los enriched.
Genera nuevos CSVs en output/enriched_resolved/ sin modificar los originales.

Cascada de desambiguacion para los 516 ambiguos:
  1) SKU del enriched coincide con SKU del candidato en base madre
  2) Solo uno de los candidatos tiene carpeta en R2
  3) Estado del candidato no es 'Finalizada'  (preferir Activa/Pausada)
  4) Categoria_ML coincide en mayor prefijo con Categoria del candidato
  5) Lo que quede -> manual_review.csv
"""
import sys
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler")
ENRICHED_DIR = ROOT / "output" / "enriched"
OUT_DIR = ROOT / "output" / "enriched_resolved"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MASTER_DB = ROOT / "mercado libre db.xlsx"
IMAGES_DIR = Path(r"C:\fotos_ml_2026-04-23_1641")
LOG_DIR = Path(r"C:\embler")
LOG_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_REVIEW = LOG_DIR / "manual_review_ambiguos.csv"
REPORTE = LOG_DIR / "reporte_resolucion.txt"

ID_COL = "Id_ML"
TIT_COL = "Título_ML"

def norm(s):
    if s is None: return ""
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)

def cat_prefix_score(a, b):
    """Cuanto coincide el prefijo de categoria entre dos paths separados por '>'."""
    if not a or not b: return 0
    pa = [p.strip().lower() for p in str(a).split(">")]
    pb = [p.strip().lower() for p in str(b).split(">")]
    n = 0
    for x, y in zip(pa, pb):
        if x == y: n += 1
        else: break
    return n

# ----------------------------------------------------------------------
# Cargar base madre y construir indices
# ----------------------------------------------------------------------
print("Cargando base madre...")
master = pd.read_excel(MASTER_DB, sheet_name="Hoja1", dtype=str, engine="openpyxl")
master["__id"]  = master["Id"].fillna("").astype(str).str.strip()
master["__tit_exact"] = master["Título"].fillna("")
master["__tit_norm"]  = master["Título"].apply(norm)
master["__sku"] = master["SKU"].fillna("").astype(str).str.strip().str.upper()
master["__cat"] = master["Categoría"].fillna("")
master["__estado"] = master["Estado"].fillna("")

# Por Id rapido
by_id = {row["__id"]: row for _, row in master.iterrows()}

# Titulo exacto -> [ids]
exact_idx = defaultdict(list)
norm_idx  = defaultdict(list)
for _, r in master.iterrows():
    if r["__tit_exact"]: exact_idx[r["__tit_exact"]].append(r["__id"])
    if r["__tit_norm"]:  norm_idx[r["__tit_norm"]].append(r["__id"])

# Carpetas R2
print("Cargando carpetas R2...")
FOLDER_PATTERN = re.compile(r"^MLM\d+(-\w+)?$")
r2_folders = {p.name for p in IMAGES_DIR.iterdir() if p.is_dir() and FOLDER_PATTERN.match(p.name)}
print(f"  Carpetas R2 validas: {len(r2_folders)}")

# ----------------------------------------------------------------------
# Funciones de matching y desambiguacion
# ----------------------------------------------------------------------
def match_titulo(titulo_e, titulo_n):
    if titulo_e and titulo_e in exact_idx:
        return exact_idx[titulo_e], "titulo_exacto"
    if titulo_n and titulo_n in norm_idx:
        return norm_idx[titulo_n], "titulo_normalizado"
    return [], "sin_match"

def disambiguate(ids, sku_enriched, cat_enriched):
    """Aplica cascada. Devuelve (id_final, metodo, candidatos_finales) o (None, metodo, finales)."""
    method = ""
    cands = list(ids)

    # 1) SKU
    if sku_enriched:
        sku_match = [i for i in cands if by_id[i]["__sku"] == sku_enriched]
        if len(sku_match) == 1:
            return sku_match[0], "sku", sku_match
        if len(sku_match) > 1:
            cands = sku_match
            method = "sku_parcial"

    # 2) R2
    r2_match = [i for i in cands if i in r2_folders]
    if len(r2_match) == 1:
        return r2_match[0], "r2", r2_match
    if 1 < len(r2_match) < len(cands):
        cands = r2_match
        method = "r2_parcial"

    # 3) Estado: descartar Finalizada
    no_fin = [i for i in cands if "finalizada" not in by_id[i]["__estado"].lower()]
    if len(no_fin) == 1:
        return no_fin[0], "estado", no_fin
    if 1 < len(no_fin) < len(cands):
        cands = no_fin
        method = "estado_parcial"

    # 4) Categoria - mayor prefijo comun
    if cat_enriched:
        scored = [(cat_prefix_score(by_id[i]["__cat"], cat_enriched), i) for i in cands]
        max_score = max(s for s, _ in scored) if scored else 0
        best = [i for s, i in scored if s == max_score and s > 0]
        if len(best) == 1:
            return best[0], "categoria", best
        if 1 < len(best) < len(cands):
            cands = best
            method = "categoria_parcial"

    # 5) No se pudo desambiguar
    return None, method or "ambiguo", cands

# ----------------------------------------------------------------------
# Procesar cada enriched
# ----------------------------------------------------------------------
log_lines = []
def log(msg=""):
    print(msg)
    log_lines.append(msg)

log("=" * 70)
log("APLICACION DE Id_ML RECUPERADOS")
log("=" * 70)

global_counts = defaultdict(int)
manual_rows = []

for path in sorted(ENRICHED_DIR.glob("*.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    if ID_COL not in df.columns:
        continue

    # columnas de tracking
    df["id_ml_origen"] = ""
    df["id_ml_metodo"] = ""
    df.loc[df[ID_COL].notna() & (df[ID_COL].astype(str).str.strip() != ""), "id_ml_origen"] = "original"

    mask_vacio = df[ID_COL].isna() | (df[ID_COL].astype(str).str.strip() == "")
    log(f"\n{path.name}: {len(df)} filas, {mask_vacio.sum()} sin Id_ML")

    cnt = defaultdict(int)
    for idx in df[mask_vacio].index:
        row = df.loc[idx]
        titulo_e = str(row.get(TIT_COL, "") or "").strip()
        titulo_n = norm(titulo_e)
        sku = ""
        for c in ("SKU_ML", "SKU_MC"):
            v = row.get(c)
            if v is not None and str(v).strip() and str(v).strip().upper() not in ("NAN", "0"):
                sku = str(v).strip().upper()
                break
        cat = row.get("Categoría_ML", "") or ""

        ids, metodo_match = match_titulo(titulo_e, titulo_n)
        if not ids:
            cnt["sin_match"] += 1
            df.at[idx, "id_ml_metodo"] = "sin_match"
            continue

        if len(ids) == 1:
            df.at[idx, ID_COL] = ids[0]
            df.at[idx, "id_ml_origen"] = "recuperado"
            df.at[idx, "id_ml_metodo"] = f"{metodo_match}_unico"
            cnt[f"{metodo_match}_unico"] += 1
            continue

        # Ambiguo - cascada
        elegido, metodo_dis, cands_finales = disambiguate(ids, sku, cat)
        if elegido is not None:
            df.at[idx, ID_COL] = elegido
            df.at[idx, "id_ml_origen"] = "recuperado"
            df.at[idx, "id_ml_metodo"] = f"disamb_{metodo_dis}"
            cnt[f"disamb_{metodo_dis}"] += 1
        else:
            df.at[idx, "id_ml_metodo"] = f"manual_{metodo_dis}"
            cnt[f"manual_{metodo_dis}"] += 1
            manual_rows.append({
                "archivo_origen": path.name,
                "fila_origen": idx,
                TIT_COL: titulo_e,
                "SKU_enriched": sku,
                "Categoría_ML": cat,
                "candidatos_count_inicial": len(ids),
                "candidatos_iniciales": ";".join(ids),
                "candidatos_finales": ";".join(cands_finales),
                "metodo_parcial": metodo_dis,
            })

    for k, v in sorted(cnt.items()):
        log(f"  {k}: {v}")
        global_counts[k] += v

    out_path = OUT_DIR / path.name.replace("_enriched.csv", "_resolved.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path.name}")

# ----------------------------------------------------------------------
# Manual review CSV
# ----------------------------------------------------------------------
if manual_rows:
    pd.DataFrame(manual_rows).to_csv(MANUAL_REVIEW, index=False, encoding="utf-8-sig")
log(f"\nManual review: {len(manual_rows)} filas en {MANUAL_REVIEW}")

# ----------------------------------------------------------------------
# Resumen global
# ----------------------------------------------------------------------
log("\n" + "=" * 70)
log("RESUMEN GLOBAL")
log("=" * 70)
total_recuperado = sum(v for k, v in global_counts.items() if not k.startswith("manual") and k != "sin_match")
total_manual = sum(v for k, v in global_counts.items() if k.startswith("manual"))
total_sin = global_counts.get("sin_match", 0)
log(f"Productos sin Id_ML iniciales: 2460")
log(f"  Recuperados automaticamente: {total_recuperado}")
log(f"  Quedan para revision manual: {total_manual}")
log(f"  Sin match en base madre: {total_sin}")
log("\nDesglose por metodo:")
for k, v in sorted(global_counts.items()):
    log(f"  {k}: {v}")

REPORTE.write_text("\n".join(log_lines), encoding="utf-8")
print(f"\n[OK] Reporte: {REPORTE}")
print(f"[OK] Carpeta nueva: {OUT_DIR}")
