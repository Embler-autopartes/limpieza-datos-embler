---
name: corregir-datos
description: |
  Corrige los CSVs enriquecidos de Embler para arreglar dos problemas detectados por Migue en abril 2026:
  (1) las compatibilidades vehiculares vienen mal extraídas porque el skill anterior uso la columna
  `Compatibilidades_ML` de MercadoLibre (incompleta, actua como requisito de publicacion, no como catalogo),
  cuando la fuente correcta es el bloque "APLICA PARA LOS SIGUIENTES MODELOS:" dentro de `Descripción_ML`;
  (2) la `seccion_descripcion` quedo pobre y no menciona lo que incluye el producto cuando es un kit/juego.
  Este skill re-procesa `output/enriched/*_enriched.csv` y genera `output/corrected/*_corrected.csv`
  con compatibilidades COMPLETAS (una linea por modelo, sin perder ninguno) y descripcion mejorada.
  Se activa con frases como: "corrige las compatibilidades", "arregla los outputs", "re-procesa las
  compatibilidades desde la descripcion", "corrige los datos", "aplica las correcciones de Migue",
  "corrige refacciones_motor", "corrige todos los enriched", o cualquier referencia a `output/corrected/`.
---

# Corregir Datos Embler

Este skill corrige dos problemas en los CSVs enriquecidos por `procesar-datos`:

1. **Compatibilidades mal extraidas** — el skill anterior uso `Compatibilidades_ML` (columna de MercadoLibre que es incompleta y a veces incorrecta, porque ML la exige como requisito para publicar aunque no refleje el catalogo real). La fuente correcta es el texto dentro de `Descripción_ML`, que contiene un bloque consistente `"APLICA PARA LOS SIGUIENTES MODELOS: ..."` con TODAS las configuraciones de vehiculos. Migue confirmo con la encargada de ML que el 99% de las publicaciones tienen este bloque completo.
2. **Descripcion pobre** — el texto comercial generado no mencionaba lo que el producto incluye (relevante en kits: juego de juntas, kit de distribucion, etc.). Cuando la descripcion original trae `"INCLUYE: ..."` debemos incorporarlo.

## Argumentos

- `/corregir-datos refacciones_motor` — corrige esa categoria.
- `/corregir-datos all` — corrige todas las categorias en `output/enriched/`.
- `/corregir-datos refacciones_motor --dry-run` — solo estadisticas, no escribe.
- `/corregir-datos refacciones_motor --sample 50` — procesa solo las primeras 50 filas (util para validar).

## Flujo de trabajo

### 1. Preparacion

1. Verifica que exista `output/enriched/<categoria>_enriched.csv` (o lista las categorias disponibles si no se paso una).
2. Explica brevemente al usuario que se hara: se van a re-extraer compatibilidades desde `Descripción_ML`, reescribir `seccion_descripcion`, regenerar `shopify_body_html`, y agregar la nueva columna `seccion_compatibilidades`.
3. Pide confirmacion antes de correr sobre todas las categorias (son ~13K filas).

### 2. Ejecutar el script

Todo el trabajo lo hace un script de Python deterministico (no usa LLM, para que el resultado sea reproducible y auditable):

```bash
python3 scripts/04_corregir_enriched.py <categoria>
python3 scripts/04_corregir_enriched.py all
```

El script:
- Lee `output/enriched/<categoria>_enriched.csv`.
- Para cada fila:
  1. Extrae el bloque `"APLICA PARA LOS SIGUIENTES MODELOS: ..."` de `Descripción_ML`.
  2. Lo parte por marca (BMW / Mercedes-Benz / Audi / VW / Porsche / Volvo / Mini / Land Rover / Jaguar / SEAT / Smart / Fiat / Alfa Romeo / Bentley / Rolls-Royce).
  3. Normaliza cada entrada a `Marca Modelo Años — N cil NL Tipo-Motor`.
  4. Extrae opcionalmente el bloque `"INCLUYE: ..."` como prosa limpia.
