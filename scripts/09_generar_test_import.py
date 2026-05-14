"""
Genera un CSV de prueba con ~10 productos diversos del catalogo final
para validar el import a Shopify antes del batch completo.

Selecciona 1 producto por (Marca, Grupo) hasta tener 10, priorizando
las marcas y grupos con mas volumen.

Salida: outputs/YYYY-MM-DD-test-import-productos/test-shopify-import.csv
"""
import csv
from collections import defaultdict, Counter
from datetime import date
from pathlib import Path

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "outputs" / "2026-05-09-USAR-shopify-import"
OUT_DIR = ROOT / "outputs" / f"{date.today().isoformat()}-test-import-productos"
OUT_FILE = OUT_DIR / "test-shopify-import.csv"

COL_MARCA = "Marca (product.metafields.custom.marca)"
COL_GRUPO = "Grupo (product.metafields.custom.grupo)"
COL_SUB = "Sub Grupo (product.metafields.custom.sub_grupo)"

# Combinaciones objetivo (Marca, Grupo) — diversificadas
TARGET_PAIRS = [
    ("BMW", "Motor"),
    ("BMW", "Frenos"),
    ("Mercedes-Benz", "Suspensión"),
    ("Mercedes-Benz", "Motor"),
    ("Audi", "Frenos"),
    ("Mini", "Suspensión"),
    ("Volkswagen", "Motor"),
    ("Porsche", "Suspensión de aire"),
    ("Land Rover", "Suspensión"),
    ("Smart", "Motor"),
]


def load_all_rows():
    """Devuelve lista de (filename, header, [grupos_de_filas_por_producto])."""
    files = []
    for fp in sorted(SRC_DIR.glob("*.csv")):
        with fp.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        files.append((fp.name, header, rows))
    return files


def group_by_product(header, rows):
    """Agrupa filas multi-row de Shopify: parent (con Title) + filas de imagen."""
    fidx = {h: i for i, h in enumerate(header)}
    title_i = fidx["Title"]

    products = []
    current = None
    for row in rows:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        if row[title_i].strip():
            if current:
                products.append(current)
            current = [row]
        else:
            if current is not None:
                current.append(row)
    if current:
        products.append(current)
    return products


def main():
    print(f"Leyendo {SRC_DIR}")
    files = load_all_rows()

    # Buscamos coincidencias por (Marca, Grupo)
    chosen = {}  # (marca, grupo) -> (filename, header, product_rows)
    for fname, header, rows in files:
        fidx = {h: i for i, h in enumerate(header)}
        marca_i = fidx[COL_MARCA]
        grupo_i = fidx[COL_GRUPO]

        for prod_rows in group_by_product(header, rows):
            parent = prod_rows[0]
            marca = parent[marca_i].strip()
            grupo = parent[grupo_i].strip()
            key = (marca, grupo)
            if key in TARGET_PAIRS and key not in chosen:
                chosen[key] = (fname, header, prod_rows)
            if len(chosen) == len(TARGET_PAIRS):
                break
        if len(chosen) == len(TARGET_PAIRS):
            break

    # Header — usamos el del primer archivo (todos comparten schema)
    base_header = files[0][1]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_prods = 0
    n_rows = 0
    with OUT_FILE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(base_header)
        for key in TARGET_PAIRS:
            if key not in chosen:
                print(f"  [no encontrado] {key}")
                continue
            fname, header, prod_rows = chosen[key]
            assert header == base_header, f"schema mismatch en {fname}"
            for row in prod_rows:
                w.writerow(row)
                n_rows += 1
            n_prods += 1
            parent = prod_rows[0]
            fidx = {h: i for i, h in enumerate(header)}
            print(f"  ✓ {key[0]:<14} {key[1]:<20} {parent[fidx['Title']][:60]}")

    print(f"\nProductos: {n_prods}  filas (incl. multi-imagen): {n_rows}")
    print(f"Archivo:   {OUT_FILE}")


if __name__ == "__main__":
    main()
