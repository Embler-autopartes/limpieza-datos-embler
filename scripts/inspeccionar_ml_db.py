"""
Inspecciona 'mercado libre db.xlsx' para entender su estructura
antes de hacer match por titulo con los enriched.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

XLSX = Path(r"C:\Users\Autom\OneDrive\Desktop\base con fotos\limpieza-datos-embler\mercado libre db.xlsx")

print(f"Archivo: {XLSX.name}")
print(f"Tamano: {XLSX.stat().st_size:,} bytes\n")

xl = pd.ExcelFile(XLSX, engine="openpyxl")
print(f"Hojas ({len(xl.sheet_names)}): {xl.sheet_names}\n")

for sheet in xl.sheet_names:
    print("=" * 80)
    print(f"HOJA: {sheet}")
    print("=" * 80)
    df = pd.read_excel(XLSX, sheet_name=sheet, dtype=str, engine="openpyxl")
    print(f"Filas: {len(df)}")
    print(f"Columnas ({len(df.columns)}):")
    for c in df.columns:
        non_null = df[c].notna().sum()
        sample = df[c].dropna().astype(str).head(2).tolist()
        sample = [s[:140] + ("..." if len(s) > 140 else "") for s in sample]
        print(f"  - {c!r}  ({non_null}/{len(df)} no vacios)")
        for s in sample:
            print(f"      ej: {s}")
    print()
