#!/usr/bin/env python3
"""
Construye la tabla de homologacion Embler -> TecDoc (match por nombre).
Entrada:  categorias_tecdoc.json (811 nodos)  +  _arbol_marca_grupo_subgrupo.json (15 grupos / 310 subgrupos)
Salida:   homologacion.csv  (grupo_embler, subgrupo_embler, prod, -> sistema_tecdoc, grupo_tecdoc,
                              subgrupo_tecdoc, tecdoc_node_id, confianza, needs_review)
Metodo determinista: normalizacion + diccionario de sinonimos MX->TecDoc + score por tokens.
"""
import json, csv, re, unicodedata
from collections import defaultdict

CATS = json.load(open("categorias_tecdoc.json", encoding="utf-8"))
ARBOL = json.load(open("../Procesamiento de Catálogo/outputs/_arbol_marca_grupo_subgrupo.json", encoding="utf-8"))

# ---------- aplanar arbol TecDoc a lista de nodos con su sistema raiz ----------
SISTEMAS = {s["shortCutId"]: s["shortCutName"] for s in CATS["shortcuts"]}
nodes = []  # {id,name,parent,sistema_root}
def walk(n, root_name):
    nodes.append({"id": n["id"], "name": n["name"], "root": root_name})
    for c in n["children"]:
        walk(c, root_name)
for r in CATS["arbol"]:
    walk(r, r["name"])  # la raiz del arbol de assembly groups es el sistema de facto

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)

def tokens(s):
    return set(norm(s).split())

