"""Estadisticas rapidas de urls.csv vs los CSVs de final-listo-shopify."""
import csv
import sys
from pathlib import Path
from collections import defaultdict

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).parent
URLS_PATH = ROOT / "urls.csv"
SHOPIFY_DIR = ROOT / "final-listo-shopify"

# Cargar urls.csv
folder_imgs = defaultdict(list)
with URLS_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        folder_imgs[row["folder"]].append(row)

print(f"urls.csv:")
print(f"  productos (carpetas) con imgs: {len(folder_imgs)}")
print(f"  total URLs: {sum(len(v) for v in folder_imgs.values())}")
counts = [len(v) for v in folder_imgs.values()]
print(f"  imgs por producto: min={min(counts)} max={max(counts)} prom={sum(counts)/len(counts):.1f}")

# Cargar IDs de cada CSV de final-listo-shopify
print(f"\nCSVs de final-listo-shopify:")
total_rows = 0
total_with_imgs = 0
total_without_imgs = 0
for csv_path in sorted(SHOPIFY_DIR.glob("*.csv")):
    ids_in_csv = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids_in_csv.add(row["Id"])
    matched = ids_in_csv & set(folder_imgs.keys())
    unmatched = ids_in_csv - set(folder_imgs.keys())
    total_rows += len(ids_in_csv)
    total_with_imgs += len(matched)
    total_without_imgs += len(unmatched)
    print(f"  {csv_path.name}: {len(ids_in_csv)} productos, {len(matched)} con imgs ({100*len(matched)/len(ids_in_csv):.0f}%), {len(unmatched)} sin imgs")

print(f"\nTOTAL: {total_rows} productos, {total_with_imgs} con imgs ({100*total_with_imgs/total_rows:.0f}%), {total_without_imgs} sin imgs")
