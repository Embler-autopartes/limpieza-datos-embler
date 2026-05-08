"""
Genera CSVs Shopify-ready alineados al modelo del theme Embler (mayo 7 2026).

Cambios vs final-shopify-estructura-sitio/:
- Vacía Vendor, Product Category, Type y Tags (el theme no los usa).
- Agrega 3 metafields jerárquicos para colecciones automáticas:
    custom.marca       (BMW, Mercedes-Benz, Audi, ...)
    custom.grupo       (Motor, Suspensión, Dirección, Frenos, Enfriamiento, ...)
    custom.sub_grupo   (Bombas de Agua, Soportes de Motor, Bieletas, ...)
- Mantiene los demás metafields que ya usa el theme (Filtros, Características, etc.).

Salida: final-shopify-sitio-terminado-mayo/<categoria>.csv
"""
import csv, glob, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'final-shopify-estructura-sitio')
OUT_DIR = os.path.join(ROOT, 'final-shopify-sitio-terminado-mayo')
NEW_OUT_SOURCES = [
    os.path.join(ROOT, 'new-output/ml_con_match'),
    os.path.join(ROOT, 'new-output/ml_sin_match'),
]

# Display labels para Marca (kebab-case en data fuente -> nombre formal)
MARCA_DISPLAY = {
    'bmw': 'BMW',
    'mercedes-benz': 'Mercedes-Benz',
    'audi': 'Audi',
    'mini': 'Mini',
    'porsche': 'Porsche',
    'smart': 'Smart',
    'volkswagen': 'Volkswagen',
    'volvo': 'Volvo',
    'land-rover': 'Land Rover',
    'sprinter': 'Sprinter',
    'jaguar': 'Jaguar',
    'seat': 'Seat',
    'bentley': 'Bentley',
    'fiat': 'Fiat',
}

# Reglas de mapeo level3 (path ML) -> Grupo (modelo Embler)
L3_TO_GRUPO = {
    'Motor': 'Motor',
    'Filtros': 'Motor',
    'Inyección': 'Motor',
    'Encendido': 'Motor',
    'Poleas': 'Motor',
    'Frenos': 'Frenos',
    'Transmisión': 'Transmisión',
    'Carrocería': 'Colisión',
    'Iluminación': 'Colisión',
    'Refacciones de Exterior': 'Colisión',
    'Climatización': 'Enfriamiento',
    'Motoventiladores': 'Enfriamiento',
    'Sistemas de Refrigeración': 'Enfriamiento',
    'Tuning Exterior': 'Tuning',
    'Sistema Eléctrico': 'Eléctrico',
    'Instalaciones Eléctricas': 'Eléctrico',
    'Sensores': 'Eléctrico',
    'Cables y Conectores': 'Eléctrico',
    'Reproductores': 'Eléctrico',
    'Alarmas y Accesorios': 'Eléctrico',
    'Baterías': 'Eléctrico',
    'Herramientas para Baterías': 'Herramientas',
    'Caja de Herramientas': 'Herramientas',
    'Refacciones de Habitáculo': 'Accesorios',
    'Accesorios para el Exterior': 'Accesorios',
    'Accesorios para el Interior': 'Accesorios',
    'Accesorios de Exterior': 'Accesorios',
    'Cerraduras y Llaves': 'Accesorios',
    'Llaveros': 'Accesorios',
    'Piezas Cromadas': 'Accesorios',
    'Anticorrosivos para Autos': 'Accesorios',
    'Indumentaria Táctica': 'Accesorios',
    'Líquidos': 'Accesorios',
    'Escapes': 'Escape',
    'Chasis': 'Chasis',
    'Ejes': 'Chasis',
    'Bastidores': 'Chasis',
    'Ventanas y Sellos': 'Colisión',
    'Componentes de Seguridad': 'Accesorios',
    'Extracción': 'Otros',
    'Elevación': 'Herramientas',
    'Repuestos de Cabina': 'Accesorios',
    'Autos y Camionetas': 'Otros',
    'Motos': 'Otros',
    'Minería de Criptomonedas': 'Otros',
    'Figuras de Acción': 'Otros',
    'Otros': 'Otros',
}

# Para "Suspensión y Dirección" hacemos split en 3 grupos del menú
DIRECCION_SUBS = {
    'Terminales de Dirección', 'Cajas de Dirección', 'Mangueras Dirección Hidráulica',
    'Depósito Líquido Hidráulico', 'Sensores de Dirección',
    'Cajas de Dirección Hidráulica', 'Flector de Dirección', 'Kits de Dirección Hidráulica',
    'Terminales Interiores', 'Columnas de Dirección',
}


def split_susp_dir(sub_grupo):
    sub_lower = sub_grupo.lower()
    if 'aire' in sub_lower or sub_grupo == 'Compresores':
        return 'Suspensión de aire'
    if sub_grupo in DIRECCION_SUBS or 'dirección' in sub_lower:
        return 'Dirección'
    return 'Suspensión'


def derive_grupo_subgrupo(path):
    parts = [p.strip() for p in path.split('>')] if path else []
    if len(parts) < 3:
        return ('Otros', '')
    l3 = parts[2]
    sub = parts[-1] if len(parts) >= 4 else ''

    if l3 == 'Suspensión y Dirección':
        grupo = split_susp_dir(sub)
    else:
        grupo = L3_TO_GRUPO.get(l3, 'Otros')

    return (grupo, sub or l3)


