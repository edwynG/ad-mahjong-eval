from mahjong_rules import WINDS, DRAGONS, SUITS, MINOR_HONORS

POINTS_CHOW = 0
POINTS_FLOWER = 4
POINTS_MAHJONG_CHOW = 20
POINTS_MAHJONG_PUNG = 30
MAX_TOTAL_POINTS = 20000

WIND_TO_FLOWER_NUM = {'E': '1', 'S': '2', 'W': '3', 'N': '4'}

# Función auxiliar para saber si un grupo está oculto o cerrado
def is_hidden(group: dict) -> bool:
    return group["visibility"] in ["closed", "concealed"]

# Calcula la cuenta base tradicional sumando los puntos de cada grupo, flores y bonos
def calculate_base_points(groups: list, flowers: list, has_chow: bool) -> tuple:
    base = 0
    log = []
    
    # Puntos por tener flores
    if len(flowers) > 0:
        flower_points = len(flowers) * POINTS_FLOWER
        base = base + flower_points
        log.append(f"Flores: {flower_points}")

    # Puntos por cada grupo (Pung o Kong)
    for g in groups:
        group_type = g["group_type"]
        is_honor = g["is_honor"]
        is_concealed = is_hidden(g)
        group_points = 0
        
        if group_type == "pung":
            if is_honor:
                if is_concealed:
                    group_points = 8
                else:
                    group_points = 4
            else:
                if is_concealed:
                    group_points = 4
                else:
                    group_points = 2
            
            base = base + group_points
            
            if is_honor:
                log.append(f"Pung honor: {group_points}")
            else:
                log.append(f"Pung pinta: {group_points}")
                
        elif group_type == "kong":
            if is_honor:
                if is_concealed:
                    group_points = 32
                else:
                    group_points = 16
            else:
                if is_concealed:
                    group_points = 16
                else:
                    group_points = 8
            
            base = base + group_points
            
            if is_honor:
                log.append(f"Kong honor: {group_points}")
            else:
                log.append(f"Kong pinta: {group_points}")
                
        elif group_type == "pair":
            base_piece = g["pieces"][0]
            # Si el par es de dragones, da 4 puntos fijos
            if base_piece == "DR" or base_piece == "DV" or base_piece == "DB":
                group_points = 4
                base = base + group_points
                log.append(f"Ojos dragon: {group_points}")

    # Bono por hacer Mahjong
    if has_chow:
        bonus = POINTS_MAHJONG_CHOW
    else:
        bonus = POINTS_MAHJONG_PUNG
        
    base = base + bonus
    log.append(f"Bono Mahjong: {bonus}")

    return base, log

