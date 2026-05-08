"""Elimina filas cuyo Id no aparece en urls.csv (productos sin fotos en R2)."""
import csv
import os
import sys
from pathlib import Path

csv.field_size_limit(2**31 - 1)

DIR = Path(__file__).parent
URLS_PATH = DIR.parent / "urls.csv"

# Set de IDs con fotos
ids_con_fotos = set()
with URLS_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ids_con_fotos.add(row["folder"])

print(f"IDs con fotos en R2: {len(ids_con_fotos)}\n")

total_kept = 0
total_removed = 0
for csv_path in sorted(DIR.glob("*.csv")):
    tmp_path = csv_path.with_suffix(".csv.tmp")
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as fin:
            reader = csv.reader(fin)
            header = next(reader)
            try:
                id_idx = header.index("Id")
            except ValueError:
                print(f"{csv_path.name}: SIN columna 'Id' - skip")
                continue

            kept = 0
            removed = 0
            with tmp_path.open("w", encoding="utf-8", newline="") as fout:
                writer = csv.writer(fout)
                writer.writerow(header)
                for row in reader:
                    if len(row) <= id_idx:
                        removed += 1
                        continue
                    if row[id_idx] in ids_con_fotos:
                        writer.writerow(row)
                        kept += 1
                    else:
                        removed += 1

        os.replace(tmp_path, csv_path)
        total_kept += kept
        total_removed += removed
        print(f"{csv_path.name}: kept={kept}, removed={removed}")
    except PermissionError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        print(f"{csv_path.name}: LOCKED - skipped ({e})")

print(f"\nTOTAL: kept={total_kept}, removed={total_removed}")
