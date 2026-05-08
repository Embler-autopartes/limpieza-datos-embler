"""
Extrae las filas con Id_ML vacio (sin match en MercadoLibre) de todos los CSVs enriched.
Guarda en C:\\embler\\productos_sin_id_ml.csv con columna 'archivo_origen' al inicio.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ENRICHED_DIR = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\output\enriched")
OUT_FILE = Path(r"C:\embler\productos_sin_id_ml.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

ID_COL = "Id_ML"
parts = []
totales = []

for path in sorted(ENRICHED_DIR.glob("*.csv")):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    if ID_COL not in df.columns:
        continue
    mask = df[ID_COL].isna() | (df[ID_COL].astype(str).str.strip() == "")
    sin_id = df[mask].copy()
    sin_id.insert(0, "archivo_origen", path.name)
    parts.append(sin_id)
    totales.append((path.name, len(sin_id), len(df)))
    print(f"  {path.name}: {len(sin_id)} sin Id_ML / {len(df)} totales")

resultado = pd.concat(parts, ignore_index=True)
resultado.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

print(f"\nTotal filas exportadas: {len(resultado)}")
print(f"Archivo: {OUT_FILE}")
