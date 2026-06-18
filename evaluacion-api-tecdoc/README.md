# Evaluación de la API TecDoc — Proyecto buscador de partes (Embler)

> Carpeta de **evaluación** (junio 2026). Documenta las pruebas en vivo de la API TecDoc
> (TecAlliance, Pegasus 3.0) y la conclusión sobre si sirve para construir el **buscador
> de partes por vehículo** de Embler. Antes se llamaba `base-pruebas/`.
>
> El pipeline de **homologación/migración a Shopify** (otro tema) vive aparte en
> `../homologacion-tecdoc/` y lo usa el skill `tecdoc-shopify`.

---

## Veredicto en una línea

La API es la correcta y el flujo del buscador por vehículo quedó mapeado y validado en
estructura. La cuenta **DEMO** (provider `25099`) trae **artículos completos en español**
(106k piezas con OEM/specs/GTIN) pero **sin vehículos de pasajeros** (tipo P/V = 0; solo
camiones tipo K). El bloqueo es de **provisión de datos**, no técnico: con el plan de pago
que incluya Passenger Car para MX, los mismos requests ya probados regresan los autos
europeos. Decisión: **no pedir más a la DEMO** — cumplió su propósito.

Detalle completo y el porqué de la extrapolación: ver los documentos abajo.

---

## Por dónde empezar

| Orden | Documento | Qué encontrarás |
|---|---|---|
| 1 | **`EXTRAPOLACION-EUROPEAS-TECDOC.md`** | **Conclusión final**: qué se comprobó en vivo, cómo extrapola a BMW/Mercedes/Audi, riesgo residual y **checklist de aceptación** para el día 1 del plan de pago. |
| 2 | `DOCUMENTACION-API-TECDOC.md` | Bitácora completa de las pruebas (2026-06-10 y 06-11): conexión, métodos que sí/no funcionan, gotchas de parámetros, flujo del buscador. |
| 3 | `ANALISIS-TECDOC.md` | Análisis del paquete de datos `Suspension.7z` (formato TAF de SACHS/BOGE): estructura de tablas, modelo de datos, cómo parsearlo. |
| 4 | `PROYECTO-BUSCADOR-TECDOC-AUGETEC.html` | Documento entregado a **Augetec**: contexto del negocio, resultados de pruebas, arquitectura deseada (Odoo dueño de datos) y scope solicitado. |

---

## Contenido de la carpeta

### Documentación y conclusiones
- `EXTRAPOLACION-EUROPEAS-TECDOC.md` — conclusión final + checklist de aceptación
- `DOCUMENTACION-API-TECDOC.md` — bitácora de pruebas del API
- `ANALISIS-TECDOC.md` — análisis del paquete TAF (`Suspension.7z`)
- `PROYECTO-BUSCADOR-TECDOC-AUGETEC.html` — brief para Augetec
- `acceso-api.md` — credenciales DEMO enviadas por el proveedor (vigencia 30 días)

### Pruebas / código
- `test_modulo_vehiculos.py` — diagnóstico re-ejecutable (requests bien formados vs datos no provisionados). Sirve como checklist el día 1 del plan de pago.
- `tecdoc_client.py` — cliente Python con la config verificada que funciona.
- `TecDoc_var.postman_collection.json` — colección Postman del proveedor (Ricardo, 06-11).

### Datos de muestra (proveedor, formato TAF)
- `Suspension.7z` + `extracted/` — datos de SACHS (0032) y BOGE (0014): solo artículos, sin vehículos.

### Referencia oficial (PDFs)
- `WS Pegasus principales metodos.pdf` — **doc oficial de métodos del API** (la referencia clave)
- `Web Services metodos y end points - TecDoc.pdf` — endpoints y enlaces
- `TecDoc-Data-Format_Version_2.7_EN_2.0.28.pdf` — spec del formato TAF (207 págs)
- `260605 WS QUO00000339-1.PDF` — cotización del proveedor (contexto comercial)
