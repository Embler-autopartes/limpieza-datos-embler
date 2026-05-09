"""
Actualiza UNICAMENTE las imagenes del folder final-shopify-sitio-terminado-mayo
con las URLs limpias del catalogo R2 actual (urls.csv) — sin tocar nada mas.

- Match: ML ID extraido del Image Src antiguo de cada producto.
- Productos sin match en urls.csv (foto eliminada): se eliminan del CSV.
- Filas multi-imagen de Shopify (Handle + Image Src + Image Position) se regeneran.

Salida: final-shopify-sitio-terminado-mayo-actualizado/<categoria>.csv
"""
import csv, os, re, sys
from collections import defaultdict, Counter
from pathlib import Path

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "final-shopify-sitio-terminado-mayo"
OUT_DIR = ROOT / "final-shopify-sitio-terminado-mayo-actualizado"
URLS_CSV = ROOT / "urls.csv"

ID_RE = re.compile(r"r2\.dev/(MLM\d+)(?:-\w+)?/")


def load_urls():
    folder_urls = defaultdict(list)
    with URLS_CSV.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            folder_urls[row["folder"]].append((int(row["img_num"]), row["url"]))
    for k in folder_urls:
        folder_urls[k].sort()
        folder_urls[k] = [u for _, u in folder_urls[k]]
    return folder_urls


def process(src_path, dst_path, folder_urls, stats):
    with src_path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    fidx = {h: i for i, h in enumerate(header)}
    h_handle = fidx["Handle"]
    h_title = fidx["Title"]
    h_img = fidx["Image Src"]
    h_pos = fidx["Image Position"]

    # Agrupar filas por producto (parent + sus filas de imagen siguientes)
    products = []
    current = None
    for row in rows:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        if row[h_title].strip():
            if current:
                products.append(current)
            current = {"parent": row, "extras": []}
        else:
            if current is None:
                continue  # fila huerfana al inicio
            current["extras"].append(row)
    if current:
        products.append(current)

    out_rows = []
    kept = 0
    dropped = 0
    for prod in products:
        parent = prod["parent"]
        old_img = parent[h_img].strip()
        m = ID_RE.search(old_img)
        ml_id = m.group(1) if m else None

        if not ml_id or ml_id not in folder_urls:
            dropped += 1
            stats["dropped_by_file"][src_path.name] += 1
            continue

        new_urls = folder_urls[ml_id]
        kept += 1

        # Parent: sobrescribir Image Src y Image Position=1
        parent[h_img] = new_urls[0]
        parent[h_pos] = "1"
        out_rows.append(parent)

        # Filas adicionales: una por cada URL extra
        # Plantilla: filas vacias excepto Handle + Image Src + Image Position
        if len(new_urls) > 1:
            handle = parent[h_handle]
            for i, url in enumerate(new_urls[1:], start=2):
                extra = [""] * len(header)
                extra[h_handle] = handle
                extra[h_img] = url
                extra[h_pos] = str(i)
                out_rows.append(extra)

        stats["imgs_total"] += len(new_urls)

    with dst_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(out_rows)

    stats["products_kept"] += kept
    stats["products_dropped"] += dropped
    return kept, dropped, len(out_rows)


def main():
    print(f"Cargando urls.csv ...")
    folder_urls = load_urls()
    print(f"  {len(folder_urls)} folders en R2")
    print(f"\nSrc:  {SRC_DIR}")
    print(f"Dst:  {OUT_DIR}\n")

    OUT_DIR.mkdir(exist_ok=True)
    stats = {
        "products_kept": 0,
        "products_dropped": 0,
        "imgs_total": 0,
        "dropped_by_file": Counter(),
    }

    print(f"{'archivo':<35} {'kept':<7} {'dropped':<8} {'rows_out':<9}")
    print("-" * 65)
    for src in sorted(SRC_DIR.glob("*.csv")):
        dst = OUT_DIR / src.name
        k, d, n = process(src, dst, folder_urls, stats)
        print(f"{src.name:<35} {k:<7} {d:<8} {n:<9}")

    print("-" * 65)
    print(f"\n=== Resumen ===")
    print(f"Productos kept:    {stats['products_kept']}")
    print(f"Productos dropped: {stats['products_dropped']}")
    print(f"Imagenes totales:  {stats['imgs_total']}")
    print(f"Promedio imgs/prod: {stats['imgs_total']/max(stats['products_kept'],1):.2f}")

    if stats["dropped_by_file"]:
        print("\nDropped por archivo:")
        for f, n in stats["dropped_by_file"].most_common():
            print(f"  {n:>4}  {f}")


if __name__ == "__main__":
    main()
