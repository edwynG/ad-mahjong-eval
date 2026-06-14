import re

def decode_play(visual_line):
    """
    Toma una línea de entrada del dataset y la descompone en un diccionario.
    """
    line = visual_line.strip()
    
    # Extraer ID de la línea (el primer elemento separado por espacio)
    id_parts = line.split(maxsplit=1)
    line_id = id_parts[0].strip()
    remaining_line = id_parts[1] if len(id_parts) > 1 else ''
    
    # Extraer Vientos [VP / VR]
    winds_match = re.search(r'\[(.*?)/(.*?)\]', remaining_line)
    own_wind, round_wind = None, None
    if winds_match:
        own_wind = winds_match.group(1).strip()
        round_wind = winds_match.group(2).strip()
        
    # Extraer Flores <...>
    flowers_match = re.search(r'<(.*?)>', remaining_line)
    flowers = []
    if flowers_match and flowers_match.group(1).strip():
        # Separamos las flores encontradas por espacios
        flowers = flowers_match.group(1).strip().split()
        
    #  Extraer Pieza Ganadora *...*
    winning_match = re.search(r'\*(.*?)\*', remaining_line)
    winning_piece = winning_match.group(1).strip() if winning_match else None
    
    # Extraer Grupos de la mano (lo que está entre los vientos y las flores o la ganadora)
    hand_start = winds_match.end() if winds_match else 0
    
    if flowers_match:
        hand_end = flowers_match.start()
    elif winning_match:
        hand_end = winning_match.start()
    else:
        hand_end = len(remaining_line)
    
    # Nos quedamos con la zona del medio y la separamos por espacios
    hand_zone = remaining_line[hand_start:hand_end].strip()
    raw_groups = hand_zone.split()
    
    return {
        "id": line_id,
        "own_wind": own_wind,
        "round_wind": round_wind,
        "groups": raw_groups,
        "flowers": flowers,
        "winning_piece": winning_piece
    }

# Bloque de prueba
if __name__ == '__main__':
    # Usando el ejemplo 1 del /docs/statement.pdf
    test_line = "1 [E / E] [B4-B4-B4-B4] [B8-B8-B8-B8] [B1-B1-B1] {S-S-S} (B5-B5) <R1 R4> *B5*"
    result = decode_play(test_line)
    
    for key, value in result.items():
        print(f"{key.upper()}: {value}")