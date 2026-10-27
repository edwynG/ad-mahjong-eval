from src.mahjong_rules import WINDS, DRAGONS, SUITS, MINOR_HONORS


POINTS_CHOW = 0
POINTS_FLOWER = 4
POINTS_MAHJONG_CHOW = 20
POINTS_MAHJONG_PUNG = 30
MAX_TOTAL_POINTS = 20000

WIND_TO_FLOWER_NUM = {'E': '1', 'S': '2', 'W': '3', 'N': '4'}

def is_hidden(group: dict) -> bool:
    """
    Función auxiliar para saber si un grupo está oculto o cerrado
    """
    return group["visibility"] in ["closed", "concealed"]

def calculate_base_points(groups: list, flowers: list, has_chow: bool) -> tuple:
    """
    Calcula la cuenta base tradicional sumando los puntos de cada grupo, flores y bonos
    """
    base = 0
    log = []
    
    # Puntos por cada grupo (Pung o Kong)
    for g in groups:
        group_type = g["group_type"]
        is_honor = g["is_honor"]
        is_concealed = is_hidden(g)
        group_points = 0
        
        if group_type == "pung":
            if is_honor:
                group_points = 8 if is_concealed else 4
                desc = 'pung oculto honor' if is_concealed else 'pung abierto honor'
            else:
                group_points = 4 if is_concealed else 2
                desc = 'pung oculto pinta' if is_concealed else 'pung abierto pinta'
            base += group_points
            log.append(f"{base} {desc} {group_points} ")
        elif group_type == "kong":
            if is_honor:
                group_points = 32 if is_concealed else 16
                desc = 'kung oculto honor' if is_concealed else 'kung abierto honor'
            else:
                group_points = 16 if is_concealed else 8
                desc = 'kung oculto pinta' if is_concealed else 'kung abierto pinta'
            base += group_points
            log.append(f"{base} {desc} {group_points} ")
        elif group_type == "pair":
            base_piece = g["pieces"][0]
            # Solo los ojos de dragon rojo (DR) dan 4 puntos fijos
            if base_piece == "DR":
                group_points = 4
                base += group_points
                log.append(f"{base} ojos dragon {group_points} ")

    # Bono por hacer Mahjong
    if has_chow:
        bonus = POINTS_MAHJONG_CHOW
        desc_mahjong = 'mahjong con chow 20 '
    else:
        bonus = POINTS_MAHJONG_PUNG
        desc_mahjong = 'mahjong sin chow 30 '
        
    base += bonus
    log.append(f"{base} {desc_mahjong}")

    # Puntos por tener flores
    if len(flowers) > 0:
        flower_points = len(flowers) * POINTS_FLOWER
        base += flower_points
        log.append(f"{base} flores: {len(flowers)} para {flower_points} puntos")

    raw_base = base
    rounded_base = int(round(raw_base / 10.0) * 10)
    log.append(f"Total puntos: {raw_base} para {rounded_base}")

    return rounded_base, log

def calculate_doubles(groups: list, flowers: list, own_wind: str, round_wind: str, has_chow: bool) -> tuple:
    """
    Calcula la cantidad de multiplicadores (dobles) por características como el viento, dragones o si es limpia
    """
    doubles = 0
    log = []

    # Contar cuantas flores rojas y negras tenemos
    red_flowers = [f for f in flowers if f.startswith('R')]
    black_flowers = [f for f in flowers if f.startswith('G')]
    
    has_red_bouquet = (len(red_flowers) == 4)
    has_black_bouquet = (len(black_flowers) == 4)

    # Asignar dobles por ramilletes
    if has_red_bouquet:
        doubles += 4
        log.append("[+] 4 Dobles: Ramillete Rojo")
        
    if has_black_bouquet:
        doubles += 4
        log.append("[+] 4 Dobles: Ramillete Negro")

    # Dobles por vientos y dragones
    for g in groups:
        g_type = g["group_type"]
        if g_type == "pung" or g_type == "kong":
            piece = g["pieces"][0]
            if piece == own_wind:
                doubles += 1
                log.append(f"[+] 1 Doble: Pung/Kung de Viento Propio ({piece})")
            elif piece == round_wind:
                doubles += 1
                log.append(f"[+] 1 Doble: Pung/Kung de Viento de Ronda ({piece})")
            elif piece in DRAGONS:
                doubles += 1
                log.append(f"[+] 1 Doble: Pung/Kung de Dragon ({piece})")

    # Asignar doble por cada flor propia (salvo si ya está en ramillete completo de su color)
    wind_number = WIND_TO_FLOWER_NUM.get(own_wind, '')
    for f in flowers:
        if f.endswith(wind_number):
            if f.startswith('R') and has_red_bouquet:
                continue
            if f.startswith('G') and has_black_bouquet:
                continue
            doubles += 1
            log.append(f"[+] 1 Doble: Flor Propia detectada ({f})")

    # Separar grupos para evaluar mahjong limpio/sucio
    used_suits = []
    for g in groups:
        if g["nature"] == "suit" or g["group_type"] == "chow":
            suit_char = g["pieces"][0][0]
            if suit_char not in used_suits:
                used_suits.append(suit_char)

    has_winds_or_dragons = any(g["nature"] in ["wind", "dragon"] for g in groups)
    chows = [g for g in groups if g["group_type"] == "chow"]

    suit_numbers = set()
    for g in groups:
        if g["nature"] == "suit" or g["group_type"] == "chow":
            for piece in g["pieces"]:
                if len(piece) > 1 and piece[1].isdigit():
                    suit_numbers.add(piece[1])

    # Evaluar MAH-JONGG LIMPIO
    if len(used_suits) == 1 and not has_winds_or_dragons:
        if len(chows) == 0:
            doubles += 5
            log.append("[+] 5 Dobles: MAH-JONGG LIMPIO (Solo Pungs/Kungs de una pinta)")
        elif len(chows) == 4:
            doubles += 4
            log.append("[+] 4 Dobles: MAH-JONGG LIMPIO (Solo Chows de una pinta)")
        else:
            doubles += 3
            log.append("[+] 3 Dobles: MAH-JONGG LIMPIO (Pungs y Chows de una pinta)")
            
    # Evaluar MAH-JONGG SUCIO / LIMPIO HONORES
    elif len(used_suits) == 1 and has_winds_or_dragons:
        if '1' in suit_numbers and '9' in suit_numbers and len(chows) == 0:
            suit_name = used_suits[0]
            doubles += 3
            log.append(f"[+] 3 Dobles: MAH-JONGG LIMPIO Honores (Pinta {suit_name} con Ases y Nueves)")
        else:
            doubles += 2
            log.append("[+] 2 Dobles: MAH-JONGG SUCIO (Honores con pinta)")

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
        doubles += 4
        log.append("[+] 4 Dobles: Escolares Mayores")
    elif len(dragon_pungs) == 2 and has_dragon_pair:
        doubles += 3
        log.append("[+] 3 Dobles: Escolares Menores")

    return doubles, log