# Calcula la cantidad de multiplicadores (dobles) por características como el viento, dragones o si es limpia
def calculate_doubles(groups: list, flowers: list, own_wind: str, round_wind: str, has_chow: bool) -> tuple:
    doubles = 0
    log = []

    # Contar cuantas flores rojas y negras tenemos
    red_flowers = []
    black_flowers = []
    
    for flower in flowers:
        if flower.startswith('R'):
            red_flowers.append(flower)
        elif flower.startswith('G'):
            black_flowers.append(flower)
            
    has_red_bouquet = (len(red_flowers) == 4)
    has_black_bouquet = (len(black_flowers) == 4)

    # Revisar si tenemos la flor que corresponde a nuestro asiento
    wind_number = WIND_TO_FLOWER_NUM.get(own_wind, '')
    has_own_flower = False
    
    for flower in flowers:
        if flower.endswith(wind_number):
            has_own_flower = True
            break

    # Asignar dobles por ramilletes
    if has_red_bouquet:
        doubles = doubles + 4
        log.append("[+] 4 Dobles: Ramillete Rojo")
        
    if has_black_bouquet:
        doubles = doubles + 4
        log.append("[+] 4 Dobles: Ramillete Negro")
    
    # Asignar doble por flor propia si NO está ya cobrada dentro de un ramillete
    if has_own_flower:
        flower_in_red_bouquet = False
        flower_in_black_bouquet = False
        
        if has_red_bouquet:
            for f in flowers:
                if f.endswith(wind_number) and f.startswith('R'):
                    flower_in_red_bouquet = True
                    break
                    
        if has_black_bouquet:
            for f in flowers:
                if f.endswith(wind_number) and f.startswith('G'):
                    flower_in_black_bouquet = True
                    break
                    
        if not flower_in_red_bouquet and not flower_in_black_bouquet:
            doubles = doubles + 1
            log.append("[+] 1 Doble: Flor Propia")

    # Dobles por vientos y dragones
    for g in groups:
        g_type = g["group_type"]
        if g_type == "pung" or g_type == "kong":
            piece = g["pieces"][0]
            if piece == own_wind or piece == round_wind:
                doubles = doubles + 1
                log.append(f"[+] 1 Doble: Pung/Kong Viento ({piece})")
            elif piece in DRAGONS:
                doubles = doubles + 1
                log.append(f"[+] 1 Doble: Pung/Kong Dragón ({piece})")

    # Separar grupos para evaluar mahjong limpio/sucio
    chows = []
    honor_pungs = []
    
    for g in groups:
        if g["group_type"] == "chow":
            chows.append(g)
        elif g["group_type"] == "pung" or g["group_type"] == "kong":
            if g["nature"] == "suit" and g["is_honor"]:
                honor_pungs.append(g)
                
    # Obtener todas las pintas distintas usadas en la mano
    used_suits = []
    for g in groups:
        if g["nature"] == "suit" or g["group_type"] == "chow":
            suit_char = g["pieces"][0][0]
            if suit_char not in used_suits:
                used_suits.append(suit_char)
                
    num_suits = len(used_suits)
    
    # Contar si hay vientos o dragones
    has_winds_or_dragons = False
    for g in groups:
        if g["nature"] == "wind" or g["nature"] == "dragon":
            has_winds_or_dragons = True
            break
            
    is_clean_hand = (num_suits == 1)

    # Evaluar MAH-JONGG LIMPIO
    if is_clean_hand and has_winds_or_dragons == False:
        if len(chows) == 0:
            if len(honor_pungs) > 0:
                doubles = doubles + 3
                log.append("[+] 3 Dobles: Limpio Honores")
            else:
                doubles = doubles + 5
                log.append("[+] 5 Dobles: Limpio puros pungs")
        elif len(chows) == 4:
            doubles = doubles + 4
            log.append("[+] 4 Dobles: Limpio puros chows")
        else:
            doubles = doubles + 3
            log.append("[+] 3 Dobles: Limpio pungs y chows")
            
    # Evaluar MAH-JONGG SUCIO
    if num_suits == 1 and has_winds_or_dragons == True:
        if len(chows) == 0:
            doubles = doubles + 2
            log.append("[+] 2 Dobles: Sucio pinta sin chow")
        else:
            doubles = doubles + 1
            log.append("[+] 1 Doble: Sucio pinta con chow")

    # Evaluar ESCOLARES
    dragon_pungs = []
    has_dragon_pair = False
    
    for g in groups:
        if g["group_type"] == "pung" or g["group_type"] == "kong":
            if g["nature"] == "dragon":
                dragon_pungs.append(g)
        elif g["group_type"] == "pair":
            if g["nature"] == "dragon":
                has_dragon_pair = True
                
    if len(dragon_pungs) == 3:
        doubles = doubles + 4
        log.append("[+] 4 Dobles: Escolares Mayores")
    elif len(dragon_pungs) == 2 and has_dragon_pair:
        doubles = doubles + 3
        log.append("[+] 3 Dobles: Escolares Menores")

    return doubles, log

