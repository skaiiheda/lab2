"""Версионируемое key-value хранилище и стратегии разрешения конфликтов."""

from dataclasses import dataclass
from typing import Any, Callable
from .vector_clock import compare_vectors


@dataclass
class VersionedValue:
    value: Any
    vector_clock: list[int]
    updated_order: int = 0


@dataclass
class PutResult:
    key: str
    value: Any
    vector_clock: list[int]
    conflict: bool
    strategy: str
    message: str


class VersionedKV:
    """Хранилище с обнаружением конкурентных версий.

    LWW выбирает последнее полученное обновление. Merge складывает числа
    или соединяет строки через '|'. Вектор итоговой версии — покомпонентный
    максимум конфликтующих векторов.
    """

    def __init__(self, strategy: str = "LWW") -> None:
        if strategy not in {"LWW", "MERGE"}:
            raise ValueError("Стратегия должна быть LWW или MERGE")
        self.strategy = strategy
        self._data: dict[str, VersionedValue] = {}
        self._order = 0
        self.history: list[PutResult] = []

    def get(self, key: str) -> VersionedValue | None:
        item = self._data.get(key)
        return None if item is None else VersionedValue(item.value, item.vector_clock.copy(), item.updated_order)

    @staticmethod
    def _merge_values(a: Any, b: Any) -> Any:
        if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
            return a + b
        if isinstance(a, str) and isinstance(b, str):
            return f"{a}|{b}"
        raise TypeError("Merge поддерживает только два числа или две строки одного типа")

    @staticmethod
    def _merge_vectors(a: list[int], b: list[int]) -> list[int]:
        if len(a) != len(b):
            raise ValueError("Размеры векторов не совпадают")
        return [max(x, y) for x, y in zip(a, b)]

    def put(self, key: str, value: Any, vector_clock: list[int]) -> PutResult:
        if not key:
            raise ValueError("Ключ не должен быть пустым")
        if not vector_clock or any(not isinstance(v, int) or v < 0 for v in vector_clock):
            raise ValueError("Вектор должен содержать неотрицательные целые числа")
        self._order += 1
        current = self._data.get(key)
        if current is None:
            self._data[key] = VersionedValue(value, vector_clock.copy(), self._order)
            result = PutResult(key, value, vector_clock.copy(), False, self.strategy, "Создана первая версия")
        else:
            relation = compare_vectors(current.vector_clock, vector_clock)
            if relation == "BEFORE":
                # Новая версия причинно позже текущей.
                self._data[key] = VersionedValue(value, vector_clock.copy(), self._order)
                result = PutResult(key, value, vector_clock.copy(), False, self.strategy, "Принята более новая причинная версия")
            elif relation in {"AFTER", "EQUAL"}:
                # Запоздавшая старая версия игнорируется; равная версия не меняет значение.
                result = PutResult(key, current.value, current.vector_clock.copy(), False, self.strategy,
                                   "Обновление устарело или имеет ту же версию; текущее значение сохранено")
            else:
                merged_clock = self._merge_vectors(current.vector_clock, vector_clock)
                if self.strategy == "LWW":
                    # Порядок получения используется как детерминированная замена физического времени.
                    self._data[key] = VersionedValue(value, merged_clock, self._order)
                    result = PutResult(key, value, merged_clock.copy(), True, self.strategy,
                                       "Обнаружен конфликт; победило последнее полученное обновление")
                else:
                    merged_value = self._merge_values(current.value, value)
                    self._data[key] = VersionedValue(merged_value, merged_clock, self._order)
                    result = PutResult(key, merged_value, merged_clock.copy(), True, self.strategy,
                                       "Обнаружен конфликт; значения объединены")
        self.history.append(result)
        return result
