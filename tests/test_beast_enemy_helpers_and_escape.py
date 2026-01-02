from pymonster import utils
from pymonster.beast import Beast
from .conftest import fill49

# Test : locate_unique_enemy_moves, get_enemy_positions, score_safe_moves, escape


def test_get_enemy_positions_excludes_allies(beast):
    """
    Ein Gegnerzeichen '>' wird ignoriert, wenn dort eigentlich
    ein eigenes Beast steht.
    """
    # Unser Beast sitzt bei (10,10)
    beast.set_abs_x(10)
    beast.set_abs_y(10)

    # Gegner relativ bei (1,0)
    rows = [
        ".......",
        ".......",
        ".......",
        "...B>..",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    # Ally sitzt auf der absoluten Gegnerposition (11,10)
    ally = Beast()
    ally.set_id(2)
    ally.set_abs_x(11)
    ally.set_abs_y(10)

    utils.GLOBAL_BEAST_LIST = [beast, ally]

    enemy_positions = beast.get_enemy_positions()
    # wird als Ally erkannt -> keine Gegner
    assert enemy_positions == []


def test_get_enemy_positions_simple_enemy(beast):
    rows = [
        ".......",
        ".......",
        ".......",
        "...B>..",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    # nur unser Beast in der Liste
    utils.GLOBAL_BEAST_LIST = [beast]

    enemy_positions = beast.get_enemy_positions()
    # Gegner liegt relativ bei (1,0)
    assert (1, 0) in enemy_positions


def test_score_safe_moves_prefers_farther_away(beast):
    # Gegner am Ursprung
    safe_moves = [(0, 1), (0, 3)]
    enemy_list = [(0, 0)]

    sorted_moves, scores = beast.score_safe_moves(safe_moves, enemy_list)
    # (0,3) ist weiter weg von (0,0) als (0,1)
    assert sorted_moves[0] == (0, 3)
    assert scores[sorted_moves[0]] > scores[sorted_moves[1]]


def test_escape_no_enemies_returns_empty(beast):
    env = fill49("." * 49)
    beast.set_environment(env)

    result = beast.escape()
    assert result == []


def test_escape_avoids_danger_zone(beast):
    """
    Ein Gegner unter uns -> Moves im 5x5 um den Gegner gelten als Gefahr.
    """
    rows = [
        ".......",
        ".......",
        ".......",
        "...B...",
        ".......",
        "...>...",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    moves = beast.escape()
    # es sollte zumindest Moves geben
    assert isinstance(moves, list)

    # direkter Move in Richtung des Gegners (0,1) sollte nicht als safe gelten
    assert (0, 1) not in moves


def test_locate_unique_enemy_moves(beast):
    """
    Mehrere Gegner ('>', '=') sollen zu einer Liste einzigartiger Moves führen.
    """
    rows = [
        "..>....",
        "...=...",
        ".......",
        "...B...",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    moves = beast.locate_unique_enemy_moves()

    # jeder Gegner hat ein 5x5 um sich; wir erwarten NICHT, wie viele genau
    # aber: Moves dürfen keine Duplikate enthalten
    assert isinstance(moves, list)
    assert len(moves) == len(set(moves))
    assert (0, 0) in moves
