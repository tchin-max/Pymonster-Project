from pymonster import utils
from pymonster.beast import Beast

# Test: _is_safe_move


def test_is_safe_move_no_other_beasts(beast):
    # GLOBAL_BEAST_LIST kommt aus Fixture: [beast]
    assert beast._is_safe_move((1, 0)) is True
    assert beast._is_safe_move((-1, 0)) is True


def test_is_safe_move_collision_with_other_beast(beast):
    # zweites Beast, das genau auf das Zielfeld von move=(1,0) kommt
    other = Beast()
    other.set_id(2)

    # unser Beast sitzt bei (10,10), move (1,0) -> (11,10)
    beast.set_abs_x(10)
    beast.set_abs_y(10)
    other.set_abs_x(11)
    other.set_abs_y(10)

    utils.GLOBAL_BEAST_LIST = [beast, other]

    assert beast._is_safe_move((1, 0)) is False  # kollidiert
    assert beast._is_safe_move((-1, 0)) is True  # andere Richtung ist safe
