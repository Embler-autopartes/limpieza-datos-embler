# -*- coding: utf-8 -*-
"""
Reescribe con IA (Batches API de Claude) SOLO la seccion Descripcion del
Body (HTML) del catalogo Shopify, y reensambla el HTML respetando el orden:
   Compatibilidades -> Antes de Comprar -> Envio -> Politica de Devolucion ->
   Descripcion (reescrita) -> Preguntas Frecuentes

Reglas de reescritura (en el system prompt): acortar, util para el comprador,
SIN inventar, sin el bloque de marca "Frey/Embler" ni logistica (garantia/envio/
devoluciones), sin el parrafo "Compatible con N...".

Requisitos:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Uso:
    # 1) Enviar el batch (imprime el BATCH_ID)
    python scripts/17_reescribir_descripciones_ia.py --submit [--model claude-sonnet-4-6] [--limit N]

    # 2) Ver estado
    python scripts/17_reescribir_descripciones_ia.py --status BATCH_ID

    # 3) Cuando termine, aplicar resultados y escribir el CSV nuevo
    python scripts/17_reescribir_descripciones_ia.py --apply BATCH_ID

Salida:
    Procesamiento de Catálogo/outputs/2026-06-12/catalogo_completo_final_ia.csv
"""
import csv
import re
import os
import sys
import json

csv.field_size_limit(10 ** 9)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "Procesamiento de Catálogo", "outputs", "2026-06-12")
INPUT = os.path.join(OUTDIR, "catalogo_completo_final.csv")
OUTPUT = os.path.join(OUTDIR, "catalogo_completo_final_ia.csv")
# mapa custom_id(handle) -> texto reescrito devuelto por el batch
RESULTS_JSON = os.path.join(OUTDIR, "ia_descripciones_resultado.json")

DEFAULT_MODEL = "claude-sonnet-4-6"

ORDER = [
    "Compatibilidades",
    "Antes de Comprar",
    "Envio",
    "Politica de Devolucion",
    "Descripcion",
    "Preguntas Frecuentes",
]

SYSTEM_PROMPT = """\
Eres redactor de fichas de producto para Embler Autopartes Europeas (refacciones \
para autos europeos: BMW, Mercedes-Benz, Audi, VW, Porsche, Volvo, Mini, Jaguar).

Tu tarea: reescribir SOLO la seccion "Descripcion" de un producto para que sea \
mas corta, clara y util para quien va a comprar.

REGLAS ESTRICTAS:
1. NO inventes informacion. Usa unicamente los datos que aparecen en el titulo y \
   en la descripcion original, mas el conocimiento general de para que sirve el \
   tipo de pieza nombrado en el titulo (definicion de la pieza). No agregues \
   medidas, materiales, anios ni compatibilidades que no esten en la fuente.
2. ELIMINA por completo:
   - El bloque de marca promocional tipo "Marca Original Frey, importada y \
     especializada... OEM-grade aleman" y cualquier variante de marca propia \
     (Frey, Embler).
   - Todo lo de garantia, envio, DHL/FedEx, entrega inmediata y politicas de \
     devolucion (ya esta en otras secciones de la ficha).
   - El parrafo "Compatible con N configuraciones de ..." (ya esta en otra seccion).
   - Cualquier clasificacion de vehiculo claramente erronea (p. ej. "aplica a \
     moto/cuatriciclo" o "linea pesada" cuando el titulo es un auto): omitela.
3. CONSERVA, si estan en la fuente:
   - Que es la pieza y para que sirve (1 frase, concreta).
   - Material/acabado, lado de instalacion, nota de "se entrega en primer / debe \
     pintarse", contenido del kit, "se vende individual / como kit".
   - Numeros de parte y codigo OEM EXACTAMENTE como aparecen.
   - Si la marca es un fabricante externo real (p. ej. Bosch, Senp), puedes \
     incluir una linea neutral "Marca: X". Marcas propias (Frey, Embler): omitelas.
4. Tono claro y directo, en espanol, util para el comprador. Maximo ~140 palabras.
5. FORMATO DE SALIDA: solo parrafos HTML <p>...</p> (2 a 4 parrafos). Nada de \
   <h2>, nada de markdown, nada de texto fuera de las etiquetas <p>. No incluyas \
   el encabezado "Descripcion".

Devuelve unicamente el HTML de los parrafos."""