def detect_classic(groups: list, flowers: list, own_wind: str, round_wind: str, winning_piece: str) -> tuple:
    """
    Comprueba si la mano cumple con alguna de las configuraciones raras (Clásicos)
    """
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
            
    # LA FLOR DEL CEREZO (20.000 puntos)
    # Requisitos: Que la pieza ganadora sea el 5 de Ruedas (B5) y se haya cargado la flor propia (última flor obtenida)
    wind_number = WIND_TO_FLOWER_NUM.get(own_wind, '')
    if winning_piece == "B5" and flowers and flowers[-1].endswith(wind_number):
        return 20000, "LA FLOR DEL CEREZO", ["B5 ganadora y flor propia cargada"]

    # PESCANDO LA LUNA DEL FONDO DEL MAR (20.000 puntos)
    # Requisitos: Hacer Mahjong con el as de ruedas (B1) como última pieza de la jugada
    if winning_piece == "B1":
        return 20000, "PESCANDO LA LUNA DEL FONDO DEL MAR", ["B1 ganadora"]

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
    all_honors_set = set(WINDS) | set(DRAGONS) | {s + '1' for s in SUITS} | {s + '9' for s in SUITS}
    flat_pieces = []
    for g in groups:
        flat_pieces.extend(g["pieces"])
        
    if len(flat_pieces) == 14 and set(flat_pieces) == all_honors_set and all_hidden:
        return 2500, "13 MARAVILLAS", []

    # Si no encaja en ninguna, devolvemos 0 puntos de clásicos
    return 0, "", []

def evaluate_hand(parsed_hand: dict) -> dict:
    """
    Función principal que coordina todo el cálculo: decide si es clásica o tradicional y junta base + dobles
    """
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

    classic_points, classic_name, classic_log = detect_classic(groups, flowers, own_wind, round_wind, winning_piece)

    if classic_points > 0:
        base = classic_points
        style = classic_name
        log = [f"Mano Clásica: {style}"] + classic_log
        
        # En manos clásicas los dobles tradicionales no aplican.
        # Si es viento ESTE y la mano es menor a 15.000 puntos, duplica (1 doble)
        if own_wind == 'E' and classic_points < 15000:
            doubles = 1
            total = base * 2
            log.append("ESTE cobra doble")
        else:
            doubles = 0
            total = base
    else:
        # Manejo de fallos en grupos para manos tradicionales
        for g in groups:
            if g["group_type"] in ["invalid", "single"]:
                return {"visual": parsed_hand.get("visual", ""), "base": 0, "dobles": 0, "total": 0, "estilo": "INVALIDO", "log": ["Grupos inválidos encontrados."]}

        style = "TRADICIONAL"
        base, b_log = calculate_base_points(groups, flowers, has_chow)
        log = b_log

        doubles, d_log = calculate_doubles(groups, flowers, own_wind, round_wind, has_chow)
        for l in d_log:
            log.append(l)

        raw_total = base * (2 ** doubles)
        total = int(round(raw_total / 100.0) * 100)
        log.append(f"Total mano: {raw_total} para {total}")

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
