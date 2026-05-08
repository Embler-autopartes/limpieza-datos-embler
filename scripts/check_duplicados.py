"""Verifica duplicados de Id_ML en output/with_images/ tras la recuperacion."""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\output\with_images")
ID_COL = "Id_ML"

# Recolectar
id_to_files = defaultdict(list)
per_file = {}
for path in sorted(DIR.glob("*_with_images.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    ids = df[df[ID_COL].notna() & (df[ID_COL].astype(str).str.strip() != "")][ID_COL].astype(str).str.strip().tolist()
    per_file[path.name] = ids
    for i in ids:
        id_to_files[i].append(path.name)

total = sum(len(v) for v in per_file.values())
unique = len(id_to_files)
print(f"Total filas con Id_ML: {total}")
print(f"Total Ids unicos: {unique}")
print(f"Duplicados (Ids repetidos): {total - unique}\n")

# Duplicados dentro del mismo archivo
print("Duplicados DENTRO del mismo archivo:")
for fname, ids in per_file.items():
    cnt = Counter(ids)
    dups = [(i, c) for i, c in cnt.items() if c > 1]
    if dups:
        print(f"  {fname}: {len(dups)} ids duplicados, {sum(c-1 for _, c in dups)} filas extra")
        for i, c in dups[:10]:
            print(f"    {i} x{c}")

# Duplicados entre archivos
print("\nDuplicados ENTRE archivos diferentes:")
cross = {i: locs for i, locs in id_to_files.items() if len(set(locs)) > 1}
print(f"  Total Ids que aparecen en >1 archivo: {len(cross)}")
for i, locs in list(cross.items())[:20]:
    cnt = Counter(locs)
    summary = ", ".join(f"{f}({c})" for f, c in cnt.items())
    print(f"    {i}  ->  {summary}")

# Tracking: distinguir si los dups vienen de recuperados o originales
print("\n\nDesglose por origen (id_ml_origen):")
all_dfs = {}
for path in sorted(DIR.glob("*_with_images.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df["__file"] = path.name
    all_dfs[path.name] = df
big = pd.concat(all_dfs.values(), ignore_index=True)
big = big[big[ID_COL].notna() & (big[ID_COL].astype(str).str.strip() != "")]
big[ID_COL] = big[ID_COL].astype(str).str.strip()
dup_mask = big[ID_COL].duplicated(keep=False)
dup_rows = big[dup_mask].sort_values(ID_COL)
print(f"Filas en grupos duplicados: {len(dup_rows)}")
print(f"  con id_ml_origen='original':   {(dup_rows['id_ml_origen']=='original').sum()}")
print(f"  con id_ml_origen='recuperado': {(dup_rows['id_ml_origen']=='recuperado').sum()}")
print(f"\nMuestra de duplicados (primeros 10 grupos):")
for _id, grp in list(dup_rows.groupby(ID_COL))[:10]:
    print(f"  {_id}:")
    for _, r in grp.iterrows():
        print(f"    [{r['__file']}]  origen={r['id_ml_origen']}  metodo={r['id_ml_metodo']}  titulo={str(r.get('Título_ML',''))[:80]}")
