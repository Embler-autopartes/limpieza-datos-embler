"""
Libreria de parsing deterministico para extraer datos de la columna `descripcion` de MercadoLibre:

  - Bloque "APLICA PARA LOS SIGUIENTES MODELOS:"  -> lista de vehiculos compatibles (la fuente
    correcta del catalogo de compatibilidad; la columna `Compatibilidades` viene incompleta).
  - Bloque "INCLUYE:"                              -> componentes que trae el producto si es kit/juego.

Importable desde 02_preparar_batch_v2.py para enriquecer cada batch antes de mandarlo al LLM,
y desde 04_corregir_enriched.py si se necesita re-procesar enriched antiguos.

Toda la logica es regex deterministica — el mismo input produce siempre el mismo output, sin LLM.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Regex para localizar los bloques dentro de la descripcion
# ---------------------------------------------------------------------------

END_MARKERS = (
    r'ENV[IÍ]OS?\s+A\b', r'EMBLER\s+AUTOPARTES', r'CALIDAD\s+ORIGINAL',
    r'GARANTIZADOS?\s+CONTRA', r'ESPECIALISTAS\s+EN', r'PARA\s+EVITARTE',
    r'MUY\s+IMPORTANTE', r'CONT[AÁ]CTANOS', r'PRECIO\s+POR\s+PIEZA',
    r'CAT[AÁ]LOGO', r'\*{2,}',
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


# ---------------------------------------------------------------------------
# Extractores de bloques
# ---------------------------------------------------------------------------

def extraer_bloque_compat(descripcion: str) -> str:
    if not descripcion:
        return ''
    m = RX_COMPAT_BLOCK.search(descripcion)
    if not m:
        return ''
    body = m.group('body')
    return re.sub(r'\s+', ' ', body).strip()


def extraer_incluye(descripcion: str) -> str:
    """Devuelve prosa limpia de lo que incluye el producto.

    No parsea en lista (las descripciones de ML rara vez separan items con comas);
    devuelve el bloque en sentence case preservando siglas tecnicas.
    """
    if not descripcion:
        return ''
    m = RX_INCLUYE.search(descripcion)
    if not m:
        return ''
    raw = re.sub(r'\s+', ' ', m.group('body')).strip().rstrip('.').strip(',').strip()
    if not raw or len(raw) > 600:
        return ''
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


# ---------------------------------------------------------------------------
# Parsing de cada vehiculo dentro del bloque
# ---------------------------------------------------------------------------

def normalizar_marca(token: str) -> str:
    return BRAND_LOOKUP.get(token.upper().strip(), '')


def split_vehiculos(bloque: str) -> list:
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
    palabras = s.split()
    out = []
    for w in palabras:
        up = w.upper()
        if re.match(r'^[A-Z]\d+[A-Z0-9]*$', up):
            out.append(up)
            continue
        if re.match(r'^\d+(?:\.\d+)?[A-Za-z]+$', w):
            m = re.match(r'^(\d+(?:\.\d+)?)([A-Za-z]+)$', w)
            if m:
                num, suf = m.group(1), m.group(2).lower()
                if len(suf) == 2 and suf in ('li', 'ci'):
                    suf = suf[0].upper() + suf[1:]
                out.append(num + suf)
                continue
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
    s = re.sub(r'\b(\d+)\s*cil\b', r'\1 cil', s, flags=re.IGNORECASE)
    return s


# ---------------------------------------------------------------------------
# Generadores de texto
# ---------------------------------------------------------------------------

def agrupar_por_serie(vehiculos: list) -> dict:
    grupos = defaultdict(list)
    for v in vehiculos:
        modelo = v['modelo']
        tokens = modelo.split()
        if not tokens:
            serie = modelo
        elif tokens[0].lower() in ('clase', 'serie'):
            serie = ' '.join(tokens[:2])
        else:
            serie = tokens[0]
        grupos[(v['brand'], serie)].append(v)
    return grupos


def generar_caract_compatibilidad(vehiculos: list, titulo: str = '') -> str:
    if not vehiculos:
        return ''
    grupos = agrupar_por_serie(vehiculos)
    partes = []
    for (brand, serie), items in grupos.items():
        modelos = []
        for v in items:
            m = v['modelo']
            if v['anios']:
                m = f"{m} ({v['anios']})"
            modelos.append(m)
        seen = set()
        unicos = [x for x in modelos if not (x.lower() in seen or seen.add(x.lower()))]
        partes.append(f"{brand} {serie}: " + ', '.join(unicos))
    parrafo = '. '.join(partes) + '.'
    parrafo = f'Aplica para: {parrafo}'
    if len(parrafo) > 900:
        parrafo = parrafo[:880].rsplit(',', 1)[0] + '... (lista completa en la sección de compatibilidades).'
    return parrafo


def generar_seccion_compatibilidades(vehiculos: list) -> str:
    """Lista completa, una linea por modelo."""
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


def marcas_desde_vehiculos(vehiculos: list) -> list:
    orden = ['BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Porsche', 'Volvo',
             'Mini', 'Land Rover', 'Jaguar', 'SEAT', 'Smart', 'Fiat',
             'Alfa Romeo', 'Bentley', 'Rolls-Royce']
    set_marcas = {v['brand'] for v in vehiculos}
    return [m for m in orden if m in set_marcas]


# ---------------------------------------------------------------------------
# API publica de alto nivel
# ---------------------------------------------------------------------------

def parsear_descripcion(descripcion: str, titulo: str = '') -> dict:
    """Parsea la descripcion ML y devuelve todos los datos derivados.

    Retorna un dict con:
      - bloque_compat: el texto crudo del bloque APLICA PARA (string vacio si no hay)
      - vehiculos: list[dict] con cada compatibilidad parseada
      - num_vehiculos: cantidad
      - marcas_vehiculo: list ordenada de marcas extraidas
      - caract_compatibilidad: parrafo agrupado por serie (para campo del mismo nombre)
      - seccion_compatibilidades: lista completa, una linea por modelo
      - incluye_texto: prosa del bloque INCLUYE (string vacio si no hay)
    """
    bloque = extraer_bloque_compat(descripcion)
    vehiculos = []
    if bloque:
        for entry in split_vehiculos(bloque):
            v = parse_vehiculo(entry)
            if v:
                vehiculos.append(v)
    return {
        'bloque_compat': bloque,
        'vehiculos': vehiculos,
        'num_vehiculos': len(vehiculos),
        'marcas_vehiculo': marcas_desde_vehiculos(vehiculos),
        'caract_compatibilidad': generar_caract_compatibilidad(vehiculos, titulo),
        'seccion_compatibilidades': generar_seccion_compatibilidades(vehiculos),
        'incluye_texto': extraer_incluye(descripcion),
    }
