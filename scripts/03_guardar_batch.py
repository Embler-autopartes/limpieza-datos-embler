"""
Guarda los resultados de un batch procesado en el CSV enriched.
Lee el CSV original y agrega/actualiza las 6 columnas nuevas.

Uso:
    python scripts/03_guardar_batch.py <categoria> <resultados_json>

Ejemplo:
    python scripts/03_guardar_batch.py refacciones_motor output/refacciones_motor_batch_result.json

El JSON de resultados debe tener esta estructura:
{
  "resultados": [
    {
      "_fila_original": 0,
      "caract_marca": "...",
      "caract_origen": "...",
      "caract_tipo_vehiculo": "...",
      "caract_compatibilidad": "...",
      "seccion_descripcion": "...",
      "seccion_antes_de_comprar": "...",
      "seccion_envio": "...",
      "seccion_faq": "...",
      "productos_relacionados": "...",
      "revision_humana": "..."
    },
    ...
  ]
}
"""

import csv
import json
import sys
import os

COLUMNAS_NUEVAS = [
    "caract_marca",
    "caract_origen",
    "caract_tipo_vehiculo",
    "caract_compatibilidad",
    "seccion_descripcion",
    "seccion_antes_de_comprar",
    "seccion_envio",
    "seccion_faq",
    "productos_relacionados",
    "revision_humana",
]


def main():
    if len(sys.argv) != 3:
        print(
            "Uso: python scripts/03_guardar_batch.py <categoria> <resultados_json>"
        )
        sys.exit(1)

    categoria = sys.argv[1]
    resultados_path = sys.argv[2]

    csv_original = f"output/{categoria}.csv"
    csv_enriched = f"output/{categoria}_enriched.csv"

    if not os.path.exists(csv_original):
        print(f"Error: No existe {csv_original}")
        sys.exit(1)

    if not os.path.exists(resultados_path):
        print(f"Error: No existe {resultados_path}")
        sys.exit(1)

    # Leer resultados
    with open(resultados_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = data.get("resultados", [])
    if not resultados:
        print("Error: No hay resultados en el JSON")
        sys.exit(1)

    # Indexar resultados por fila original
    resultados_por_fila = {}
    for r in resultados:
        fila = r.get("_fila_original")
        if fila is not None:
            resultados_por_fila[fila] = r

    print(f"Resultados cargados: {len(resultados_por_fila)} filas")

    # Leer CSV existente (enriched si ya existe, sino original)
    csv_input = csv_enriched if os.path.exists(csv_enriched) else csv_original

    with open(csv_input, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        filas = list(reader)

    print(f"CSV leido: {csv_input} ({len(filas)} filas)")

    # Verificar si ya tiene columnas nuevas
    tiene_columnas_nuevas = COLUMNAS_NUEVAS[0] in headers

    if not tiene_columnas_nuevas:
        headers.extend(COLUMNAS_NUEVAS)
        for fila in filas:
            fila.extend([""] * len(COLUMNAS_NUEVAS))

    # Encontrar indices de columnas nuevas
    indices_nuevas = {}
    for col in COLUMNAS_NUEVAS:
        if col in headers:
            indices_nuevas[col] = headers.index(col)

    # Aplicar resultados
    aplicados = 0
    for fila_idx, resultado in resultados_por_fila.items():
        if fila_idx < len(filas):
            for col in COLUMNAS_NUEVAS:
                if col in indices_nuevas and col in resultado:
                    valor = resultado[col]
                    # Si es dict o list, convertir a JSON string
                    if isinstance(valor, (dict, list)):
                        valor = json.dumps(valor, ensure_ascii=False)
                    filas[fila_idx][indices_nuevas[col]] = str(valor)
            aplicados += 1

    # Escribir CSV enriched
    with open(csv_enriched, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(filas)

    print(f"Resultados aplicados: {aplicados} filas")
    print(f"CSV enriched guardado: {csv_enriched}")

    # Estadisticas
    filas_con_datos = 0
    for fila in filas:
        if len(fila) > indices_nuevas.get("descripcion_ecommerce", 999):
            if fila[indices_nuevas["descripcion_ecommerce"]].strip():
                filas_con_datos += 1

    print(f"Progreso total: {filas_con_datos}/{len(filas)} filas enriquecidas")


if __name__ == "__main__":
    main()