# ---------- diccionario de sinonimos MX -> termino(s) TecDoc ----------
# clave: subgrupo o palabra MX (normalizada);  valor: terminos que aparecen en nombres TecDoc
SYN = {
    "balatas": "freno disco pastillas", "balatas de tambor": "freno tambor",
    "discos de freno": "freno disco", "discos de frenos": "freno disco",
    "calipers": "caliper", "sensor abs": "regulacion dinamica conduccion sensor",
    "sensor pastillas de freno": "indicador desgaste", "cilindros maestros": "cilindro principal freno",
    "bombas de vacio": "bomba vacio", "booster": "servofrenos", "cables de freno de mano": "freno mano cables",
    "marchas": "sistema arranque", "alternadores": "alternador",
    "bobinas de encendido": "bobina encendido", "bujias": "bujia encendido",
    "bujias de encendido": "bujia encendido", "bujias precalentadoras": "bujia precalentamiento",
    "cables de bujias": "cable encendido", "modulos de encendido": "modulo encendido",
    "bandas de accesorios": "correa poli v", "tensores poly v": "correa poli v polea",
    "poleas de distribucion": "polea distribucion", "cadenas de distribucion": "distribucion",
    "kit de distribucion": "correa dentada juego", "banda de distribucion": "correa dentada",
    "poleas": "polea", "poleas de ciguenal": "polea ciguenal accionamiento",
    "poleas de alternador": "rueda libre alternador", "tensores de cadena": "distribucion",
    "filtros de aceite": "filtro aceite", "filtros de aire": "filtro aire",
    "filtros de cabina": "filtro aire interior", "filtros de gasolina": "filtro combustible",
    "filtros de gasoil": "filtro combustible", "filtros hidraulicos": "filtro hidraulico",
    "kits de filtros": "filtro", "porta filtros": "filtro",
    "bombas de agua": "bomba agua", "termostato": "termostato", "radiadores de agua": "radiador agua",
    "manguera de radiador": "mangueras tuberias bridas refrigeracion", "tomas de agua": "mangueras refrigeracion",
    "deposito anticongelante": "anticongelante", "tapas de radiadores": "radiador",
    "ventilador de radiador": "ventilador", "motoventilador completo": "ventilador",
    "motoventiladores": "ventilador", "motor de motoventilador": "ventilador",
    "fan clutches": "ventilador", "radiadores de aceite": "radiador aceite",
    "soportes de motor": "suspension motor", "juntas": "juntas", "empaques": "juntas",
    "retenes": "juntas", "sellos": "juntas", "anillos de motor": "pistones",
    "bombas de aceite": "lubricacion bomba", "tapa de aceite": "lubricacion",
    "bayonetas nivel de aceite": "varilla nivel aceite", "carters completos": "lubricacion",
    "sensores de oxigeno": "sonda lambda", "sonda lambda": "sonda lambda",
    "sensor maf": "alimentacion aire sensor", "sensor map": "preparacion mezcla sensor",
    "sensor de posicion": "generador transmisor impulsos", "sensores de ciguenal": "generador transmisor impulsos",
    "sensor de temperatura": "interruptor sensor refrigeracion", "sensores de aceite": "interruptor presion aceite",
    "turbos": "compresor", "valvula egr": "depuracion gases escape", "valvulas egr": "depuracion gases escape",
    "valvula iac": "preparacion mezcla", "cuerpo de aceleracion": "preparacion mezcla",
    "inyectores": "preparacion mezcla", "bombas inyectoras": "preparacion mezcla",
    "multiples admision": "alimentacion aire", "colectores de admision": "alimentacion aire",
    "mangueras de admision": "alimentacion aire", "mangueras de intercooler": "alimentacion aire",
    "radiadores de intercooler": "refrigeracion aire", "bombas de combustible": "alimentacion combustible bomba",
    "arboles de levas": "distribucion", "engranes de arbol de levas": "distribucion",
    "punterias hidraulicas": "distribucion", "tapa de distribucion": "distribucion",
    "amortiguadores": "amortiguador", "bases de amortiguador": "soporte amortiguador columna",
    "topes de amortiguador": "soporte amortiguador", "brazo de suspension": "travesanos barras",
    "brazos de suspension": "travesanos barras", "horquillas de suspension": "travesanos barras",
    "bujes de suspension": "travesanos barras", "bieletas": "estabilizador piezas sujecion",
    "barras estabilizadoras": "estabilizador", "rotulas": "rotulas", "cubre polvo": "cubrepolvo",
    "baleros de rueda": "cubo cojinetes rueda", "mazas de ruedas": "cubo cojinetes rueda",
    "flechas completas": "eje transmision", "kits de suspension": "juego suspension completo",
    "resortes": "suspension muelle", "barras de torsion": "suspension",
    "bolsas de aire para suspension": "suspension neumatica", "suspension de aire": "suspension neumatica",
    "compresores": "suspension neumatica", "aisladores": "suspension",
    "terminales de direccion": "barras acoplamiento", "terminales interiores": "barras acoplamiento",
    "cajas de direccion": "mecanismo bomba direccion", "cajas de direccion hidraulica": "mecanismo bomba direccion",
    "deposito liquido hidraulico": "deposito compensacion aceite hidraulico",
    "mangueras direccion hidraulica": "mangueras tubos volante", "flector de direccion": "elementos transmision direccion",
    "columnas de direccion": "columna direccion", "sensores de direccion": "sensor angulo direccion",
    "kits de direccion hidraulica": "mecanismo bomba direccion",
    "cardan": "arbol transmision", "flechas cardan": "arbol transmision", "ejes de transmision": "eje transmision",
    "kit clutch": "juego clutch", "volante de clutch": "volante motor", "collarin de clutch": "collarin liberacion central",
    "bombas de clutch": "accionamiento clutch", "soportes de cajas": "transmision manual",
    "diferenciales": "diferencial", "cajas de transferencia": "caja transmision",
    "cajas de velocidades": "transmision manual", "selectoras": "transmision manual",
    "eje trasero": "transmision ejes", "reten de flecha": "eje transmision",
    "amortiguadores de cajuela": "tapas cofres puertas", "parrillas": "parte delantera vehiculo",
    "faros delanteros": "faros principales", "focos de xenon": "faros principales luces",
    "calaveras": "parte trasera vehiculo luces", "calaveras traseras": "parte trasera vehiculo",
    "molduras para puertas": "embellecedores molduras", "molduras para faros": "embellecedores molduras",
    "emblemas": "embellecedores molduras emblemas", "manijas para puertas": "manija puerta",
    "espejos retrovisores laterales": "carroceria", "lunas de espejos laterales": "carroceria",
    "salpicaderas": "partes carroceria salpicadera defensa", "facias delanteras": "parte delantera vehiculo",
    "facias traseras": "parte trasera vehiculo", "cofres": "tapas cofres", "bisagras de puertas": "tapas puertas",
    "plumillas limpiaparabrisas": "limpieza vidrios brazo", "motores de limpiaparabrisas": "motor limpiaparabrisas",
    "brazos de limpiaparabrisas": "brazo limpiaparabrisas", "depositos limpiaparabrisas": "deposito agua lavado",
    "sensores tpms": "rueda fijacion", "birlos de ruedas": "rueda fijacion",
    "cantoneras": "embellecedores molduras", "cerraduras de puerta": "cerraduras exterior",
    "cerraduras de cajuela y porton": "cerraduras exterior", "cerraduras de cofre": "cerraduras exterior",
    "elevador para ventanas": "elevador ventanas", "manijas alza cristales": "elevador ventanas",
    "sensores de reversa": "sistema asistencia manejo", "refrigerante y anticongelante": "anticongelante",
    "spoilers": "parte delantera vehiculo", "alerones": "parte trasera vehiculo",
    "cableado": "piezas individuales juego cables", "baterias": "bateria",
    "motores de arranque": "sistema arranque", "modulos de fusibles": "caja portafusibles",
    "compresor": "compresor piezas aire acondicionado", "condensador": "condensador",
    "valvula calefaccion": "valvulas control calefaccion", "mangueras de calefaccion": "tubos mangueras calefaccion",
    "motor calefaccion": "ventilador piezas calefaccion",
    "discos de frenos": "freno disco", "balatas de frenos": "freno disco pastillas", "zapatas de freno": "freno tambor",
    "spoiler": "carroceria",
}

