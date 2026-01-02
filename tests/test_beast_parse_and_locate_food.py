import numpy as np
from .conftest import fill49

# Test: parse_environment & locate_food_list


def test_parse_environment_shape_and_center(beast):
    env = fill49(".<.........*....>...**.....<.........=...*....*..")
    beast.set_environment(env)

    field = beast.parse_environment(env)
    assert field.shape == (7, 7)
    assert field[3][3] == "B"


def test_locate_food_list_single_food(beast):
    # Futter rechts-oben von B
    rows = [
        ".......",
        ".......",
        "....*..",
        "...B...",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    food_moves = beast.locate_food_list()
    assert food_moves == [(1, -1)]  # dx=+1 (rechts), dy=-1 (oben)


def test_locate_food_list_multiple_food(beast):
    rows = [
        ".......",
        "..*.*..",
        ".......",
        "...B...",
        ".......",
        "..*.*..",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    food_moves = sorted(beast.locate_food_list())

    # vier Futterpositionen erwartet:
    assert (-1, -2) in food_moves
    assert (1, -2) in food_moves
    assert (-1, 2) in food_moves
    assert (1, 2) in food_moves
    assert len(food_moves) == 4
