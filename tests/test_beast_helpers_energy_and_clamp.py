import math

# Test: _move_energy, _is_move_within_energy_limit, _clamp_move


def test_move_energy_basic(beast):
    # 3-4-5-Dreieck: hypot(3,4) = 5
    move = (3, 4)
    energy = beast._move_energy(move)
    assert math.isclose(energy, 5.0)


def test_is_move_within_energy_limit_true(beast):
    beast.set_priority_energy(3.0)
    assert beast._is_move_within_energy_limit((2, 2)) is True


def test_is_move_within_energy_limit_false(beast):
    beast.set_priority_energy(2.0)
    # Distanz sqrt(3^2 + 0^2) = 3 > 2
    assert beast._is_move_within_energy_limit((3, 0)) is False


def test_clamp_move_default_max_step(beast):
    dx, dy = beast._clamp_move(10, -10)  # default max_step=2
    assert (dx, dy) == (2, -2)


def test_clamp_move_custom_max_step(beast):
    dx, dy = beast._clamp_move(5, -3, max_step=1)
    assert (dx, dy) == (1, -1)


def test_clamp_move_already_in_range(beast):
    dx, dy = beast._clamp_move(1, -2, max_step=2)
    assert (dx, dy) == (1, -2)