# sistema(s) raiz TecDoc preferidos por cada grupo Embler (para desambiguar cruces)
PREF = {
    "Motor": {"Motor", "Filtro", "Refrigeración", "Sistema de encendido/incandescencia",
              "Transmisión por correas", "Alimentación de combustible", "Preparación de combustible",
              "Calefacción/Ventilación", "Sistema de escape"},
    "Suspensión": {"Suspensión / Amortiguación", "Suspensión de eje/Guía de rueda/Ruedas"},
    "Suspensión de aire": {"Suspensión / Amortiguación"},
    "Frenos": {"Kit de freno", "Sistema de aire comprimido"},
    "Chasis": {"Kit de freno", "Suspensión de eje/Guía de rueda/Ruedas"},
    "Colisión": {"Carrocería", "Sistema eléctrico", "Limpieza de vidrios", "Sistema de cierre",
                 "Equipamiento interior", "Limpieza de faros"},
    "Accesorios": {"Accesorios", "Equipamiento interior", "Sistema de cierre", "Sistemas de confort"},
    "Enfriamiento": {"Refrigeración", "Calefacción/Ventilación", "Aire acondicionado"},
    "Transmisión": {"Transmisión", "Clutch/piezas de montaje", "Tracción a las ruedas", "Transmisión por ejes"},
    "Dirección": {"Dirección"},
    "Eléctrico": {"Sistema eléctrico"},
    "Escape": {"Sistema de escape"},
    "Tuning": {"Carrocería"},
    "Herramientas": set(),
    "Otros": set(),
}

def best_match(grupo, subgrupo):
    """Devuelve (node, score). score 0-1. Sesga hacia el sistema preferido del grupo."""
    key = norm(subgrupo)
    expanded = SYN.get(key, "")
    q = tokens(subgrupo) | tokens(expanded)
    for stop in ("de", "para", "la", "el", "y", "del"):
        q.discard(stop)
    pref = PREF.get(grupo, set())
    best, best_s = None, 0.0
    for nd in nodes:
        nt = tokens(nd["name"])
        if not nt or not q:
            continue
        inter = len(q & nt)
        if inter == 0:
            continue
        score = inter / max(len(nt), 1) * 0.6 + inter / max(len(q), 1) * 0.4
        if expanded and tokens(expanded) & nt:
            score += 0.2
        # sesgo por sistema preferido del grupo
        if pref:
            if nd["root"] in pref:
                score += 0.25
            else:
                score -= 0.30
        if score > best_s:
            best, best_s = nd, score
    return best, round(min(max(best_s, 0.0), 1.0), 2)

