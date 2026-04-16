# Patron de extraccion de compatibilidades desde `Descripción_ML`

## Ubicacion del bloque

El texto de `Descripción_ML` sigue esta estructura tipica en 80-95% de los productos:

```
<NOMBRE DEL PRODUCTO EN MAYUSCULAS>  INCLUYE: <componentes>  MUY IMPORTANTE: PARA EVITARTE MOLESTIAS ...  APLICA PARA LOS SIGUIENTES MODELOS:  <LISTA DE VEHICULOS>  ENVIOS A CDMX Y TODO EL PAIS ...  EMBLER AUTOPARTES EUROPEAS ESPECIALISTAS EN ...  CALIDAD ORIGINAL ...
```

Las dos secciones relevantes:

1. **INCLUYE:** — lo que trae el producto (kits, juegos, pares). Presente solo en ~2% de los productos.
2. **APLICA PARA LOS SIGUIENTES MODELOS:** — la lista completa de configuraciones de vehiculos compatibles. Presente en 79-96% segun la categoria.

## Regex principal

```python
RX_COMPAT_BLOCK = re.compile(
    r'APLICA\s+(?:PARA\s+LOS\s+SIGUIENTES\s+MODELOS|SOLO\s+PARA|PARA)\s*[:.]?\s+'
    r'(?P<body>.*?)(?=(?:' + END_ALT + r')|\Z)',
    re.IGNORECASE | re.DOTALL,
)
```

Donde `END_ALT` combina los marcadores que cierran el bloque: `ENVIOS A`, `EMBLER AUTOPARTES`, `CALIDAD ORIGINAL`, `GARANTIZADOS CONTRA`, `ESPECIALISTAS EN`, `PARA EVITARTE`, `MUY IMPORTANTE`, `CONTACTANOS`, `PRECIO POR PIEZA`, `CATALOGO`, `**`.

## Formato de cada entrada de vehiculo

Cada vehiculo sigue este orden fijo:

```
<MARCA> <MODELO-Y-VERSION> <AÑO o RANGO "YYYY AL YYYY"> <N CILINDROS> <N.N LITROS> <TIPO_MOTOR>
```

Ejemplos reales:

- `BMW 550i GRAN TURISMO 2011 AL 2014 8 CILINDROS 4.4 LITROS BI TURBO`
- `BMW X5 5.0i PREMIUM 2011 AL 2013 8 CILINDROS 4.4 LITROS BI TURBO`
- `BMW 750Li 2010 AL 2013 8 CILINDROS 4.4 LITROS ASPIRACION NATURAL`
- `BMW X6 50i M PERFORMANCE 2013 AL 2014 8 CILINDROS 4.4 LITROS BI TURBO`

## Separacion de vehiculos

Las entradas vienen separadas por espacios dobles (no saltos de linea). El parser las separa usando un lookahead por marca conocida, sin depender del espaciado:

```python
RX_VEHICLE_START = re.compile(r'\b(?:' + BRANDS_RX + r')\b', re.IGNORECASE)
matches = list(RX_VEHICLE_START.finditer(bloque))
# Cada match marca el inicio de una nueva entrada.
```

## Marcas reconocidas (orden importa)

El mapeo esta en `BRANDS_CANON` dentro del script. El orden es critico: las marcas compuestas (`MERCEDES BENZ`, `LAND ROVER`, `ALFA ROMEO`, `MINI COOPER`, `ROLLS ROYCE`) aparecen ANTES de las simples para evitar que `MERCEDES` capture `MERCEDES BENZ` primero.

```
MERCEDES BENZ / MERCEDES-BENZ / MERCEDES  →  Mercedes-Benz
LAND ROVER / LAND-ROVER                    →  Land Rover
ALFA ROMEO / ALFA-ROMEO                    →  Alfa Romeo
ROLLS ROYCE / ROLLS-ROYCE                  →  Rolls-Royce
MINI COOPER / MINI                         →  Mini
BMW                                        →  BMW
AUDI                                       →  Audi
VOLKSWAGEN / VW                            →  Volkswagen
PORSCHE / PORCHE (typo comun)              →  Porsche
VOLVO                                      →  Volvo
JAGUAR                                     →  Jaguar
SEAT / SMART / FIAT / BENTLEY              →  (tal cual)
```

## Normalizacion del modelo

La funcion `_titulo_modelo` aplica estas reglas al tokenizar:

| Patron del token | Ejemplo input | Output |
|------------------|---------------|--------|
| Codigo de chassis / motor (letra + digitos) | `X5`, `Z4`, `F10`, `N63B44` | mayuscula completa (`X5`, `N63B44`) |
| Modelo con sufijo minusculo | `550i`, `335ci`, `5.0i` | conserva minuscula (`550i`, `335ci`, `5.0i`) |
| Modelo con sufijo `Li` o `Ci` | `750Li`, `335Ci` | capitaliza el sufijo (`750Li`) |
| Siglas especificas | `AMG`, `GTI`, `TDI`, `TFSI`, `RS`, `GT` | mayuscula |
| Letra solitaria (M, X, Z, S, etc.) | `M SPORT` | preserva mayuscula (`M Sport`) |
| Resto | `GRAN TURISMO`, `LUXURY` | Capitalizado (`Gran Turismo`, `Luxury`) |

## Normalizacion del motor

- `CILINDROS` → `cil`
- `N.N LITROS` → `N.NL`
- `BI TURBO` / `BITURBO` → `Bi-Turbo`
- `TWIN TURBO` → `Twin-Turbo`
- `SCROLL TWIN TURBO` → `Scroll Twin-Turbo`
- `TURBOCARGADO` / `TURBOCOMPRESOR` → `Turbo`
- `ASPIRACION NATURAL` → `Aspiración natural`

## Manejo de edge cases

| Caso | Comportamiento |
|------|----------------|
| `Descripción_ML` vacia o no tiene "APLICA PARA..." | No extrae, flaggea `[BUSCAR] Compatibilidad vehicular...` en `revision_humana` |
| Bloque muy corto (<2 vehiculos) | Se conservan igual, el cliente puede ver lo que hay |
| Marca no reconocida | Se ignora la entrada (previene meter basura) |
| Entrada sin año/motor parseable | Se conserva el modelo sin los metadatos tecnicos |
| Duplicados exactos (titulo + año) | Se deduplican en la seccion |

## Tabla de cobertura observada (13K productos)

| Categoria | Filas | Con compatibilidades | % |
|-----------|-------|----------------------|---|
| refacciones_frenos | 1089 | 1035 | 95.0% |
| refacciones_carroceria | 500 | 460 | 92.0% |
| refacciones_clima | 117 | 107 | 91.5% |
| tuning | 95 | 86 | 90.5% |
| refacciones_motor | 4983 | 4455 | 89.4% |
| refacciones_electrico | 317 | 281 | 88.6% |
| refacciones_otros | 1717 | 1520 | 88.5% |
| refacciones_suspension | 3970 | 3240 | 81.6% |
| refacciones_transmision | 221 | 176 | 79.6% |
| **Total** | **13036** | **11360** | **87.1%** |

Las ~1700 filas sin compatibilidades extraibles reciben el flag `[BUSCAR] Compatibilidad vehicular: no se pudo extraer de la descripción — revisar listing ML.` en la columna `revision_humana`, para que el equipo los revise manualmente.
