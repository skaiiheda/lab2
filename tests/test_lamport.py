import pytest
from src.lamport_clock import LamportClock


def test_increment():
    clock = LamportClock()
    assert clock.increment() == 1
    assert clock.increment() == 2


def test_update_uses_max_plus_one():
    clock = LamportClock(4)
    assert clock.update(7) == 8
    assert clock.update(2) == 9


def test_negative_values_rejected():
    with pytest.raises(ValueError):
        LamportClock(-1)
    with pytest.raises(ValueError):
        LamportClock().update(-1)
