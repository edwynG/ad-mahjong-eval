import os
from src.parser import decode_play, process_play
from src.mahjong_rules import classify_group, is_valid_chow


def test_parser():
    line = "1 [E / E] [B4-B4-B4-B4] [B8-B8-B8-B8] [B1-B1-B1] {S-S-S} (B5-B5) <R1 R4> *B5*"
    data = decode_play(line)
    assert data["id"] == "1"
    assert data["own_wind"] == "E"
    assert len(data["groups"]) == 5
    assert data["winning_piece"] == "B5"


def test_rules():
    assert is_valid_chow(["B1", "B2", "B3"]) is True
    assert is_valid_chow(["B1", "C2", "B3"]) is False
    assert classify_group("[B4-B4-B4-B4]")["group_type"] == "kong"
    assert classify_group("{S-S-S}")["visibility"] == "concealed"


def test_dataset():
    input_file = os.path.join(os.path.dirname(__file__), 'data', 'input_maestro.txt')
    sol_file = os.path.join(os.path.dirname(__file__), 'data', 'soluciones_maestro.txt')
    with open(input_file, 'r', encoding='utf-8') as f_in, open(sol_file, 'r', encoding='utf-8') as f_sol:
        lines = [line.strip() for line in f_in if line.strip()]
        expected_lines = [line.strip() for line in f_sol if line.strip()]

    for line, exp in zip(lines, expected_lines):
        play_id, res_str = process_play(line)
        assert play_id != -1, f"Error en jugada: {line}"
        assert "ERROR" not in res_str, f"Error en resultado: {res_str}"
        got_parts = [p.strip() for p in res_str.split('|')]
        exp_parts = [p.strip() for p in exp.split('|')]
        assert got_parts[1:5] == exp_parts[1:5], f"Mismatch en jugada {play_id}: GOT {got_parts[1:5]} vs EXP {exp_parts[1:5]}"

    print(f"✔ Dataset validado ({len(lines)} jugadas coinciden 100% con soluciones_maestro.txt).")


def test_classic_hands():
    classic_cases = [
        ("PESCANDO LA LUNA DEL FONDO DEL MAR", 20000, "50 [S / S] [C2-C3-C4] [C5-C5-C5] [C7-C7-C7] [P2-P3-P4] (B1-B1) <> *B1*"),
        ("LA FLOR DEL CEREZO", 20000, "51 [E / E] [C2-C3-C4] [C5-C5-C5] [C7-C7-C7] [P2-P3-P4] (B5-B5) <R1> *B5*"),
        ("GRANDES SAMURAIS", 20000, "52 [S / S] (E-E) (S-S) (W-W) (N-N) (DR-DR) (DV-DV) (DB-DB) <> *DB*"),
        ("BENDICION CELESTIAL", 15000, "53 [E / E] [B2-B2-B2] [B4-B4-B4] [B8-B8-B8] [DB-DB-DB] (E-E) <> *E*"),
        ("JASPE ROJO", 15000, "54 [S / S] [P1-P1-P1] [P5-P5-P5] [P7-P7-P7] [P9-P9-P9] (DR-DR) <> *DR*"),
        ("GRAN MURALLA CHINA", 15000, "55 [S / S] [C1-C1-C1] [C3-C3-C3] [C5-C5-C5] [C7-C7-C7] (C9-C9) <> *C9*"),
        ("CIUDAD PROHIBIDA", 15000, "56 [S / S] [C2-C2-C2] [C4-C4-C4] [C6-C6-C6] [C8-C8-C8] (DR-DR) <> *DR*"),
        ("ROSA DE LOS VIENTOS", 10000, "57 [S / S] [E-E-E] [S-S-S] [W-W-W] [N-N-N] (C1-C1) <> *C1*"),
        ("TIFON ORIENTAL", 10000, "58 [S / S] [E-E-E] [S-S-S] [W-W-W] [DR-DR-DR] (N-N) <> *N*"),
        ("ARMONIA CELESTE", 10000, "59 [E / E] [DR-DR-DR] [DV-DV-DV] [DB-DB-DB] [E-E-E] (W-W) <> *W*"),
        ("HIJOS DE LA NOCHE", 7500, "60 [S / S] (P1-P1) (P2-P2) (P3-P3) (P4-P4) (P5-P5) (P6-P6) (P7-P7) <> *P7*"),
        ("ASES Y NUEVES", 5000, "61 [S / S] [C1-C1-C1] [C9-C9-C9] [P1-P1-P1] [B9-B9-B9] (B1-B1) <> *C1*"),
        ("JASPE VERDE", 5000, "62 [S / S] [P2-P3-P4] [P6-P6-P6] [P8-P8-P8] [DV-DV-DV] (P2-P2) <> *P2*"),
        ("GRAN SEGUIDILLA REAL", 2500, "63 [S / S] [B1-B2-B3] [B4-B5-B6] [B7-B8-B9] [DV-DV-DV] (S-S) <> *S*"),
        ("7 SAMURAIS", 2500, "64 [S / S] (P1-P1) (P9-P9) (C1-C1) (C9-C9) (B1-B1) (B9-B9) (DR-DR) <> *DR*"),
        ("13 MARAVILLAS", 2500, "65 [S / S] {E} {S} {W} {N} {DR} {DV} {DB} {C1} {C9} {P1} {P9} {B1} (B9-B9) <> *B9*"),
    ]

    for name, expected_base, play in classic_cases:
        res = process_play(play)[1]
        parts = [p.strip() for p in res.split('|')]
        assert parts[4] == name, f"Error en {name}: estilo obtenido fue {parts[4]}"
        assert int(parts[1]) == expected_base, f"Error en base de {name}: esperada {expected_base}, obtenida {parts[1]}"

    # Gran seguidilla real con viento Este (ejemplo 23 del enunciado)
    ex23 = "23 [E / E] [B1-B2-B3] [B4-B5-B6] [B7-B8-B9] [DV-DV-DV] (E-E) <> *E*"
    res_23 = process_play(ex23)[1]
    assert "GRAN SEGUIDILLA REAL" in res_23
    assert "| 2500 | 1 | 5000 |" in res_23

    print("✔ Las 16 Manos Clásicas del enunciado validadas exitosamente.")


if __name__ == '__main__':
    print("Ejecutando pruebas...")
    test_parser()
    test_rules()
    test_classic_hands()
    test_dataset()
    print("✔ Todas las pruebas pasaron correctamente.")

