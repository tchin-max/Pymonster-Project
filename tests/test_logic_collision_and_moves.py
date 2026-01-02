"""Tests für Kollisionslogik und Move-Auswahl in 
logic.check_beast_collision und logic.valid_first_move."""

import pytest

from pymonster import logic, beast, utils


# --- check_beast_collision ---------------------------------------------------


def test_check_beast_collision_no_other_beasts(monkeypatch):
    """Prüft, dass ohne andere Beasts keine Kollision erkannt wird."""
    monkeypatch.setattr(logic.utils, "GLOBAL_BEAST_LIST", [], raising=False)

    move = (1, 1)
    abs_x = 0
    abs_y = 0
    result = logic.check_beast_collision(move, abs_x, abs_y)
    assert result is True


def test_check_beast_collision_direct_hit(monkeypatch):
    """Prüft, dass eine Kollision erkannt wird, wenn das Ziel auf einem anderen Beast liegt."""
    beast_tester = beast.Beast()
    beast_tester.set_id(1)
    beast_tester.set_abs_x(1)
    beast_tester.set_abs_y(1)

    monkeypatch.setattr(
        logic.utils, "GLOBAL_BEAST_LIST", [beast_tester], raising=False
    )

    move = (1, 1)
    abs_x, abs_y = 0, 0

    result = logic.check_beast_collision(move, abs_x, abs_y)
    assert result is False  # Kollision mit Beast bei (1,1)


def test_check_beast_collision_with_wrap(monkeypatch):
    """Prüft, dass auch nach Wrap am Spielfeldrand eine Kollision erkannt wird."""
    # Beast steht bei MIN_ABS_X,0
    beast_tester = beast.Beast()
    beast_tester.set_id(1)
    beast_tester.set_abs_x(logic.MIN_ABS_X)
    beast_tester.set_abs_y(0)

    monkeypatch.setattr(
        utils, "GLOBAL_BEAST_LIST", [beast_tester], raising=False
    )

    # wir stehen am rechten Rand und bewegen uns +1 nach rechts -> wrap auf MIN_ABS_X
    move = (1, 0)
    result = logic.check_beast_collision(move, abs_x=logic.MAX_ABS_X, abs_y=0)

    assert (
        result is False
    )  # wegen Wrap kollidiert es mit Beast bei MIN_ABS_X,0


# --- valid_first_move --------------------------------------------------------


def test_valid_first_move_picks_first_valid(monkeypatch):
    """Prüft, dass der erste kollisionsfreie und günstige Move gewählt wird."""
    # Kollisionen ignorieren -> immer frei
    monkeypatch.setattr(
        logic, "check_beast_collision", lambda move, x, y: True
    )

    sorted_moves = [
        ((1, 0), 10),  # Energiebedarf 1
        ((2, 0), 5),  # Energiebedarf 2
    ]
    current_energy = 1.5

    move, energy, prio = logic.valid_first_move(
        sorted_moves, current_energy, abs_x=0, abs_y=0
    )

    assert move == (1, 0)
    assert energy == pytest.approx(1.0)
    assert prio == 10


def test_valid_first_move_skips_too_expensive(monkeypatch):
    """Prüft, dass zu teure Moves übersprungen und günstigere gewählt werden."""
    monkeypatch.setattr(
        logic, "check_beast_collision", lambda move, x, y: True
    )

    sorted_moves = [
        ((2, 0), 10),  # Energie 2
        ((1, 0), 5),  # Energie 1
    ]
    current_energy = 1.5

    move, energy, prio = logic.valid_first_move(
        sorted_moves, current_energy, abs_x=0, abs_y=0
    )

    assert move == (1, 0)
    assert energy == pytest.approx(1.0)
    assert prio == 5


def test_valid_first_move_skips_zero_move(monkeypatch):
    """Prüft, dass der (0,0)-Move übersprungen wird, auch wenn er günstig ist."""
    monkeypatch.setattr(
        logic, "check_beast_collision", lambda move, x, y: True
    )

    sorted_moves = [
        ((0, 0), 10),
        ((1, 1), 7),
    ]
    current_energy = 10.0

    move, energy, prio = logic.valid_first_move(
        sorted_moves, current_energy, abs_x=0, abs_y=0
    )

    assert move == (1, 1)
    assert energy == pytest.approx((2**0.5))
    assert prio == 7


def test_valid_first_move_returns_default_if_none_valid(monkeypatch):
    """Prüft, dass (0,0) zurückgegeben wird, wenn alle Moves kollidieren."""
    # Kollision überall
    monkeypatch.setattr(
        logic, "check_beast_collision", lambda move, x, y: False
    )

    sorted_moves = [((1, 0), 10)]
    current_energy = 100.0

    move, energy, prio = logic.valid_first_move(
        sorted_moves, current_energy, abs_x=0, abs_y=0
    )

    assert move == (0, 0)
    assert energy == 0.0
    assert prio == 0