# ---------- utilidades de parseo del Body ----------
def split_sections(html):
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.S)
    preludio = parts[0]
    sections = []
    for i in range(1, len(parts), 2):
        title = re.sub(r"</?h2>", "", parts[i]).strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((title, content))
    return preludio, sections


def get_descripcion(html):
    _, sections = split_sections(html)
    for title, content in sections:
        if title == "Descripcion":
            return content
    return ""


def to_plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def reassemble(html, nueva_desc_html):
    """Reordena las secciones y sustituye el contenido de Descripcion."""
    preludio, sections = split_sections(html)
    by_title = {}
    extras = []
    for title, content in sections:
        if title == "Descripcion":
            content = nueva_desc_html
        if title in ORDER:
            by_title[title] = content
        else:
            extras.append((title, content))
    new = preludio
    for title in ORDER:
        if title in by_title:
            new += "<h2>%s</h2>%s" % (title, by_title[title])
    for title, content in extras:
        new += "<h2>%s</h2>%s" % (title, content)
    return new


def iter_products():
    """Devuelve (handle, title, body, descripcion_plain) por producto con Body."""
    with open(INPUT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            b = row["Body (HTML)"]
            if not b.strip():
                continue
            desc = get_descripcion(b)
            if not desc.strip():
                continue
            yield row["Handle"], row["Title"], b, to_plain(desc)


# ---------- submit ----------
def submit(model, limit=None):
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    client = anthropic.Anthropic()
    requests = []
    seen = set()
    for handle, title, _body, desc in iter_products():
        if handle in seen:
            continue
        seen.add(handle)
        user = (
            "TITULO: %s\n\nDESCRIPCION ORIGINAL:\n%s\n\n"
            "Reescribe la seccion Descripcion siguiendo las reglas." % (title, desc)
        )
        requests.append(Request(
            custom_id=handle[:64],
            params=MessageCreateParamsNonStreaming(
                model=model,
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user}],
            ),
        ))
        if limit and len(requests) >= limit:
            break

    print("Productos a procesar:", len(requests), "| modelo:", model)
    batch = client.messages.batches.create(requests=requests)
    print("BATCH_ID:", batch.id)
    print("Estado:", batch.processing_status)
    print("\nVerifica con:  python scripts/17_reescribir_descripciones_ia.py --status", batch.id)


def status(batch_id):
    import anthropic
    b = anthropic.Anthropic().messages.batches.retrieve(batch_id)
    print("Estado:", b.processing_status)
    print("Conteos:", b.request_counts)


def apply(batch_id):
    import anthropic
    client = anthropic.Anthropic()
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print("El batch aun no termina. Estado:", b.processing_status)
        return

    rewrites = {}
    errores = 0
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            msg = result.result.message
            text = next((blk.text for blk in msg.content if blk.type == "text"), "").strip()
            # asegurar que viene envuelto en <p>...</p>
            if text and "<p>" not in text:
                text = "<p>%s</p>" % text
            rewrites[result.custom_id] = text
        else:
            errores += 1
    print("Reescrituras OK:", len(rewrites), "| errores:", errores)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(rewrites, f, ensure_ascii=False)

    # escribir CSV nuevo
    with open(INPUT, encoding="utf-8", newline="") as fin, \
         open(OUTPUT, "w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=r.fieldnames)
        w.writeheader()
        cambiados = 0
        for row in r:
            b = row["Body (HTML)"]
            if b and b.strip():
                key = row["Handle"][:64]
                nueva = rewrites.get(key)
                if nueva:
                    row["Body (HTML)"] = reassemble(b, nueva)
                    cambiados += 1
            w.writerow(row)
    print("Body reescritos:", cambiados)
    print("Salida:", OUTPUT)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = DEFAULT_MODEL
    if "--model" in args:
        model = args[args.index("--model") + 1]
    limit = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])

    if "--submit" in args:
        submit(model, limit)
    elif "--status" in args:
        status(args[args.index("--status") + 1])
    elif "--apply" in args:
        apply(args[args.index("--apply") + 1])
    else:
        print(__doc__)
