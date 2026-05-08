"""
Recupera Id_ML faltantes de los enriched cruzando 'Título_ML' contra
'mercado libre db.xlsx' (Hoja1, columna 'Título').

NO modifica los enriched. Genera dos archivos en C:\\embler\\:
  - recuperados_id_ml.csv  (filas con match unico o multiple, con metadatos)
  - sin_match_titulo.csv   (filas que no encontraron match)
Y un reporte resumen impreso.
"""
import sys
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ENRICHED_DIR = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\output\enriched")
MASTER_DB = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\mercado libre db.xlsx")
OUT_DIR = Path(r"C:\embler")
OUT_RECUPERADOS = OUT_DIR / "recuperados_id_ml.csv"
OUT_SIN_MATCH = OUT_DIR / "sin_match_titulo.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)
ID_COL = "Id_ML"
TIT_COL = "Título_ML"

def norm(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    # Quitar acentos
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    # Colapsar espacios
    s = re.sub(r"\s+", " ", s)
    return s

# ----------------------------------------------------------------------
# 1) Cargar base madre
# ----------------------------------------------------------------------
print("Cargando base madre...")
master = pd.read_excel(MASTER_DB, sheet_name="Hoja1", dtype=str, engine="openpyxl")
print(f"  Filas: {len(master)}")
print(f"  Con Id no vacio: {master['Id'].notna().sum()}")
print(f"  Con Título no vacio: {master['Título'].notna().sum()}")

master["__tit_exact"] = master["Título"].fillna("")
master["__tit_norm"] = master["Título"].apply(norm)
master["__sku_norm"] = master["SKU"].fillna("").astype(str).str.strip().str.upper()

# Indices: titulo -> lista de Ids
exact_idx = defaultdict(list)
for i, row in master.iterrows():
    t = row["__tit_exact"]
    if t:
        exact_idx[t].append(row["Id"])

norm_idx = defaultdict(list)
for i, row in master.iterrows():
    t = row["__tit_norm"]
    if t:
        norm_idx[t].append(row["Id"])

sku_idx = defaultdict(list)
for i, row in master.iterrows():
    s = row["__sku_norm"]
    if s and s not in ("0", "NAN"):
        sku_idx[s].append(row["Id"])

print(f"  Titulos exactos unicos: {len(exact_idx)}")
print(f"  Titulos normalizados unicos: {len(norm_idx)}")
print(f"  SKUs unicos validos: {len(sku_idx)}")

# ----------------------------------------------------------------------
# 2) Recoger filas sin Id_ML de los enriched
# ----------------------------------------------------------------------
print("\nLeyendo enriched y filtrando sin Id_ML...")
faltantes = []
for path in sorted(ENRICHED_DIR.glob("*.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    if ID_COL not in df.columns:
        continue
    mask = df[ID_COL].isna() | (df[ID_COL].astype(str).str.strip() == "")
    sub = df.loc[mask].copy()
    sub.insert(0, "archivo_origen", path.name)
    sub.insert(1, "fila_origen", sub.index)
    faltantes.append(sub)
    print(f"  {path.name}: {len(sub)} sin Id_ML")
faltantes = pd.concat(faltantes, ignore_index=True)
print(f"  Total sin Id_ML: {len(faltantes)}")

# Cuantos tienen Titulo_ML poblado?
faltantes["__tit_exact"] = faltantes[TIT_COL].fillna("").astype(str).str.strip()
faltantes["__tit_norm"] = faltantes[TIT_COL].apply(norm)
con_titulo = (faltantes["__tit_exact"] != "").sum()
print(f"  De esos, con Titulo_ML poblado: {con_titulo}")
print(f"  Sin Titulo_ML: {len(faltantes) - con_titulo}")

# Tambien preparar SKU del enriched (probamos SKU_ML primero, luego SKU_MC)
def get_sku_norm(row):
    for col in ("SKU_ML", "SKU_MC"):
        v = row.get(col)
        if v is not None and str(v).strip() and str(v).strip().upper() not in ("NAN", "0"):
            return str(v).strip().upper()
    return ""
faltantes["__sku_norm"] = faltantes.apply(get_sku_norm, axis=1)
con_sku = (faltantes["__sku_norm"] != "").sum()
print(f"  Con SKU (ML o MC) utilizable: {con_sku}")

# ----------------------------------------------------------------------
# 3) Matching
# ----------------------------------------------------------------------
print("\nMatching por Titulo_ML (exact -> normalizado), fallback SKU...")
result_rows = []
estado_counts = defaultdict(int)

for idx, row in faltantes.iterrows():
    titulo_e = row["__tit_exact"]
    titulo_n = row["__tit_norm"]
    sku = row["__sku_norm"]

    metodo = ""
    ids_match = []

    if titulo_e and titulo_e in exact_idx:
        ids_match = exact_idx[titulo_e]
        metodo = "titulo_exacto"
    elif titulo_n and titulo_n in norm_idx:
        ids_match = norm_idx[titulo_n]
        metodo = "titulo_normalizado"
    elif sku and sku in sku_idx:
        ids_match = sku_idx[sku]
        metodo = "sku_fallback"
    else:
        metodo = "sin_match"

    if metodo == "sin_match":
        estado_counts["sin_match"] += 1
        result_rows.append({
            **row.drop(["__tit_exact", "__tit_norm", "__sku_norm"]).to_dict(),
            "match_metodo": "sin_match",
            "match_count": 0,
            "match_ids": "",
            "match_id_propuesto": "",
        })
    elif len(ids_match) == 1:
        estado_counts[f"{metodo}_unico"] += 1
        result_rows.append({
            **row.drop(["__tit_exact", "__tit_norm", "__sku_norm"]).to_dict(),
            "match_metodo": metodo,
            "match_count": 1,
            "match_ids": ids_match[0],
            "match_id_propuesto": ids_match[0],
        })
    else:
        estado_counts[f"{metodo}_ambiguo"] += 1
        result_rows.append({
            **row.drop(["__tit_exact", "__tit_norm", "__sku_norm"]).to_dict(),
            "match_metodo": metodo,
            "match_count": len(ids_match),
            "match_ids": ";".join(ids_match),
            "match_id_propuesto": "",  # ambiguo: no proponer
        })

resultado = pd.DataFrame(result_rows)

# ----------------------------------------------------------------------
# 4) Salidas
# ----------------------------------------------------------------------
con_match = resultado[resultado["match_metodo"] != "sin_match"].copy()
sin_match = resultado[resultado["match_metodo"] == "sin_match"].copy()

# Mover columnas match al inicio para revisar facil
def front(df, cols):
    return df[cols + [c for c in df.columns if c not in cols]]

front_cols = ["archivo_origen", "fila_origen", "match_metodo", "match_count", "match_id_propuesto", "match_ids", TIT_COL, "SKU_ML", "SKU_MC", "NOMBRE_ARTICULO_MC"]
front_cols = [c for c in front_cols if c in con_match.columns]
con_match = front(con_match, front_cols)
sin_match = front(sin_match, [c for c in front_cols if c in sin_match.columns])

con_match.to_csv(OUT_RECUPERADOS, index=False, encoding="utf-8-sig")
sin_match.to_csv(OUT_SIN_MATCH, index=False, encoding="utf-8-sig")

# ----------------------------------------------------------------------
# 5) Reporte
# ----------------------------------------------------------------------
print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print(f"Filas sin Id_ML procesadas: {len(faltantes)}")
print()
for k in sorted(estado_counts):
    print(f"  {k}: {estado_counts[k]}")
print()
total_unico = sum(v for k, v in estado_counts.items() if k.endswith("_unico"))
total_ambiguo = sum(v for k, v in estado_counts.items() if k.endswith("_ambiguo"))
sin = estado_counts.get("sin_match", 0)
print(f"  -> Match unico (Id propuesto auto): {total_unico}")
print(f"  -> Match ambiguo (varios Ids, requiere revision): {total_ambiguo}")
print(f"  -> Sin match: {sin}")
print()
print(f"Archivos generados:")
print(f"  {OUT_RECUPERADOS}  ({len(con_match)} filas)")
print(f"  {OUT_SIN_MATCH}  ({len(sin_match)} filas)")
