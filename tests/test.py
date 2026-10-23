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
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        play_id, res_str = process_play(line)
        assert play_id != -1, f"Error en jugada: {line}"
        assert "ERROR" not in res_str, f"Error en resultado: {res_str}"

    print(f"✔ Dataset validado ({len(lines)} jugadas procesadas sin errores).")


if __name__ == '__main__':
    print("Ejecutando pruebas...")
    test_parser()
    test_rules()
    test_dataset()
    print("✔ Todas las pruebas pasaron correctamente.")
