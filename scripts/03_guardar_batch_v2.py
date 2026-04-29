"""
Guarda los resultados de un batch procesado en el CSV enriched.
Adaptado a la estructura new-output/<hoja>/.

Uso:
    python scripts/03_guardar_batch_v2.py <categoria> <resultados_json> [<hoja>] [<output_root>]

Ejemplo:
    python scripts/03_guardar_batch_v2.py herramientas new-output/ml_con_match/herramientas_batch_result.json
    python scripts/03_guardar_batch_v2.py herramientas new-output_v2/ml_con_match/herramientas_batch_result.json ml_con_match new-output_v2
"""

import csv
import json
import sys
import os

OUTPUT_ROOT_DEFAULT = "new-output"

COLUMNAS_NUEVAS = [
    "caract_marca",
    "caract_origen",
    "caract_tipo_vehiculo",
    "caract_compatibilidad",
    "seccion_descripcion",
    "seccion_compatibilidades",
    "seccion_antes_de_comprar",
    "seccion_envio",
    "seccion_devoluciones",
    "seccion_faq",
    "productos_relacionados",
    "shopify_handle",
    "shopify_title",
    "shopify_body_html",
    "shopify_product_category",
    "shopify_type",
    "shopify_tags",
    "shopify_published",
    "shopify_option1_name",
    "shopify_option1_value",
    "shopify_variant_sku",
    "shopify_variant_price",
    "shopify_variant_compare_price",
    "shopify_variant_weight",
    "shopify_variant_weight_unit",
    "shopify_image_src",
    "shopify_image_alt_text",
    "shopify_seo_title",
    "shopify_seo_description",
    "shopify_status",
    "revision_humana",
]


def main():
    if len(sys.argv) not in (3, 4, 5):
        print(
            "Uso: python scripts/03_guardar_batch_v2.py <categoria> <resultados_json> [<hoja>] [<output_root>]"
        )
        sys.exit(1)

    categoria = sys.argv[1]
    resultados_path = sys.argv[2]
    hoja = sys.argv[3] if len(sys.argv) >= 4 else "ml_con_match"
    output_root = sys.argv[4] if len(sys.argv) == 5 else OUTPUT_ROOT_DEFAULT

    csv_original = os.path.join(output_root, hoja, f"{categoria}.csv")
    csv_enriched = os.path.join(output_root, hoja, f"{categoria}_enriched.csv")

    if not os.path.exists(csv_original):
        print(f"Error: No existe {csv_original}")
        sys.exit(1)

    if not os.path.exists(resultados_path):
        print(f"Error: No existe {resultados_path}")
        sys.exit(1)

    with open(resultados_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = data.get("resultados", [])
    if not resultados:
        print("Error: No hay resultados en el JSON")
        sys.exit(1)

    resultados_por_fila = {}
    for r in resultados:
        fila = r.get("_fila_original")
        if fila is not None:
            resultados_por_fila[fila] = r

    print(f"Resultados cargados: {len(resultados_por_fila)} filas")

    csv_input = csv_enriched if os.path.exists(csv_enriched) else csv_original

    with open(csv_input, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        filas = list(reader)

    print(f"CSV leido: {csv_input} ({len(filas)} filas)")

    tiene_columnas_nuevas = COLUMNAS_NUEVAS[0] in headers

    if not tiene_columnas_nuevas:
        headers.extend(COLUMNAS_NUEVAS)
        for fila in filas:
            fila.extend([""] * len(COLUMNAS_NUEVAS))

    indices_nuevas = {}
    for col in COLUMNAS_NUEVAS:
        if col in headers:
            indices_nuevas[col] = headers.index(col)

    aplicados = 0
    for fila_idx, resultado in resultados_por_fila.items():
        if fila_idx < len(filas):
            for col in COLUMNAS_NUEVAS:
                if col in indices_nuevas and col in resultado:
                    valor = resultado[col]
                    if isinstance(valor, (dict, list)):
                        valor = json.dumps(valor, ensure_ascii=False)
                    filas[fila_idx][indices_nuevas[col]] = str(valor)
            aplicados += 1

    with open(csv_enriched, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(filas)

    print(f"Resultados aplicados: {aplicados} filas")
    print(f"CSV enriched guardado: {csv_enriched}")

    filas_con_datos = 0
    idx_desc = indices_nuevas.get("seccion_descripcion")
    if idx_desc is not None:
        for fila in filas:
            if len(fila) > idx_desc and fila[idx_desc].strip():
                filas_con_datos += 1

    print(f"Progreso total: {filas_con_datos}/{len(filas)} filas enriquecidas")


if __name__ == "__main__":
    main()
