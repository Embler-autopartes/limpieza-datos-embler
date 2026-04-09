"""
Prepara un batch de filas de un CSV de categoria para procesamiento con IA.
Extrae solo los campos relevantes y genera un JSON simplificado.

Uso:
    python scripts/02_preparar_batch.py <categoria> <inicio> <cantidad>

Ejemplo:
    python scripts/02_preparar_batch.py refacciones_motor 0 50

Output:
    Escribe output/<categoria>_batch.json con el batch listo para procesar.
    Incluye un indice de todos los productos para buscar relacionados.
"""

import csv
import json
import sys
import os

# Columnas a extraer para el procesamiento (indice -> nombre corto)
COLUMNAS_PROCESAMIENTO = {
    3: "nombre_tecnico",
    7: "unidad_venta",
    11: "id_ml",
    13: "categoria",
    14: "titulo",
    15: "descripcion",
    16: "precio",
    17: "sku",
    21: "garantia",
    24: "compatibilidades",
    25: "compatibilidades_restricciones",
    26: "marca",
    27: "numero_parte",
    29: "tipo_vehiculo",
    30: "origen",
    31: "codigo_oem",
    36: "marca_normalizada",
    37: "subcategoria",
}


def main():
    if len(sys.argv) != 4:
        print("Uso: python scripts/02_preparar_batch.py <categoria> <inicio> <cantidad>")
        print("Ejemplo: python scripts/02_preparar_batch.py refacciones_motor 0 50")
        sys.exit(1)

    categoria = sys.argv[1]
    inicio = int(sys.argv[2])
    cantidad = int(sys.argv[3])

    csv_path = f"output/{categoria}.csv"
    if not os.path.exists(csv_path):
        print(f"Error: No existe {csv_path}")
        print(f"Archivos disponibles:")
        for f in sorted(os.listdir("output")):
            if f.endswith(".csv") and "_enriched" not in f and "_batch" not in f:
                print(f"  {f.replace('.csv', '')}")
        sys.exit(1)

    # Leer CSV completo
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        todas_filas = list(reader)

    total = len(todas_filas)
    print(f"CSV: {csv_path} ({total} filas)")
    print(f"Batch: filas {inicio} a {min(inicio + cantidad, total) - 1}")

    # Extraer batch
    batch_filas = todas_filas[inicio : inicio + cantidad]
    batch = []

    for i, row in enumerate(batch_filas):
        producto = {"_fila_original": inicio + i}
        for col_idx, nombre in COLUMNAS_PROCESAMIENTO.items():
            if col_idx < len(row):
                producto[nombre] = row[col_idx].strip() if row[col_idx] else ""
            else:
                producto[nombre] = ""
        batch.append(producto)

    # Crear indice de todos los productos para buscar relacionados
    indice = []
    for row in todas_filas:
        if len(row) > 37:
            indice.append(
                {
                    "sku": row[17].strip() if row[17] else "",
                    "titulo": row[14].strip()[:80] if row[14] else "",
                    "subcategoria": row[37].strip() if row[37] else "",
                    "marca_normalizada": row[36].strip() if row[36] else "",
                }
            )

    output = {
        "categoria": categoria,
        "batch_inicio": inicio,
        "batch_cantidad": len(batch),
        "total_filas": total,
        "productos": batch,
        "indice_catalogo": indice,
    }

    output_path = f"output/{categoria}_batch.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Batch guardado en {output_path}")
    print(f"  Productos en batch: {len(batch)}")
    print(f"  Productos en indice: {len(indice)}")

    return output_path


if __name__ == "__main__":
    main()