# ---------- agregar subgrupos por grupo ----------
grupos = defaultdict(lambda: defaultdict(int))
for marca, gs in ARBOL.items():
    for g, subs in gs.items():
        for sub, n in subs.items():
            grupos[g][sub] += n

# ---------- overrides manuales (decididos por criterio de autopartes) ----------
# (grupo, subgrupo) -> (sistema_root_TecDoc, nombre_exacto_nodo_TecDoc)
OVERRIDE = {
    # Accesorios
    ("Accesorios", "Llaveros"): ("Accesorios", "Accesorios"),
    ("Accesorios", "Otros"): ("Accesorios", "Accesorios"),
    ("Accesorios", "Porta Placas"): ("Accesorios", "Accesorios"),
    ("Accesorios", "Pomos de Palanca de Cambio"): ("Equipamiento interior", "Sistema de palancas manuales y pedales"),
    ("Accesorios", "Bolsas de Aire"): ("Sistemas de seguridad", "Sistema de bolsa de aire"),
    ("Accesorios", "Rejillas de Faros de Niebla"): ("Carrocería", "Parte delantera del vehículo"),
    ("Accesorios", "Portavasos"): ("Equipamiento interior", "Portabebidas"),
    ("Accesorios", "Difusores de Aire"): ("Equipamiento interior", "Revestimiento"),
    ("Accesorios", "De Cierres Centralizados"): ("Sistema de cierre", "Cierre centralizado"),
    ("Accesorios", "Tableros"): ("Equipamiento interior", "Tablero de instrumentos"),
    ("Accesorios", "Pastillas de Encendido"): ("Sistema de encendido/incandescencia", "Sistema de encendido/incandescencia"),
    ("Accesorios", "Rejillas de Luz"): ("Carrocería", "Luces"),
    # Chasis
    ("Chasis", "Parrillas de Facias"): ("Carrocería", "Parte delantera del vehículo"),
    ("Chasis", "Mandos de Encendido"): ("Sistema de encendido/incandescencia", "Sistema de encendido/incandescencia"),
    # Colisión
    ("Colisión", "Otros"): ("Carrocería", "Carrocería"),
    ("Colisión", "Biseles"): ("Carrocería", "Embellecedores/Molduras/Emblemas/Protectores"),
    ("Colisión", "Ojos de Gato"): ("Sistema eléctrico", "Reflectores/Reflectores laterales"),
    ("Colisión", "Focos"): ("Sistema eléctrico", "Luces"),
    ("Colisión", "Eléctricos"): ("Sistema eléctrico", "Sistema eléctrico"),
    ("Colisión", "Guías de Facias"): ("Carrocería", "Partes de la carrocería/Salpicadera/Defensa"),
    ("Colisión", "Ojos de Ángel"): ("Sistema eléctrico", "Luces"),
    ("Colisión", "Ópticas Delanteras"): ("Carrocería", "Faros principales/Pieza insertable"),
    ("Colisión", "Tapones de Tuercas"): ("Suspensión de eje/Guía de rueda/Ruedas", "Rueda/Fijación de la rueda"),
    # Eléctrico
    ("Eléctrico", "Carcasas para Controles"): ("Sistema eléctrico", "Sistema eléctrico"),
    ("Eléctrico", "Sin Pantalla"): ("Sistema eléctrico", "Sistema eléctrico"),
    ("Eléctrico", "Otros"): ("Sistema eléctrico", "Sistema eléctrico"),
    # Enfriamiento
    ("Enfriamiento", "Tolvas"): ("Refrigeración", "Ventilador"),
    ("Enfriamiento", "Otros"): ("Refrigeración", "Refrigeración"),
    ("Enfriamiento", "Otros Motoventiladores"): ("Refrigeración", "Ventilador"),
    ("Enfriamiento", "Controles"): ("Refrigeración", "Aparato de control"),
    ("Enfriamiento", "Interruptores"): ("Refrigeración", "Interruptor/Sensor"),
    # Escape
    ("Escape", "Otros"): ("Sistema de escape", "Sistema de escape"),
    # Frenos
    ("Frenos", "Otros"): ("Kit de freno", "Kit de freno"),
    ("Frenos", "Kits Completos"): ("Kit de freno", "Kit de freno"),
    ("Frenos", "Pastillas"): ("Kit de freno", "Freno de disco"),
    # Herramientas (sin equivalente limpio -> Servicio)
    ("Herramientas", "Cables Pasa Corriente"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    ("Herramientas", "Otros"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    ("Herramientas", "Caja de Herramientas"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    # Motor
    ("Motor", "Otros"): ("Motor", "Motor"),
    ("Motor", "Tapas de Punterías"): ("Motor", "Culata de cilindro / Piezas de montaje"),
    ("Motor", "Bielas"): ("Motor", "Bloque motor"),
    ("Motor", "Engranes"): ("Motor", "Distribución del motor"),
    ("Motor", "Cigüeñales"): ("Motor", "Accionamiento del cigüeñal"),
    ("Motor", "Monoblock"): ("Motor", "Bloque motor"),
    ("Motor", "Motores Completos"): ("Motor", "Bloque motor"),
    ("Motor", "Carburadores"): ("Preparación de combustible", "Sistema de carburador"),
    ("Motor", "Computadoras"): ("Motor", "Sistema eléctrico del motor"),
    ("Motor", "Chicotes Aceleradores"): ("Preparación de combustible", "Preparación de mezcla"),
    ("Motor", "Vapor de Gasolina"): ("Alimentación de combustible", "Sistema AKF"),
    ("Motor", "Balancines"): ("Motor", "Distribución del motor"),
    ("Motor", "Riel de Inyectores"): ("Preparación de combustible", "Preparación de mezcla"),
    ("Motor", "Reguladores de Voltaje"): ("Sistema eléctrico", "Alternador/piezas"),
    ("Motor", "Bulbo de Temperatura"): ("Refrigeración", "Interruptor/Sensor"),
    # Otros (catch-all -> Servicio)
    ("Otros", "Otros"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    ("Otros", "(sin sub)"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    ("Otros", "Extractores de Polea"): ("Piezas de servicio, inspección y mantenimiento", "Piezas de servicio, inspección y mantenimiento"),
    ("Otros", "Para Transmisión Manual"): ("Transmisión", "Transmisión manual"),
    # Suspensión
    ("Suspensión", "Otros"): ("Suspensión / Amortiguación", "Suspensión / Amortiguación"),
    # Transmisión
    ("Transmisión", "Cables Selectoras de Cambios"): ("Transmisión", "Transmisión manual"),
    ("Transmisión", "Interrupores de Marcha Atrás"): ("Transmisión", "Transmisión manual"),

    # --- correcciones de matches automaticos erroneos (auto-auditoria) ---
    ("Frenos", "Sensores de Velocidad"): ("Kit de freno", "Regulación dinámica de conducción"),
    ("Frenos", "Sensores ABS"): ("Kit de freno", "Regulación dinámica de conducción"),
    ("Frenos", "Sistema de Frenado"): ("Kit de freno", "Kit de freno"),
    ("Frenos", "Kits de Frenos"): ("Kit de freno", "Kit de freno"),
    ("Frenos", "Mangueras de Freno"): ("Kit de freno", "Tubos flexibles de frenos"),
    ("Frenos", "Interruptores de Luz de Freno"): ("Kit de freno", "Interruptor de luces freno"),
    ("Transmisión", "Kits de Reparación"): ("Transmisión", "Transmisión manual"),
    ("Transmisión", "Mangueras para Enfriadores"): ("Transmisión", "Transmisión"),
    ("Motor", "Otros Sensores"): ("Motor", "Sistema eléctrico del motor"),
    ("Motor", "Poleas de Bombas de Agua"): ("Refrigeración", "Bomba de agua / Junta"),
    ("Motor", "Bases de Bombas de Agua"): ("Refrigeración", "Bomba de agua / Junta"),
    ("Motor", "Poleas de Bomba de Dirección"): ("Dirección", "Mecanismo/bomba de dirección"),
    ("Motor", "Poleas de Accesorios"): ("Transmisión por correas", "Polea"),
    ("Motor", "Poleas de Tensor"): ("Transmisión por correas", "Polea"),
    ("Motor", "Mangueras de Enfriador"): ("Refrigeración", "Mangueras/tuberías/bridas"),
    ("Motor", "Mangueras de Turbo"): ("Motor", "Alimentación de aire"),
    ("Motor", "Depósito de Refrigerante"): ("Refrigeración", "Anticongelante"),
    ("Motor", "Kit de Afinación"): ("Piezas de servicio, inspección y mantenimiento", "Intervalo de inspección"),
    ("Accesorios", "Manijas de Puertas"): ("Sistema de cierre", "Manija de puerta"),
    ("Accesorios", "Sensores de Reversa"): ("Sistemas de seguridad", "Sistema de asistencia de manejo"),
    ("Enfriamiento", "Filtro Acumulador"): ("Aire acondicionado", "Secador"),
    ("Colisión", "Birlos de Ruedas"): ("Suspensión de eje/Guía de rueda/Ruedas", "Rueda/Fijación de la rueda"),
    ("Suspensión", "Bombas"): ("Suspensión / Amortiguación", "Regulación de nivel/hidráulica de suspensión"),
    ("Suspensión", "Flechas Completas"): ("Tracción a las ruedas", "Eje de transmisión"),
    ("Motor", "Alternadores"): ("Sistema eléctrico", "Alternador/piezas"),
    ("Motor", "Marchas"): ("Sistema eléctrico", "Sistema de arranque"),
}

# indice nombre+root -> node
by_name_root = {}
for nd in nodes:
    by_name_root.setdefault((nd["root"], nd["name"]), nd)

def resolve_override(g, sub):
    tgt = OVERRIDE.get((g, sub))
    if not tgt:
        return None
    return by_name_root.get(tgt)

rows = []
unresolved_override = []
for g in grupos:
    for sub, n in grupos[g].items():
        ovr = resolve_override(g, sub)
        if ovr:
            node, score = ovr, 1.0
            rows.append({
                "grupo_embler": g, "subgrupo_embler": sub, "productos": n,
                "tecdoc_sistema": node["root"], "tecdoc_subgrupo": node["name"],
                "tecdoc_node_id": node["id"], "confianza": "override", "needs_review": "",
            })
            continue
        node, score = best_match(g, sub)
        rows.append({
            "grupo_embler": g, "subgrupo_embler": sub, "productos": n,
            "tecdoc_sistema": node["root"] if node else "",
            "tecdoc_subgrupo": node["name"] if node else "",
            "tecdoc_node_id": node["id"] if node else "",
            "confianza": score,
            "needs_review": "SI" if (node is None or score < 0.45) else "",
        })

rows.sort(key=lambda r: (-r["productos"]))
with open("homologacion.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

# verificar que todos los overrides resolvieron a un nodo real
bad = [(g, s, t) for (g, s), t in OVERRIDE.items() if by_name_root.get(t) is None]
if bad:
    print("!!! OVERRIDES QUE NO RESOLVIERON (nombre/sistema no existe en el arbol):")
    for g, s, t in bad:
        print(f"    ({g} / {s}) -> {t}")
    print()

total = len(rows)
review = sum(1 for r in rows if r["needs_review"])
overrides = sum(1 for r in rows if r["confianza"] == "override")
prod_total = sum(r["productos"] for r in rows)
prod_review = sum(r["productos"] for r in rows if r["needs_review"])
print(f"Subgrupos homologados: {total}")
print(f"  Override manual: {overrides}  | Match automatico: {total-overrides-review}  | Sin resolver: {review}")
print(f"Productos cubiertos con match confiable: {prod_total-prod_review}/{prod_total} ({100*(prod_total-prod_review)//prod_total}%)")
print("\n=== TOP 25 por volumen (verifica el match) ===")
for r in rows[:25]:
    flag = "  <-- REVISAR" if r["needs_review"] else ""
    print(f"  {r['productos']:>5}  {r['grupo_embler']:>16} / {r['subgrupo_embler']:<28} -> [{r['tecdoc_sistema']}] {r['tecdoc_subgrupo']} (conf {r['confianza']}){flag}")
print("\nGuardado: homologacion.csv")