# Comprueba si la mano cumple con alguna de las configuraciones raras (Clásicos o Límites)
def detect_classic(groups: list, flowers: list, own_wind: str, round_wind: str, winning_piece: str) -> tuple:
    # Verificamos si toda la mano está oculta
    all_hidden = True
    for g in groups:
        if is_hidden(g) == False:
            all_hidden = False
            break
            
    # Separar grupos por tipo
    chows = []
    pairs = []
    pungs_and_kongs = []
    
    for g in groups:
        if g["group_type"] == "chow":
            chows.append(g)
        elif g["group_type"] == "pair":
            pairs.append(g)
        elif g["group_type"] == "pung" or g["group_type"] == "kong":
            pungs_and_kongs.append(g)
            
    # Extraer una lista simple con absolutamente todas las piezas de la mano sin repetir
    all_pieces = []
    for g in groups:
        for piece in g["pieces"]:
            if piece not in all_pieces:
                all_pieces.append(piece)

    # === BLOQUE 20.000 PUNTOS ===

    if len(pairs) == 7:
        # GRANDES SAMURAIS (20.000 puntos)
        # Requisitos: 7 pares exclusivos de vientos y dragones. Debe ser totalmente oculta.
        is_grandes_samurais = True
        for p in all_pieces:
            if p not in WINDS and p not in DRAGONS:
                is_grandes_samurais = False
                break
        if is_grandes_samurais and all_hidden:
            return 20000, "GRANDES SAMURAIS", []
            
        # HIJOS UNIDOS (20.000 puntos)
        # Requisitos: 7 pares exclusivos de ases y nueves de cualquier pinta. Debe ser totalmente oculta.
        is_hijos_unidos = True
        for p in all_pieces:
            is_minor_honor = len(p) > 1 and p[1] in MINOR_HONORS
            if not is_minor_honor:
                is_hijos_unidos = False
                break
        if is_hijos_unidos and all_hidden:
            return 20000, "HIJOS UNIDOS", []

    # LA FLOR DEL CEREZO (20.000 puntos)
    # Requisitos: Que la pieza ganadora sea el 5 de Ruedas (B5) y se tenga la flor propia del viento
    wind_number = WIND_TO_FLOWER_NUM.get(own_wind, '')
    has_own_flower = False
    for flower in flowers:
        if flower.endswith(wind_number):
            has_own_flower = True
            break
    if winning_piece == "B5" and has_own_flower:
        return 20000, "LA FLOR DEL CEREZO", ["B5 ganadora y flor propia"]

    # === BLOQUE 15.000 PUNTOS ===
    
    # BENDICION CELESTIAL (15.000 puntos)
    # Requisitos: Pungs de 2, 4 y 8 de ruedas (B2, B4, B8), pung de dragon blanco (DB) y ojos de viento propio o predominante
    if len(pungs_and_kongs) == 4 and len(pairs) == 1:
        has_b2 = False; has_b4 = False; has_b8 = False; has_db = False
        for g in pungs_and_kongs:
            if g["pieces"][0] == 'B2': has_b2 = True
            elif g["pieces"][0] == 'B4': has_b4 = True
            elif g["pieces"][0] == 'B8': has_b8 = True
            elif g["pieces"][0] == 'DB': has_db = True
        is_wind_pair = pairs[0]["pieces"][0] == own_wind or pairs[0]["pieces"][0] == round_wind
        if has_b2 and has_b4 and has_b8 and has_db and is_wind_pair:
            return 15000, "BENDICION CELESTIAL", []

    # JASPE ROJO (15.000 puntos)
    # Requisitos: Solamente palos rojos (P1, P5, P7, P9) y opcionalmente el dragón rojo (DR)
    is_jaspe_rojo = True
    valid_red_pieces = ['P1', 'P5', 'P7', 'P9', 'DR']
    for p in all_pieces:
        if p not in valid_red_pieces:
            is_jaspe_rojo = False
            break
    if is_jaspe_rojo:
        return 15000, "JASPE ROJO", []

    # GRAN MURALLA CHINA (15.000 puntos)
    # Requisitos: Todo debe estar conformado por chinos impares (C1, C3, C5, C7, C9)
    is_gran_muralla = True
    muralla_pieces = ['C1', 'C3', 'C5', 'C7', 'C9']
    for p in all_pieces:
        if p not in muralla_pieces:
            is_gran_muralla = False
            break
    if is_gran_muralla:
        return 15000, "GRAN MURALLA CHINA", []
        
    # CIUDAD PROHIBIDA (15.000 puntos)
    # Requisitos: Todo conformado por chinos pares (C2, C4, C6, C8) y opcionalmente Dragón Rojo (DR)
    is_ciudad_prohibida = True
    ciudad_pieces = ['C2', 'C4', 'C6', 'C8', 'DR']
    for p in all_pieces:
        if p not in ciudad_pieces:
            is_ciudad_prohibida = False
            break
    if is_ciudad_prohibida:
        return 15000, "CIUDAD PROHIBIDA", []

    # === BLOQUE 10.000 PUNTOS ===

    num_wind_pungs = 0
    for g in pungs_and_kongs:
        if g["pieces"][0] in WINDS:
            num_wind_pungs += 1

    # ROSA DE LOS VIENTOS (10.000 puntos)
    # Requisitos: 4 Pungs de los 4 vientos y un par de cualquier cosa
    if num_wind_pungs == 4:
        return 10000, "ROSA DE LOS VIENTOS", []
        
    # TIFON ORIENTAL (10.000 puntos)
    # Requisitos: 3 Pungs de vientos, 1 pung de dragón y un par del último viento restante
    if num_wind_pungs == 3:
        num_dragon_pungs = 0
        for g in pungs_and_kongs:
            if g["pieces"][0] in DRAGONS:
                num_dragon_pungs += 1
        if num_dragon_pungs == 1 and len(pairs) == 1:
            if pairs[0]["pieces"][0] in WINDS:
                return 10000, "TIFON ORIENTAL", []

    # ARMONIA CELESTE (10.000 puntos)
    # Requisitos: Pungs de los 3 dragones (blanco, verde, rojo), pung del viento propio o predominante, ojos de cualquier honor
    if len(pungs_and_kongs) == 4 and len(pairs) == 1:
        num_dragon_pungs = 0
        for g in pungs_and_kongs:
            if g["pieces"][0] in DRAGONS:
                num_dragon_pungs += 1
        if num_dragon_pungs == 3:
            has_wind_pung = False
            for g in pungs_and_kongs:
                if g["pieces"][0] == own_wind or g["pieces"][0] == round_wind:
                    has_wind_pung = True
                    break
            if has_wind_pung and pairs[0]["is_honor"]:
                return 10000, "ARMONIA CELESTE", []

    # === BLOQUE 7.500 PUNTOS ===

    if len(pairs) == 7:
        # HIJOS DE LA NOCHE (7.500 puntos)
        # Requisitos: 7 pares de una misma pinta, sin vientos ni dragones. Debe ser totalmente oculta.
        is_hijos_noche = True
        unique_suit = ""
        for p in all_pieces:
            if p in WINDS or p in DRAGONS:
                is_hijos_noche = False
                break
            if unique_suit == "":
                unique_suit = p[0]
            elif p[0] != unique_suit:
                is_hijos_noche = False
                break
        if is_hijos_noche and all_hidden:
            return 7500, "HIJOS DE LA NOCHE", []

    # === BLOQUE 5.000 PUNTOS ===
    
    # GRAN SEGUIDILLA REAL (5.000 puntos)
    # Requisitos: Tres chows que armen 1-2-3, 4-5-6 y 7-8-9 de la misma pinta. Un Pung de dragón. Un par de viento (propio o de ronda). Debe ser totalmente oculta.
    if len(chows) == 3 and len(pungs_and_kongs) == 1 and len(pairs) == 1:
        chow_suits = []
        chow_starts = []
        for c in chows:
            suit = c["pieces"][0][0]
            number = c["pieces"][0][1:]
            if suit not in chow_suits:
                chow_suits.append(suit)
            chow_starts.append(number)
        if len(chow_suits) == 1:
            if '1' in chow_starts and '4' in chow_starts and '7' in chow_starts:
                is_dragon_pung = pungs_and_kongs[0]["pieces"][0] in DRAGONS
                is_wind_pair = pairs[0]["pieces"][0] in [own_wind, round_wind]
                if is_dragon_pung and is_wind_pair and all_hidden:
                    return 5000, "GRAN SEGUIDILLA REAL", ["Mano oculta"]
    
    # ASES Y NUEVES (5.000 puntos)
    # Requisitos: Únicamente Pungs y un Par conformado estrictamente por ases (1) y nueves (9)
    if len(pungs_and_kongs) == 4 and len(pairs) == 1:
        is_ases_y_nueves = True
        for g in pungs_and_kongs:
            if not (g["is_honor"] and g["nature"] == "suit"):
                is_ases_y_nueves = False
                break
        if not pairs[0]["is_honor"]:
            is_ases_y_nueves = False
        if is_ases_y_nueves:
            return 5000, "ASES Y NUEVES", []

    # JASPE VERDE (5.000 puntos)
    # Requisitos: Solamente palos verdes (P2, P3, P4, P6, P8) y opcionalmente el dragón verde (DV)
    is_jaspe_verde = True
    valid_green_pieces = ['P2', 'P3', 'P4', 'P6', 'P8', 'DV']
    for p in all_pieces:
        if p not in valid_green_pieces:
            is_jaspe_verde = False
            break
    if is_jaspe_verde:
        return 5000, "JASPE VERDE", []

    # === BLOQUE 2.500 PUNTOS ===

    # GRAN SEGUIDILLA REAL (2.500 puntos)
    # Requisitos: Tres chows que armen 1-2-3, 4-5-6 y 7-8-9 de la misma pinta. Un Pung de dragón. Un par de viento (propio o de ronda).
    if len(chows) == 3 and len(pungs_and_kongs) == 1 and len(pairs) == 1:
        chow_suits = []
        chow_starts = []
        for c in chows:
            suit = c["pieces"][0][0]
            number = c["pieces"][0][1:]
            if suit not in chow_suits:
                chow_suits.append(suit)
            chow_starts.append(number)
        if len(chow_suits) == 1:
            if '1' in chow_starts and '4' in chow_starts and '7' in chow_starts:
                is_dragon_pung = pungs_and_kongs[0]["pieces"][0] in DRAGONS
                is_wind_pair = pairs[0]["pieces"][0] in [own_wind, round_wind]
                if is_dragon_pung and is_wind_pair:
                    return 2500, "GRAN SEGUIDILLA REAL", []

    if len(pairs) == 7:
        # 7 SAMURAIS (2.500 puntos)
        # Requisitos: 7 pares de honores (vientos, dragones o ases/nueves sin importar pinta). Debe ser totalmente oculta.
        is_7_samurais = True
        for p in all_pieces:
            is_wind = p in WINDS
            is_dragon = p in DRAGONS
            is_minor_honor = len(p) > 1 and p[1] in MINOR_HONORS
            if not is_wind and not is_dragon and not is_minor_honor:
                is_7_samurais = False
                break
        if is_7_samurais and all_hidden:
            return 2500, "7 SAMURAIS", []

    # 13 MARAVILLAS (2.500 puntos)
    # Requisitos: 1 honor de cada uno (4 vientos, 3 dragones, 6 ases/nueves), y uno de ellos repetido para formar el par. Debe ser totalmente oculta.
    all_honors_required = []
    for w in WINDS: all_honors_required.append(w)
    for d in DRAGONS: all_honors_required.append(d)
    for s in SUITS:
        all_honors_required.append(s + '1')
        all_honors_required.append(s + '9')
        
    if len(groups) == 13 and len(all_pieces) == 13:
        is_13_maravillas = True
        for piece in all_pieces:
            if piece not in all_honors_required:
                is_13_maravillas = False
                break
        if is_13_maravillas and all_hidden:
            return 2500, "13 MARAVILLAS", []

    # Si no encaja en ninguna, devolvemos 0 puntos de clásicos
    return 0, "", []

