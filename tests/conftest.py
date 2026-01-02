# tests/conftest.py
import pytest
from pymonster.beast import Beast
from pymonster import utils


@pytest.fixture
def beast():
    """Standard-Beast-Fixure, die in vielen Tests wiederverwendet wird."""
    b = Beast()
    b.set_id(1)
    b.set_energy(100.0)
    b.set_abs_x(10)
    b.set_abs_y(10)

    # Standard: nur dieses Beast ist aktiv
    utils.GLOBAL_BEAST_LIST = [b]
    return b


def fill49(s: str) -> str:
    """Füllt einen Environment-String auf exakt 49 Zeichen auf."""
    if len(s) >= 49:
        return s[:49]
    return s + "." * (49 - len(s))