- Sobreescribe las columnas:
  - `caract_compatibilidad` — parrafo corto agrupado por serie (ej: `"BMW 550i: 550i Gran Turismo (2011-2014), 550i M Sport (2012-2016). BMW X5: X5 50i Excellence (2014-2018)..."`).
  - `seccion_compatibilidades` — **NUEVA columna**: lista completa, una linea por modelo, en el mismo orden que la descripcion original. Ninguna compatibilidad se pierde.
  - `seccion_descripcion` — se mantiene el parrafo existente pero se agrega "Este producto incluye: ..." (si la descripcion original trae INCLUYE) y una linea final con el numero de configuraciones compatibles.
  - `shopify_tags` — recalculado a partir de las marcas extraidas del bloque (antes podia salir inconsistente con la realidad).
  - `shopify_body_html` — regenerado con la nueva seccion `<h2>Compatibilidades</h2>` como `<ul>` entre la descripcion y "Antes de Comprar".
  - `shopify_seo_description` — incluye hasta 3 modelos compatibles si estan disponibles.
  - `revision_humana` — remueve flags viejos de compatibilidad; agrega `[BUSCAR] Compatibilidad vehicular: no se pudo extraer de la descripción` si el bloque no aparece.
- Escribe `output/corrected/<categoria>_corrected.csv`.

### 3. Reporte y validacion

Al terminar, reporta al usuario:
- Total de filas procesadas.
- % con compatibilidades extraidas (esperado: 80-95% segun la categoria).
- % con bloque INCLUYE detectado (bajo — solo kits).
- Filas que quedaron sin compatibilidades (para revision_humana).
- Ruta del archivo `output/corrected/<categoria>_corrected.csv`.

Muestra una fila de ejemplo al usuario para que valide el formato antes de correr sobre todas las categorias. Incluye `caract_compatibilidad`, las primeras 5 lineas de `seccion_compatibilidades`, y la `seccion_descripcion` completa.

### 4. Que NO hace este skill

- **No toca** `output/enriched/*_enriched.csv` (los originales se preservan por si hay que recomparar).
- **No regenera FAQs, envio, devoluciones ni `caract_*` no relacionados con compatibilidad** — esas secciones ya estaban bien segun la revision de Migue.
- **No usa LLM** — todo el parsing es deterministico sobre regex, para que el mismo input produzca el mismo output y se pueda auditar celda por celda.
- **No cambia precios, SKUs, ni handles** — solo las columnas listadas arriba.

## Detalles del parsing de compatibilidades

El patron `"APLICA PARA LOS SIGUIENTES MODELOS:"` aparece en 79-96% de los productos segun la categoria. El bloque termina cuando aparece cualquiera de estos marcadores: `ENVIOS A`, `EMBLER AUTOPARTES`, `CALIDAD ORIGINAL`, `GARANTIZADOS CONTRA`, `ESPECIALISTAS EN`, `PARA EVITARTE`, `MUY IMPORTANTE`, `CONTACTANOS`, `PRECIO POR PIEZA`, o al final del texto.

Cada entrada de vehiculo sigue el formato: `<MARCA> <MODELO> <AÑOS> <CILINDROS> <LITROS> <TIPO_MOTOR>`. Por ejemplo:

```
BMW 550i GRAN TURISMO 2011 AL 2014 8 CILINDROS 4.4 LITROS BI TURBO
```

Se normaliza a:

```
BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo
```

Detalles tecnicos completos (regex, normalizacion de modelos tipo "550i", "X5 5.0i", "750Li", mapeo de marcas) en `references/patron_extraccion.md`.

## Contexto del negocio

Migue solicito estas correcciones despues de revisar manualmente una muestra con la encargada de MercadoLibre. La observacion clave: **las compatibilidades de MercadoLibre no son el catalogo fiel — el texto de la descripcion si lo es** (porque lo escriben a mano los vendedores y ML no les pone limite de longitud alli).

Orden de confianza para el dato de compatibilidad, de mayor a menor:
1. Bloque `APLICA PARA LOS SIGUIENTES MODELOS:` en `Descripción_ML` ✓ (lo que usa este skill).
2. Titulo del producto (menciones casuales de modelos).
3. Columna `Compatibilidades_ML` (descartada — incompleta).
