from pymonster import utils
from .conftest import fill49


# Test: (Normaler Split + Notfall-Split)


def test_split_normal_conditions_met(beast):
    """
    Normaler Split:
      - Energie > 80
      - durchschnittliche Energie pro Runde >= 2.5
      - keine Hunt- oder Escape-Moves
      - mindestens 4 Food-Moves
    """
    beast.set_energy(100.0)
    # round_abs erhöhen, damit avg > 2.5 wird: 100/30 ≈ 3.33
    beast.set_round_abs(30)

    # keine Gegner, kein Escape
    beast.set_hunt_list([])
    beast.set_escape_list([])

    # food_list künstlich setzen
    food_moves = [(0, -1), (1, 0), (-1, 0), (0, 1)]
    beast.set_food_list(food_moves)

    # mehrere eigene Beasts -> kein Notfall-Split
    utils.GLOBAL_BEAST_LIST = [beast, object()]

    move, do_split = beast.split()
    assert do_split is True
    assert move in food_moves or move in [(0, -1), (0, 1), (1, 0), (-1, 0)]


def test_split_not_enough_energy(beast):
    beast.set_energy(50.0)
    beast.set_round_abs(30)
    beast.set_food_list([(0, -1)] * 4)
    beast.set_hunt_list([])
    beast.set_escape_list([])

    # Dummy-Environment setzen (kein Futter, keine Gegner, aber 49 Zeichen)
    env = fill49("." * 49)
    beast.set_environment(env)

    # Mehr als ein Beast -> kein Notfall-Split
    utils.GLOBAL_BEAST_LIST = [beast, object()]

    move, do_split = beast.split()
    assert do_split is False
    assert move is None


def test_emergency_split_single_beast(beast):
    """
    Notfall-Split:
      - nur ein eigenes Beast
      - Energie >= 50
      - Runde >= 100
      - mind. ein Futter im Sichtfeld
      - keine Gegner im 5x5
    """
    beast.set_energy(60.0)
    beast.set_round_abs(100)

    # Sichtfeld: ein Futter, keine Gegner
    rows = [
        ".......",
        ".......",
        "...*...",
        "...B...",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(rows))
    beast.set_environment(env)

    beast.set_food_list([(0, -1)])
    beast.set_hunt_list([])
    beast.set_escape_list([])

    # nur dieses eine Beast existiert
    utils.GLOBAL_BEAST_LIST = [beast]

    move, do_split = beast.split()
    assert do_split is True
    assert move in [(0, -1), (0, 1), (1, 0), (-1, 0)]
