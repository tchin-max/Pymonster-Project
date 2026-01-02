"""Tests für Rollen-Presets und die rollenbasierte Auswahlfunktion in controller
 (ROLE_CONFIGS und choose_role_by_score)."""

from pymonster import controller


def test_role_configs_structure():
    """Prüft, dass ROLE_CONFIGS alle erwarteten Rollen und Keys enthält."""
    expected_roles = {"farmer", "hunter", "backbag"}
    assert set(controller.ROLE_CONFIGS.keys()) == expected_roles

    for role, cfg in controller.ROLE_CONFIGS.items():
        # Jede Rolle muss diese Schlüssel haben
        for key in ("food", "hunt", "kill", "escape", "energy"):
            assert key in cfg, f"Key '{key}' fehlt in ROLE_CONFIGS['{role}']"
            # einfache Plausibilitätschecks
            if key != "energy":
                assert isinstance(cfg[key], int)
            else:
                assert isinstance(cfg[key], float)


# Zufälle sind nicht testbar daher werden ganz elegant die Codestellen mit
# random-Anwendung durch eine fake Funktion mithilfe monkeypatching manipuliert. 
# Änderung liegt nur im Scope unseren tests.
# Danach wird monkeypatching die Funktionalitäten des alten Codes zurückführen.

def test_choose_role_by_score_low_uses_backbag_heavy_weights(monkeypatch):
    """Prüft, dass bei niedrigem Score (<1.25) die Backbag-Rolle stark gewichtet wird."""
    captured = {}

    def fake_choices(population, weights=None, k=None):
        captured["population"] = population
        captured["weights"] = weights
        captured["k"] = k
        # egal, was zurückkommt – wir wollen nur die übergebenen Parameter testen
        return [population[0]]

    monkeypatch.setattr(controller.random, "choices", fake_choices)

    role = controller.choose_role_by_score(1.0)

    assert role in {"farmer", "hunter", "backbag"}
    assert captured["population"] == ["farmer", "hunter", "backbag"]
    assert captured["weights"] == [0.2, 0.1, 0.7]
    assert captured["k"] == 1


def test_choose_role_by_score_mid_uses_mixed_weights(monkeypatch):
    """Prüft, dass bei mittlerem Score (>=1.25 und <2.5) eine
     gemischte Gewichtung verwendet wird."""
    captured = {}

    def fake_choices(population, weights=None, k=None):
        captured["population"] = population
        captured["weights"] = weights
        captured["k"] = k
        return [population[1]]  # egal, wir testen nur Argumente

    monkeypatch.setattr(controller.random, "choices", fake_choices)

    role = controller.choose_role_by_score(2.0)

    assert role in {"farmer", "hunter", "backbag"}
    assert captured["population"] == ["farmer", "hunter", "backbag"]
    assert captured["weights"] == [0.40, 0.30, 0.30]
    assert captured["k"] == 1


def test_choose_role_by_score_high_uses_hunter_heavy_weights(monkeypatch):
    """Prüft, dass bei hohem Score (>=2.5) Hunter am stärksten gewichtet wird."""
    captured = {}

    def fake_choices(population, weights=None, k=None):
        captured["population"] = population
        captured["weights"] = weights
        captured["k"] = k
        return [population[1]]

    monkeypatch.setattr(controller.random, "choices", fake_choices)

    role = controller.choose_role_by_score(3.0)

    assert role in {"farmer", "hunter", "backbag"}
    assert captured["population"] == ["farmer", "hunter", "backbag"]
    assert captured["weights"] == [0.4, 0.5, 0.1]
    assert captured["k"] == 1
