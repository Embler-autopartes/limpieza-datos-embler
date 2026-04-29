"""
Agrega URLs de imagenes desde Cloudflare R2 a los CSVs en final/.

Para cada producto (col Id = MLM_xxx):
- shopify_image_src      = URL de la imagen principal (img01)
- shopify_image_extras   = URLs de img02..imgN separadas por '|'
- shopify_image_alt_text = texto alt ya existente (no se toca)
- revision_humana        = se agrega flag '[INCLUIR] Sin fotos en R2' si no hay carpeta

Lee el mapeo previamente indexado en new-output_v2/r2_mapeo.json
(generado al explorar el bucket — evita re-listar 111K objetos cada corrida).

Output: final-con-imagenes/<categoria>.csv
"""
import csv, json, os, sys

csv.field_size_limit(1 << 28)

PUBLIC_BASE = "https://pub-7f4859912bd64708bc328970b6821976.r2.dev"
MAPEO_PATH = "new-output_v2/r2_mapeo.json"
INPUT_DIR = "final"
OUTPUT_DIR = "final-con-imagenes"


def main():
    print(f"Cargando mapeo R2 desde {MAPEO_PATH}...")
    with open(MAPEO_PATH, encoding="utf-8") as f:
        mapeo = json.load(f)
    print(f"  {len(mapeo)} carpetas en R2")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_filas = 0
    total_con_fotos = 0
    total_sin_fotos = 0

    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.endswith(".csv"):
            continue
        in_path = os.path.join(INPUT_DIR, fname)
        out_path = os.path.join(OUTPUT_DIR, fname)

        with open(in_path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

        # Indices
        idx_id = headers.index("Id")
        idx_img_src = headers.index("shopify_image_src")
        idx_revision = headers.index("revision_humana")

        # Agregar columna shopify_image_extras si no existe
        if "shopify_image_extras" not in headers:
            headers.append("shopify_image_extras")
            for row in rows:
                row.append("")
        idx_img_extras = headers.index("shopify_image_extras")

        n_con = 0
        n_sin = 0
        for row in rows:
            mlm_id = row[idx_id].strip()
            if not mlm_id:
                continue
            keys = mapeo.get(mlm_id)
            if keys:
                # keys ya viene ordenada (img01, img02, ...) por el orden lexicografico
                urls = [f"{PUBLIC_BASE}/{k}" for k in keys]
                row[idx_img_src] = urls[0]
                row[idx_img_extras] = "|".join(urls[1:]) if len(urls) > 1 else ""
                n_con += 1
            else:
                n_sin += 1
                # agregar flag al revision_humana si no esta ya
                rev = row[idx_revision]
                flag = "[INCLUIR] Sin fotos en R2 — verificar publicacion del listing en MercadoLibre."
                if flag not in rev:
                    row[idx_revision] = (rev + "\n" + flag).strip("\n")

        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        cat = fname.replace(".csv", "")
        print(f"  {cat:<28} {len(rows):>5} filas  con_fotos={n_con:>5} sin_fotos={n_sin:>5}")
        total_filas += len(rows)
        total_con_fotos += n_con
        total_sin_fotos += n_sin

    print()
    print(f"TOTAL: {total_filas} filas")
    print(f"  Con fotos en R2: {total_con_fotos} ({100*total_con_fotos//total_filas}%)")
    print(f"  Sin fotos en R2: {total_sin_fotos} ({100*total_sin_fotos//total_filas}%)")
    print(f"\nOutput: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