# Función principal que coordina todo el cálculo: decide si es clásica o tradicional y junta base + dobles
def evaluate_hand(parsed_hand: dict) -> dict:
    own_wind = parsed_hand["own_wind"]
    round_wind = parsed_hand["round_wind"]
    flowers = parsed_hand.get("flowers", [])
    winning_piece = parsed_hand.get("winning_piece", "")
    
    groups = parsed_hand.get("groups_details", [])
    has_chow = False
    for g in groups:
        if g["group_type"] == "chow":
            has_chow = True
            break
    
    # Manejo de fallos en grupos
    for g in groups:
        if g["group_type"] == "invalid":
            return {"visual": parsed_hand.get("visual", ""), "base": 0, "dobles": 0, "total": 0, "estilo": "INVALIDO", "log": ["Grupos inválidos encontrados."]}

    classic_points, classic_name, classic_log = detect_classic(groups, flowers, own_wind, round_wind, winning_piece)

    if classic_points > 0:
        base = classic_points
        style = classic_name
        log = [f"Mano Clásica: {style}"] + classic_log
    else:
        style = "TRADICIONAL"
        base, b_log = calculate_base_points(groups, flowers, has_chow)
        log = b_log

    doubles, d_log = calculate_doubles(groups, flowers, own_wind, round_wind, has_chow)
    
    for l in d_log:
        log.append(l)

    total = base * (2 ** doubles)
    
    # El viento Este (E) siempre duplica la cuenta al final (cobra y paga doble)
    if own_wind == 'E':
        # Hay una regla del manual: un clásico de 15.000 o 20.000 NO SE DOBLA para el Este
        if classic_points >= 15000:
             pass 
        else:
             total = total * 2
             log.append("ESTE cobra doble")

    if total > MAX_TOTAL_POINTS:
        total = MAX_TOTAL_POINTS

    return {
        "visual": parsed_hand.get("visual", ""),
        "base": base,
        "dobles": doubles,
        "total": int(total),
        "estilo": style,
        "log": log
    }
