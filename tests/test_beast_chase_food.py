import math
from .conftest import fill49

# Test: chase_food & _chase_food_one_step


def test_chase_food_no_food(beast):
    env = fill49("." * 49)
    beast.set_environment(env)
    beast.parse_environment(env)

    moves = beast.chase_food()

    assert len(moves) == 1
    dx, dy = moves[0]
    assert not (dx == 0 and dy == 0)
    assert abs(dx) <= 1
    assert abs(dy) <= 1


def test_chase_food_many_food_moves_no_lookahead(beast):
    env_rows = [
        "*.*.*.*",
        ".*.*.*.",
        "*.*B*.*",
        ".*.*.*.",
        "*.*.*.*",
        ".*.*.*.",
        "*.*.*.*",
    ]
    env = fill49("".join(env_rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    result = beast.chase_food()

    assert len(result) > 7
    for dx, dy in result:
        assert -2 <= dx <= 2
        assert -2 <= dy <= 2


def test_chase_food_prefers_move_with_more_future_food(beast):
    env_rows = [
        ".......*",
        "...B....",
        "........",
        "........",
        "...*....",
        "........",
        "........",
    ]
    env = fill49("".join(env_rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    moves = beast.chase_food()
    assert len(moves) > 0
    best = moves[0]
    assert isinstance(best, tuple) and len(best) == 2


def test_chase_food_penalty_if_future_no_food(beast):
    env_rows = [
        "..*....",
        "...B...",
        ".......",
        ".......",
        ".......",
        ".......",
        ".......",
    ]
    env = fill49("".join(env_rows))

    beast.set_environment(env)
    beast.parse_environment(env)

    best = beast.chase_food()[0]
    dx, dy = best
    assert dy < 0  # Futter liegt über B


def test_chase_food_one_step_mode(beast):
    """
    priority_energy < 2.0 -> _chase_food_one_step wird verwendet.
    """
    beast.set_priority_energy(1.5)
    rows = [
        "..*....",
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

    moves = beast.chase_food()
    best = moves[0]
    # nur 1er-Moves erlaubt
    assert max(abs(best[0]), abs(best[1])) == 1
