import pytest
from src.vector_clock import VectorClock, happens_before, compare_vectors


def test_increment_copy_and_update():
    clock = VectorClock(3)
    clock.increment(1)
    copied = clock.copy()
    copied.update([2, 0, 4])
    assert clock.values == [0, 1, 0]
    assert copied.values == [2, 1, 4]


def test_happens_before_and_concurrency():
    assert happens_before([1, 0, 0], [1, 1, 0])
    assert not happens_before([1, 1, 0], [1, 0, 0])
    assert compare_vectors([1, 0, 0], [0, 1, 0]) == "CONCURRENT"
    assert compare_vectors([1, 0, 0], [1, 0, 0]) == "EQUAL"


def test_bad_vector_length():
    with pytest.raises(ValueError):
        VectorClock(3, [1, 2])
    with pytest.raises(ValueError):
        happens_before([1], [1, 2])
