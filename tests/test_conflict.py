import pytest
from src.versioned_kv import VersionedKV


def test_lww_detects_concurrent_update_and_keeps_last_received():
    store = VersionedKV("LWW")
    store.put("x", 0, [0, 0, 0])
    store.put("x", 1, [1, 0, 0])
    result = store.put("x", 0, [0, 1, 0])
    assert result.conflict
    assert result.value == 0
    assert result.vector_clock == [1, 1, 0]


def test_merge_sums_numbers():
    store = VersionedKV("MERGE")
    store.put("x", 0, [0, 0, 0])
    store.put("x", 1, [1, 0, 0])
    result = store.put("x", 0, [0, 1, 0])
    assert result.conflict
    assert result.value == 1
    assert result.vector_clock == [1, 1, 0]


def test_merge_joins_strings():
    store = VersionedKV("MERGE")
    store.put("status", "new", [1, 0, 0])
    result = store.put("status", "checked", [0, 1, 0])
    assert result.value == "new|checked"


def test_causally_newer_version_replaces_old():
    store = VersionedKV("LWW")
    store.put("x", 1, [1, 0, 0])
    result = store.put("x", 2, [2, 0, 0])
    assert not result.conflict
    assert store.get("x").value == 2


def test_merge_rejects_incompatible_types():
    store = VersionedKV("MERGE")
    store.put("x", 1, [1, 0])
    with pytest.raises(TypeError):
        store.put("x", "two", [0, 1])
