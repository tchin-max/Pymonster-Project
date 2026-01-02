# tests/test_beast_hunt_and_kill.py
import math
from .conftest import fill49

# Test: hunt, locate_hunting_list, compute_kill_list, locate_enemy_list


def test_hunt_no_enemies(beast):
    env = fill49("." * 49)
    beast.set_environment(env)
    beast.parse_environment(env)

    assert beast.hunt() == []


def test_hunt_single_enemy_above(beast):
    rows = [
        "...<...",
        "...B...",
        ".......",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    result = beast.hunt()
    assert len(result) == 1
    dx, dy = result[0]
    assert dy < 0  # Gegner über dem Beast


def test_hunt_multiple_enemies_sorted_by_distance(beast):
    rows = [
        "..<....",
        "...B...",
        "......<",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    result = beast.hunt()
    assert len(result) == 2

    d1 = math.hypot(*result[0])
    d2 = math.hypot(*result[1])
    assert d1 <= d2  # erster ist näher


def test_hunt_clamping(beast):
    rows = [
        "......<",
        ".......",
        "...B...",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    dx, dy = beast.hunt()[0]
    assert abs(dx) <= 2
    assert abs(dy) <= 2


def test_locate_hunting_list_positions(beast):
    rows = [
        "<......",
        "...B...",
        "......<",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    coords = beast.locate_hunting_list()
    # Gegner links oben bei (0,0) und rechts bei (6,2)
    assert (0, 0) in coords
    assert (6, 2) in coords


def test_compute_kill_list_from_hunting_list(beast):
    rows = [
        ".......",
        "..<....",
        "...B...",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    kill_moves = beast.compute_kill_list()
    # Futter/Gegner bei (2,1) -> rel (dx=-1, dy=-2) oder ähnlich im 5x5
    assert len(kill_moves) >= 1
    for dx, dy in kill_moves:
        assert -2 <= dx <= 2
        assert -2 <= dy <= 2


def test_locate_enemy_list_area(beast):
    # enemy an Position (0,0) -> alle coords im Bereich [-2..2]x[-2..2]
    area = beast.locate_enemy_list((0, 0))
    assert len(area) == 25
    assert (-2, -2) in area
    assert (2, 2) in area
