"""
Prepara un batch de filas de un CSV de categoria para procesamiento con IA.

Schema nuevo (CRUCE_ML_MC.xlsx) y estructura new-output/<hoja>/.

Pre-extrae deterministicamente las compatibilidades y el bloque "INCLUYE:" desde
la columna `descripcion` (no desde la columna `Compatibilidades` que esta incompleta),
para que el LLM no tenga que parsearlas: viene todo listo en el JSON del batch.

Uso:
    python scripts/02_preparar_batch_v2.py <categoria> <inicio> <cantidad> [<hoja>] [<output_root>]

Ejemplo:
    python scripts/02_preparar_batch_v2.py herramientas 0 18
    python scripts/02_preparar_batch_v2.py refacciones_motor 0 50 ml_con_match
    python scripts/02_preparar_batch_v2.py herramientas 0 18 ml_con_match new-output_v2

Output:
    Escribe <output_root>/<hoja>/<categoria>_batch.json con el batch listo para procesar.
"""

import csv
import json
import sys
import os

# Permite importar lib_compat_parser estando en la misma carpeta scripts/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_compat_parser import parsear_descripcion  # noqa: E402

# Indices del schema nuevo (hojas ML_*) -> nombre corto en el JSON
COLUMNAS_PROCESAMIENTO = {
    0: "id_ml",
    2: "categoria",
    3: "titulo",
    4: "descripcion",
    5: "precio",
    6: "sku",
    10: "garantia",
    13: "compatibilidades_ml_raw",  # columna ML cruda — NO usar como fuente principal
    14: "compatibilidades_restricciones",
    15: "marca",
    16: "numero_parte",
    18: "tipo_vehiculo",
    19: "origen",
    20: "codigo_oem",
    21: "modelo_atributo",
    22: "lado",
    24: "mc_sku_match",
    26: "mc_nombre_match",
    32: "tiene_match",
    33: "ambiguo",
    34: "marca_normalizada",
    35: "subcategoria",
    36: "categoria_archivo",
}

OUTPUT_ROOT_DEFAULT = "new-output"


def main():
    if len(sys.argv) not in (4, 5, 6):
        print(
            "Uso: python scripts/02_preparar_batch_v2.py <categoria> <inicio> <cantidad> [<hoja>] [<output_root>]"
        )
        print("Hoja default: ml_con_match  |  output_root default: new-output")
        sys.exit(1)

    categoria = sys.argv[1]
    inicio = int(sys.argv[2])
    cantidad = int(sys.argv[3])
    hoja = sys.argv[4] if len(sys.argv) >= 5 else "ml_con_match"
    output_root = sys.argv[5] if len(sys.argv) == 6 else OUTPUT_ROOT_DEFAULT

    csv_path = os.path.join(output_root, hoja, f"{categoria}.csv")
    if not os.path.exists(csv_path):
        print(f"Error: No existe {csv_path}")
        hoja_dir = os.path.join(output_root, hoja)
        if os.path.isdir(hoja_dir):
            print(f"Categorias disponibles en {hoja}:")
            for f in sorted(os.listdir(hoja_dir)):
                if f.endswith(".csv") and "_enriched" not in f and "_batch" not in f:
                    print(f"  {f.replace('.csv', '')}")
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        todas_filas = list(reader)

    total = len(todas_filas)
    print(f"CSV: {csv_path} ({total} filas)")
    print(f"Batch: filas {inicio} a {min(inicio + cantidad, total) - 1}")

    batch_filas = todas_filas[inicio : inicio + cantidad]
    batch = []
    stats_compat = 0
    stats_incluye = 0

    for i, row in enumerate(batch_filas):
        producto = {"_fila_original": inicio + i}
        for col_idx, nombre in COLUMNAS_PROCESAMIENTO.items():
            if col_idx < len(row):
                producto[nombre] = row[col_idx].strip() if row[col_idx] else ""
            else:
                producto[nombre] = ""

        # Pre-parseo deterministico desde la descripcion
        parsed = parsear_descripcion(producto["descripcion"], producto["titulo"])
        producto["num_compatibilidades"] = parsed["num_vehiculos"]
        producto["marcas_vehiculo"] = parsed["marcas_vehiculo"]
        producto["caract_compatibilidad_propuesta"] = parsed["caract_compatibilidad"]
        producto["seccion_compatibilidades_propuesta"] = parsed["seccion_compatibilidades"]
        producto["incluye_texto"] = parsed["incluye_texto"]

        if parsed["num_vehiculos"] > 0:
            stats_compat += 1
        if parsed["incluye_texto"]:
            stats_incluye += 1

        batch.append(producto)

    # Indice de todos los productos para buscar relacionados
    indice = []
    for row in todas_filas:
        if len(row) > 36:
            indice.append(
                {
                    "sku": row[6].strip() if row[6] else "",
                    "titulo": row[3].strip()[:80] if row[3] else "",
                    "subcategoria": row[35].strip() if row[35] else "",
                    "marca_normalizada": row[34].strip() if row[34] else "",
                }
            )

    output = {
        "categoria": categoria,
        "hoja": hoja,
        "batch_inicio": inicio,
        "batch_cantidad": len(batch),
        "total_filas": total,
        "productos": batch,
        "indice_catalogo": indice,
    }

    output_path = os.path.join(output_root, hoja, f"{categoria}_batch.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Batch guardado en {output_path}")
    print(f"  Productos en batch: {len(batch)}")
    print(f"  Productos en indice: {len(indice)}")
    print(f"  Con compatibilidades parseadas: {stats_compat}/{len(batch)}")
    print(f"  Con bloque INCLUYE: {stats_incluye}/{len(batch)}")


if __name__ == "__main__":
    main()
