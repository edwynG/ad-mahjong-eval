# Evaluación masiva de Mahjong (Proyecto 2026-01)

Este proyecto implementa un sistema distribuido en Python diseñado para procesar masivamente miles de configuraciones de jugadas de Mahjong. El sistema calcula las puntuaciones base, dobles, estilo de la mano e interpreta sintácticamente cada jugada basándose en las reglas del Mahjong (incluyendo Cantos Clásicos y Límites). Debido al alto volumen del dataset, el cálculo está paralelizado sobre un ambiente de paso de mensajes utilizando **MPI (`mpi4py`)**.

## 1. Arquitectura del sistema

La arquitectura está basada en el paradigma **Maestro-Trabajador (Master-Worker)**. 

Elegimos esta arquitectura porque evaluar miles de jugadas de Mahjong es un trabajo que se puede dividir muy fácilmente. Cada línea del archivo es una jugada independiente, así que no hay necesidad de que los procesos se comuniquen entre sí para resolverlas. 

Para organizarlo, dividimos los roles en dos partes muy claras:

*   **El proceso maestro (Rank 0):** Es como el director de la orquesta. Él es el único que interactúa con los archivos. Lee todas las jugadas de golpe, las pica en pedazos iguales y le reparte un pedazo a cada trabajador. Al final, se queda esperando a que todos terminen, recoge las respuestas, las vuelve a armar en el orden correcto y guarda el archivo de salida. Centralizar la lectura y escritura en este nodo evita que todos los procesos intenten escribir al mismo tiempo y colapsen el sistema.
*   **Los procesos trabajadores (Workers):** Son los obreros matemáticos. Cada uno recibe su pedazo de texto, lo procesa línea por línea sacando las cuentas, y cuando termina, empaqueta sus resultados y se los devuelve al Maestro.

## 2. Funcionalidad y lógica de cálculo

El sistema está compuesto por una serie de funciones especializadas que dividen el problema de evaluación del Mahjong en tareas pequeñas y lógicas.

### Funciones principales y su propósito

1. **`decode_play(line: str) -> dict`**: Ubicada en `parser.py`. Su propósito es "traducir" la cadena de texto plana del archivo de entrada y convertirla en un diccionario estructurado, aislando los vientos, los grupos de mesa, las flores y la pieza ganadora.
2. **`classify_group(group_str: str) -> dict`**: Analiza un grupo individual (ej: `[P2-P2-P2]`) determinando si es un Pung, Kong, Chow o Par (Ojos), cuál es su pinta base, si pertenece a los honores, y si está en estado oculto o abierto sobre la mesa.
3. **`detect_classic(groups, flowers, own_wind, round_wind, winning_piece) -> tuple`**: Ubicada en `scorer.py`. Su propósito es auditar la mano completa para verificar si coincide con las estrictas configuraciones de los **Cantos Clásicos o Límites** (ej: 13 Maravillas, Gran Seguidilla Real). Si encaja, devuelve el puntaje fijo de esa mano.
4. **`calculate_base_points(groups, flowers, has_chow) -> tuple`**: Escanea los grupos de la mano para sumar los puntos "duros" (cuenta base). Otorga puntos por tener flores, bonos matemáticos por tener kongs y pungs (especialmente si son honores), y añade el bono fijo por haber logrado el Mahjong.
5. **`calculate_doubles(groups, flowers, own_wind, round_wind, has_chow) -> tuple`**: Escanea la mano buscando combinaciones exponenciales. Otorga "dobles" si la mano es Limpia, Sucia, si hay ramilletes de flores completas, o tríos de dragones (Escolares Mayores/Menores).
6. **`evaluate_hand(parsed_hand: dict) -> dict`**: Es el punto de entrada central del motor de reglas. Su propósito es orquestar a todas las demás funciones de puntuación y aplicar la fórmula matemática final.

### ¿Cómo trabajan en conjunto para sacar las cuentas? (El ciclo completo)

La lógica funciona como una cadena de montaje industrial perfecta. Cuando un proceso trabajador recibe una línea de texto cruda, ocurre exactamente el siguiente flujo de inicio a fin:

**Paso 1: Extracción léxica**
El orquestador (`main.py`) toma la línea y se la pasa a `decode_play`. Esta función usa herramientas de separación de cadenas para extraer las partes del texto (ej: ID de la jugada, vientos, piezas en la mesa, flores) y las devuelve estructuradas en un diccionario nativo de Python para que dejen de ser un simple texto.

**Paso 2: Análisis detallado de grupos**
Antes de hacer matemáticas, el sistema necesita saber qué significa cada grupo. El orquestador hace un bucle sobre cada grupo extraído y se los pasa a `classify_group`. Esta función mira si, por ejemplo, `[P2-P2-P2]` es un Pung, si pertenece a la pinta de Círculos (P), y si sus corchetes indican que está abierto. Toda esta radiografía detallada se anexa al diccionario.

**Paso 3: Evaluación de la mano**
El diccionario, ahora totalmente desglosado y clasificado, entra a `evaluate_hand`. Aquí empieza el árbol de decisiones matemáticas:
1. Primero, se le hace una consulta a `detect_classic()`. Si esta función detecta que las piezas forman un patrón exacto como los "7 Samuráis", corta el proceso y devuelve el puntaje de límite estipulado.
2. Si no es clásica, delega el trabajo a `calculate_base_points()` para contar los puntos duros (flores y pungs).
3. Luego, le pasa la mano a `calculate_doubles()` para contar cuántos multiplicadores exponenciales posee (por ejemplo, si la mano es Limpia o tiene Escolares).

