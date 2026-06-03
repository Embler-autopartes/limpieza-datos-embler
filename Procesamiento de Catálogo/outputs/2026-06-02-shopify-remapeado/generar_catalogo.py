"""
Genera catalogo_completo.csv a partir de los 12 archivos YA_*.csv de USAR.
Alinea el schema exacto del export de Shopify, corrige mapeos incorrectos
y consolida todo en un solo archivo.

Correcciones aplicadas:
  1. Columnas reordenadas al orden del export de Shopify
  2. Columna extra 'breadcrumb' eliminada
  3. Columna 'Descripcion larga' agregada (vacia, como en el export)
  4. Vendor = "Embler Autopartes" (estaba vacio)
  5. Published = "true" (estaba "TRUE")
  6. Filtros - Refaccion = categoria de nivel superior (no el grupo)
     refacciones_* -> "Refacciones"
     accesorios    -> "Accesorios"
     tuning        -> "Tuning"
     herramientas  -> "Herramientas"
     otros         -> "Otros"
"""

import csv
import glob
import os

INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '2026-05-09-USAR-shopify-import')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'catalogo_completo.csv')

# Columnas finales en el orden exacto del export de Shopify (solo las que tienen valor)
FINAL_COLUMNS = [
    'Handle',
    'Title',
    'Body (HTML)',
    'Vendor',
    'Published',
    'Option1 Name',
    'Option1 Value',
    'Variant SKU',
    'Variant Grams',
    'Variant Inventory Tracker',
    'Variant Inventory Qty',
    'Variant Inventory Policy',
    'Variant Fulfillment Service',
    'Variant Price',
    'Variant Requires Shipping',
    'Variant Taxable',
    'Image Src',
    'Image Position',
    'Image Alt Text',
    'Gift Card',
    'SEO Title',
    'SEO Description',
    'Filtros - Refacción (product.metafields.filters.detail_1)',
    'Filtros - Año (product.metafields.filters.detail_2)',
    'Filtros - Marca de la refacción (product.metafields.filters.detail_3)',
    'Marca del auto (product.metafields.global.brand)',
    'Grupo (product.metafields.global.group)',
    'Información de envio (product.metafields.global.shipping)',
    'Sub grupo (product.metafields.global.sub_group)',
    'Marca (product.metafields.global._brand)',
    'Listado - Número de parte (product.metafields.list.detail_1)',
    'Descripción larga (product.metafields.page.descripcion_larga)',
    'Características - Marca (product.metafields.page_info.detail_1)',
    'Características - Tipo de vehículo (product.metafields.page_info.detail_2)',
    'Características - Origen (product.metafields.page_info.detail_3)',
    'Variant Weight Unit',
    'Status',
]

FILTRO_MAP = {
    'refacciones_motor':       'Refacciones',
    'refacciones_suspension':  'Refacciones',
    'refacciones_frenos':      'Refacciones',
    'refacciones_electrico':   'Refacciones',
    'refacciones_clima':       'Refacciones',
    'refacciones_carroceria':  'Refacciones',
    'refacciones_transmision': 'Refacciones',
    'refacciones_otros':       'Refacciones',
    'accesorios':              'Accesorios',
    'tuning':                  'Tuning',
    'herramientas':            'Herramientas',
    'otros':                   'Otros',
}

def get_category_key(filename):
    """Extrae la clave de categoria del nombre de archivo YA_xxx.csv o YA?_xxx.csv."""
    base = os.path.basename(filename)
    # Quitar prefijo YA_ o YA?_ o similar
    for prefix in ('YA_', 'YA?_'):
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
    else:
        # Cualquier prefijo YA + caracter + _
        if base.startswith('YA') and len(base) > 3 and base[3] == '_':
            base = base[4:]
    return base.replace('.csv', '')


def fix_row(row, filtro_top_level):
    """Devuelve un dict con exactamente FINAL_COLUMNS y los valores corregidos."""
    out = {col: '' for col in FINAL_COLUMNS}

    for col in FINAL_COLUMNS:
        if col in row:
            out[col] = row[col]

    # Las filas de continuacion (imagenes extra) solo tienen Handle + imagen.
    # Se distinguen porque no tienen Title ni Variant SKU.
    is_product_row = bool(out.get('Title', '').strip() or out.get('Variant SKU', '').strip())

    # -- Correcciones (solo en fila principal del producto) --

    if is_product_row:
        # 1. Vendor
        if not out['Vendor'].strip():
            out['Vendor'] = 'Embler Autopartes'

        # 2. Published: normalizar a lowercase
        pub = out['Published'].strip()
        if pub.upper() == 'TRUE':
            out['Published'] = 'true'
        elif pub.upper() == 'FALSE':
            out['Published'] = 'false'

        # 3. Filtros - Refaccion: valor de nivel superior segun categoria del archivo
        out['Filtros - Refacción (product.metafields.filters.detail_1)'] = filtro_top_level

    # 4. Descripcion larga: siempre vacia (campo en schema pero no poblado)
    out['Descripción larga (product.metafields.page.descripcion_larga)'] = ''

    return out


def main():
    input_files = sorted(
        glob.glob(os.path.join(INPUT_DIR, 'YA_*.csv')) +
        glob.glob(os.path.join(INPUT_DIR, 'YA?_*.csv'))
    )

    if not input_files:
        print(f"ERROR: No se encontraron archivos YA_*.csv en {INPUT_DIR}")
        return

    total_rows = 0

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=FINAL_COLUMNS)
        writer.writeheader()

        for filepath in input_files:
            cat_key = get_category_key(filepath)
            filtro_value = FILTRO_MAP.get(cat_key, cat_key.capitalize())

            with open(filepath, encoding='utf-8-sig') as in_fh:
                reader = csv.DictReader(in_fh)
                file_rows = 0
                for row in reader:
                    fixed = fix_row(row, filtro_value)
                    writer.writerow(fixed)
                    file_rows += 1

            total_rows += file_rows
            print(f"  {os.path.basename(filepath)} [{cat_key} -> '{filtro_value}']: {file_rows:,} filas")

    print(f"\nListo: {OUTPUT_FILE}")
    print(f"Total filas: {total_rows:,}")
    print(f"Columnas: {len(FINAL_COLUMNS)}")


if __name__ == '__main__':
    main()
