#!/usr/bin/env python3
"""Corrige compatibilidades y descripción de los CSVs enriched.

Motivacion (abril 2026): Migue reporto que el skill `procesar-datos` extrajo
compatibilidades desde la columna `Compatibilidades_ML` de MercadoLibre, que
es incompleta e incorrecta en muchos casos (en ML funciona como requisito
para publicar, no como catalogo fiel). La fuente correcta es el texto de
`Descripcion_ML`, bajo la seccion "APLICA PARA LOS SIGUIENTES MODELOS:".

Este script re-procesa los `*_enriched.csv` y sobreescribe:
 - caract_compatibilidad (parrafo agrupado por serie)
 - seccion_compatibilidades (NUEVA, lista completa, una linea por modelo)
 - seccion_descripcion (agrega "Qué incluye" si la descripcion original trae INCLUYE:)
 - shopify_body_html (regenera con nueva seccion de compatibilidades)
 - shopify_tags (recalculado desde el bloque de compatibilidades extraido)
 - shopify_seo_description (incluye modelos principales cuando hay datos)
 - revision_humana (agrega flag si no se extrajeron compatibilidades)

Uso:
    python3 scripts/04_corregir_enriched.py <categoria>
    python3 scripts/04_corregir_enriched.py all
    python3 scripts/04_corregir_enriched.py refacciones_motor --dry-run --sample 5
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys
from collections import defaultdict
from typing import Optional

csv.field_size_limit(sys.maxsize)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENRICHED_DIR = os.path.join(ROOT, 'output', 'enriched')
CORRECTED_DIR = os.path.join(ROOT, 'output', 'corrected')

# ---------------------------------------------------------------------------
# Extraccion de bloques desde Descripcion_ML
# ---------------------------------------------------------------------------
#
# Patron tipico de la descripcion de MercadoLibre:
#   "<resumen> ... INCLUYE: <componentes> ... MUY IMPORTANTE: ... APLICA PARA
#    LOS SIGUIENTES MODELOS: <lista de vehiculos> ENVIOS A CDMX ... EMBLER
#    AUTOPARTES EUROPEAS ..."
#
# Los marcadores de cierre del bloque de compatibilidades son consistentes.

END_MARKERS = (
    r'ENV[IÍ]OS?\s+A\b', r'EMBLER\s+AUTOPARTES', r'CALIDAD\s+ORIGINAL',
    r'GARANTIZADOS?\s+CONTRA', r'ESPECIALISTAS\s+EN', r'PARA\s+EVITARTE',
    r'MUY\s+IMPORTANTE', r'CONT[AÁ]CTANOS', r'PRECIO\s+POR\s+PIEZA',
    r'CAT[AÁ]LOGO', r'\*{2,}'
)
END_ALT = '|'.join(END_MARKERS)

RX_COMPAT_BLOCK = re.compile(
    r'APLICA\s+(?:PARA\s+LOS\s+SIGUIENTES\s+MODELOS|SOLO\s+PARA|PARA)\s*[:.]?\s+'
    r'(?P<body>.*?)(?=(?:' + END_ALT + r')|\Z)',
    re.IGNORECASE | re.DOTALL,
)

RX_INCLUYE = re.compile(
    r'INCLUYE\s*[:.]\s*(?P<body>.*?)(?=(?:MUY\s+IMPORTANTE|APLICA\s+PARA|APLICA\s+SOLO|'
    + END_ALT + r')|\Z)',
    re.IGNORECASE | re.DOTALL,
)

# Marcas de vehiculo reconocidas (orden de especificidad: compuestas primero).
BRANDS_CANON = [
    ('MERCEDES BENZ', 'Mercedes-Benz'),
    ('MERCEDES-BENZ', 'Mercedes-Benz'),
    ('LAND ROVER', 'Land Rover'),
    ('LAND-ROVER', 'Land Rover'),
    ('ALFA ROMEO', 'Alfa Romeo'),
    ('ALFA-ROMEO', 'Alfa Romeo'),
    ('ROLLS ROYCE', 'Rolls-Royce'),
    ('ROLLS-ROYCE', 'Rolls-Royce'),
    ('MINI COOPER', 'Mini'),
    ('MERCEDES', 'Mercedes-Benz'),
    ('BMW', 'BMW'),
    ('AUDI', 'Audi'),
    ('VOLKSWAGEN', 'Volkswagen'),
    ('VW', 'Volkswagen'),
    ('PORSCHE', 'Porsche'),
    ('PORCHE', 'Porsche'),
    ('VOLVO', 'Volvo'),
    ('MINI', 'Mini'),
    ('JAGUAR', 'Jaguar'),
    ('SEAT', 'SEAT'),
    ('SMART', 'Smart'),
    ('FIAT', 'Fiat'),
    ('BENTLEY', 'Bentley'),
]
BRANDS_RX = '|'.join(re.escape(b[0]) for b in BRANDS_CANON)
BRAND_LOOKUP = dict(BRANDS_CANON)

RX_VEHICLE_START = re.compile(r'\b(?:' + BRANDS_RX + r')\b', re.IGNORECASE)
RX_ANIO = re.compile(
    r'(?P<anios>\d{4}(?:\s+AL\s+\d{4})?)'
    r'\s+(?P<motor>\d+\s+CILINDROS.*)',
    re.IGNORECASE,
)


def extraer_bloque_compat(descripcion: str) -> str:
    if not descripcion:
        return ''
    m = RX_COMPAT_BLOCK.search(descripcion)
    if not m:
        return ''
    body = m.group('body')
    body = re.sub(r'\s+', ' ', body).strip()
    return body


def extraer_incluye(descripcion: str) -> str:
    """Devuelve texto plano (prosa) de lo que incluye el producto.

    No intenta parsear en lista porque las descripciones de MercadoLibre
    rara vez separan items con comas (ej: 'JUNTA DE CABEZA SELLOS DE
    VALVULA JUNTAS DE ADMISION Y DE ESCAPE'). Devolvemos el bloque en
    sentence case para que suene natural dentro del parrafo descriptivo.
    """
    if not descripcion:
        return ''
    m = RX_INCLUYE.search(descripcion)
    if not m:
        return ''
    raw = re.sub(r'\s+', ' ', m.group('body')).strip().rstrip('.').strip(',').strip()
    if not raw or len(raw) > 600:
        return ''
    # Convertir a sentence case preservando siglas tecnicas; todo en minuscula
    # excepto siglas explicitas para evitar que MAYUSCULAS del original sobrevivan.
    SIGLAS = {'BMW', 'VW', 'AMG', 'OEM', 'VIN', 'PCV', 'EGR', 'ABS', 'GTI'}
    tokens = raw.split()
    out = []
    for t in tokens:
        stripped = re.sub(r'[^\w]', '', t).upper()
        if stripped in SIGLAS:
            out.append(t.upper())
        else:
            out.append(t.lower())
    txt = ' '.join(out).strip()
    return txt[0].upper() + txt[1:] if txt else ''


def normalizar_marca(token: str) -> str:
    return BRAND_LOOKUP.get(token.upper().strip(), '')


def split_vehiculos(bloque: str) -> list:
    """Separa el bloque de compatibilidades en entradas individuales."""
    if not bloque:
        return []
    matches = list(RX_VEHICLE_START.finditer(bloque))
    entries = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(bloque)
        chunk = bloque[start:end].strip(' .\t')
        chunk = re.sub(r'\s+', ' ', chunk)
        if chunk:
            entries.append(chunk)
    return entries


def parse_vehiculo(linea: str) -> Optional[dict]:
    m = RX_VEHICLE_START.match(linea)
    if not m:
        return None
    brand_raw = linea[m.start():m.end()]
    brand = normalizar_marca(brand_raw)
    if not brand:
        return None
    resto = linea[m.end():].strip()
    anio_match = RX_ANIO.search(resto)
    if anio_match:
        modelo = resto[:anio_match.start()].strip()
        anios = anio_match.group('anios').upper().replace(' AL ', '-')
        motor_raw = anio_match.group('motor')
        motor_raw = re.sub(r'\s+', ' ', motor_raw).strip()
        motor = _formatear_motor(motor_raw)
    else:
        modelo = resto
        anios = ''
        motor = ''
    return {
        'brand': brand,
        'modelo': _titulo_modelo(modelo),
        'anios': anios,
        'motor': motor,
        'raw': linea,
    }


def _titulo_modelo(s: str) -> str:
    if not s:
        return ''
    # Conserva tokens tipo X5, 550i, F10, N63, M Sport, 5.0i, xDrive35i.
    palabras = s.split()
    out = []
    for w in palabras:
        up = w.upper()
        low = w.lower()
        # Codigos tipo X5, Z4, F10, N63B44 -> mayus completa.
        if re.match(r'^[A-Z]\d+[A-Z0-9]*$', up):
            out.append(up)
            continue
        # Modelos numericos con sufijo minusculo: 550i, 335ci, 750Li, 5.0i.
        if re.match(r'^\d+(?:\.\d+)?[A-Za-z]+$', w):
            m = re.match(r'^(\d+(?:\.\d+)?)([A-Za-z]+)$', w)
            if m:
                num, suf = m.group(1), m.group(2).lower()
                # Preserva mayusculas especificas: Li, Ci, GT.
                if len(suf) == 2 and suf in ('li', 'ci'):
                    suf = suf[0].upper() + suf[1:]
                out.append(num + suf)
                continue
        # Siglas/abreviaciones conocidas.
        if up in ('BMW', 'VW', 'AMG', 'GTI', 'GTS', 'TDI', 'TFSI', 'TSI',
                  'RS', 'GT', 'SQ', 'M', 'X', 'Z', 'A', 'B', 'C', 'E', 'S'):
            out.append(up)
            continue
        out.append(w.capitalize())
    return ' '.join(out)


def _formatear_motor(s: str) -> str:
    s = s.replace('CILINDROS', 'cil').replace('Cilindros', 'cil')
    s = re.sub(r'(\d+(?:\.\d+)?)\s*LITROS', lambda m: f'{m.group(1)}L', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s).strip().rstrip('.').strip()
    low = s.lower()
    reemplazos = {
        'bi turbo': 'Bi-Turbo', 'biturbo': 'Bi-Turbo',
        'twin turbo': 'Twin-Turbo', 'scroll twin turbo': 'Scroll Twin-Turbo',
        'turbocargado': 'Turbo', 'turbocompresor': 'Turbo',
        'aspiracion natural': 'Aspiración natural',
        'aspiración natural': 'Aspiración natural',
    }
    for k, v in reemplazos.items():
        if k in low:
            s = re.sub(k, v, s, flags=re.IGNORECASE)
    # Normalizar "8 cil" → "V8" cuando sea comun
    s = re.sub(r'\b(\d+)\s*cil\b', r'\1 cil', s, flags=re.IGNORECASE)
    return s


def agrupar_por_serie(vehiculos: list) -> dict:
    """Agrupa por (brand, serie_base) para el parrafo resumen."""
    grupos = defaultdict(list)
    for v in vehiculos:
        modelo = v['modelo']
        # "550i Gran Turismo" -> serie "550i"
        # "X5 5.0i Premium" -> serie "X5"
        # "Clase C 250" -> serie "Clase C"
        tokens = modelo.split()
        if not tokens:
            serie = modelo
        elif tokens[0].lower() in ('clase', 'serie'):
            serie = ' '.join(tokens[:2])
        else:
            serie = tokens[0]
        grupos[(v['brand'], serie)].append(v)
    return grupos


# ---------------------------------------------------------------------------
# Generacion de texto
# ---------------------------------------------------------------------------

def generar_caract_compatibilidad(vehiculos: list, titulo: str) -> str:
    if not vehiculos:
        # Fallback: si el titulo menciona modelos, avisar que se debe verificar
        return (f'Compatible con los modelos mencionados en el título. '
                f'Confirma compatibilidad exacta con tu número de VIN antes de comprar.')
    grupos = agrupar_por_serie(vehiculos)
    partes = []
    for (brand, serie), items in grupos.items():
        modelos = []
        for v in items:
            m = v['modelo']
            if v['anios']:
                m = f"{m} ({v['anios']})"
            modelos.append(m)
        # Deduplicar manteniendo orden
        seen = set()
        unicos = [x for x in modelos if not (x.lower() in seen or seen.add(x.lower()))]
        partes.append(f"{brand} {serie}: " + ', '.join(unicos))
    parrafo = '. '.join(partes) + '.'
    parrafo = f'Aplica para: {parrafo}'
    # Truncar si es muy largo
    if len(parrafo) > 900:
        parrafo = parrafo[:880].rsplit(',', 1)[0] + '... (lista completa en Compatibilidades).'
    return parrafo


def generar_seccion_compatibilidades(vehiculos: list) -> str:
    """Lista completa, una linea por modelo. Se muestra tal cual en la ficha."""
    if not vehiculos:
        return ''
    lineas = []
    seen = set()
    for v in vehiculos:
        base = f"{v['brand']} {v['modelo']}".strip()
        if v['anios']:
            base += f" {v['anios']}"
        if v['motor']:
            base += f" — {v['motor']}"
        key = base.lower()
        if key in seen:
            continue
        seen.add(key)
        lineas.append(base)
    return '\n'.join(lineas)


def mejorar_descripcion(desc_actual: str, titulo: str, marca: str, garantia_txt: str,
                       incluye_texto: str, num_vehiculos: int) -> str:
    """Reescribe la seccion_descripcion con estructura mas rica.

    Estructura:
    - Parrafo 1: Qué es + resumen tecnico (reusa la descripcion actual sin la coletilla de marca).
    - Parrafo 2 (opcional): "Este producto incluye: ..." cuando la descripcion original lo lista.
    - Parrafo 3: Compatibilidad breve + marca (garantia solo si es positiva).
    """
    desc_actual = (desc_actual or '').strip()
    # Parrafo 1: toma lo que ya estaba, quitando ultimas oraciones redundantes
    # (frases tipo "Marca X, con garantia ..." para que no se duplique).
    primer = re.split(r'(?i)\n?marca\s+[^\n]+garant[ií]a', desc_actual)[0].strip()
    primer = primer or f'{titulo}. Refacción para vehículos europeos.'

    parrafos = [primer]

    if incluye_texto:
        parrafos.append(f'Este producto incluye: {incluye_texto}.')

    if num_vehiculos:
        compat_line = (f'Compatible con {num_vehiculos} configuraciones de vehículos europeos; '
                       f'revisa la sección Compatibilidades para el listado completo.')
    else:
        compat_line = ('Verifica la compatibilidad con tu número de VIN antes de comprar '
                       'para asegurar el ajuste correcto.')

    cierre_tokens = [compat_line]
    if marca:
        cierre_tokens.append(f'Marca {marca}.')
    gar_low = garantia_txt.lower()
    if garantia_txt and 'sin garant' not in gar_low and 'no aplica' not in gar_low:
        cierre_tokens.append(garantia_txt if garantia_txt.endswith('.') else garantia_txt + '.')
    parrafos.append(' '.join(cierre_tokens))

    return '\n\n'.join(p for p in parrafos if p.strip())


def marcas_desde_vehiculos(vehiculos: list) -> list:
    orden = ['BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Porsche', 'Volvo',
             'Mini', 'Land Rover', 'Jaguar', 'SEAT', 'Smart', 'Fiat',
             'Alfa Romeo', 'Bentley', 'Rolls-Royce']
    set_marcas = {v['brand'] for v in vehiculos}
    return [m for m in orden if m in set_marcas]


def generar_body_html(sec_desc: str, sec_compat: str, sec_antes: str,
                     sec_envio: str, sec_dev: str, faq: list) -> str:
    def parrafos(txt: str) -> str:
        if not txt:
            return ''
        out = []
        for bloque in re.split(r'\n\s*\n', txt.strip()):
            bloque = bloque.strip()
            if not bloque:
                continue
            if bloque.startswith('- ') or '\n- ' in bloque:
                # Lista
                items = [l[2:].strip() for l in bloque.splitlines() if l.strip().startswith('- ')]
                if items:
                    intro = bloque.split('\n', 1)[0]
                    if not intro.startswith('- '):
                        out.append(f'<p>{intro}</p>')
                    out.append('<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>')
                    continue
            out.append('<p>' + bloque.replace('\n', '<br>') + '</p>')
        return ''.join(out)

    compat_html = ''
    if sec_compat:
        items = [l.strip() for l in sec_compat.splitlines() if l.strip()]
        compat_html = ('<h2>Compatibilidades</h2>'
                       '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>')
    faq_html = ''
    if faq:
        faq_html = '<h2>Preguntas Frecuentes</h2>' + ''.join(
            f'<h3>{f.get("pregunta","")}</h3><p>{f.get("respuesta","")}</p>' for f in faq)

    partes = [
        '<h2>Descripción</h2>' + parrafos(sec_desc),
        compat_html,
        '<h2>Antes de Comprar</h2><p>' + (sec_antes or '') + '</p>',
        '<h2>Envío</h2><p>' + (sec_envio or '') + '</p>',
        '<h2>Política de Devolución</h2>' + parrafos(sec_dev or ''),
        faq_html,
    ]
    return ''.join(p for p in partes if p)


def generar_seo_description(titulo: str, marca: str, marcas_vehiculo: list,
                            vehiculos: list) -> str:
    # Pick up to 3 distinct series-model names.
    modelos = []
    seen = set()
    for v in vehiculos:
        key = f"{v['brand']} {v['modelo']}".lower()
        if key in seen:
            continue
        seen.add(key)
        modelos.append(f"{v['brand']} {v['modelo']}")
        if len(modelos) >= 3:
            break
    nombre = re.sub(r'\s*&\s*$', '', titulo).strip()
    nombre_corto = nombre[:60]
    if modelos:
        base = f"{nombre_corto} compatible con {', '.join(modelos)}. Envío inmediato."
    else:
        marcas_txt = ', '.join(marcas_vehiculo) if marcas_vehiculo else 'autos europeos'
        base = f"{nombre_corto} para {marcas_txt}. Marca {marca}. Envío inmediato."
    if len(base) > 155:
        base = base[:152].rstrip(', ') + '...'
    return base


# ---------------------------------------------------------------------------
# Pipeline por categoria
# ---------------------------------------------------------------------------

def procesar_categoria(categoria: str, dry_run: bool = False, sample: int = 0) -> dict:
    enriched_path = os.path.join(ENRICHED_DIR, f'{categoria}_enriched.csv')
    if not os.path.exists(enriched_path):
        raise FileNotFoundError(enriched_path)

    out_path = os.path.join(CORRECTED_DIR, f'{categoria}_corrected.csv')

    with open(enriched_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    # Agregar nueva columna si no existe
    if 'seccion_compatibilidades' not in fieldnames:
        idx = fieldnames.index('caract_compatibilidad') + 1 if 'caract_compatibilidad' in fieldnames else len(fieldnames)
        fieldnames.insert(idx, 'seccion_compatibilidades')

    stats = defaultdict(int)
    stats['total'] = len(rows)

    out_rows = []
    for i, row in enumerate(rows):
        if sample and i >= sample:
            out_rows.append(row)
            continue

        desc_original = row.get('Descripción_ML', '') or ''
        titulo = row.get('Título_ML', '') or row.get('shopify_title', '')

        bloque = extraer_bloque_compat(desc_original)
        vehiculos_raw = split_vehiculos(bloque)
        vehiculos = [v for v in (parse_vehiculo(l) for l in vehiculos_raw) if v]

        incluye_texto = extraer_incluye(desc_original)

        if vehiculos:
            stats['con_compatibilidades'] += 1
        else:
            stats['sin_compatibilidades'] += 1
        if incluye_texto:
            stats['con_incluye'] += 1

        # Nuevos valores
        sec_compat = generar_seccion_compatibilidades(vehiculos)
        caract_compat = generar_caract_compatibilidad(vehiculos, titulo)

        marca_prod = row.get('caract_marca', '') or row.get('marca_normalizada', '')
        garantia_original = row.get('Garantia_ML', '') or ''
        garantia_txt = garantia_original.strip() or 'Garantía contra defectos de fabricación.'
        if not garantia_txt.endswith('.'):
            garantia_txt += '.'

        sec_desc = mejorar_descripcion(
            row.get('seccion_descripcion', '') or '',
            titulo=titulo,
            marca=marca_prod,
            garantia_txt=garantia_txt,
            incluye_texto=incluye_texto,
            num_vehiculos=len(vehiculos),
        )

        # Tags: preferir marcas extraidas del bloque; fallback a tags actuales
        marcas_veh = marcas_desde_vehiculos(vehiculos)
        shopify_tags = ', '.join(marcas_veh) if marcas_veh else row.get('shopify_tags', '')

        # SEO description nueva
        seo_desc = generar_seo_description(titulo, marca_prod, marcas_veh, vehiculos)

        # FAQ: reusar si existe (viene como JSON string)
        import json as _json
        faq_raw = row.get('seccion_faq', '') or ''
        try:
            faq_list = _json.loads(faq_raw) if faq_raw.strip().startswith('[') else []
        except Exception:
            faq_list = []

        body_html = generar_body_html(
            sec_desc=sec_desc,
            sec_compat=sec_compat,
            sec_antes=row.get('seccion_antes_de_comprar', ''),
            sec_envio=row.get('seccion_envio', ''),
            sec_dev=row.get('seccion_devoluciones', ''),
            faq=faq_list,
        )

        # revision_humana: remover flags viejos de compatibilidad e agregar uno si sigue sin datos
        flags_old = (row.get('revision_humana', '') or '').split('\n')
        flags_new = [f for f in flags_old if f and 'Compatibilidad' not in f and 'compatibilidad' not in f]
        if not vehiculos:
            flags_new.insert(0, '[BUSCAR] Compatibilidad vehicular: no se pudo extraer de la descripción — revisar listing ML.')
        row['revision_humana'] = '\n'.join(flags_new)

        row['caract_compatibilidad'] = caract_compat
        row['seccion_compatibilidades'] = sec_compat
        row['seccion_descripcion'] = sec_desc
        row['shopify_tags'] = shopify_tags
        row['shopify_body_html'] = body_html
        row['shopify_seo_description'] = seo_desc

        out_rows.append(row)

    if dry_run:
        return dict(stats)

    os.makedirs(CORRECTED_DIR, exist_ok=True)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in out_rows:
            # Asegurar que todas las claves existan
            for fn in fieldnames:
                r.setdefault(fn, '')
            writer.writerow(r)

    stats['output'] = out_path
    return dict(stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('categoria', help='Nombre base (ej: refacciones_motor) o "all".')
    ap.add_argument('--dry-run', action='store_true',
                    help='Solo muestra estadisticas, no escribe archivos.')
    ap.add_argument('--sample', type=int, default=0,
                    help='Procesa solo las primeras N filas (las demas se copian tal cual).')
    args = ap.parse_args()

    if args.categoria == 'all':
        cats = sorted(
            os.path.basename(p).replace('_enriched.csv', '')
            for p in glob.glob(os.path.join(ENRICHED_DIR, '*_enriched.csv'))
        )
    else:
        cats = [args.categoria]

    totales = defaultdict(int)
    for cat in cats:
        print(f'\n=== {cat} ===')
        try:
            stats = procesar_categoria(cat, dry_run=args.dry_run, sample=args.sample)
        except FileNotFoundError as e:
            print(f'  [SKIP] no existe: {e}')
            continue
        for k, v in stats.items():
            if isinstance(v, int):
                totales[k] += v
        total = stats.get('total', 0) or 1
        pct_compat = 100 * stats.get('con_compatibilidades', 0) / total
        pct_incluye = 100 * stats.get('con_incluye', 0) / total
        print(f'  Filas: {total}')
        print(f'  Con compatibilidades extraidas: {stats.get("con_compatibilidades",0)} ({pct_compat:.1f}%)')
        print(f'  Sin compatibilidades:           {stats.get("sin_compatibilidades",0)}')
        print(f'  Con bloque INCLUYE detectado:   {stats.get("con_incluye",0)} ({pct_incluye:.1f}%)')
        if not args.dry_run and 'output' in stats:
            print(f'  Output: {stats["output"]}')

    if len(cats) > 1:
        print('\n=== TOTAL ===')
        for k, v in totales.items():
            print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
