# -*- coding: utf-8 -*-
"""
Reescribe la seccion Descripcion del Body (HTML) SIN IA, de forma determinista:

- El parrafo de intro (que dice que es la pieza) se sustituye por una version
  corta y clara escrita a mano, mapeada por tipo de pieza. Cubre ~98% via los
  intros mas comunes; los intros genericos ("Componente del...") se rearman
  desde el titulo del producto + un diccionario de definiciones por keyword.
- Se conservan numeros de parte (recortando la explicacion generica), notas de
  "se vende / kit / primer", y lado de instalacion.
- Se elimina el bloque de marca propia (Frey/Embler) y la logistica; las marcas
  externas reales (Bosch, Senp, etc.) se dejan como "Marca: X".
- Se elimina "Compatible con N..." (redundante con Compatibilidades).
- Se reordena: Compatibilidades -> Antes de Comprar -> Envio ->
  Politica de Devolucion -> Descripcion -> Preguntas Frecuentes.

Uso:
    python scripts/18_reescribir_descripciones_local.py --sample 6
    python scripts/18_reescribir_descripciones_local.py --run
"""
import csv
import re
import os
import sys
import unicodedata
import hashlib

csv.field_size_limit(10 ** 9)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "Procesamiento de Catálogo", "outputs", "2026-06-12")
INPUT = os.path.join(OUTDIR, "catalogo_completo_final.csv")
NEWDIR = os.path.join(BASE, "Procesamiento de Catálogo", "outputs",
                      "2026-06-17-descripciones-reescritas")
# paso 1 (este script): salida intermedia. El paso 2 (scripts/19) le agrega
# las Compatibilidades y produce el archivo canónico catalogo_completo_final_reescrito.csv
OUTPUT = os.path.join(NEWDIR, "catalogo_reescrito_intermedio.csv")

ORDER = [
    "Compatibilidades", "Antes de Comprar", "Envio",
    "Politica de Devolucion", "Descripcion",
]
# secciones a eliminar por completo del Body
DROP_SECTIONS = {"Preguntas Frecuentes"}
# título a mostrar para ciertas secciones (la clave interna se conserva para el match)
TITLE_MAP = {"Antes de Comprar": "Asegura el ajuste perfecto"}

