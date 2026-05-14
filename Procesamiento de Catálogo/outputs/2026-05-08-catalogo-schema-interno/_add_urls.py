"""Agrega columnas img1..imgN con las URLs de R2, segun urls.csv (match por Id)."""
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(2**31 - 1)

DIR = Path(__file__).parent
URLS_PATH = DIR.parent / "urls.csv"

# urls.csv -> dict[folder] = lista de URLs ordenadas por img_num
folder_imgs = defaultdict(list)
with URLS_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        folder_imgs[row["folder"]].append((int(row["img_num"]), row["url"]))

for folder, items in folder_imgs.items():
    items.sort(key=lambda x: x[0])
    folder_imgs[folder] = [url for _, url in items]

max_imgs = max(len(v) for v in folder_imgs.values())
print(f"Maximo de imgs por producto: {max_imgs}\n")

img_cols = [f"img{i}" for i in range(1, max_imgs + 1)]

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

            # Si ya existen columnas img*, las quitamos primero
            existing_img_cols = {c for c in header if c.startswith("img") and c[3:].isdigit()}
            keep_idx = [i for i, c in enumerate(header) if c not in existing_img_cols]
            base_header = [header[i] for i in keep_idx]
            new_header = base_header + img_cols

            kept = 0
            with_imgs = 0
            with tmp_path.open("w", encoding="utf-8", newline="") as fout:
                writer = csv.writer(fout)
                writer.writerow(new_header)
                for row in reader:
                    if len(row) < len(header):
                        row = row + [""] * (len(header) - len(row))
                    base = [row[i] for i in keep_idx]
                    pid = row[id_idx]
                    urls = folder_imgs.get(pid, [])
                    if urls:
                        with_imgs += 1
                    img_vals = urls + [""] * (max_imgs - len(urls))
                    writer.writerow(base + img_vals)
                    kept += 1

        os.replace(tmp_path, csv_path)
        print(f"{csv_path.name}: filas={kept}, con_imgs={with_imgs}, cols img1..img{max_imgs}")
    except PermissionError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        print(f"{csv_path.name}: LOCKED - skipped ({e})")
