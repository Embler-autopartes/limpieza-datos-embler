"""
Genera archivos delta: productos que estan en final-listo-shopify (catalogo
actualizado tras el cruce con mercado libre db.xlsx) pero NO estan en
final-shopify-sitio-terminado-mayo. No los adapta — los exporta tal cual,
con el mismo schema de final-listo-shopify, para trabajarlos despues.

Salida: final-listo-shopify-delta-vs-mayo/<categoria>.csv
"""
import csv, os, re
from pathlib import Path

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).resolve().parent.parent
MAYO_DIR = ROOT / "final-shopify-sitio-terminado-mayo"
LISTO_DIR = ROOT / "final-listo-shopify"
OUT_DIR = ROOT / "final-listo-shopify-delta-vs-mayo"

ID_RE = re.compile(r"r2\.dev/(MLM\d+)(?:-\w+)?/")


def collect_mayo_ids():
    """Extrae el set de ML IDs presentes en mayo (desde Image Src)."""
    ids = set()
    for fp in sorted(MAYO_DIR.glob("*.csv")):
        with fp.open(encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                if not row.get("Title", "").strip():
                    continue
                img = row.get("Image Src", "").strip()
                m = ID_RE.search(img) if img else None
                if m:
                    ids.add(m.group(1))
    return ids


def main():
    print("Recolectando ML IDs en mayo...")
    mayo_ids = collect_mayo_ids()
    print(f"  {len(mayo_ids)} ML IDs en mayo\n")

    OUT_DIR.mkdir(exist_ok=True)

    print(f"{'archivo':<35} {'listo_total':<12} {'en_mayo':<9} {'delta':<8}")
    print("-" * 65)

    total_listo = 0
    total_in_mayo = 0
    total_delta = 0

    for src in sorted(LISTO_DIR.glob("*.csv")):
        with src.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            try:
                id_idx = header.index("Id")
            except ValueError:
                print(f"{src.name}: SIN columna 'Id' — skip")
                continue
            rows = list(reader)

        delta_rows = []
        in_mayo = 0
        for row in rows:
            if len(row) <= id_idx:
                continue
            ml_id = row[id_idx].strip()
            if ml_id in mayo_ids:
                in_mayo += 1
            else:
                delta_rows.append(row)

        dst = OUT_DIR / src.name
        with dst.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(delta_rows)

        print(f"{src.name:<35} {len(rows):<12} {in_mayo:<9} {len(delta_rows):<8}")
        total_listo += len(rows)
        total_in_mayo += in_mayo
        total_delta += len(delta_rows)

    print("-" * 65)
    print(f"{'TOTAL':<35} {total_listo:<12} {total_in_mayo:<9} {total_delta:<8}")
    print(f"\nDelta escrito en: {OUT_DIR}")


if __name__ == "__main__":
    main()
