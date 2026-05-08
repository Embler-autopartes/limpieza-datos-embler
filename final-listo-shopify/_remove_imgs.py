"""Elimina columnas img1..img20 de todos los CSVs en este directorio."""
import csv
import os
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize if os.name != "nt" else 2**31 - 1)

DIR = Path(__file__).parent
IMG_COLS = {f"img{i}" for i in range(1, 21)}

for csv_path in sorted(DIR.glob("*.csv")):
    tmp_path = csv_path.with_suffix(".csv.tmp")
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as fin:
            reader = csv.reader(fin)
            header = next(reader)
            if not any(col in IMG_COLS for col in header):
                print(f"{csv_path.name}: no img cols (skipping)")
                continue
            keep_idx = [i for i, col in enumerate(header) if col not in IMG_COLS]
            removed = [col for col in header if col in IMG_COLS]
            new_header = [header[i] for i in keep_idx]

            with tmp_path.open("w", encoding="utf-8", newline="") as fout:
                writer = csv.writer(fout)
                writer.writerow(new_header)
                row_count = 0
                for row in reader:
                    if len(row) < len(header):
                        row = row + [""] * (len(header) - len(row))
                    writer.writerow([row[i] for i in keep_idx])
                    row_count += 1

        os.replace(tmp_path, csv_path)
        print(f"{csv_path.name}: removed {len(removed)} cols, {row_count} rows kept")
    except PermissionError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        print(f"{csv_path.name}: LOCKED - skipped ({e})")

print("done")
