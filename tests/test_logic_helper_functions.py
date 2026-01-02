"""Tests für reine Helper-Funktionen in logic.py 
(Filter, Dict-Merging, Energieberechnung und Wrapping)."""

import numpy as np
import pytest

from pymonster import logic


# --- filter_valid_moves ------------------------------------------------------


def test_filter_valid_moves_empty_list():
    """Prüft, dass bei leerer Eingabe ein leeres (0,2)-Array zurückkommt."""
    numpy_food_list = []
    numpy_food_list = np.array(numpy_food_list)
    result = logic.filter_valid_moves(numpy_food_list)
    assert result.shape == (0, 2)
    assert result.dtype == np.int_


def test_filter_valid_moves_filters_outside_limit_default():
    """Prüft, dass Moves mit Betrag >= limit (Standard=3) 
    herausgefiltert werden."""
    numpy_food_list = np.array(
        [(0, 0), (2, 1), (3, 0), (-3, -1), (1, -2), (4, 0)], dtype=int
    )
    result = logic.filter_valid_moves(numpy_food_list)
    expected = np.array([[0, 0], [2, 1], [1, -2]], dtype=int)
    assert np.array_equal(result, expected)


def test_filter_valid_moves_custom_limit():
    """Prüft, dass bei höherem limit=5 auch größere Schritte erlaubt bleiben."""
    numpy_food_list = np.array([(0, 0), (4, 0), (3, 3), (-4, -1)], dtype=int)
    # limit=5 macht für unsere Anwendung kein Sinn, aber soll trotzdem aus
    # Funktionalitätsgründen geprüft werden.
    result = logic.filter_valid_moves(numpy_food_list, limit=5)
    # jetzt gilt |x| < 5 -> 4/3 sind noch ok, -4 auch
    expected = np.array([[0, 0], [4, 0], [3, 3], [-4, -1]], dtype=int)
    assert np.array_equal(result, expected)


def test_filter_valid_moves_all_within_limit():
    """Prüft, dass bei limit=3 alle Moves mit Werten 0..2 unverändert durchgehen."""
    numpy_food_list = np.array([(0, 0), (2, 1), (1, 2), (2, 2)], dtype=int)
    result = logic.filter_valid_moves(numpy_food_list, limit=3)
    expected = np.array([(0, 0), (2, 1), (1, 2), (2, 2)], dtype=int)
    assert np.array_equal(result, expected)


# --- array_to_dict -----------------------------------------------------------


def test_array_to_dict_basic():
    """Prüft, dass aus einem Array ein Dict mit absteigenden Prioritäten entsteht."""
    numpy_food_list = np.array([(1, 2), (0, 1)], dtype=int)
    prio_start = 5

    result = logic.array_to_dict(numpy_food_list, prio_start)

    assert result == {(1, 2): 5, (0, 1): 4}


def test_array_to_dict_empty_array():
    """Prüft, dass bei leerem Array ein leeres Dict zurückgegeben wird."""
    numpy_food_list = np.array([])
    result = logic.array_to_dict(numpy_food_list, 10)
    assert not result


# --- merge_dict --------------------------------------------------------------


def test_merge_dict_merges_and_sums_priorities():
    """Prüft, dass mehrere Dicts gemergt und Prioritäten aufaddiert werden."""
    d1 = {(0, 0): 5, (1, 0): 4}
    d2 = {(1, 0): 10, (0, 1): 9}
    d3 = {(0, 0): 2}

    merged = logic.merge_dict(d1, d2, d3)

    assert merged[(0, 0)] == 5 + 2
    assert merged[(1, 0)] == 4 + 10
    assert merged[(0, 1)] == 9
    assert len(merged) == 3


def test_merge_dict_with_empty_dicts():
    """Prüft, dass leere Dicts beim Mergen korrekt ignoriert werden."""
    d1 = {}
    d2 = {(1, 1): 10}
    merged = logic.merge_dict(d1, d2)
    assert merged == {(1, 1): 10}


# --- calc_move_energy --------------------------------------------------------


def test_calc_move_energy_2_1_triangle():
    """Prüft, dass für (2,1) korrekt die Hypotenuse 5.0 berechnet wird."""
    energy = logic.calc_move_energy((2, 1))
    assert energy == pytest.approx(2.23)


def test_calc_move_energy_zero_move():
    """Prüft, dass für den Null-Move (0,0) die Energie 0.0 ist."""
    energy = logic.calc_move_energy((0, 0))
    assert energy == 0.0


# --- wrap_centered -----------------------------------------------------------


def test_wrap_centered_inside_interval():
    """Prüft, dass Werte im Intervall [-2,2] unverändert bleiben."""
    # [-2, 2]
    assert logic.wrap_centered(0, -2, 2) == 0
    assert logic.wrap_centered(1, -2, 2) == 1
    assert logic.wrap_centered(-1, -2, 2) == -1


def test_wrap_centered_wraps_positive_overflow():
    """Prüft, dass positive Überläufe im Intervall [-2,2] korrekt gewrapped werden."""
    # Interval [-2, 2], span = 5
    # 3 -> -2
    assert logic.wrap_centered(3, -2, 2) == -2
    # 4 -> -1
    assert logic.wrap_centered(4, -2, 2) == -1
    # 5 -> 0
    assert logic.wrap_centered(5, -2, 2) == 0


def test_wrap_centered_wraps_negative_overflow():
    """Prüft, dass negative Überläufe im Intervall [-2,2] korrekt gewrapped werden."""
    # Interval [-2, 2], span = 5
    # -3 -> 2
    assert logic.wrap_centered(-3, -2, 2) == 2
    # -4 -> 1
    assert logic.wrap_centered(-4, -2, 2) == 1


# --- wrap_abs_coords ---------------------------------------------------------


def test_wrap_abs_coords_inside_field():
    """Prüft, dass (0,0) im Spielfeld unverändert bleibt."""
    x, y = logic.wrap_abs_coords(0, 0)
    assert x == 0
    assert y == 0


def test_wrap_abs_coords_wraps_x():
    """Prüft, dass x außerhalb des Feldes korrekt horizontal gewrapped wird."""
    # MAX_ABS_X = 35, MIN_ABS_X = -35
    x, y = logic.wrap_abs_coords(logic.MAX_ABS_X + 1, 0)
    assert x == logic.MIN_ABS_X  # 36 -> -35
    assert y == 0


def test_wrap_abs_coords_wraps_y():
    """Prüft, dass y außerhalb des Feldes korrekt vertikal gewrapped wird."""
    # MAX_ABS_Y = 16, MIN_ABS_Y = -17
    x, y = logic.wrap_abs_coords(0, logic.MIN_ABS_Y - 1)
    # -18 -> 16
    assert x == 0
    assert y == logic.MAX_ABS_Y