**Paso 4: La fórmula matemática final**
Dentro de ese mismo `evaluate_hand`, habiendo recolectado la base y los dobles de sus sub-funciones, se aplica la fórmula de cierre:
```python
# Fórmula oficial: Base multiplicada por 2 elevado a la cantidad de dobles
total = base * (2 ** doubles)

# Regla Especial: El viento Este (E) siempre duplica la cuenta al final
if own_wind == 'E': 
    total *= 2

# Se aplica el tope máximo oficial del juego (20.000 puntos)
if total > MAX_TOTAL_POINTS:
    total = MAX_TOTAL_POINTS
```

**Paso 5: Ensamblaje de la respuesta**
Terminada la matemática, `evaluate_hand` le devuelve al orquestador tres datos vitales: el `total` numérico, el `estilo` (Tradicional o el nombre del Clásico), y un arreglo de `log` (bitácora detallada de los cálculos). El orquestador (`main.py`) toma esos datos y los ensambla de vuelta en una cadena de texto, lista para viajar por la red:
```python
# Así se empaca el resultado final para enviarlo en el comm.gather
resultado_final = f"{visual_original} | {base} | {doubles} | {total} | {estilo} | {log}"
```

De esta manera el ciclo se completa: empieza con una cadena de texto plana en la entrada, se expande en diccionarios complejos para calcular las matemáticas puras, y vuelve a comprimirse en una cadena de texto enriquecida para la salida.


## 3. Mensajes involucrados (comunicaciones MPI)

En lugar de enviar mensajitos individuales por cada línea de texto (lo cual saturaría la red), decidimos usar **operaciones colectivas** para enviar paquetes grandes de información de una sola vez. Todo el ciclo de vida funciona con dos grandes mensajes:

1. **La dispersión (`comm.scatter`):** El Maestro agarra la lista gigante de jugadas y la pica. Si hay 4 procesos corriendo, hace 4 listas más pequeñas. Luego lanza un "scatter", que es básicamente un envío masivo donde le tira a cada proceso su lista correspondiente en un solo movimiento.
2. **La recolección (`comm.gather`):** Cuando los trabajadores terminan de sacar sus cuentas, tienen una lista de resultados listos. A través del "gather", le devuelven todos esos pedazos al Maestro de un solo golpe. La gran ventaja del gather es que automáticamente respeta el orden original de los procesos, garantizando que el archivo de salida mantenga el mismo orden exacto que el de entrada.

### Ejemplo práctico de entrada y salida

Para entender cómo estos mensajes transportan y transforman la data, veamos un caso real de lo que viaja por la red:

**Lo que entra al sistema (lo que envía el Maestro en el scatter):**
```text
1 [E / E] [C2-C3-C4] [C5-C5-C5] [C2-C2-C2] [C8-C8-C8] (C6-C6) <G3 R1 R4> *C6*
```
*¿Qué es esto?* Es una cadena de texto plana. Nos indica que es la jugada 1, que el viento es Este, los grupos sobre la mesa, las tres flores conseguidas y que la pieza ganadora fue C6.

**La transformación y el cálculo matemático (lo que ocurre dentro del Trabajador):**
El trabajador recibe esa línea, la desarma, e identifica lo siguiente:
*   **Grupos:** Un Chow `[C2-C3-C4]`, tres Pungs de Caracteres `[C5-C5-C5]`, `[C2-C2-C2]`, `[C8-C8-C8]`, y un par de `(C6-C6)`. Como ves, todas las fichas pertenecen a una sola familia (Caracteres "C").
*   **Flores:** Tiene 3 flores `<G3 R1 R4>`. La R1 es la "Roja 1", que corresponde numéricamente al viento Este.
*   **Viento del Jugador:** Es viento Este `[E / E]`.

Con esto, el sistema saca las cuentas reales paso a paso:
1. **Puntos Base (38 en total):** 12 puntos por las 3 flores + 6 puntos por los tres Pungs descubiertos + 20 puntos del gran bono por hacer Mahjong.
2. **Dobles o Multiplicadores (4 en total):** 3 dobles de premio por ser un "Mahjong Limpio" (todas las fichas son Caracteres y usó un Chow) + 1 doble por "Flor Propia" (el jugador es Este [1] y sacó la Roja 1).
3. **Fórmula Matemática:** La Base `38` se multiplica por 2 elevado a los `4` dobles (38 * 16 = 608). Como el jugador es viento Este, la regla oficial le premia duplicando su cuenta al final: `608 * 2 = 1216`.

**Lo que sale del sistema (lo que recibe el Maestro en el gather):**
```text
1 [E / E] [C2-C3-C4] [C5-C5-C5] [C2-C2-C2] [C8-C8-C8] (C6-C6) <G3 R1 R4> *C6* | 38 | 4 | 1216 | TRADICIONAL | ['Flores: 12', 'Bono Mahjong: 20', '[+] 1 Doble: Flor Propia', '[+] 3 Dobles: Limpio pungs y chows', 'ESTE cobra doble', ...]
```
*¿Qué es esto?* El trabajador le devolvió al Maestro la misma línea, pero le anexó puntos base (38), los dobles encontrados (4), la puntuación total matemática real (1216), el estilo de mano (Tradicional), y un arreglo tipo bitácora explicando exactamente de dónde salieron esos números.

## Instrucciones de ejecución

El programa debe correrse sobre el ambiente virtual que contiene `mpi4py`. Para ejecutar en paralelo utilizando por ejemplo 4 núcleos y el archivo de entrada deseado:

```bash
mpiexec -n 4 python main.py <archivo_de_entrada.txt>
```
