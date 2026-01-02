import math

# Test: _score_two_step_food & _score_food_moves_with_lookahead


def test_score_two_step_food_basic(beast):
    # m1 = (1,0), future_moves = [(1,0), (0,1)]
    m1 = (1, 0)
    future_moves = [(1, 0), (0, 1)]

    score_direct = beast._score_two_step_food(m1, future_moves, True)
    score_indirect = beast._score_two_step_food(m1, future_moves, False)

    # direkter Treffer hat 1 Food mehr im Score
    assert score_direct > score_indirect


def test_score_food_moves_with_lookahead_prefers_better_future(
    beast, monkeypatch
):
    """
    Wir mocken _simulate_future_environment und _food_moves_in_field,
    um gezielt Scores zu steuern.
    """

    calls = {}

    def fake_simulate_future_environment(move):
        # wir merken uns, dass diese Move simuliert wurde
        calls.setdefault("moves", []).append(move)
        return None  # Inhalt egal, da _food_moves_in_field gemockt wird

    def fake_food_moves_in_field(_field):
        # Abhängig vom zuletzt simulierten Move andere Zukunft
        last_move = calls["moves"][-1]
        if last_move == (1, 0):
            # viele zukünftige Food-Moves
            return [(1, 0), (0, 1), (-1, 0)]
        else:
            # kaum Food in Zukunft
            return [(0, 1)]

    monkeypatch.setattr(
        beast, "_simulate_future_environment", fake_simulate_future_environment
    )
    monkeypatch.setattr(
        beast, "_food_moves_in_field", fake_food_moves_in_field
    )

    moves = [(1, 0), (0, 1)]
    sorted_moves = beast._score_food_moves_with_lookahead(
        moves, is_direct_hit_path=False
    )

    # Move (1,0) hat mehr zukünftiges Futter -> sollte vorne stehen
    assert sorted_moves[0] == (1, 0)