MARCAS_AUTO = {
    "bmw", "mercedes", "mercedes-benz", "benz", "audi", "vw", "volkswagen",
    "porsche", "volvo", "mini", "jaguar", "seat", "smart", "land", "range",
    "rover", "cooper",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# --- Reescrituras por tipo de pieza (clave = inicio normalizado del intro) ---
REWRITES_RAW = {
"amortiguador de suspension del vehiculo": "Amortiguador de la suspensión: controla el movimiento del resorte para mantener la estabilidad, el confort de marcha y el agarre del neumático. Pieza de desgaste; conviene reemplazar por pares del mismo eje.",
"bolsa de aire": "Bolsa de aire (air spring) de la suspensión neumática: reemplaza al resorte con una cámara de aire presurizado. Falla típica: fuga por el caucho agrietado, el auto se baja al estacionarse.",
"radiador del motor": "Radiador del motor: intercambiador que enfría el refrigerante haciéndole pasar aire por sus aletas. Vulnerable a impactos de piedra y a corrosión interna con los años.",
"amortiguador de aire": "Amortiguador de aire (air strut) de suspensión neumática: integra la bolsa de aire con el amortiguador hidráulico. Una fuga obliga al compresor a trabajar de más y descarga la batería.",
"deposito de anticongelante expansion tank coolant reservoir o de lavaparabrisas": "Depósito de anticongelante o de lavaparabrisas: el de anticongelante contiene el refrigerante y absorbe su expansión; el de lavaparabrisas almacena el líquido limpiaparabrisas. Falla típica: rajadura del plástico con fuga.",
"deposito de anticongelante": "Depósito de anticongelante (expansion tank): contiene el refrigerante y absorbe su expansión por calor. Falla típica: se raja el plástico por edad y temperatura, con fuga y pérdida de refrigerante.",
"brazo de suspension": "Brazo de suspensión (control arm): conecta la rueda con el chasis y mantiene la geometría de la dirección. Se reemplaza cuando sus bujes o rótulas se desgastan: golpes en baches y dirección vaga.",
"bomba de agua": "Bomba de agua: hace circular el refrigerante por el motor y el radiador para mantener la temperatura. Pieza de desgaste; el sello interno falla con los años y aparece fuga por el respiradero.",
"soporte taco de motor": "Soporte (taco) de motor: bloque de caucho-metal que sujeta el motor al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones en ralentí y golpes al acelerar o cambiar de marcha.",
"termostato del sistema de refrigeracion": "Termostato: válvula que regula el paso de refrigerante al radiador según la temperatura del motor. Falla atascado abierto (el motor no calienta) o cerrado (sobrecalentamiento).",
"balatas pastillas brake pads": "Balatas (pastillas) de freno: material de fricción que aprieta el disco para detener el vehículo. Pieza de desgaste; se cambian al chillar al frenar, vibrar el pedal o encender el testigo de freno.",
"amortiguador de cofre o cajuela": "Amortiguador (pistón a gas) de cofre o cajuela: mantiene abierta la tapa sin que se caiga. Al perder gas con los años deja de sostenerla; conviene reemplazar por par.",
"sensor abs": "Sensor ABS (velocidad de rueda): mide la velocidad de cada rueda para el ABS y el control de estabilidad. Su falla enciende el testigo ABS y desactiva el sistema.",
"junta del colector de admision": "Junta del colector de admisión: sella la unión entre el colector y la cabeza para evitar entradas de aire falso. Se reemplaza al desmontar el colector; dañada causa ralentí irregular y códigos de mezcla pobre.",
"horquilla bandeja tijera de suspension": "Horquilla (bandeja) de suspensión: brazo en forma de A que conecta la rueda al chasis y permite el movimiento de la suspensión. Se reemplaza cuando sus bujes o rótulas se desgastan.",
"sensor de desgaste de balata": "Sensor de desgaste de balata: al gastarse la balata, el sensor se corta y enciende el testigo de freno. Se reemplaza junto con las balatas nuevas.",
"disco de freno rotor": "Disco de freno (rotor): superficie sobre la que actúan las balatas para detener el vehículo. Pieza de desgaste; se reemplaza por desgaste, ranurado o alabeo (vibración al frenar).",
"parrilla delantera del vehiculo": "Parrilla delantera: panel que cubre el frontal del cofre, deja pasar aire al radiador y define la imagen del auto. Suele dañarse por impactos de piedra o golpes menores.",
"junta de cabeza del motor": "Junta de cabeza (head gasket): sella la cámara de combustión entre el block y la cabeza y separa los conductos de aceite y refrigerante. Su falla mezcla fluidos, baja la compresión y sobrecalienta el motor.",
"buje bushing casquillo de suspension": "Buje (casquillo) de suspensión: pieza de caucho-metal que aísla la unión entre componentes de la suspensión y absorbe vibraciones. Al cuartearse aparecen golpes en baches y holgura.",
"tensor tensioner hidraulico o mecanico de cadena": "Tensor de cadena de tiempo o banda: mantiene la tensión correcta compensando el desgaste. Falla típica: tableteo de cadena en frío que persiste si la falla avanza.",
"junta de tapa de valvulas": "Junta de tapa de válvulas: sella la tapa superior de la cabeza y contiene el aceite del tren de válvulas. Muy común que fugue al endurecerse el caucho (manchas de aceite, residuo en las bujías).",
"bobina de encendido": "Bobina de encendido (ignition coil): eleva los 12V de la batería al alto voltaje que necesita la bujía para la chispa. Una bobina dañada apaga su cilindro: ralentí irregular y código P0300-P0306.",
"bieleta tirante sway bar link": "Bieleta (tirante) de la barra estabilizadora: conecta el brazo de suspensión con la barra estabilizadora. Al aflojarse sus rótulas aparece un golpeteo al pasar baches a baja velocidad.",
"polea del motor de cigue": "Polea del motor (de cigüeñal o de accesorios): la de cigüeñal integra un amortiguador de vibraciones de caucho que se degrada con los años; las de accesorios mueven alternador, dirección, A/C y bomba de agua.",
"arbol de levas camshaft": "Árbol de levas (camshaft) o su engrane: abre y cierra las válvulas sincronizado con el cigüeñal. En motores con VVT/VANOS, el actuador del extremo es la parte más afectada con los años.",
"reten o sello para componentes del motor": "Retén o sello del motor: contiene el aceite del componente (árbol de levas, cigüeñal, bomba) y bloquea polvo y agua. Se reemplaza siempre que se desmonta la pieza que sella.",
"bujia de encendido spark plug": "Bujía de encendido (spark plug): genera la chispa que enciende la mezcla en cada ciclo. Al desgastarse causa ralentí irregular, falta de potencia, arranque difícil y mayor consumo (código P0300-P0306).",
"turbocompresor turbo del motor": "Turbocompresor (turbo): comprime el aire de admisión aprovechando los gases de escape para dar más potencia. Falla por falta de lubricación, aceite contaminado o fatiga térmica de los rodamientos.",
"defensa parachoque o facia": "Defensa (parachoques): panel de carrocería que cubre el frontal o la trasera y aloja, según versión, los sensores de estacionamiento. Suele reemplazarse tras golpes menores.",
"banda correa de distribucion": "Banda de distribución o de accesorios: la de distribución sincroniza el cigüeñal con las levas; la de accesorios mueve alternador, dirección y A/C. Es mantenimiento periódico; su rotura puede dañar el motor.",
"bomba de direccion hidraulica": "Bomba de dirección hidráulica: genera la presión que asiste el giro del volante. Falla por desgaste interno (dirección dura) o por líquido contaminado que daña sus sellos.",
"terminal de direccion tie rod end": "Terminal de dirección (tie rod end): rótula que une la cremallera con la rueda y transmite el giro. Al aflojarse aparece holgura en el volante antes de mover las ruedas.",
"carter oil pan del motor": "Cárter (oil pan): depósito inferior que contiene el aceite del motor. Se reemplaza tras golpes en el piso o cuando se barre la rosca del tapón de drenado.",
"kit completo de cadena de tiempo": "Kit completo de cadena de tiempo: incluye cadena, tensor, guías y engranes para renovar todo el sistema de distribución. Recomendado sobre cambiar solo la cadena para no repetir la falla.",
"barra estabilizadora anti roll bar": "Barra estabilizadora (sway bar): reduce el balanceo del auto en curvas conectando ambos lados del eje. Rara vez se daña; lo común es que fallen sus bujes o bieletas.",
"valvula del motor admision o escape": "Válvula de motor (admisión o escape): controla la entrada de mezcla y la salida de gases en la cámara. Pieza estructural; se reemplaza durante reparación de la cabeza.",
"faro delantero del vehiculo": "Faro delantero: ilumina el frente en marcha nocturna (alta/baja) e integra funciones como direccional y luz de día (DRL). Vulnerable a impactos, opacado del cristal por UV y entrada de humedad.",
"manguera del sistema de refrigeracion": "Manguera del sistema de refrigeración: conduce el anticongelante entre radiador, bomba, termostato y motor. Se reemplaza al mostrar grietas, abultamientos o fugas.",
"alternador generador de corriente alterna": "Alternador: genera la electricidad que alimenta el auto en marcha y mantiene cargada la batería; lo mueve la banda de accesorios. Su falla descarga la batería y enciende el testigo de carga.",
"balastra modulo electronico de control de luz xenon": "Balastra (módulo) para faros HID/xenón: genera el alto voltaje que enciende el foco xenón y regula su arco. Una balastra dañada provoca focos que parpadean, no encienden o cambian de color.",
"junta del carter de aceite": "Junta del cárter de aceite: sella el cárter contra el block para evitar fugas. Falla típica: gotas de aceite bajo el motor y nivel que baja seguido.",
"moldura o embellecedor de carroceria": "Moldura o embellecedor exterior (techo, puerta, bisel de faro, etc.): pieza decorativa que además protege la carrocería de rayones menores.",
"rotula ball joint": "Rótula (ball joint) de suspensión o dirección: junta esférica que permite girar y mover la rueda. Al fallar su sello entra suciedad y aparece holgura: golpes en baches y dirección vaga.",
"manija manilla manija de puerta exterior": "Manija exterior de puerta: se acciona para abrir desde fuera; en algunos modelos integra el sensor keyless (Comfort Access). Suele venir sin pintar. Falla por rotura del mecanismo o del sensor.",
"rejilla o inserto del frontal": "Rejilla o inserto del frontal: panel con malla que se inserta en la parrilla o en aperturas de la facia; es estético y guía el aire a los radiadores. Se reemplaza por daño o para personalizar el acabado.",
"junta del colector de escape": "Junta del colector de escape: sella la unión entre el colector y la cabeza conteniendo los gases calientes. Falla típica: soplido (ticking) en frío que desaparece o se mantiene al calentar.",
"calavera luz trasera": "Calavera (luz trasera): integra freno, posición, direccional y reversa. Se daña por impactos, opacado por UV o humedad interna. Algunos modelos traen la pieza de salpicadera y la de cajuela por separado.",
"cadena de tiempo timing chain": "Cadena de tiempo (timing chain): sincroniza el cigüeñal con las levas. No tiene cambio programado, pero se desgasta con los años: tableteo y, en casos graves, salto de tiempo que daña el motor.",
"polea tensora del sistema de banda": "Polea tensora: mantiene la tensión de la banda de accesorios o de distribución. Su rodamiento se afloja con los años y aparece chillido o vibración.",
"filtro de aceite del motor": "Filtro de aceite: atrapa partículas y contaminantes del aceite del motor. Se cambia en cada servicio de aceite; saturado, abre el bypass y deja pasar suciedad.",
"kit de juntas de motor": "Kit de juntas de motor: incluye todas las juntas y sellos para una reparación mayor (cabeza, válvulas, admisión, escape, cárter, etc.). Sale más económico que comprarlas por separado.",
"biela del motor connecting rod": "Biela (connecting rod): conecta el pistón con el cigüeñal y transmite la fuerza de la combustión. Pieza estructural; se reemplaza solo en reparación mayor del block.",
"soporte central del cardan": "Soporte central del cardán (chumacera/center bearing): sostiene y alinea el cardán en su punto medio y absorbe vibraciones. Al cuartearse el caucho aparecen vibraciones a cierta velocidad y golpes al acelerar.",
"junta de goma del cardan": "Junta de goma del cardán (flex disc/guibo): disco de caucho que conecta el cardán con la transmisión o el diferencial y absorbe vibraciones. Al cuartearse vibra a 60-100 km/h; si se rompe, es falla de seguridad.",
"kit de cables de bujia": "Kit de cables de bujía: conducen el alto voltaje de la bobina (o distribuidor) a cada bujía. Aplica a motores con sistema DIS o distribuidor; no a motores COP (cada bujía con su bobina).",
"piston del motor con bulones y aros": "Pistón con bulón y aros: pieza estructural del motor en aluminio forjado o fundido. Se reemplaza solo en reparación mayor del block (overhaul).",
"junta o empaque del motor": "Junta o empaque de motor: mantiene la estanqueidad entre dos superficies del motor (cabeza-block, colector, tapa de válvulas, etc.). Se reemplaza siempre que se desarma el componente.",
"actuador electrico de la chapa de cerradura": "Actuador eléctrico de la chapa de cerradura: motor que mueve el mecanismo del cierre centralizado. Falla por motor quemado, engranes rotos o falsa conexión (común en puertas traseras y cajuela de BMW).",
"kit completo de clutch embrague": "Kit de clutch (embrague) para transmisión manual: incluye disco, plato de presión y collarín. Transmite el torque del motor a la caja y permite cambiar de marcha. Pieza de desgaste.",
"cristal luna de carroceria": "Cristal (luna) de carrocería: de puerta, lateral o trasero, templado o laminado según la posición. Algunos integran calefactor, antena o sensor de lluvia. Se reemplaza por rotura.",
"motor de arranque starter motor o marcha": "Motor de arranque (marcha): gira el motor durante el arranque hasta que enciende. Es de los componentes que más corriente consume; requiere batería en buen estado.",
"espejo retrovisor lateral o componente del espejo": "Espejo retrovisor lateral o uno de sus componentes (cristal, carcasa, motor, direccional): los espejos modernos integran ajuste eléctrico, calefactor, direccional y sensor de punto ciego. Revisa la ficha por el componente exacto.",
"compresor del sistema de aire acondicionado": "Compresor del aire acondicionado: comprime el refrigerante para que el sistema enfríe; lo mueve la banda con un embrague electromagnético. Su falla deja de enfriar, hace ruido al activarse o fuga por el sello.",
"intercooler": "Intercooler: enfría el aire comprimido del turbo antes de entrar al motor para dar más potencia y eficiencia. Vulnerable a impactos de piedra y a obstrucción interna por aceite del turbo.",
"soporte de transmision transmission mount": "Soporte de transmisión: bloque de caucho-metal que sujeta la caja al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones en ralentí y golpes al cambiar de marcha.",
"ventilador del radiador radiator fan": "Ventilador del radiador: motor eléctrico con aspas que fuerza aire por el radiador y el condensador cuando el avance no basta para enfriar. Se reemplaza si se quema el motor o se rompen las aspas.",
"tornilleria abrazaderas o accesorios de fijacion": "Tornillería y accesorios de fijación de suspensión (tornillos TTY, tuercas de rótula, clips). Estos tornillos especiales se reemplazan al desmontar; no se reutilizan.",
"cable del freno de mano": "Cable del freno de mano: une la palanca con los frenos traseros. Falla por desgaste (la palanca sube mucho), oxidación (cable atascado, freno que no libera) o ruptura.",
"puerta o panel de puerta del vehiculo": "Puerta o panel de puerta: la puerta exterior se monta a las charnelas; el panel es la cubierta interior de la cabina. La puerta viene sin cerradura, ventana ni motor — se transfieren de la original.",
"salpicadera guardafango o fender": "Salpicadera (guardafango) o tolva interior: la salpicadera es el panel sobre la rueda; la tolva protege el interior del agua y las piedras. Se reemplazan por golpes o por degradación del plástico.",
"motor del ventilador motoventilador o blower motor": "Motor del ventilador (soplador de cabina o motoventilador del frente): el de cabina mueve el aire del A/C hacia el interior; el del frente enfría el radiador. Su falla deja sin flujo de aire o sobrecalienta en tráfico.",
"bomba de aceite oil pump": "Bomba de aceite: genera la presión de lubricación que protege bancadas, bielas y árbol de levas. Falla crítica: una bomba dañada arruina el motor por falta de lubricación.",
"componente de la caja transfer": "Componente de la caja transfer (4WD/AWD): la transfer reparte el torque entre los ejes. En xDrive/4Matic/quattro suele fallar el servomotor o los baleros del eje.",
"manguera o codo del cuerpo de aceleracion": "Manguera/codo de admisión (intake boot): conecta el cuerpo de aceleración con el colector o el filtro de aire. Al endurecerse y agrietarse causa entrada de aire falso, ralentí irregular y mezcla pobre.",
"bomba maestra del freno master cylinder": "Bomba maestra de freno (master cylinder): convierte la fuerza del pedal en presión hidráulica para los cuatro frenos. Falla típica: el pedal se va al piso al mantenerlo pisado (fuga interna).",
"modulo electronico de control ecu": "Módulo de control del motor (ECU/DME/Motronic): cerebro del motor que gestiona inyección, encendido y emisiones. Suele requerir codificación al VIN en taller especializado.",
"chapa de cerradura del vehiculo": "Chapa de cerradura: mecanismo de la puerta o cajuela que libera la apertura; integra motor del cierre centralizado y sensor de posición. Falla por actuador quemado o mecanismo desgastado.",
"filtro de aceite de la transmision automatica": "Filtro de aceite de transmisión automática: atrapa partículas del ATF para proteger solenoides y embragues. Se cambia obligatoriamente junto con el aceite ATF; a veces viene integrado con la cuba.",
"reten o sello para componentes de la transmision": "Retén o sello de transmisión o eje motriz: contiene el aceite de la caja o diferencial y bloquea polvo y agua. Se reemplaza al desmontar el componente; su labio se cuartea con el uso.",
"aleron trasero": "Alerón de defensa: pieza aerodinámica que se monta en la defensa para generar carga o redirigir el aire. Estético-deportivo; complementa los paquetes M/AMG/S-Line.",
"panal del radiador radiator core": "Panal de radiador (radiator core): intercambiador que enfría el refrigerante con el paso de aire por sus aletas. Vulnerable a impactos de piedra y corrosión interna con los años.",
"valvula solenoide vvt": "Válvula solenoide VVT / VANOS: dirige el aceite al actuador del árbol de levas variable para optimizar potencia y consumo. Su falla da códigos del sistema variable y pérdida de torque en bajas.",
"caliper pinza mordaza de freno": "Caliper (mordaza) de freno: aloja las balatas y los pistones que las empujan contra el disco. Falla por pistones atascados por óxido, fugas por sellos o guías engranadas.",
"tubo o pozo de bujia spark plug tube": "Tubo/pozo de bujía (spark plug tube): aloja la bujía y la bobina dentro de la tapa de válvulas, con un sello que impide que el aceite entre al pozo. Al fallar el sello entra aceite y falla la combustión (común en BMW 6 cil).",
"kit de reparacion del sistema vanos": "Kit de reparación VANOS para BMW M52/M54/M56: renueva los sellos internos del sistema de levas variable, restaurando su función sin cambiar la unidad completa. Trabajo especializado.",
"resistencia tambien llamada herizo": "Resistencia del soplador (erizo / módulo del blower): regula la velocidad del ventilador del A/C. Al quemarse, el ventilador deja de funcionar en algunas velocidades o se apaga; puede oler a quemado.",
"tubo de agua del sistema de calefaccion": "Tubo de agua del sistema de enfriamiento: conducto rígido de aluminio o plástico que lleva el refrigerante entre motor, calefactor y depósito. Falla por fuga en la junta o rotura del plástico (común en BMW 6 cil).",
}
# clave normalizada -> rewrite, ordenadas por longitud de clave desc (gana la mas larga)
REWRITES = sorted(((norm(k), v) for k, v in REWRITES_RAW.items()),
                  key=lambda kv: -len(kv[0]))

GENERIC_PREFIXES = [norm(p) for p in (
    "componente de", "soporte brazo o refuerzo",
)]

# Definiciones por keyword para intros genericos (se busca en la pieza del titulo)
KEYWORD_DEFS_RAW = [
    # --- tipos frecuentes que el titulo nombra distinto / faltaban ---
    ("enfriador de aceite", "Enfriador de aceite (oil cooler): intercambiador que baja la temperatura del aceite del motor o de la transmisión para protegerlo del sobrecalentamiento."),
    ("enfriador aceite", "Enfriador de aceite (oil cooler): intercambiador que baja la temperatura del aceite del motor o de la transmisión para protegerlo del sobrecalentamiento."),
    ("enfriador de", "Enfriador (intercambiador de calor) del sistema indicado en el título: baja la temperatura del fluido para protegerlo del sobrecalentamiento."),
    ("tornillo estabilizador", "Bieleta (tornillo estabilizador / sway bar link): conecta el brazo de suspensión con la barra estabilizadora. Al aflojarse sus rótulas aparece golpeteo al pasar baches."),
    ("filtro aceite", "Filtro de aceite: atrapa partículas y contaminantes del aceite del motor. Se cambia en cada servicio de aceite."),
    ("bomba gasolina", "Bomba de combustible: envía el combustible del tanque al motor a la presión requerida."),
    ("cubre polvo", "Cubrepolvo (fuelle/bota): protege una junta o rótula del polvo y el agua. Al romperse entra suciedad y se daña el componente que protege."),
    ("cubrepolvo", "Cubrepolvo (fuelle/bota): protege una junta o rótula del polvo y el agua. Al romperse entra suciedad y se daña el componente que protege."),
    ("balero maza", "Balero (rodamiento) de maza/rueda: permite el giro libre de la rueda. Al desgastarse zumba en marcha y genera holgura."),
    ("balero doble", "Balero (rodamiento) doble de rueda: permite el giro libre de la rueda. Al desgastarse zumba en marcha y genera holgura."),
    ("balero de", "Balero (rodamiento): permite el giro libre de la pieza que aloja. Al desgastarse zumba o genera holgura."),
    ("balero", "Balero (rodamiento): permite el giro libre de la pieza que aloja. Al desgastarse zumba o genera holgura."),
    ("tapa de punterias", "Tapa de punterías (tapa de válvulas): cubre el tren de válvulas en la parte alta de la cabeza. Su junta fuga aceite al endurecerse el caucho."),
    ("tapa punterias", "Tapa de punterías (tapa de válvulas): cubre el tren de válvulas en la parte alta de la cabeza. Su junta fuga aceite al endurecerse el caucho."),
    ("tubo de agua", "Tubo de agua del sistema de enfriamiento: conducto rígido que lleva el refrigerante entre motor, calefactor y depósito. Falla por fuga en la junta o rotura del plástico."),
    ("tubo agua", "Tubo de agua del sistema de enfriamiento: conducto rígido que lleva el refrigerante entre motor, calefactor y depósito. Falla por fuga en la junta o rotura del plástico."),
    ("flecha homocinetica", "Flecha homocinética (junta CV): transmite el giro del diferencial a la rueda permitiendo el movimiento de la suspensión y la dirección. Falla típica: cubrepolvo roto y traqueteo al girar."),
    ("separador de aceite", "Separador de aceite (oil separator / válvula PCV): separa el aceite de los gases del cárter antes de devolverlos a la admisión. Al fallar consume aceite y da ralentí irregular."),
    ("separador aceite", "Separador de aceite (oil separator / válvula PCV): separa el aceite de los gases del cárter antes de devolverlos a la admisión. Al fallar consume aceite y da ralentí irregular."),
    ("deposito direccion", "Depósito de líquido de dirección hidráulica: almacena el aceite que asiste el giro del volante."),
    ("licuadora", "Licuadora (cremallera) de dirección hidráulica: convierte el giro del volante en movimiento de las ruedas. Falla por fugas de aceite y dirección dura o con holgura."),
    ("control maestro", "Control maestro de elevavidrios: switch del lado del conductor que opera los vidrios eléctricos y el seguro de puertas."),
    ("brida toma", "Toma/brida de agua: conexión del circuito de refrigeración donde se unen mangueras y sensores. Suele fugar al agrietarse el plástico con el calor."),
    ("toma de agua", "Toma/brida de agua: conexión del circuito de refrigeración donde se unen mangueras y sensores. Suele fugar al agrietarse el plástico con el calor."),
    ("empaque enfriador", "Empaque/junta del enfriador de aceite: sella el enfriador contra el block para evitar fugas de aceite o refrigerante."),
    ("liga enfriador", "Empaque/junta del enfriador de aceite: sella el enfriador contra el block para evitar fugas de aceite o refrigerante."),
    ("llavero", "Llavero de colección con el logo o emblema de la marca. Artículo de merchandising (no es una refacción)."),
    ("condensador", "Condensador del aire acondicionado: disipa el calor del refrigerante (va delante del radiador). Vulnerable a impactos de piedra y a fugas por corrosión."),
    ("evaporador", "Evaporador del aire acondicionado: absorbe el calor del interior para enfriar la cabina. Falla por fugas internas de refrigerante."),
    ("inyector", "Inyector de combustible: pulveriza el combustible en la admisión o el cilindro. Su falla causa ralentí irregular y mayor consumo."),
    ("junta de cabeza", "Junta de cabeza (head gasket): sella la cámara de combustión entre el block y la cabeza. Su falla mezcla aceite y refrigerante y sobrecalienta el motor."),
    ("damper", "Damper / polea de cigüeñal (harmonic balancer): integra un amortiguador de vibraciones de torsión. Su caucho se agrieta o desprende con los años."),
    # --- tipos de pieza mayores (para intros genericos cuyo titulo si los nombra) ---
    ("amortiguador de cofre", "Amortiguador (pistón a gas) de cofre o cajuela: mantiene abierta la tapa sin que se caiga. Al perder gas deja de sostenerla; conviene reemplazar por par."),
    ("amortiguador cofre", "Amortiguador (pistón a gas) de cofre o cajuela: mantiene abierta la tapa sin que se caiga. Al perder gas deja de sostenerla; conviene reemplazar por par."),
    ("amortiguador de cajuela", "Amortiguador (pistón a gas) de cofre o cajuela: mantiene abierta la tapa sin que se caiga. Al perder gas deja de sostenerla; conviene reemplazar por par."),
    ("amortiguador cajuela", "Amortiguador (pistón a gas) de cofre o cajuela: mantiene abierta la tapa sin que se caiga. Al perder gas deja de sostenerla; conviene reemplazar por par."),
    ("amortiguador de aire", "Amortiguador de aire (air strut) de suspensión neumática: integra la bolsa de aire con el amortiguador hidráulico. Una fuga obliga al compresor a trabajar de más y descarga la batería."),
    ("amortiguador", "Amortiguador de la suspensión: controla el movimiento del resorte para mantener la estabilidad, el confort de marcha y el agarre del neumático. Pieza de desgaste; conviene reemplazar por pares del mismo eje."),
    ("sensor de estacionamiento", "Sensor de estacionamiento (PDC): detecta la distancia a obstáculos al estacionar y avisa al sistema de alerta del vehículo."),
    ("sensor estacionamiento", "Sensor de estacionamiento (PDC): detecta la distancia a obstáculos al estacionar y avisa al sistema de alerta del vehículo."),
    ("sensor abs", "Sensor ABS (velocidad de rueda): mide la velocidad de cada rueda para el ABS y el control de estabilidad. Su falla enciende el testigo ABS."),
    ("balatas", "Balatas (pastillas) de freno: material de fricción que aprieta el disco para detener el vehículo. Pieza de desgaste; se cambian al chillar al frenar, vibrar el pedal o encender el testigo de freno."),
    ("balata", "Balatas (pastillas) de freno: material de fricción que aprieta el disco para detener el vehículo. Pieza de desgaste; se cambian al chillar al frenar o encender el testigo de freno."),
    ("disco de freno", "Disco de freno (rotor): superficie sobre la que actúan las balatas para detener el vehículo. Pieza de desgaste; se reemplaza por desgaste, ranurado o alabeo (vibración al frenar)."),
    ("disco freno", "Disco de freno (rotor): superficie sobre la que actúan las balatas para detener el vehículo. Pieza de desgaste; se reemplaza por desgaste, ranurado o alabeo (vibración al frenar)."),
    ("caliper", "Caliper (mordaza) de freno: aloja las balatas y los pistones que las empujan contra el disco. Falla por pistones atascados por óxido o fugas por sellos."),
    ("parrilla", "Parrilla del frontal: panel que cubre el frente del cofre, deja pasar aire al radiador y define la imagen del auto. Suele dañarse por impactos de piedra o golpes menores."),
    ("defensa", "Defensa (parachoques): panel de carrocería del frontal o la trasera que aloja, según versión, los sensores de estacionamiento. Suele reemplazarse tras golpes menores."),
    ("bomba de agua", "Bomba de agua: hace circular el refrigerante por el motor y el radiador para mantener la temperatura. El sello interno falla con los años y aparece fuga por el respiradero."),
    ("radiador", "Radiador del motor: intercambiador que enfría el refrigerante haciéndole pasar aire por sus aletas. Vulnerable a impactos de piedra y a corrosión interna con los años."),
    ("soporte de motor", "Soporte (taco) de motor: bloque de caucho-metal que sujeta el motor al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones en ralentí y golpes al acelerar."),
    ("soporte motor", "Soporte (taco) de motor: bloque de caucho-metal que sujeta el motor al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones en ralentí y golpes al acelerar."),
    ("taco de motor", "Soporte (taco) de motor: bloque de caucho-metal que sujeta el motor al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones en ralentí y golpes al acelerar."),
    ("soporte de transmision", "Soporte de transmisión: bloque de caucho-metal que sujeta la caja al chasis y absorbe sus vibraciones. Al cuartearse aparecen vibraciones y golpes al cambiar de marcha."),
    ("brazo de suspension", "Brazo de suspensión (control arm): conecta la rueda con el chasis y mantiene la geometría de la dirección. Se reemplaza cuando sus bujes o rótulas se desgastan."),
    ("horquilla", "Horquilla (bandeja) de suspensión: brazo que conecta la rueda al chasis y permite el movimiento de la suspensión. Se reemplaza cuando sus bujes o rótulas se desgastan."),
    ("terminal de direccion", "Terminal de dirección (tie rod end): rótula que une la cremallera con la rueda y transmite el giro. Al aflojarse aparece holgura en el volante."),
    ("rotula", "Rótula (ball joint) de suspensión o dirección: junta esférica que permite girar y mover la rueda. Al fallar su sello aparece holgura: golpes en baches y dirección vaga."),
    ("bieleta", "Bieleta (tirante) de la barra estabilizadora: conecta el brazo de suspensión con la barra. Al aflojarse sus rótulas aparece golpeteo al pasar baches a baja velocidad."),
    ("barra estabilizadora", "Barra estabilizadora (sway bar): reduce el balanceo en curvas conectando ambos lados del eje. Rara vez se daña; lo común es que fallen sus bujes o bieletas."),
    ("buje", "Buje (casquillo) de suspensión: pieza de caucho-metal que aísla la unión entre componentes de la suspensión y absorbe vibraciones. Al cuartearse aparecen golpes y holgura."),
    ("bobina de encendido", "Bobina de encendido: eleva los 12V de la batería al alto voltaje que necesita la bujía para la chispa. Una bobina dañada apaga su cilindro (código P0300-P0306)."),
    ("bobina", "Bobina de encendido: eleva los 12V de la batería al alto voltaje que necesita la bujía para la chispa. Una bobina dañada apaga su cilindro (código P0300-P0306)."),
    ("bujias", "Bujías de encendido: generan la chispa que enciende la mezcla en cada ciclo. Al desgastarse causan ralentí irregular, falta de potencia y mayor consumo."),
    ("bujia", "Bujía de encendido: genera la chispa que enciende la mezcla en cada ciclo. Al desgastarse causa ralentí irregular, falta de potencia y mayor consumo."),
    ("alternador", "Alternador: genera la electricidad que alimenta el auto en marcha y mantiene cargada la batería. Su falla descarga la batería y enciende el testigo de carga."),
    ("motor de arranque", "Motor de arranque (marcha): gira el motor durante el arranque hasta que enciende. Requiere batería en buen estado por su alto consumo."),
    ("marcha", "Motor de arranque (marcha): gira el motor durante el arranque hasta que enciende. Requiere batería en buen estado por su alto consumo."),
    ("compresor", "Compresor del aire acondicionado: comprime el refrigerante para que el sistema enfríe; lo mueve la banda. Su falla deja de enfriar, hace ruido o fuga por el sello."),
    ("calavera", "Calavera (luz trasera): integra freno, posición, direccional y reversa. Se daña por impactos, opacado por UV o humedad interna."),
    ("faro", "Faro delantero: ilumina el frente en marcha nocturna (alta/baja) e integra direccional y luz de día. Vulnerable a impactos, opacado por UV y entrada de humedad."),
    ("espejo", "Espejo retrovisor lateral o uno de sus componentes (cristal, carcasa, motor, direccional). Los modernos integran ajuste eléctrico, calefactor y sensor de punto ciego."),
    ("manija", "Manija exterior de puerta: se acciona para abrir desde fuera; algunos modelos integran el sensor keyless. Suele venir sin pintar."),
    ("manilla", "Manija exterior de puerta: se acciona para abrir desde fuera; algunos modelos integran el sensor keyless. Suele venir sin pintar."),
    ("tensor", "Tensor de banda o cadena: mantiene la tensión correcta compensando el desgaste. Su rodamiento o mecanismo se afloja con los años (chillido o tableteo)."),
    ("termostato", "Termostato: válvula que regula el paso de refrigerante al radiador según la temperatura del motor. Falla atascado abierto (no calienta) o cerrado (sobrecalienta)."),
    ("deposito de anticongelante", "Depósito de anticongelante: contiene el refrigerante y absorbe su expansión por calor. Falla típica: se raja el plástico con fuga."),
    ("deposito anticongelante", "Depósito de anticongelante: contiene el refrigerante del sistema de enfriamiento y absorbe su expansión por calor."),
    ("deposito de agua", "Depósito de anticongelante: contiene el refrigerante del sistema de enfriamiento y absorbe su expansión por calor."),
    ("bomba de direccion", "Bomba de dirección hidráulica: genera la presión que asiste el giro del volante. Falla por desgaste interno (dirección dura) o líquido contaminado."),
    ("bomba de aceite", "Bomba de aceite: genera la presión de lubricación que protege bancadas, bielas y árbol de levas. Falla crítica que puede arruinar el motor."),
    ("turbo", "Turbocompresor (turbo): comprime el aire de admisión con los gases de escape para dar más potencia. Falla por falta de lubricación o fatiga térmica."),
    ("intercooler", "Intercooler: enfría el aire comprimido del turbo antes de entrar al motor para más potencia y eficiencia. Vulnerable a impactos y a obstrucción por aceite."),
    ("clutch", "Kit de clutch (embrague) de transmisión manual: disco, plato de presión y collarín. Transmite el torque del motor a la caja. Pieza de desgaste."),
    ("embrague", "Kit de embrague (clutch) de transmisión manual: disco, plato de presión y collarín. Transmite el torque del motor a la caja. Pieza de desgaste."),
    ("ventilador", "Ventilador del radiador: motor eléctrico con aspas que fuerza aire por el radiador y el condensador cuando el avance no basta. Se reemplaza si se quema el motor o se rompen las aspas."),
    ("manguera", "Manguera del sistema de refrigeración: conduce el anticongelante entre radiador, bomba, termostato y motor. Se reemplaza al mostrar grietas, abultamientos o fugas."),
    ("moldura", "Moldura o embellecedor exterior: pieza decorativa que además protege la carrocería de rayones menores."),
    ("salpicadera", "Salpicadera (guardafango) o tolva interior: panel sobre la rueda o protección interior contra agua y piedras. Se reemplaza por golpes o degradación del plástico."),
    ("cristal", "Cristal (luna) de carrocería: de puerta, lateral o trasero. Algunos integran calefactor, antena o sensor de lluvia. Se reemplaza por rotura."),
    ("balastra", "Balastra (módulo) para faros HID/xenón: genera el alto voltaje que enciende el foco y regula su arco. Dañada, el foco parpadea, no enciende o cambia de color."),
    # --- piezas chicas / mantenimiento ---
    ("filtro de aceite", "Filtro de aceite: atrapa partículas y contaminantes del aceite del motor. Se cambia en cada servicio de aceite."),
    ("filtro de aire", "Filtro de aire: retiene polvo y suciedad del aire que entra al motor. Se reemplaza por servicio."),
    ("filtro aire", "Filtro de aire: retiene polvo y suciedad del aire que entra al motor. Se reemplaza por servicio."),
    ("filtro de cabina", "Filtro de cabina (antipolen): limpia el aire que entra a la cabina por el A/C."),
    ("filtro cabina", "Filtro de cabina (antipolen): limpia el aire que entra a la cabina por el A/C."),
    ("filtro de polen", "Filtro de cabina (antipolen): limpia el aire que entra a la cabina por el A/C."),
    ("filtro de combustible", "Filtro de combustible: retiene impurezas del combustible antes de los inyectores."),
    ("filtro de gasolina", "Filtro de combustible: retiene impurezas del combustible antes de los inyectores."),
    ("filtro diesel", "Filtro de combustible (diésel): retiene impurezas y agua antes del sistema de inyección."),
    ("sensor de oxigeno", "Sensor de oxígeno (sonda lambda): mide el oxígeno del escape para ajustar la mezcla. Su falla sube el consumo y enciende el check engine."),
    ("sensor oxigeno", "Sensor de oxígeno (sonda lambda): mide el oxígeno del escape para ajustar la mezcla. Su falla sube el consumo y enciende el check engine."),
    ("sonda lambda", "Sensor de oxígeno (sonda lambda): mide el oxígeno del escape para ajustar la mezcla."),
    ("sensor maf", "Sensor MAF (masa de aire): mide el aire que entra al motor para dosificar el combustible. Su falla causa tirones y falta de potencia."),
    ("sensor de masa", "Sensor MAF (masa de aire): mide el aire que entra al motor para dosificar el combustible."),
    ("masa de aire", "Sensor MAF (masa de aire): mide el aire que entra al motor para dosificar el combustible."),
    ("sensor de arbol", "Sensor de árbol de levas: informa la posición de las levas a la computadora para el encendido y la inyección."),
    ("sensor arbol", "Sensor de árbol de levas: informa la posición de las levas a la computadora para el encendido y la inyección."),
    ("sensor de levas", "Sensor de árbol de levas: informa la posición de las levas a la computadora para el encendido y la inyección."),
    ("sensor de ciguenal", "Sensor de cigüeñal: informa la posición y velocidad del cigüeñal; su falla impide el arranque."),
    ("sensor ciguenal", "Sensor de cigüeñal: informa la posición y velocidad del cigüeñal; su falla impide el arranque."),
    ("sensor de cigue", "Sensor de cigüeñal: informa la posición y velocidad del cigüeñal; su falla impide el arranque."),
    ("valvula pcv", "Válvula PCV: regula los gases del cárter de vuelta a la admisión. Al fallar causa fugas de aceite y ralentí irregular."),
    ("fan clutch", "Fan clutch (embrague del ventilador): acopla el ventilador al motor según la temperatura para enfriar el radiador."),
    ("motoventilador", "Motoventilador: ventilador eléctrico que enfría el radiador y el condensador cuando el avance del auto no basta."),
    ("inyector", "Inyector de combustible: pulveriza el combustible en la admisión o el cilindro. Su falla causa ralentí irregular y mayor consumo."),
    ("bomba de gasolina", "Bomba de combustible: envía el combustible del tanque al motor a la presión requerida."),
    ("bomba de combustible", "Bomba de combustible: envía el combustible del tanque al motor a la presión requerida."),
    ("cuerpo de aceleracion", "Cuerpo de aceleración: regula el aire que entra al motor según el pedal del acelerador."),
    ("valvula egr", "Válvula EGR: recircula parte de los gases de escape para reducir emisiones. Tiende a obstruirse con carbón."),
    ("emblema", "Emblema/insignia de carrocería: pieza decorativa de identificación del modelo."),
    ("cantonera", "Cantonera/moldura de salpicadera: pieza plástica de protección y estética del costado."),
    ("modulo led", "Módulo LED de iluminación: controla las luces LED del faro o la calavera."),
    ("herramienta", "Herramienta especializada de servicio para motores europeos. Revisa la ficha para la aplicación exacta."),
    ("base filtro", "Base/portafiltro de aceite: aloja el filtro y dirige el aceite del motor; suele incluir enfriador y sellos."),
    ("base de filtro", "Base/portafiltro de aceite: aloja el filtro y dirige el aceite del motor; suele incluir enfriador y sellos."),
    ("polea", "Polea: transmite el giro de la banda a un accesorio del motor; su rodamiento se desgasta con el uso."),
    ("valvula", "Válvula del sistema; revisa la ficha para su función exacta."),
    ("sensor", "Sensor electrónico del vehículo; revisa la ficha para la magnitud que mide y su posición."),
]
KEYWORD_DEFS = [(norm(k), v) for k, v in KEYWORD_DEFS_RAW]
KEYWORD_DEFS.sort(key=lambda kv: -len(kv[0]))

MARCAS_PROPIAS = ("marca original", "marca embler")

# ---------- secciones fijas (Envio / Antes de Comprar) ----------
NEW_ENVIO = (
    "<p>Tenemos stock disponible para entrega inmediata:</p>"
    "<ul>"
    "<li>⚡ Envío Exprés (30 - 60 min): Entrega para CDMX, Edo. Méx., Querétaro y Puebla</li>"
    "<li>📦 Envío Nacional (mismo día): Despachamos hoy mismo a todo el país vía FedEx, DHL o Estafeta</li>"
    "</ul>"
)
ANTES_COMPRAR = (
    "<p>Una vez realizada tu compra, un asesor te contactará brevemente para "
    "validar la compatibilidad con tu número de serie (VIN) y garantizar que "
    "recibas exactamente lo que tu auto necesita.</p>"
)
ENVIO_GENERICO = ("Tenemos stock disponible para entrega inmediata. Enviamos el "
                  "mismo dia de tu pago a Ciudad de Mexico y a todo el pais via "
                  "DHL o FedEx.")

# ---------- productos complemento (sugerencia por tipo de pieza) ----------
def _C(parts, reason):
    """La sugerencia de complemento se guarda como (piezas, motivo); el envoltorio
    (apertura/cierre) se arma al vuelo, variándolo por producto."""
    return (parts, reason)


# Variantes de apertura y cierre del párrafo de complemento (se elige por hash del
# handle, para que no sea idéntico en todo el catálogo).
_OPEN = [
    "Para asegurar una reparación completa y evitar fallas recurrentes, te recomendamos revisar también ",
    "Aprovecha la reparación para revisar también ",
    "Para que el arreglo dure y no regrese la falla, conviene revisar también ",
    "Te recomendamos atender al mismo tiempo ",
]
_CLOSE = [
    " Consulta con nuestro asesor para confirmar disponibilidad y armar tu reparación completa.",
    " Escríbenos y un asesor te ayuda a reunir todo en un solo pedido.",
    " Pregúntale a nuestro asesor por la disponibilidad de estas piezas.",
    " Consúltanos y te ayudamos a dejar la reparación completa.",
]


def build_complemento(tup, handle):
    """Arma el párrafo final desde (piezas, motivo), con envoltorio variado."""
    if not tup or not isinstance(tup, tuple):
        return ""
    parts, reason = tup
    h = int(hashlib.md5((handle or "").encode("utf-8")).hexdigest(), 16)
    apertura = _OPEN[h % len(_OPEN)]
    cierre = _CLOSE[(h // len(_OPEN)) % len(_CLOSE)]
    return apertura + parts + ". " + reason + cierre


COMPLEMENTO_GENERICO = _C(
    "las piezas asociadas (juntas, sellos y tornillería) o la del lado opuesto del eje",
    "Suelen desgastarse al mismo ritmo y, si se reutilizan, pueden provocar que la falla "
    "regrese poco después de la reparación.")
_ENFRIA = _C(
    "el anticongelante, las mangueras de refrigeración y la tapa del depósito",
    "Trabajan en el mismo circuito de enfriamiento y, si están desgastados, pueden "
    "provocar fugas o que el motor vuelva a sobrecalentar.")
_FRENO_B = _C(
    "los discos de freno, el sensor de desgaste de balata y el líquido de frenos",
    "Trabajan junto con las balatas y, si están desgastados, pueden generar vibración, "
    "ruido o un frenado deficiente.")
_FRENO_D = _C(
    "las balatas, el sensor de desgaste de balata y el líquido de frenos",
    "Trabajan junto con el disco y, si están desgastados, pueden generar vibración, ruido "
    "o un frenado deficiente.")
_SUSP = _C(
    "las rótulas, los bujes y las bieletas de la suspensión",
    "Trabajan en conjunto y, si presentan holgura o desgaste, pueden provocar ruidos, "
    "golpeteos al pasar baches y desgaste irregular del neumático.")
_ENC = _C(
    "las bujías y las bobinas de encendido, además de los sellos o pozos de bujía",
    "Si alguno está desgastado o con fuga de aceite, puede provocar fallos de combustión, "
    "ralentí irregular o el testigo de motor encendido.")
_DIST = _C(
    "el tensor, las guías, las poleas y los sellos del sistema de distribución",
    "Trabajan junto con la cadena o banda y, si están desgastados, pueden generar ruido o "
    "saltos de tiempo poco después del cambio.")
_JUNTAS = _C(
    "el kit de juntas de motor, los sellos o retenes y los birlos de cabeza",
    "Si se reutilizan piezas viejas, pueden aparecer nuevas fugas de aceite o refrigerante "
    "tras el armado.")
_CARRO = _C(
    "los clips o grapas de montaje y el servicio de pintura para igualar el color",
    "Sin ellos, la pieza puede quedar floja o con un acabado que no coincide con tu "
    "vehículo.")
_AC = _C(
    "el filtro deshidratador, la válvula de expansión y la carga de gas del A/C",
    "Trabajan en el mismo circuito y, si no se atienden, el sistema puede volver a fallar "
    "o no enfriar correctamente.")

# (token a buscar en intro+titulo) -> sugerencia. Cadena vacia = sin complemento.
COMPLEMENTOS_RAW = [
    ("deposito de anticongelante", _ENFRIA), ("deposito anticongelante", _ENFRIA),
    ("bomba de agua", _C("el anticongelante, el termostato y la banda que la acciona", "Trabajan en el mismo sistema de enfriamiento y, si están desgastados, pueden provocar fugas o sobrecalentamiento poco después del cambio.")),
    ("bomba agua", _C("el anticongelante, el termostato y la banda que la acciona", "Trabajan en el mismo sistema de enfriamiento y, si están desgastados, pueden provocar fugas o sobrecalentamiento poco después del cambio.")),
    ("radiador", _C("el anticongelante, las mangueras del radiador, la tapa del radiador y el termostato", "Trabajan en el mismo circuito de enfriamiento y, si están desgastados, pueden provocar fugas o que el motor vuelva a sobrecalentar.")),
    ("termostato", _ENFRIA),
    ("manguera", _ENFRIA), ("tubo de agua", _ENFRIA), ("tubo agua", _ENFRIA),
    ("toma de agua", _ENFRIA), ("brida toma", _ENFRIA),
    ("enfriador", _C("las juntas o empaques del enfriador y el aceite o anticongelante según el sistema", "Si se reutiliza un empaque viejo, puede aparecer una fuga nueva poco después de instalar el enfriador.")),
    ("motoventilador", _C("el anticongelante, el radiador y el sensor de temperatura", "Trabajan en el sistema de enfriamiento y, si fallan, el motor puede volver a sobrecalentar en tráfico.")),
    ("ventilador", _C("el anticongelante, el radiador y el sensor de temperatura", "Trabajan en el sistema de enfriamiento y, si fallan, el motor puede volver a sobrecalentar en tráfico.")),
    ("balata", _FRENO_B),
    ("disco de freno", _FRENO_D), ("disco freno", _FRENO_D),
    ("sensor de desgaste", _C("las balatas y los discos de freno", "Este sensor se activa con el desgaste de las balatas; si no se cambian juntas, el testigo de freno puede encenderse de nuevo.")),
    ("caliper", _C("las balatas, los discos, las mangueras de freno y el líquido de frenos", "Trabajan junto con el caliper y, si están desgastados, pueden generar fugas, vibración o un frenado deficiente.")),
    ("bomba maestra", _C("el líquido de frenos, la purga del sistema y el estado de balatas y discos", "Trabajan en el mismo sistema hidráulico y, si no se atienden, el pedal puede seguir sintiéndose esponjoso.")),
    ("freno de mano", _C("las balatas o zapatas traseras y el mecanismo del freno de mano", "Trabajan en conjunto y, si están desgastados, el freno de mano puede seguir sin sujetar bien.")),
    ("amortiguador de cofre", ""), ("amortiguador cofre", ""),
    ("amortiguador de cajuela", ""), ("amortiguador cajuela", ""),
    ("amortiguador de aire", _C("el compresor de la suspensión neumática y las válvulas del sistema", "Trabajan en el mismo sistema y, si el compresor está forzado, la nueva bolsa o amortiguador puede volver a fallar.")),
    ("bolsa de aire", _C("el compresor de la suspensión neumática y las válvulas del sistema", "Trabajan en el mismo sistema y, si el compresor está forzado, la nueva bolsa o amortiguador puede volver a fallar.")),
    ("amortiguador", _C("las bases o cazoletas de amortiguador, los bujes y las bieletas de la suspensión", "Trabajan en conjunto y, si presentan desgaste, pueden provocar ruidos y un manejo inestable aunque el amortiguador sea nuevo.")),
    ("brazo de suspension", _SUSP), ("horquilla", _SUSP), ("buje", _SUSP),
    ("rotula", _SUSP),
    ("terminal de direccion", _C("las rótulas, la terminal del otro lado y la alineación posterior", "Trabajan en conjunto en la dirección y, si una está gastada, el volante puede seguir con holgura y desgastar los neumáticos.")),
    ("bieleta", _C("los bujes de la barra estabilizadora, las rótulas y la bieleta del otro lado", "Trabajan en conjunto y, si una está floja, el golpeteo al pasar baches puede continuar.")),
    ("tornillo estabilizador", _C("los bujes de la barra estabilizadora, las rótulas y la bieleta del otro lado", "Trabajan en conjunto y, si una está floja, el golpeteo al pasar baches puede continuar.")),
    ("barra estabilizadora", _C("los bujes y las bieletas de la barra estabilizadora", "Trabajan en conjunto y, si están gastados, el balanceo y los ruidos en curva pueden continuar.")),
    ("balero", _C("la maza de rueda, el sensor ABS y la tornillería de eje", "Trabajan en conjunto y, si la maza o el sensor están dañados, puede aparecer zumbido o el testigo ABS de nuevo.")),
    ("soporte de motor", _C("los demás soportes de motor y de transmisión", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones y los golpes al acelerar pueden continuar.")),
    ("soporte motor", _C("los demás soportes de motor y de transmisión", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones y los golpes al acelerar pueden continuar.")),
    ("taco de motor", _C("los demás soportes de motor y de transmisión", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones y los golpes al acelerar pueden continuar.")),
    ("soporte de transmision", _C("los soportes de motor y la tornillería", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones al cambiar de marcha pueden continuar.")),
    ("soporte transmision", _C("los soportes de motor y la tornillería", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones al cambiar de marcha pueden continuar.")),
    ("flecha homocinetica", _C("los cubrepolvos o botas, la grasa y el balero de rueda", "Trabajan en conjunto y, si el cubrepolvo se rompe, entra suciedad y la junta nueva puede dañarse pronto.")),
    ("cubre polvo", _C("la junta o rótula que protege y la grasa de relleno", "Si la junta interior ya tiene desgaste, conviene cambiarla junto con el cubrepolvo para no repetir el trabajo.")),
    ("cubrepolvo", _C("la junta o rótula que protege y la grasa de relleno", "Si la junta interior ya tiene desgaste, conviene cambiarla junto con el cubrepolvo para no repetir el trabajo.")),
    ("licuadora", _C("el líquido de dirección, las terminales y la alineación posterior", "Trabajan en conjunto y, si no se atienden, la dirección puede seguir dura o con holgura.")),
    ("bomba de direccion", _C("el líquido de dirección hidráulica y las mangueras de presión y retorno", "Trabajan en el mismo circuito y, si el líquido está contaminado, la bomba nueva puede dañarse pronto.")),
    ("deposito direccion", _C("el líquido de dirección, la bomba y las mangueras", "Trabajan en el mismo circuito y, si el líquido está sucio, conviene cambiarlo al instalar el depósito.")),
    ("bujia", _ENC),
    ("bobina", _C("las bujías de encendido y los conectores de la bobina", "Trabajan en conjunto y, si las bujías están gastadas, los fallos de combustión pueden continuar.")),
    ("cables de bujia", _C("las bujías de encendido y la tapa o rotor del distribuidor si aplica", "Trabajan en conjunto y, si las bujías están gastadas, los fallos de encendido pueden continuar.")),
    ("pozo de bujia", _ENC), ("tubo o pozo", _ENC),
    ("filtro de aceite de la transmision", _C("el aceite ATF y la junta de la cuba", "Se cambian en el mismo servicio y, si se reutiliza la junta, puede aparecer una fuga nueva.")),
    ("filtro de aceite", _C("el aceite del motor y el filtro de aire", "Se cambian en el mismo servicio para mantener el motor protegido y con buen rendimiento.")),
    ("filtro aceite", _C("el aceite del motor y el filtro de aire", "Se cambian en el mismo servicio para mantener el motor protegido y con buen rendimiento.")),
    ("filtro de aire", _C("el filtro de cabina y, en el servicio, el aceite del motor y su filtro", "Se cambian en el mismo mantenimiento y, descuidados, pueden afectar el rendimiento del motor.")),
    ("filtro aire", _C("el filtro de cabina y, en el servicio, el aceite del motor y su filtro", "Se cambian en el mismo mantenimiento y, descuidados, pueden afectar el rendimiento del motor.")),
    ("filtro de cabina", _C("el filtro de aire del motor y la limpieza del sistema de A/C", "Se atienden en el mismo servicio y, descuidados, pueden generar malos olores y menor flujo de aire en la cabina.")),
    ("filtro cabina", _C("el filtro de aire del motor y la limpieza del sistema de A/C", "Se atienden en el mismo servicio y, descuidados, pueden generar malos olores y menor flujo de aire en la cabina.")),
    ("filtro de combustible", _C("la bomba de combustible y el estado de los inyectores", "Trabajan en el mismo circuito y, si están sucios, las fallas de alimentación pueden continuar.")),
    ("filtro de gasolina", _C("la bomba de combustible y el estado de los inyectores", "Trabajan en el mismo circuito y, si están sucios, las fallas de alimentación pueden continuar.")),
    ("cadena de tiempo", _DIST), ("vanos", _DIST), ("banda", _DIST),
    ("polea tensora", _DIST), ("tensor", _DIST), ("polea", _DIST),
    ("arbol de levas", _C("los sellos o retenes, la junta de tapa de válvulas y los solenoides VVT/VANOS", "Trabajan en conjunto y, si se reutilizan sellos viejos, pueden aparecer fugas o códigos del sistema variable.")),
    ("valvula solenoide vvt", _C("los sellos del árbol de levas y la junta de tapa de válvulas", "Trabajan en el mismo sistema y, si hay fugas de aceite, el código del sistema variable puede regresar.")),
    ("tapa de valvulas", _C("las juntas de bujía o pozo, las bobinas y los sellos del árbol de levas", "Trabajan en la misma zona y, si hay fuga de aceite, puede dañar las bobinas y provocar fallos de encendido.")),
    ("tapa de punterias", _C("las juntas de bujía o pozo, las bobinas y los sellos del árbol de levas", "Trabajan en la misma zona y, si hay fuga de aceite, puede dañar las bobinas y provocar fallos de encendido.")),
    ("tapa punterias", _C("las juntas de bujía o pozo, las bobinas y los sellos del árbol de levas", "Trabajan en la misma zona y, si hay fuga de aceite, puede dañar las bobinas y provocar fallos de encendido.")),
    ("colector de admision", _C("la limpieza del cuerpo de aceleración y las juntas relacionadas", "Trabajan en el mismo sistema de admisión y, si hay entradas de aire falso, el ralentí puede seguir irregular.")),
    ("colector de escape", _C("los birlos o tuercas del colector y la junta del turbo si aplica", "Trabajan en la misma zona caliente y, si se reutilizan birlos vencidos, el soplido del escape puede regresar.")),
    ("junta de cabeza", _JUNTAS), ("kit de juntas", _JUNTAS), ("junta o empaque", _JUNTAS),
    ("carter", _C("el aceite, el filtro de aceite y la junta del cárter", "Se atienden en el mismo trabajo y, si se reutiliza la junta, puede aparecer una fuga nueva.")),
    ("bomba de aceite", _C("el aceite, el filtro de aceite y la junta o sello asociado", "Trabajan en el mismo sistema de lubricación y, descuidados, pueden comprometer la presión de aceite.")),
    ("turbo", _C("las mangueras de admisión, las juntas del turbo y un cambio de aceite limpio", "Trabajan junto con el turbo y, si el aceite está sucio, el turbo nuevo puede dañarse pronto.")),
    ("intercooler", _C("las mangueras de admisión y las abrazaderas", "Trabajan junto con el intercooler y, si están agrietadas, puede haber pérdida de presión y de potencia.")),
    ("cuerpo de aceleracion", _C("la limpieza del cuerpo de aceleración, su junta y las abrazaderas", "Trabajan en el mismo sistema de admisión y, descuidados, el ralentí puede seguir irregular.")),
    ("valvula pcv", _C("la junta o empaque y las mangueras del sistema PCV", "Trabajan en conjunto y, si una manguera está dura o rota, el consumo de aceite o el ralentí irregular pueden continuar.")),
    ("separador de aceite", _C("la junta o empaque y las mangueras del sistema PCV", "Trabajan en conjunto y, si una manguera está dura o rota, el consumo de aceite o el ralentí irregular pueden continuar.")),
    ("separador aceite", _C("la junta o empaque y las mangueras del sistema PCV", "Trabajan en conjunto y, si una manguera está dura o rota, el consumo de aceite o el ralentí irregular pueden continuar.")),
    ("reten", _C("el aceite del componente y las juntas asociadas", "Se atienden en el mismo trabajo y, si se reutilizan piezas viejas, puede aparecer una fuga nueva.")),
    ("piston", _JUNTAS), ("biela", _JUNTAS), ("valvula del motor", _JUNTAS),
    ("alternador", _C("la banda de accesorios y el tensor", "Trabajan en conjunto y, si la banda o el tensor están gastados, el chillido o la falta de carga pueden continuar.")),
    ("motor de arranque", _C("la batería y los cables de arranque", "Trabajan en conjunto y, si la batería está débil, el arranque puede seguir fallando aunque la marcha sea nueva.")),
    ("marcha", _C("la batería y los cables de arranque", "Trabajan en conjunto y, si la batería está débil, el arranque puede seguir fallando aunque la marcha sea nueva.")),
    ("sensor abs", _C("el balero o maza de rueda, así como la limpieza del anillo dentado o tone ring", "Estos componentes trabajan directamente con el sensor ABS y, si presentan desgaste o suciedad, pueden provocar nuevamente testigos en el tablero o lecturas incorrectas.")),
    ("sensor de estacionamiento", _C("los demás sensores PDC del mismo grupo y la calibración posterior", "Trabajan en conjunto y, si otro sensor está dañado, el sistema de estacionamiento puede seguir marcando error.")),
    ("sensor estacionamiento", _C("los demás sensores PDC del mismo grupo y la calibración posterior", "Trabajan en conjunto y, si otro sensor está dañado, el sistema de estacionamiento puede seguir marcando error.")),
    ("balastra", _C("el foco de xenón (HID) y el estado del conector", "Trabajan en conjunto y, si el foco está agotado, la luz puede seguir parpadeando o sin encender.")),
    ("compresor", _AC), ("condensador", _AC), ("evaporador", _AC),
    ("resistencia", _C("el filtro de cabina y el motor del soplador", "Trabajan en conjunto y, si el soplador está forzado, la resistencia nueva puede volver a quemarse.")),
    ("clutch", _C("el volante motor (o su rectificado), el cilindro o collarín y el balero piloto", "Trabajan en conjunto y, si se reutilizan piezas gastadas, el embrague nuevo puede vibrar o durar menos.")),
    ("embrague", _C("el volante motor (o su rectificado), el cilindro o collarín y el balero piloto", "Trabajan en conjunto y, si se reutilizan piezas gastadas, el embrague nuevo puede vibrar o durar menos.")),
    ("caja transfer", _C("el aceite de la transfer y los baleros del eje", "Trabajan en conjunto y, si el aceite está degradado, la falla puede regresar pronto.")),
    ("cardan", _C("la otra junta o soporte del cardán y los baleros", "Envejecen al mismo ritmo y, si se deja uno gastado, las vibraciones al acelerar pueden continuar.")),
    ("parrilla", _CARRO), ("rejilla", _CARRO), ("moldura", _CARRO),
    ("defensa", _CARRO), ("salpicadera", _CARRO), ("aleron", _CARRO),
    ("faro", _C("las grapas o soportes del faro y, si aplica, el foco o la balastra", "Trabajan en conjunto y, sin las grapas correctas, el faro puede quedar flojo o con holgura.")),
    ("calavera", _C("las grapas o soportes y los focos si aplica", "Trabajan en conjunto y, sin las grapas correctas, la calavera puede quedar floja.")),
    ("espejo", _C("el cristal del espejo y la tapa o carcasa si están dañados", "Trabajan en conjunto y, si una parte está dañada, conviene cambiarla al mismo tiempo para un acabado uniforme.")),
    ("manija", _C("la chapa de cerradura y la pintura para igualar el color", "Trabajan en conjunto y, si la chapa está dañada, la puerta puede seguir sin abrir bien.")),
    ("manilla", _C("la chapa de cerradura y la pintura para igualar el color", "Trabajan en conjunto y, si la chapa está dañada, la puerta puede seguir sin abrir bien.")),
    ("chapa de cerradura", _C("el actuador o chapa de las otras puertas si presentan el mismo síntoma", "Suelen fallar al mismo tiempo y, si se deja una gastada, el cierre centralizado puede volver a fallar.")),
    ("control maestro", _C("los switches individuales de las otras puertas", "Trabajan en conjunto y, si otro switch falla, algún vidrio puede seguir sin responder.")),
    ("sensor de oxigeno", _C("la limpieza del sistema y los sensores relacionados", "Trabajan en conjunto en el control de emisiones y, si otro sensor falla, el check engine puede seguir encendido.")),
    ("sensor maf", _C("el filtro de aire y la limpieza del cuerpo de aceleración", "Trabajan en el mismo sistema de admisión y, si el filtro está sucio, los tirones pueden continuar.")),
    ("cristal", _CARRO), ("puerta", _CARRO),
    ("llavero", ""), ("emblema", ""),
]
COMPLEMENTOS = sorted(((norm(k), v) for k, v in COMPLEMENTOS_RAW),
                      key=lambda kv: -len(kv[0]))

# Respaldo por Sub grupo (metafield) cuando el token no hace match. Evita el
# complemento genérico en piezas que el título nombra de forma distinta.
SUBGRUPO_COMP_RAW = {
    "bombas de combustible": _C("el filtro de combustible y el estado de los inyectores", "Trabajan en el mismo circuito de alimentación y, si están sucios, las fallas pueden continuar."),
    "filtros de gasolina": _C("la bomba de combustible y el estado de los inyectores", "Trabajan en el mismo circuito de alimentación y, si están sucios, las fallas pueden continuar."),
    "inyectores": _C("el filtro de combustible y la limpieza del sistema de inyección", "Trabajan en el mismo circuito y, si el combustible llega sucio, el ralentí irregular puede continuar."),
    "sensores de oxigeno": _C("la limpieza del sistema de escape y los sensores relacionados", "Trabajan en conjunto en el control de emisiones y, si otro falla, el check engine puede seguir encendido."),
    "sensores de cigueñal": _C("el sensor de árbol de levas y el estado del cableado", "Trabajan juntos en el control del motor y, si fallan, el arranque o el ralentí pueden seguir irregulares."),
    "sensor de temperatura": _C("el anticongelante, el termostato y el estado del cableado", "Trabajan en el sistema de enfriamiento y, si fallan, la lectura de temperatura o el ventilador pueden seguir con problemas."),
    "sensor maf": _C("el filtro de aire y la limpieza del cuerpo de aceleración", "Trabajan en el mismo sistema de admisión y, si el filtro está sucio, los tirones pueden continuar."),
    "sensor map": _C("la limpieza del cuerpo de aceleración y las mangueras de admisión", "Trabajan en el mismo sistema de admisión y, si hay fugas de aire, el ralentí puede seguir irregular."),
    "sensor de posicion": _C("los sensores relacionados y el estado del cableado", "Trabajan en el control del motor y, si otro falla, los códigos pueden continuar."),
    "sensores de aceite": _C("el aceite, el filtro de aceite y la junta del sensor", "Se atienden en el mismo servicio y, si se reutiliza la junta, puede aparecer una fuga."),
    "cadenas de distribucion": _C("el tensor, las guías, las poleas y los sellos del sistema de distribución", "Trabajan junto con la cadena y, si están desgastados, pueden generar ruido o saltos de tiempo poco después del cambio."),
    "punterias hidraulicas": _C("el aceite, el filtro de aceite y la junta de tapa de válvulas", "Las punterías dependen de la presión y limpieza del aceite; conviene un cambio fresco para que no sigan sonando."),
    "bayonetas nivel de aceite": _C("el aceite, el filtro de aceite y el sello de la bayoneta", "Se atienden en el mismo servicio de aceite."),
    "tapa de aceite": _C("la junta de la tapa y el nivel de aceite del motor", "Si la junta está dura, conviene cambiarla para evitar fugas."),
    "tomas de agua": _ENFRIA,
    "discos de freno": _FRENO_D,
    "brazo de suspension": _SUSP,
    "bolsas de aire para suspension": _C("el compresor de la suspensión neumática y las válvulas del sistema", "Trabajan en el mismo sistema y, si el compresor está forzado, la pieza nueva puede volver a fallar."),
    "plumillas limpiaparabrisas": _C("las plumillas del otro lado y el líquido limpiaparabrisas", "Se cambian en par para una limpieza pareja del parabrisas."),
}
SUBGRUPO_COMP = {norm(k): v for k, v in SUBGRUPO_COMP_RAW.items()}


def complemento_for(intro_text, title, subgrupo=""):
    hay = norm(intro_text) + " " + norm(title)
    for key, val in COMPLEMENTOS:  # mas largo primero
        if key in hay:
            return val  # tupla (piezas, motivo) o "" -> sin complemento
    sg = norm(subgrupo)
    if sg in SUBGRUPO_COMP:
        return SUBGRUPO_COMP[sg]
    return COMPLEMENTO_GENERICO


# ---------- parseo ----------
def split_sections(html):
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.S)
    preludio = parts[0]
    sections = []
    for i in range(1, len(parts), 2):
        title = re.sub(r"</?h2>", "", parts[i]).strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((title, content))
    return preludio, sections


def first_sentence(text):
    m = re.match(r"\s*(.*?\.)(?:\s|$)", text, re.S)
    return m.group(1).strip() if m else text.strip()


def part_from_title(title):
    """Extrae el nombre de la pieza del titulo (antes de la marca del auto)."""
    toks = title.split()
    out = []
    for t in toks:
        tl = norm(t)
        if tl in MARCAS_AUTO or re.match(r"^\d", tl):
            break
        out.append(t)
    if not out:
        out = toks[:3]
    return " ".join(out).strip()


def keyword_def(title):
    npieza = norm(part_from_title(title))
    for kw, d in KEYWORD_DEFS:
        if kw in npieza:
            return d
    return None


def weak_title(title):
    return ("%s: refacción para vehículo europeo. Revisa el título y el número "
            "de parte de la ficha para confirmar la pieza exacta."
            % part_from_title(title))


def build_intro_generico(title):
    return keyword_def(title) or weak_title(title)


# Marcadores (normalizados) de frases/clausulas de falla o sintoma -> se eliminan
FAILURE_MARKERS = [
    "falla tipica", "falla por", "fallan tipicamente", "falla atascad", "su falla",
    "al cuartearse", "al desgastarse", "al aflojarse", "al fallar", "al perder gas",
    "al romperse", "al endurecerse", "al gastarse", "al girar",
    "se cuartea", "se afloja", "se reemplaza por desgaste", "se reemplaza por golpes",
    "se reemplaza tras", "se reemplaza por impactos", "se dana", "se danan", "danarse",
    "se cambian al", "aparece fuga", "aparece golpeteo", "aparece holgura",
    "aparece chillido", "aparece un golpeteo", "aparece vibracion",
    "aparecen vibraciones", "aparecen golpes", "vibra a", "zumba", "tableteo",
    "chillido", "golpeteo", "traqueteo", "sintomas", "vulnerable a", "pierde gas",
    "consume aceite", "deja de", "no enciende", "parpadea", "sobrecalent",
    "ralenti irregular", "perdida de potencia", "falta de potencia", "codigo p0",
    "mayor consumo", "sube el consumo", "tirones", "testigo", "check engine",
    "atascad", "quemad", "rajadura", "grietas", "obstruccion", "impide el arranque",
    "descarga la bateria", "salto de tiempo", "arruinar el motor", "dana el motor",
    "suele danarse", "suele reemplazarse", "golpes en baches", "holgura", "fuga",
    "ruido", "cuartea",
]


def _es_falla(clause):
    nc = norm(clause)
    return any(mk in nc for mk in FAILURE_MARKERS)


def strip_failures(text):
    """Elimina las frases/clausulas que describen fallas o sintomas."""
    sents = re.split(r"(?<=\.)\s+", text.strip())
    kept = []
    for sent in sents:
        clauses = [c for c in sent.split("; ") if not _es_falla(c)]
        if not clauses:
            continue
        s2 = "; ".join(clauses).strip()
        if s2 and not s2.endswith("."):
            s2 += "."
        kept.append(s2)
    return " ".join(kept).strip()


def reescribir_intro(intro_text, title):
    n = norm(intro_text)
    txt = None
    for gp in GENERIC_PREFIXES:
        if n.startswith(gp):
            txt = build_intro_generico(title)
            break
    if txt is None:
        for key, rw in REWRITES:  # ya ordenadas por longitud desc
            if n.startswith(key):
                txt = rw
                break
    if txt is None:
        # cola larga: intentar definicion por keyword del titulo; si no, recortar
        kd = keyword_def(title)
        if kd:
            txt = kd
        elif any(x in n for x in ("te recomendamos confirmar", "no esta estructurada",
                                  "ficha fue public", "datos minimos")):
            # plantilla alterna (intro = titulo + boilerplate) -> nombrar la pieza
            txt = weak_title(title)
        else:
            frases = re.findall(r".*?\.(?:\s|$)", intro_text, re.S)
            txt = "".join(frases[:2]).strip() or intro_text.strip()
    return strip_failures(txt)


def drop_asesor(text):
    """Quita las frases de la cola 'consulta con nuestro asesor' (upsell viejo)."""
    sents = re.split(r"(?<=\.)\s+", text.strip())
    kept = [s for s in sents if "asesor" not in norm(s)]
    return " ".join(kept).strip()


def limpiar_descripcion(content, title, handle="", subgrupo=""):
    paras = re.findall(r"<p>(.*?)</p>", content, re.S)
    intro0 = paras[0] if paras else ""
    out = []
    for idx, p in enumerate(paras):
        s = p.strip()
        low = norm(s)
        if idx == 0:
            out.append(reescribir_intro(s, title))
            continue
        if low.startswith("se vende") or low.startswith("se entrega"):
            limpio = drop_asesor(s)
            if limpio:
                out.append(limpio)
            continue
        # red de seguridad: elimina cualquier parrafo de logistica/promo restante
        if ("Embler Autopartes Europeas mantiene stock" in s
                or "via DHL" in s or "Garantia del vendedor" in s
                or "politicas de devolucion" in s
                or low.startswith("producto de merchandising")):
            continue
        if low.startswith("compatible con"):
            continue
        if low.startswith("por el titulo aplica"):
            continue
        if low.startswith("por las marcas y modelos mencionados"):
            continue
        if low.startswith("especificaciones de referencia"):
            txt = first_sentence(s)
            m = re.search(r"Lado de instalaci[oó]n:\s*[^.]*\.", s)
            if m:
                txt += " " + m.group(0).strip()
            out.append(txt)
            continue
        if low.startswith("marca "):
            if any(low.startswith(mp) for mp in MARCAS_PROPIAS):
                continue  # marca propia (Frey/Embler) -> fuera
            # marca externa real -> "Marca: X."
            m = re.match(r"Marca\s+([^,\.]+)", s)
            if m:
                out.append("Marca: %s." % m.group(1).strip())
            continue
        out.append(s)
    comp = build_complemento(complemento_for(intro0, title, subgrupo), handle)
    if comp:
        out.append(comp)
    return "".join("<p>%s</p>" % p for p in out if p)


def nuevo_envio(content):
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", content)).strip()
    # elimina la frase generica de envio, sea cual sea su cola hasta el punto
    extra = re.sub(r"^.*?via DHL o FedEx[^.]*\.\s*", "", txt).strip()
    html = NEW_ENVIO
    if extra and "entrega inmediata" not in norm(extra) and len(extra) > 3:
        html += "<p>%s</p>" % extra
    return html


def nueva_politica(content):
    paras = [p for p in re.findall(r"<p>(.*?)</p>", content, re.S)
             if not norm(p).startswith("asegura el ajuste perfecto")]
    return "".join("<p>%s</p>" % p for p in paras)


def restructure(html, title, handle="", subgrupo=""):
    if not html or not html.strip():
        return html
    preludio, sections = split_sections(html)
    by_title, extras = {}, []
    for t, content in sections:
        if t in DROP_SECTIONS:
            continue
        if t == "Descripcion":
            content = limpiar_descripcion(content, title, handle, subgrupo)
        elif t == "Envio":
            content = nuevo_envio(content)
        elif t == "Antes de Comprar":
            if "llavero" not in norm(title) and "llavero" not in norm(content):
                content = ANTES_COMPRAR
        elif t == "Politica de Devolucion":
            content = nueva_politica(content)
        if t in ORDER:
            by_title[t] = content
        else:
            extras.append((t, content))
    new = preludio
    for t in ORDER:
        if t in by_title:
            new += "<h2>%s</h2>%s" % (TITLE_MAP.get(t, t), by_title[t])
    for t, content in extras:
        new += "<h2>%s</h2>%s" % (TITLE_MAP.get(t, t), content)
    return new.replace("Mercedes-Benz", "Mercedes Benz")


def run_sample(n=6):
    prefijos = ["Parrilla", "Balatas", "Bomba De Agua", "Amortiguador",
                "Sensor", "Filtro", "Disco", "Bobina"]
    used, shown = set(), 0
    with open(INPUT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            b = row["Body (HTML)"]
            if not b.strip():
                continue
            t = row["Title"]
            key = next((p for p in prefijos if t.startswith(p)), None)
            if key is None or key in used:
                continue
            used.add(key)
            _, secs = split_sections(b)
            orig = next((c for tt, c in secs if tt == "Descripcion"), "")
            nueva = limpiar_descripcion(
                orig, t, row["Handle"],
                row.get("Sub grupo (product.metafields.global.sub_group)", ""))
            print("=" * 80)
            print("PRODUCTO:", t)
            print("--- DESCRIPCION ANTES:")
            print(re.sub(r"</p>", "</p>\n", orig).strip())
            print("--- DESCRIPCION DESPUES:")
            print(re.sub(r"</p>", "</p>\n", nueva).strip())
            print()
            shown += 1
            if shown >= n:
                break


def run_full():
    os.makedirs(NEWDIR, exist_ok=True)
    with open(INPUT, encoding="utf-8", newline="") as fin, \
         open(OUTPUT, "w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=r.fieldnames)
        w.writeheader()
        # Mercedes-Benz -> Mercedes Benz (sin guion) en TODAS las columnas
        # excepto Handle (cambiar handles rompe el match con Shopify). El regex
        # respeta el caso original: "Mercedes-Benz"->"Mercedes Benz",
        # "mercedes-benz"->"mercedes benz" (metafields), etc.
        MERC_RX = re.compile(r"(?i)(mercedes)-(benz)")
        total = cambiados = 0
        for row in r:
            total += 1
            b = row["Body (HTML)"]
            if b and b.strip():
                nb = restructure(
                    b, row["Title"], row["Handle"],
                    row.get("Sub grupo (product.metafields.global.sub_group)", ""))
                if nb != b:
                    cambiados += 1
                row["Body (HTML)"] = nb
            for c in r.fieldnames:
                if c == "Handle":
                    continue
                v = row.get(c)
                if v and "-" in v and "mercedes" in v.lower():
                    row[c] = MERC_RX.sub(r"\1 \2", v)
            w.writerow(row)
    print("Filas totales:", total)
    print("Body reescritos:", cambiados)
    print("Salida:", OUTPUT)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--run" in a:
        run_full()
    elif "--sample" in a:
        i = a.index("--sample")
        n = int(a[i + 1]) if i + 1 < len(a) and a[i + 1].isdigit() else 6
        run_sample(n)
    else:
        print(__doc__)
