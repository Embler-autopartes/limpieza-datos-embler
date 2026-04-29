"""
Reescribe los CSVs de final-con-imagenes/ para tener una imagen por columna:
img1, img2, ..., img20.

Agrupa carpetas R2 que pertenecen al mismo MLM base — por ejemplo
MLM704945564-178179707693/ y MLM704945564-178179707695/ son variantes del
mismo listing MLM704945564 y sus fotos se consolidan.

Los productos con menos imagenes dejan las columnas restantes vacias.
"""
import csv, json, os, re
from collections import defaultdict

csv.field_size_limit(1 << 28)

PUBLIC_BASE = "https://pub-7f4859912bd64708bc328970b6821976.r2.dev"
MAPEO_PATH = "new-output_v2/r2_mapeo.json"
OUTPUT_DIR = "final-con-imagenes"
MAX_IMGS = 20

IMG_COLS = [f"img{i}" for i in range(1, MAX_IMGS + 1)]
RX_BASE = re.compile(r"^(MLM\d+)")


def main():
    print(f"Cargando mapeo R2 desde {MAPEO_PATH}...")
    with open(MAPEO_PATH, encoding="utf-8") as f:
        mapeo_raw = json.load(f)

    # Agrupar variantes (MLMxxx-yyy y MLMxxx-zzz) bajo el MLM base
    mapeo = defaultdict(list)
    for folder, keys in mapeo_raw.items():
        m = RX_BASE.match(folder)
        base = m.group(1) if m else folder
        # Mantener orden estable por nombre completo de la key
        mapeo[base].extend(keys)
    for k in mapeo:
        mapeo[k].sort()
    print(f"  {len(mapeo_raw)} carpetas raw -> {len(mapeo)} IDs base (variantes consolidadas)")

    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(OUTPUT_DIR, fname)

        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = list(next(reader))
            rows = [list(row) for row in reader]

        idx_id = headers.index("Id")

        # Quitar shopify_image_src, shopify_image_extras y cualquier img* preexistente (idempotente)
        cols_to_remove = []
        for ci, col in enumerate(headers):
            if col == "shopify_image_src" or col == "shopify_image_extras" or col.startswith("img"):
                cols_to_remove.append(ci)
        # Eliminar de mayor a menor para no descalibrar indices
        for ci in sorted(cols_to_remove, reverse=True):
            for row in rows:
                if ci < len(row):
                    row.pop(ci)
            headers.pop(ci)

        # Agregar img1..imgN al final
        headers.extend(IMG_COLS)
        for row in rows:
            row.extend([""] * MAX_IMGS)

        idx_img = {col: headers.index(col) for col in IMG_COLS}
        idx_revision = headers.index("revision_humana")
        FLAG_SIN_FOTOS = "[INCLUIR] Sin fotos en R2"

        # Llenar y reconciliar flag
        n_con = 0
        n_sin = 0
        for row in rows:
            mlm_id = row[idx_id].strip() if idx_id < len(row) else ""
            keys = mapeo.get(mlm_id, []) if mlm_id else []
            if keys:
                for i, key in enumerate(keys[:MAX_IMGS]):
                    row[idx_img[f"img{i+1}"]] = f"{PUBLIC_BASE}/{key}"
                # remover flag si lo tenia (ahora si tiene fotos)
                rev_lines = [
                    l for l in row[idx_revision].split("\n")
                    if FLAG_SIN_FOTOS not in l
                ]
                row[idx_revision] = "\n".join(rev_lines)
                n_con += 1
            else:
                # asegurar flag presente
                rev = row[idx_revision]
                if FLAG_SIN_FOTOS not in rev:
                    flag = (
                        FLAG_SIN_FOTOS
                        + " — verificar publicacion del listing en MercadoLibre."
                    )
                    row[idx_revision] = (rev + "\n" + flag).strip("\n")
                n_sin += 1

        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        except PermissionError:
            print(f"  SKIP (locked): {fname} — cerrar archivo y reintentar")
            continue

        cat = fname.replace(".csv", "")
        print(f"  {cat:<28} {len(rows):>5} filas  con_fotos={n_con:>5}  sin_fotos={n_sin:>5}")

    print(f"\nOutput: {OUTPUT_DIR}/  (columnas img1..img{MAX_IMGS})")


if __name__ == "__main__":
    main()
