# tests/test_beast_simulation_and_food_moves.py
import numpy as np
from .conftest import fill49


def _find_positions(field, symbol):
    coords = []
    for y in range(field.shape[0]):
        for x in range(field.shape[1]):
            if field[y, x] == symbol:
                coords.append((x, y))
    return coords


def test_simulate_future_environment_shifts_field(beast):
    # Ein einzelnes Futter RECHTS direkt neben B
    rows = [
        ".......",
        ".......",
        ".......",
        "...B*..",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    original = beast.parse_environment(env)
    original_food = _find_positions(original, "*")
    assert len(original_food) == 1

    future = beast._simulate_future_environment(
        (1, 0)
    )  # Beast geht nach rechts
    future_food = _find_positions(future, "*")

    # Beast ist wieder in der Mitte
    assert future[3, 3] == "B"

    # Das Futter wurde "gefressen" -> kein '*' mehr im Sichtfeld
    assert len(future_food) == 0
