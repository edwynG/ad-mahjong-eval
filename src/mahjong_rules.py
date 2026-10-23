# CONSTANTES GLOBALES 
# Usamos sets {} para garantizar búsquedas O(1) de altísima eficiencia
WINDS = {'E', 'S', 'W', 'N'}
DRAGONS = {'DR', 'DV', 'DB'}
SUITS = {'C', 'P', 'B'}
MINOR_HONORS = {'1', '9'}

def is_valid_chow(pieces: list) -> bool:
    """
    Verifica si una lista de exactamente 3 piezas forma un Chow válido (una secuencia consecutiva de la misma familia).
    """
    suits_in_group = [p[0] for p in pieces]
    
    # Verificamos contra la constante global SUITS
    if len(set(suits_in_group)) != 1 or suits_in_group[0] not in SUITS:
        return False
        
    try:
        numbers = sorted([int(p[1:]) for p in pieces])
        return numbers[0] + 1 == numbers[1] and numbers[1] + 1 == numbers[2]
    except ValueError:
        return False

def classify_group(raw_group: str) -> dict:
    """
    Toma la cadena de un grupo (ej: '[C2-C3-C4]') y la clasifica devolviendo un diccionario con su tipo (Pung, Kong, Chow, Par), pinta base, si es honor, y su estado (oculto o abierto).
    """
    raw = raw_group.strip()
    visibility = "unknown"
    group_type = "invalid" 
    nature = "unknown"
    is_honor = False
    
    if raw.startswith('[') and raw.endswith(']'):
        visibility = "open"
    elif raw.startswith('{') and raw.endswith('}'):
        visibility = "concealed"
    elif raw.startswith('(') and raw.endswith(')'):
        visibility = "open"
        
    clean_group = raw[1:-1]
    pieces = clean_group.split('-')
    length = len(pieces)

    unique_pieces = set(pieces)
    
    if len(unique_pieces) == 1:
        if length == 2:
            group_type = "pair"
        elif length == 3:
            group_type = "pung"
        elif length == 4:
            group_type = "kong"
    elif length == 3:
        if is_valid_chow(pieces):
            group_type = "chow"
            
    if group_type != "invalid":
        base_piece = pieces[0]
        
        # Búsquedas instantáneas en memoria usando las constantes globales
        if base_piece in WINDS:
            nature = "wind"
            is_honor = True
        elif base_piece in DRAGONS:
            nature = "dragon"
            is_honor = True
        elif base_piece[0] in SUITS:
            nature = "suit"
            # Solo es honor si no es un chow y es un 1 o un 9
            if group_type != "chow" and len(base_piece) > 1 and base_piece[1] in MINOR_HONORS:
                is_honor = True

    return {
        "raw": raw,
        "visibility": visibility,
        "group_type": group_type,
        "nature": nature,
        "is_honor": is_honor,
        "pieces": pieces
    }

# Pruebas de fuego
if __name__ == '__main__':
    test_groups = [
        '[B4-B4-B4-B4]',  # Kong válido
        '[B1-B2-B3]',     # Chow válido
        '[B1-C2-P3]',     # Invalido (Pintas mezcladas)
        '[B2-B4-B6]',     # Invalido (Misma pinta, no consecutivos)
        '{S-S-S}',        # Pung válido (Oculto)
        '[E-S-W]',        # Invalido (No se puede hacer Chow de vientos)
        '(B5-B5)'         # Par válido
    ]
    
    for g in test_groups:
        result = classify_group(g)
        print(f"Raw: {result['raw']:<15} | Type: {result['group_type']:<7} | "
              f"Vis: {result['visibility']:<9} | Nature: {result['nature']:<6} | "
              f"Honor: {result['is_honor']}")