def build_lookups():
    ml_id_to_path = {}
    sku_to_paths = collections.defaultdict(list)
    for d in NEW_OUT_SOURCES:
        for f in sorted(glob.glob(os.path.join(d, '*.csv'))):
            if f.endswith('_enriched.csv'):
                continue
            with open(f, encoding='utf-8') as fh:
                r = csv.DictReader(fh)
                for row in r:
                    ml_id = (row.get('Id') or '').strip()
                    sku = (row.get('SKU') or '').strip()
                    path = (row.get('Categoría') or '').strip()
                    if not path:
                        continue
                    if ml_id:
                        ml_id_to_path[ml_id] = path
                    if sku:
                        sku_to_paths[sku].append(path)
    return ml_id_to_path, sku_to_paths


ML_ID_RE = re.compile(r'(MLM\d+)')


def lookup_path(image_src, sku, ml_id_to_path, sku_to_paths):
    if image_src:
        m = ML_ID_RE.search(image_src)
        if m and m.group(1) in ml_id_to_path:
            return ml_id_to_path[m.group(1)]
    if sku and sku in sku_to_paths:
        # si todos los paths coinciden, usar; si no, tomar el más común
        paths = sku_to_paths[sku]
        if len(set(paths)) == 1:
            return paths[0]
        return collections.Counter(paths).most_common(1)[0][0]
    return ''


NEW_COLS = [
    'Marca (product.metafields.custom.marca)',
    'Grupo (product.metafields.custom.grupo)',
    'Sub Grupo (product.metafields.custom.sub_grupo)',
]
INSERT_AFTER = 'Características - Origen (product.metafields.page_info.detail_3)'
EMPTY_FIELDS = ['Vendor', 'Product Category', 'Type', 'Tags']


def process_file(src_path, dst_path, ml_id_to_path, sku_to_paths, stats):
    with open(src_path, encoding='utf-8') as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    insert_idx = header.index(INSERT_AFTER) + 1
    new_header = header[:insert_idx] + NEW_COLS + header[insert_idx:]
    fidx = {h: i for i, h in enumerate(header)}
    title_i = fidx['Title']
    sku_i = fidx['Variant SKU']
    img_i = fidx['Image Src']
    brand_i = fidx['Marca del auto (product.metafields.global.brand)']

    new_rows = []
    for row in rows:
        if len(row) < len(header):
            row = row + [''] * (len(header) - len(row))

        if row[title_i]:  # parent row
            stats['parent_rows'] += 1

            path = lookup_path(row[img_i], row[sku_i], ml_id_to_path, sku_to_paths)
            if path:
                stats['matched'] += 1
                grupo, sub_grupo = derive_grupo_subgrupo(path)
            else:
                stats['unmatched'] += 1
                grupo, sub_grupo = '', ''
                stats['unmatched_files'][os.path.basename(src_path)] += 1

            marca_kebab = (row[brand_i] or '').strip().lower()
            marca_display = MARCA_DISPLAY.get(marca_kebab, '')
            if not marca_display and marca_kebab:
                # fallback: capitalizar partes
                marca_display = ' '.join(p.capitalize() for p in marca_kebab.split('-'))

            if marca_display:
                stats['with_marca'] += 1
            if grupo:
                stats['with_grupo'] += 1
                stats['grupos'][grupo] += 1
            if sub_grupo:
                stats['with_subgrupo'] += 1
                stats['subgrupos'][sub_grupo] += 1

            for f_ in EMPTY_FIELDS:
                if f_ in fidx:
                    row[fidx[f_]] = ''

            new_meta = [marca_display, grupo, sub_grupo]
        else:
            new_meta = ['', '', '']

        new_rows.append(row[:insert_idx] + new_meta + row[insert_idx:])

    with open(dst_path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(new_header)
        w.writerows(new_rows)

    return len(new_rows)


def main():
    print(f"Source: {SRC_DIR}")
    print(f"Output: {OUT_DIR}")
    print()
    print("Construyendo lookups (ML ID + SKU)...")
    ml_id_to_path, sku_to_paths = build_lookups()
    print(f"  ML IDs: {len(ml_id_to_path)}  |  SKUs: {len(sku_to_paths)}")
    print()

    os.makedirs(OUT_DIR, exist_ok=True)

    stats = {
        'parent_rows': 0,
        'matched': 0,
        'unmatched': 0,
        'with_marca': 0,
        'with_grupo': 0,
        'with_subgrupo': 0,
        'grupos': collections.Counter(),
        'subgrupos': collections.Counter(),
        'unmatched_files': collections.Counter(),
    }

    files = sorted(glob.glob(os.path.join(SRC_DIR, '*.csv')))
    files = [f for f in files if not os.path.basename(f).startswith('muestra')]

    for src in files:
        name = os.path.basename(src)
        dst = os.path.join(OUT_DIR, name)
        n = process_file(src, dst, ml_id_to_path, sku_to_paths, stats)
        print(f"  ✓ {name}: {n} filas escritas")

    print()
    print("=== Stats ===")
    print(f"Parent rows (productos):    {stats['parent_rows']}")
    print(f"Matched a path ML:          {stats['matched']} ({stats['matched']/stats['parent_rows']*100:.1f}%)")
    print(f"Sin match:                  {stats['unmatched']}")
    print(f"Con Marca poblada:          {stats['with_marca']}")
    print(f"Con Grupo poblado:          {stats['with_grupo']}")
    print(f"Con Sub Grupo poblado:      {stats['with_subgrupo']}")

    print("\n=== Distribución de Grupos ===")
    for v, n in stats['grupos'].most_common():
        print(f"  {n:>5}  {v}")

    print(f"\n=== Sub Grupos únicos: {len(stats['subgrupos'])} ===")
    print("Top 25:")
    for v, n in stats['subgrupos'].most_common(25):
        print(f"  {n:>4}  {v}")

    if stats['unmatched_files']:
        print("\n=== Sin match por archivo ===")
        for v, n in stats['unmatched_files'].most_common():
            print(f"  {n:>4}  {v}")


if __name__ == '__main__':
    main()
